import os
from flask import Flask, g, send_file, abort, redirect, jsonify, make_response, render_template, request
import sqlite3
import logging
from utils import get_db, get_global
import json


logging.basicConfig(level=logging.INFO)

app = Flask(__name__)

# TODO: arguments or env vars for globals
# TODO: users, authentication
# TODO: fix navigation - annotated vs unannotated, collections, user-owned vs global
# TODO: annotation modes - radial vs simple bounding box vs free polygon
# TODO: text/metadata options - symbols, etc
# TODO: control points
# TODO: add casing detection model and pre-compute detections
# TODO: mouseover polygon color change
# TODO: better db representation of metadata, geometry
# TODO: migrate to jquery/modern widget framework
# TODO: deal with unusual image shapes, enable zoom, panning, etc. tiling very large images
# TODO: double-check replace events are updating the annotation id correctly.
# TODO: adding more images
# TODO: host db online/ migrate to modern/robust db.
# TODO: e2e image processing pipeline/user experience
# TODO: proper RESTful API


@app.teardown_appcontext
def close_connection(exception):
    db = getattr(g, '_database', None)
    if db is not None:
        db.close()


# UI routes 
@app.route("/")
def home():
    return redirect('/annotate/')


@app.route("/annotate/")
@app.route("/annotate/<int:id>")
def annotate(id=None):
    show_annot = request.args.get('show_annot')
    if id is None:
        cur = get_db().cursor()
        if show_annot:
            cur.execute("SELECT MIN(images.img_id) AS id from images")
        else:
            cur.execute("SELECT MIN(images.img_id) AS id from images LEFT OUTER JOIN annotations ON annotations.img_id IS null")
        id = next(cur, [{'id': None}])['id']
    return render_template('annotate.html', id=id)


# maybe this could be a static route to storage?
@app.route("/images/<int:img_id>")
def img(img_id):
    try:
        cur = get_db().cursor()
        cur.execute("SELECT * FROM images WHERE img_id=={}".format(img_id))
        result = next(cur, [None])
        logging.info('Found image {}'.format(result))
        img_home = get_global('img_home')
        logging.info(f'image root {img_home}')
        filename = os.path.join(img_home, result['filename'])
        return send_file(filename, mimetype='image/jpeg')
    except Exception as e:
        abort(404)


# REST methods
@app.route("/images/<int:img_id>/annotations", methods=['GET'])
def get_annotation(img_id):
    cur = get_db().cursor()
    cur.execute("SELECT anno_id, geometry, annotation, metadata FROM annotations WHERE img_id={}".format(img_id))
    columns = [column[0] for column in cur.description]
    results = []
    for row in cur.fetchall():
        row = dict(zip(columns, row))
        row['geometry'] = json.loads(row['geometry'])
        row['metadata'] = json.loads(row['metadata'])
        results.append(row)

    return jsonify(results)


@app.route("/annotations/", methods=['POST'])
def post_annotation():
    req = request.get_json()
    logging.info("POST request: {}".format(req))

    # TODO: validate the payload.
    # TODO: escape quotes and other dangerous chars
    con = get_db()
    cur = con.cursor()
    # anno_id , img_id , geometry , annotation , metadata 
    cmd = "INSERT INTO annotations (anno_id,img_id,geometry,annotation,metadata) VALUES (null, {}, '{}', '{}', '{}')".format(
        req['img_id'], json.dumps(req['geometry']), req['annotation'], json.dumps(req['metadata'])
    )
    logging.info(cmd)
    cur.execute(cmd)
    con.commit()
    cur.execute('SELECT COUNT(*) AS c FROM annotations')
    result = next(cur, [None])['c']
    logging.info('found {} rows'.format(result))
    return jsonify({"message": "Annotation posted", "id": cur.lastrowid})


@app.route("/annotations/<int:anno_id>", methods=['PUT'])
def replace_annotation(anno_id):
    req = request.get_json()
    logging.info("POST replace request: {}".format(req))

    # TODO: validate the payload.
    # TODO: escape quotes and other dangerous chars
    # TODO: change this to an update rather than delete/insert?
    con = get_db()
    cur = con.cursor()
    # anno_id , img_id , geometry , annotation , metadata 
    cmd1 = "DELETE FROM annotations WHERE anno_id={}".format(anno_id)
    cmd = "INSERT INTO annotations (anno_id,img_id,geometry,annotation,metadata) VALUES (null, {}, '{}', '{}', '{}')".format(
        req['img_id'], json.dumps(req['geometry']), req['annotation'], json.dumps(req['metadata'])
    )
    logging.info(cmd1)
    logging.info(cmd)
    cur.execute(cmd1)
    cur.execute(cmd)
    con.commit()
    cur.execute('SELECT COUNT(*) AS c FROM annotations')
    result = next(cur, [None])['c']
    logging.info('found {} rows'.format(result))
    return jsonify({"message": "Annotation posted", "id": cur.lastrowid})


@app.route("/annotations/<int:anno_id>", methods=['DELETE'])
def delete_annotation(anno_id):
    req = request.get_json()
    logging.info("DELETE request: {}".format(req))

    # TODO: validate the payload.    
    con = get_db()
    cur = con.cursor()
    cmd = "DELETE FROM annotations WHERE anno_id={}".format(anno_id)
    logging.info(cmd)
    cur.execute(cmd)
    con.commit()
    return jsonify(success=True)

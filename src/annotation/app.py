import os
from flask import Flask, g, send_file, abort, redirect, jsonify, make_response, render_template, request
import logging
from utils import get_db, get_global
import json
import sqlalchemy as sqldb


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
# TODO: env variable for database URI


# TODO: maybe this should move to utils?
@app.teardown_appcontext
def close_connection(exception):
    db = getattr(g, '_db', None)
    if db is not None:
        db.engine.dispose()
        g._db = None


# UI routes
@app.route("/")
def home():
    return redirect('/annotate/')


@app.route("/annotate/")
@app.route("/annotate/<int:id>")
def annotate(id=None):
    show_annot = request.args.get('show_annot')
    logging.info(f'show_annot: {show_annot} , ({not show_annot}')
    if id is None:
        db = get_db()
        images = db.metadata.tables['images']
        query = sqldb.select([sqldb.func.min(images.c.img_id).label('id')])
        if not show_annot:
            # TODO: this seems broken
            annotations = db.metadata.tables['annotations']
            query = \
                query.select_from(
                    images.outerjoin(
                        annotations,
                        images.c.img_id == annotations.c.img_id)
                ).filter(annotations.c.img_id == None)
        result = db.connection.execute(query).one()
        id = result['id']
    return render_template('annotate.html', id=id)


# maybe this could be a static route to storage?
@app.route("/images/<int:img_id>")
def img(img_id):
    try:
        db = get_db()
        images = db.metadata.tables['images']
        query = sqldb.select(images).where(images.c.img_id == img_id)
        result = db.connection.execute(query).one()
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
    db = get_db()
    annos = db.metadata.tables['annotations']
    query = sqldb.select(
        annos.c.anno_id,
        annos.c.geometry,
        annos.c.annotation,
        annos.c.metadata).where(annos.c.img_id == img_id)
    result = db.connection.execute(query).fetchall()
    results = []
    for row in result:
        row = dict(row)
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
    db = get_db()

    # anno_id , img_id , geometry , annotation , metadata
    annos = db.metadata.tables['annotations']
    result = db.connection.execute(annos.insert(), {
        'img_id': req['img_id'],
        'geometry': json.dumps(req['geometry']),
        'annotation': req['annotation'],
        'metadata': json.dumps(req['metadata'])
    })
    # cur.execute('SELECT COUNT(*) AS c FROM annotations')
    # result = next(cur, [None])['c']
    # logging.info('found {} rows'.format(result))
    return jsonify({
        "message": "Annotation posted",
        "id": result.inserted_primary_key['anno_id']
    })


@app.route("/annotations/<int:anno_id>", methods=['PUT'])
def replace_annotation(anno_id):
    req = request.get_json()
    logging.info("PUT replace request: {}".format(req))

    # TODO: validate the payload.
    # TODO: escape quotes and other dangerous chars
    # TODO: change this to an update rather than delete/insert?
    db = get_db()
    annos = db.metadata.tables['annotations']
    upd = annos.update().where(annos.c.anno_id == anno_id).values(
        {
            'img_id': req['img_id'],
            'geometry': json.dumps(req['geometry']),
            'annotation': req['annotation'],
            'metadata': json.dumps(req['metadata'])
        }
    )
    # TODO: do we need to get/validate the return result?
    db.connection.execute(upd)

    # cur.execute('SELECT COUNT(*) AS c FROM annotations')
    # result = next(cur, [None])['c']
    # logging.info('found {} rows'.format(result))
    return jsonify({"message": "Annotation updated", "id": anno_id})


@app.route("/annotations/<int:anno_id>", methods=['DELETE'])
def delete_annotation(anno_id):
    req = request.get_json()
    logging.info("DELETE request: {}".format(req))

    # TODO: validate the payload.
    db = get_db()
    annos = db.metadata.tables['annotations']
    db.connection.execute(annos.delete().where(annos.c.anno_id == anno_id))
    return jsonify(success=True)

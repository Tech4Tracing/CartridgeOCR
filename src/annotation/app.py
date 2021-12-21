import os
from flask import Flask, g, send_file, abort, redirect, jsonify
import sqlite3
import logging
from utils import get_db, get_global
from flask import render_template, request

logging.basicConfig(level=logging.INFO)

app = Flask(__name__)

# TODO: arguments or env vars for globals
# TODO: users, authentication
# TODO: fix navigation
# TODO: annotation modes
# TODO: List polygons
# TODO: control points
# TODO: capture, list annotations
# TODO: add model and detections

@app.teardown_appcontext
def close_connection(exception):
    db = getattr(g, '_database', None)
    if db is not None:
        db.close()

@app.route("/")
def home():
    return redirect('/annotate/')


@app.route("/img/<id>")
def img(id):
    try:
        cur = get_db().cursor()
        cur.execute("SELECT * FROM images WHERE img_id=={}".format(id))
        result = next(cur, [None])
        logging.info('Found image {}'.format(result))
        img_home = get_global('img_home')
        logging.info('image root {}'.format(img_home))
        filename = os.path.join(img_home, result['filename'])
        return send_file(filename, mimetype='image/jpeg')
    except Exception as e:
        abort(404)


@app.route("/annotations/<int:img_id>")
def annotations(img_id):
    cur = get_db().cursor()
    cur.execute("SELECT anno_id, geometry, annotation, metadata FROM annotations WHERE img_id={}".format(img_id))
    return jsonify(cur.fetchall())


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
        id = next(cur, [{'id':None}])['id']
    return render_template('annotate.html', id=id)

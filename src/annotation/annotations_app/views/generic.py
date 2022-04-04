import json
import logging
import os

import sqlalchemy as sqldb
from flask import send_file, abort, redirect, jsonify, render_template, request
from flask_login import current_user, login_required

from annotations_app import app

from annotations_app.utils import get_db, get_global, parse_boolean, db_session


@app.route("/")
def index():
    if current_user.is_authenticated:
        return redirect('/annotate/')
    else:
        return render_template('unauth.html')


@app.route("/annotate/")
@app.route("/annotate/<string:annotation_id>")
@login_required
def annotate(annotation_id=None):
    show_annot = parse_boolean(request.args.get('show_annot', False))
    logging.info('show_annot: %s (%s) for %s', annotation_id, show_annot, current_user)
    if annotation_id is None:
        db = get_db()
        images = db.metadata.tables['images']
        query = sqldb.select([sqldb.func.min(images.c.id).label('id')])
        if not show_annot:
            annotations = db.metadata.tables['annotations']
            query = \
                query.select_from(
                    images.outerjoin(
                        annotations,
                        images.c.id == annotations.c.img_id)
                ).filter(annotations.c.img_id == None)
        result = db.connection.execute(query).one()
        annotation_id = result['id']
    return render_template('annotate.html', id=annotation_id, name=current_user.name.split(' ')[0])


@app.route('/annotate/prev/<int:id>')
@login_required
def prev_image(id):
    """Move to the previous image to `id`. If show_annot is false,
    it will be the first image < `id` which is not annotated."""
    nav_annot = parse_boolean(request.cookies.get('show_annot', False))
    logging.info(f'prev: {id} , ({nav_annot})')
    db = get_db()
    images = db.metadata.tables['images']
    query = sqldb.select([sqldb.func.max(images.c.id).label('id')]).where(images.c.id < id)
    if not nav_annot:
        annotations = db.metadata.tables['annotations']
        query = \
            query.select_from(
                images.outerjoin(
                    annotations,
                    images.c.id == annotations.c.img_id)
            ).filter(annotations.c.img_id == None)
    result = db.connection.execute(query).one_or_none()
    if result is not None:
        id = result['id']
    return annotate(id)


@app.route('/annotate/next/<int:id>')
@login_required
def next_image(id):
    """Move to the next image after `id`. If show_annot is false,
    it will be the first image > `id` which is not annotated."""
    nav_annot = parse_boolean(request.cookies.get('show_annot', False))
    logging.info(f'prev: {id} , ({nav_annot})')
    db = get_db()
    images = db.metadata.tables['images']
    query = sqldb.select([sqldb.func.min(images.c.id).label('id')]).where(images.c.id > id)
    if not nav_annot:
        annotations = db.metadata.tables['annotations']
        query = \
            query.select_from(
                images.outerjoin(
                    annotations,
                    images.c.id == annotations.c.img_id)
            ).filter(annotations.c.img_id == None)
    result = db.connection.execute(query).one_or_none()
    if result is not None:
        id = result['id']
    return annotate(id)


# TODO: deprecated 
# maybe this could be a static route to storage?
@app.route("/images/<string:img_id>")
@login_required
def img(img_id):
    try:
        db = get_db()
        images = db.metadata.tables['images']
        query = sqldb.select(images).where(images.c.id == img_id)
        result = db.connection.execute(query).one()
        logging.info('Found image {}'.format(result))
        img_home = get_global('img_home')
        logging.info(f'image root {img_home}')
        filename = os.path.join(img_home, result['filename'])
        return send_file(filename, mimetype='image/jpeg')
    except Exception as e:
        print(e)
        abort(404)


import logging
import os

import sqlalchemy as sqldb
from flask import send_file, abort, render_template, request
from flask_login import current_user, login_required
# from flask import render_template
# from flask_login import current_user

from annotations_app.flask_app import app
from annotations_app.models.base import ImageCollection, Image
from annotations_app.utils import get_db, get_global, parse_boolean, db_session


# @app.route("/")
# def index():
#     if current_user.is_authenticated:
#         return redirect("/annotate/")
#     else:
#         return render_template("unauth.html")


# the react widget catch-all page (apart of other existing endpoints like API)
@app.route('/', defaults={'path': ''})
@app.route('/<path:path>')
def index(path):
    if current_user.is_authenticated:
        return render_template("ui/index.html")
    else:
        return render_template("unauth.html")


# TODO: update to use the ORM model.
@app.route("/old/annotate/")
@app.route("/old/annotate/<string:image_id>")
@login_required
def annotate(image_id=None):
    show_annot = parse_boolean(request.args.get("show_annot", False))
    logging.info("show_annot: %s (%s) for %s", image_id, show_annot, current_user)
    if image_id is None:
        db = get_db()
        images = db.metadata.tables["images"]
        query = sqldb.select([sqldb.func.min(images.c.id).label("id")])
        if not show_annot:
            annotations = db.metadata.tables["annotations"]
            query = query.select_from(
                images.outerjoin(annotations, images.c.id == annotations.c.image_id)
            ).filter(annotations.c.image_id == None)
        result = db.connection.execute(query).one()
        image_id = result["id"]

    return render_template(
        "annotate.html",
        id=image_id,
        current_user=current_user,
    )


@app.route("/old/annotate/<string:id>/prev")
@login_required
def prev_image(id):
    """Move to the previous image to `id`. If show_annot is false,
    it will be the first image < `id` which is not annotated."""
    nav_annot = parse_boolean(request.cookies.get("show_annot", False))
    logging.info(f"prev: {id} , ({nav_annot})")
    db = get_db()
    images = db.metadata.tables["images"]
    query = sqldb.select([sqldb.func.max(images.c.id).label("id")]).where(
        images.c.id < id
    )
    if not nav_annot:
        annotations = db.metadata.tables["annotations"]
        query = query.select_from(
            images.outerjoin(annotations, images.c.id == annotations.c.image_id)
        ).filter(annotations.c.image_id == None)
    result = db.connection.execute(query).one_or_none()
    if result is not None:
        id = result["id"]
    return annotate(id)


@app.route("/old/annotate/<string:id>/next")
@login_required
def next_image(id):
    """Move to the next image after `id`. If show_annot is false,
    it will be the first image > `id` which is not annotated."""
    nav_annot = parse_boolean(request.cookies.get("show_annot", False))
    logging.info(f"prev: {id} , ({nav_annot})")
    db = get_db()
    images = db.metadata.tables["images"]
    query = sqldb.select([sqldb.func.min(images.c.id).label("id")]).where(
        images.c.id > id
    )
    if not nav_annot:
        annotations = db.metadata.tables["annotations"]
        query = query.select_from(
            images.outerjoin(annotations, images.c.id == annotations.c.image_id)
        ).filter(annotations.c.image_id == None)
    result = db.connection.execute(query).one_or_none()
    if result is not None:
        id = result["id"]
    return annotate(id)


# TODO: deprecated
# maybe this could be a static route to storage?
@app.route("/old/images/<string:image_id>")
@login_required
def img(image_id):
    try:
        db = get_db()
        images = db.metadata.tables["images"]
        query = sqldb.select(images).where(images.c.id == image_id)
        result = db.connection.execute(query).one()
        logging.info("Found image {}".format(result))
        img_home = get_global("img_home")
        logging.info(f"image root {img_home}")
        filename = os.path.join(img_home, result["filename"])
        return send_file(filename, mimetype="image/jpeg")
    except Exception as e:
        print(e)
        abort(404)


@app.route("/old/collections/")
@app.route("/old/collections/<string:collection_id>/")
@app.route("/old/collections/<string:collection_id>/<int:page>")
@login_required
def collections(collection_id=None, page=0):
    from math import ceil

    page_size = 25
    with db_session() as db:
        collections = db.query(ImageCollection).filter(
            ImageCollection.user_id == current_user.id,
        )
        images = None
        collection_name = None
        # TODO: enforce a sort order for paging?
        if collection_id is not None:
            images = (
                db.query(Image)
                .filter(
                    Image.collections.any(
                        sqldb.and_(
                            ImageCollection.id == collection_id,
                            ImageCollection.user_id == current_user.id,
                        )
                    )
                )
                .order_by(Image.created_at)
            )
            collection_name = (
                db.query(ImageCollection)
                .filter(ImageCollection.id == collection_id)
                .first()
                .name
            )
        total_pages = ceil(images.count() / page_size) if images else 0
        images = images[page * page_size: (page + 1) * page_size] if images else []
        return render_template(
            "collections.html",
            collection_name=collection_name,
            collection_id=collection_id,
            collection_list=collections,
            image_list=images,
            pages=total_pages,
            page=page,
        )

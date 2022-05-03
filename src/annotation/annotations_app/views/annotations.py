import json

from flask import request, abort
from flask_login import login_required, current_user

from annotations_app.flask_app import app, db as new_db
from annotations_app import schemas
from annotations_app.config import logging
from annotations_app.models.base import ImageCollection, Image, Annotation
from annotations_app.utils import db_session
from sqlalchemy import and_


@app.route("/api/v0/annotations", methods=["GET"])
@login_required
def annotations_list():
    """List of annotations for a given user/collection/image
    ---
    get:
      parameters:
        - in: query
          name: collection_id
          schema:
            type: string
          required: false
          description: Unique collection ID
        - in: query
          name: image_id
          schema:
            type: string
          required: false
          description: Unique image ID in the specified collection
      responses:
        200:
          description: List of all annotations for the given user/collection/image, depending on specificity
          content:
            application/json:
              schema: AnnotationListSchema
    """
    with db_session() as db:
        # TODO: add 404s for collection or image mismatch
        args = request.args
        image_id = args.get("image_id")
        collection_id = args.get("collection_id")

        logging.info(
            f"GET annotations collection_id: {collection_id} image_id: {image_id}"
        )
        queryset = db.query(Annotation).filter(
            and_(
                Image.id == image_id if image_id is not None else True,
                Annotation.image_id == Image.id,
                Image.collections.any(
                    and_(
                        ImageCollection.id == collection_id
                        if collection_id is not None
                        else True,
                        ImageCollection.user_id == current_user.id,
                    )
                ),
            )
        )

        total = queryset.count()
        results = queryset.order_by(
            "id"
        )  # TODO: this will re-order the display order of the annotations.

        return schemas.AnnotationListSchema().dump(
            {
                "total": total,
                "annotations": results,
            }
        )


# TODO: geometry and metadata types
# TODO: multipart/form request?
@app.route("/api/v0/annotations", methods=["POST"])
@login_required
def annotation_post():
    """Upload annotation to collection (or without one)
    ---
    post:
        requestBody:
          content:
            application/json:
              schema:
                type: object
                properties:
                  image_id:
                    type: string
                  geometry:
                    type: object
                  annotation:
                    type: string
                  metadata_:
                    type: object
        responses:
            201:
              description: Details about the created annotation
              content:
                application/json:
                  schema: AnnotationDisplaySchema
    """
    logging.info("Uploading annotation for user %s", current_user.id)

    with db_session() as db:
        req = request.get_json()
        image_id = req["image_id"] if "image_id" in req else None

        if not image_id:
            abort(404)

        image_in_db = (
            db.query(Image)
            .filter(
                Image.id == image_id,
                Image.collections.any(ImageCollection.user_id == current_user.id),
            )
            .first()
        )

        if not image_in_db:
            abort(404)

        # create database object if succesfull

        annotation_in_db = Annotation(
            image_id=image_id,
            geometry=json.dumps(req["geometry"]),
            annotation=req["annotation"],
            metadata_=json.dumps(req["metadata_"]),
        )
        db.add(annotation_in_db)
        db.commit()
        db.refresh(annotation_in_db)
        return schemas.AnnotationDisplaySchema().dump(annotation_in_db)


@app.route("/api/v0/annotations/<string:annotation_id>", methods=["PUT"])
@login_required
def annotation_replace(annotation_id):
    """Replace/update annotation
    ---
    put:
        parameters:
        - in: path
          name: annotation_id
          schema:
            type: string
          required: true
          description: Unique annotation ID
        requestBody:
          content:
            application/json:
              schema:
                type: object
                properties:
                  image_id:
                    type: string
                  geometry:
                    type: object
                  annotation:
                    type: string
                  metadata_:
                    type: object
        responses:
            201:
              description: Details about the updated annotation
              content:
                application/json:
                  schema: AnnotationDisplaySchema
    """
    logging.info("PUT annotation request for user %s", current_user.id)

    # TODO: validate the payload.
    # TODO: escape quotes and other dangerous chars
    with db_session() as db:
        req = request.get_json()
        image_id = req["image_id"] if "image_id" in req else None
        image_in_db = (
            db.query(Image)
            .filter(
                Image.id == image_id,
                Image.collections.any(ImageCollection.user_id == current_user.id),
            )
            .first()
        )

        if not image_in_db:
            abort(404)

        # create database object if succesfull
        # TODO: test/sanity check
        annotation_in_db = (
            db.query(Annotation)
            .filter(
                Annotation.id == annotation_id,
                Image.id == image_id,
                Image.collections.any(ImageCollection.user_id == current_user.id),
            )
            .first()
        )
        if not annotation_in_db:
            abort(404)

        annotation_in_db.geometry = json.dumps(req["geometry"])
        annotation_in_db.annotation = req["annotation"]
        annotation_in_db.metadata_ = json.dumps(req["metadata_"])

        # db.update(annotation_in_db)
        db.commit()
        db.refresh(annotation_in_db)
        return schemas.AnnotationDisplaySchema().dump(annotation_in_db)


@app.route("/api/v0/annotations/<string:annotation_id>", methods=["DELETE"])
@login_required
def annotation_delete(annotation_id):
    """Remove the annotation
    ---
    delete:
      parameters:
        - in: path
          name: annotation_id
          schema:
            type: string
          required: true
          description: Unique annotation ID
      responses:
        202:
          description: Success
    """
    logging.info("DELETE annotation request for user %s", current_user.id)
    # TODO: test/sanity check
    annotation_in_db = (
        new_db.session.query(Annotation)
        .filter(
            Annotation.id == annotation_id,
            Image.id == Annotation.image_id,
            Image.collections.any(ImageCollection.user_id == current_user.id),
        )
        .first()
    )

    if not annotation_in_db:
        abort(404)

    new_db.session.delete(annotation_in_db)
    new_db.session.commit()
    return ("", 204)

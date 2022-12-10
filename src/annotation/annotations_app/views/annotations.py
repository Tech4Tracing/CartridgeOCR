import json

from flask import request, abort
from flask_login import login_required, current_user

from annotations_app.flask_app import app, db as new_db
from annotations_app import schemas
from annotations_app.config import logging
from annotations_app.models.base import ImageCollection, Image, Annotation
from sqlalchemy import and_


@app.route("/api/v0/annotations", methods=["GET"])
@login_required
def annotations_list():
    """List of annotations for a given user/collection/image. This endpoint is not paginated,
    caller is supposed to filter it by collection or image first (or both) to avoid too much
    data transfered
    ---
    get:
      parameters:
        - in: query
          name: collection_id
          schema:
            type: string
          required: false
          description: The collection ID to filter on
        - in: query
          name: image_id
          schema:
            type: string
          required: false
          description: The image ID; if provided only annotations for that image are returned
      responses:
        200:
          description: List of all annotations for the given user/collection/image, depending on specificity
          content:
            application/json:
              schema: AnnotationListSchema
    """
    args = request.args
    image_id = args.get("image_id") or None
    collection_id = args.get("collection_id") or None

    # retrieve image and collection (if requested) just to ensure they exist and visible
    if image_id:
        Image.get_image_or_abort(image_id, current_user)
    if collection_id:
        ImageCollection.get_collection_or_abort(collection_id, current_user)

    this_user_collections = ImageCollection.get_collections_for_user(current_user)

    queryset = new_db.session.query(Annotation).filter(
        and_(
            # filter by image
            Annotation.image_id == image_id if image_id else True,
            # filter by collection (including only collections visible to user if no collection is provided)
            Annotation.image_id == Image.id,
            Image.collection_id.in_(this_user_collections.with_entities(ImageCollection.id).distinct()),
            Image.collection_id == collection_id if collection_id else True,
        )
    )

    total = queryset.count()
    results = queryset.order_by(
        "created_at", "id",
    )

    return schemas.AnnotationListSchema().dump(
        {
            "total": total,
            "annotations": results,
        }
    )


# TODO: geometry and metadata types
@app.route("/api/v0/annotations", methods=["POST"])
@login_required
def annotation_post():
    """Create annotation for image
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

    req = request.get_json()

    image_id = req["image_id"] if "image_id" in req else None
    if not image_id:
        abort(400, description="image_id parameter is required")

    Image.get_image_or_abort(image_id, current_user)  # ensure exists and available

    # create database object if succesfull
    annotation_in_db = Annotation(
        image_id=image_id,
        geometry=json.dumps(req["geometry"]),
        annotation=req["annotation"],
        metadata_=json.dumps(req["metadata_"]),
    )
    new_db.session.add(annotation_in_db)
    new_db.session.commit()
    new_db.session.refresh(annotation_in_db)
    return schemas.AnnotationDisplaySchema().dump(annotation_in_db), 201


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
    req = request.get_json()

    image_id = req["image_id"] if "image_id" in req else None
    if not image_id:
        abort(400, description="image_id parameter is required")

    Image.get_image_or_abort(image_id, current_user)  # ensure exists and available

    # retrieve existing annotation object
    # TODO: test/sanity check
    annotation_in_db = (
        new_db.session.query(Annotation)
        .filter(
            Annotation.id == annotation_id,
            Image.id == image_id,
            # don't need image access filter while checked above
        )
        .first()
    )
    if not annotation_in_db:
        abort(404)

    annotation_in_db.geometry = json.dumps(req["geometry"])
    annotation_in_db.annotation = req["annotation"]
    annotation_in_db.metadata_ = json.dumps(req["metadata_"])
    new_db.session.commit()
    new_db.session.refresh(annotation_in_db)
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
        204:
          description: Success
    """
    logging.info("DELETE annotation request for user %s", current_user.id)
    # TODO: test/sanity check
    this_user_collections = ImageCollection.get_collections_for_user(current_user)

    annotation_in_db = (
        new_db.session.query(Annotation)
        .filter(
            Annotation.id == annotation_id,
            Image.id == Annotation.image_id,
            Image.collection_id.in_(this_user_collections.with_entities(ImageCollection.id).distinct()),
        )
        .first()
    )

    if not annotation_in_db:
        abort(404)

    new_db.session.delete(annotation_in_db)
    new_db.session.commit()
    return ("", 204)

import mimetypes
from io import BytesIO

from flask import request, send_file, redirect
from flask_login import login_required, current_user

from annotations_app.flask_app import app, db
from annotations_app import schemas
from annotations_app.config import logging
from annotations_app.models.base import ImageCollection, Image, Annotation
from annotations_app.repos.azure_storage_provider import (
    AzureStorageProvider as StorageProvider,
)


@app.route("/api/v0/images", methods=["POST"])
@login_required
def image_post():
    """Upload image to collection (or without one)
    ---
    post:
        requestBody:
          content:
            multipart/form-data:
              schema:
                type: object
                properties:
                  collection_id:
                    type: string
                  mimetype:
                    type: string
                  file:
                    type: string
                    format: binary
        responses:
            201:
              description: Details about the created image
              content:
                application/json:
                  schema: ImageDisplaySchema
    """
    logging.info("Uploading image for user %s", current_user.id)
    if "file" not in request.files or not request.files["file"].filename:
        return (
            schemas.Errors().dump(
                {"errors": [{"title": "ValidationError", "detail": "No file provided"}]}
            ),
            400,
        )

    # ensure collection exists and retrieve it
    collection_id = request.form.get("collection_id")
    collection_in_db = None
    if not collection_id:
        # use default collection (which shall be created if doesn't exist)
        collection_in_db = (
            db.session.query(ImageCollection)
            .filter(
                ImageCollection.user_id == current_user.id,
                ImageCollection.name == "Default",
            )
            .first()
        )
        if collection_in_db is None:
            # default is not created, create it
            collection_in_db = ImageCollection(
                user_id=current_user.id,
                name="Default",
            )
            db.session.add(collection_in_db)
            db.session.commit()
            db.session.refresh(collection_in_db)

    if collection_in_db is None:
        collection_in_db = (
            db.session.query(ImageCollection)
            .filter(
                ImageCollection.user_id == current_user.id,
                ImageCollection.id == request.form["collection_id"],
            )
            .first()
        )
        if not collection_in_db:
            return schemas.Errors().dump(
                {
                    "errors": [
                        {
                            "title": "ValidationError",
                            "detail": "Can't find that collection",
                        }
                    ]
                }
            )

    # TODO: file format validation? file size validation? duplicates? etc

    # upload the file to storage
    readable_file = BytesIO(
        request.files["file"].read()
    )  # all goes to memory, which is fine for images for most cases
    storage_provider = StorageProvider()
    storage_file_key, size = storage_provider.upload_file(
        current_user.id, readable_file, request.files["file"].filename
    )

    # create database object if succesfull

    default_mimetype = mimetypes.guess_type(
        request.files["file"].filename, strict=False
    )[0]

    mime = request.form.get("mimetype") or default_mimetype or "binary/octet-stream"
    image_in_db = Image(
        mimetype=mime,
        size=size,
        storageKey=storage_file_key,
        collection_id=collection_in_db.id,
    )
    db.session.add(image_in_db)
    db.session.commit()
    db.session.refresh(image_in_db)
    return schemas.ImageDisplaySchema().dump(image_in_db)


@app.route("/api/v0/images", methods=["GET"])
@login_required
def images_list():
    """List of images, optionally (TODO) filtered by collection
    ---
    get:
      parameters:
        - in: query
          name: collection_id
          schema:
            type: integer
          required: false
          description: the collection ID to filter upon
      responses:
        200:
          description: List of all images for the given user
          content:
            application/json:
              schema: ImageListSchema
    """
    collection_id = request.args.get("collection_id")
    # TODO: ensure that the collection ID is visible to the given user
    # it won't return anything if the ID is incorrect but it's better to raise 404

    this_user_collections = ImageCollection.get_collections_for_user(current_user)

    queryset = db.session.query(Image).filter(
        Image.collection_id.in_(this_user_collections.with_entities(ImageCollection.id).distinct()),
    )
    if collection_id:
        queryset = queryset.filter(
            Image.collection_id == collection_id
        )
    total = queryset.count()
    results = queryset.order_by("id")
    return schemas.ImageListSchema().dump(
        {
            "total": total,
            "images": results,
        }
    )


@app.route("/api/v0/images/<string:image_id>", methods=["GET"])
@login_required
def image_detail(image_id: str):
    """Return requested image information as JSON
    ---
    get:
      parameters:
        - in: path
          name: image_id
          schema:
            type: string
          required: true
          description: Unique image ID
      responses:
        200:
          description: JSON with the image info
          content:
            application/json:
              schema: ImageDisplaySchema
    """
    image_in_db = Image.get_image_or_abort(image_id, current_user)
    return schemas.ImageDisplaySchema().dump(image_in_db)


@app.route("/api/v0/images/<string:image_id>", methods=["DELETE"])
@login_required
def image_delete(image_id: str):
    """Remove the image both from database and storage
    ---
    delete:
      parameters:
        - in: path
          name: image_id
          schema:
            type: string
          required: true
          description: Unique image ID
      responses:
        202:
          description: Success
    """
    # TODO: clean up any orphaned annotations
    image_in_db = Image.get_image_or_abort(image_id, current_user)
    storage_provider = StorageProvider()
    storage_provider.delete_file(image_in_db.storageKey)
    db.session.delete(image_in_db)
    db.session.commit()
    return ("", 204)


@app.route("/api/v0/images/<string:image_id>/binary", methods=["GET"])
@login_required
def image_retrieve(image_id: str):
    """Return binary image content
    ---
    get:
      parameters:
        - in: path
          name: image_id
          schema:
            type: string
          required: true
          description: Unique image ID
      responses:
        200:
          description: Binary image content
    """
    image_in_db = Image.get_image_or_abort(image_id, current_user)

    storage_provider = StorageProvider()
    stored_file_buffer = storage_provider.retrieve_file_buffer(
        image_in_db.storageKey,
    )
    return send_file(
        BytesIO(stored_file_buffer),
        attachment_filename=image_in_db.filename,
        mimetype=image_in_db.mimetype,
        as_attachment=False,
    )


@app.route("/api/v0/images/<string:image_id>/link", methods=["GET"])
@login_required
def image_link(image_id: str):
    """Return pre-signed short-lived link to the image
    ---
    get:
      parameters:
        - in: path
          name: image_id
          schema:
            type: string
          required: true
          description: Unique image ID
      responses:
        302:
          description: Redirect user to the real image location
    """
    image_in_db = Image.get_image_or_abort(image_id, current_user)

    storage_provider = StorageProvider()

    return redirect(
        storage_provider.get_file_presigned_link(
            storage_key=image_in_db.storageKey,
            content_type=image_in_db.mimetype,
        )
    )


@app.route("/api/v0/images/<string:image_id>/annotations", methods=["GET"])
@login_required
def image_annotations(image_id):
    """List of annotations for a given image
    ---
    get:
      parameters:
        - in: path
          name: image_id
          schema:
            type: string
          required: true
          description: Unique image ID
      responses:
        200:
          description: List of all annotations for the given image
          content:
            application/json:
              schema: AnnotationListSchema
    """
    Image.get_image_or_abort(image_id, current_user)  # just to ensure the image exists

    queryset = db.session.query(Annotation).filter(Annotation.image_id == image_id)
    total = queryset.count()
    results = queryset.order_by(
        "created_at", "id"
    )  # TODO: this will re-order the display order of the annotations (use created_at datetime?)

    return schemas.AnnotationListSchema().dump(
        {
            "total": total,
            "annotations": results,
        }
    )

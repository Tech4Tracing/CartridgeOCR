import mimetypes
from io import BytesIO

from flask import request, send_file, abort
from flask_login import login_required, current_user

from annotations_app import app, schemas
from annotations_app.config import logging
from annotations_app.models.base import ImageCollection, Image, Annotation
from annotations_app.repos.azure_storage_provider import (
    AzureStorageProvider as StorageProvider,
)
from annotations_app.utils import db_session


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

    with db_session() as db:
        # ensure collection exists and retrieve it
        # if "collection_id" not in request.form or not request.form["collection_id"]:
        #     return Errors().dump({"errors": [{"title": "ValidationError", "detail": "No collection ID provided"}]})
        collection_id = request.form.get("collection_id")
        collection_in_db = None
        if not collection_id:
            # use default collection (which shall be created if doesn't exist)
            collection_in_db = (
                db.query(ImageCollection)
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
                db.add(collection_in_db)
                db.commit()
                db.refresh(collection_in_db)

        if collection_in_db is None:
            collection_in_db = (
                db.query(ImageCollection)
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
        )  # all goes to memory, which is fine for images
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
        )
        db.add(image_in_db)
        db.commit()
        db.refresh(image_in_db)
        collection_in_db.images.append(image_in_db)
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
    with db_session() as db:
        queryset = db.query(Image).filter(
            Image.collections.any(ImageCollection.user_id == current_user.id),
        )
        if collection_id:
            queryset = queryset.filter(
                Image.collections.any(ImageCollection.id == collection_id)
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
    with db_session() as db:
        image_in_db = (
            db.query(Image)
            .filter(
                Image.id == image_id,
                Image.collections.any(ImageCollection.user_id == current_user.id),
            )
            .first()
        )
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
    with db_session() as db:
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
        storage_provider = StorageProvider()
        storage_provider.delete_file(image_in_db.storageKey)
        db.delete(image_in_db)
        db.commit()
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
    with db_session() as db:
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
    with db_session() as db:
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

        queryset = db.query(Annotation).filter(Annotation.image_id == image_id)
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

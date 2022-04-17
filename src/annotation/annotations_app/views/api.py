import json
import mimetypes
from io import BytesIO

from flask import jsonify, render_template, request, send_file, abort
from flask_login import login_required, current_user

from annotations_app import app, spec
from annotations_app.models.base import ImageCollection, Image, Annotation
from annotations_app.repos.azure_storage_provider import AzureStorageProvider as StorageProvider
from annotations_app.utils import db_session
from annotations_app.config import logging
from annotations_app.views import schemas, api_users
from sqlalchemy import and_

@app.route('/api/v0/openapi.json', methods=["GET"])
@login_required
def openapi_json():
    return jsonify(spec.to_dict())


@app.route('/api/v0/', methods=["GET"])
@login_required
def openapi_ui():
    return render_template('swagger-ui.html')


@app.route("/api/v0/collections", methods=["GET"])
@login_required
def collections_get():
    """List collections
    ---
    get:
      responses:
        200:
          description: List of all collections for the given user
          content:
            application/json:
              schema: CollectionsListSchema
    """
    with db_session() as db:
        queryset = db.query(ImageCollection).filter(
            ImageCollection.user_id == current_user.id,
        )
        total = queryset.count()
        results = queryset.order_by("id")

        return schemas.CollectionsListSchema().dump(
            {
                "total": total,
                "collections": results,
            }
        )


@app.route('/api/v0/collections', methods=["POST"])
@login_required
def collections_post():
    """Create new collection
    ---
    post:
        requestBody:
          content:
            application/json:
              schema: CollectionCreateSchema
              example:
                name: the 3d bunch
        responses:
            201:
              description: The created schema content
              content:
                application/json:
                  schema: CollectionDisplaySchema
    """
    req = request.json
    # TODO: if req is None ...
    collection_in_db = ImageCollection(
        user_id=current_user.id,
        name=req["name"],
    )
    with db_session() as db:
        db.add(collection_in_db)
        db.commit()
        db.refresh(collection_in_db)
        return schemas.CollectionDisplaySchema().dump(collection_in_db)


@app.route("/api/v0/collections/<string:collection_id>", methods=["DELETE"])
@login_required
def collection_delete(collection_id: str):
    """Remove the collection (but what to do with the images?)
    ---
    delete:
      parameters:
        - in: path
          name: collection_id
          schema:
            type: string
          required: true
          description: Unique collection ID
      responses:
        202:
          description: Success
    """
    with db_session() as db:
        collection_in_db = db.query(ImageCollection).filter(
            ImageCollection.id == collection_id,
            ImageCollection.user_id == current_user.id,
        ).first()
        if not collection_in_db:
            abort(404)

        first_existing_image = db.query(Image).filter(
            Image.collections.any(ImageCollection.id.in_([collection_in_db.id])),
        ).first()

        if first_existing_image:
            return schemas.Errors().dump({"errors": [{"title": "ValidationError", "detail": "The collection has images - delete them first"}]}), 400

        db.delete(collection_in_db)
        db.commit()
        return ('', 204)


@app.route('/api/v0/images', methods=["POST"])
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
    if 'file' not in request.files or not request.files["file"].filename:
        return schemas.Errors().dump({"errors": [{"title": "ValidationError", "detail": "No file provided"}]}), 400

    with db_session() as db:
        # ensure collection exists and retrieve it
        # if "collection_id" not in request.form or not request.form["collection_id"]:
        #     return Errors().dump({"errors": [{"title": "ValidationError", "detail": "No collection ID provided"}]})
        collection_id = request.form.get("collection_id")
        collection_in_db = None
        if not collection_id:
            # use default collection (which shall be created if doesn't exist)
            collection_in_db = db.query(ImageCollection).filter(
                ImageCollection.user_id == current_user.id,
                ImageCollection.name == "Default"
            ).first()
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
            collection_in_db = db.query(ImageCollection).filter(
                ImageCollection.user_id == current_user.id,
                ImageCollection.id == request.form["collection_id"]
            ).first()
            if not collection_in_db:
                return schemas.Errors().dump({"errors": [{"title": "ValidationError", "detail": "Can't find that collection"}]})

        # TODO: file format validation? file size validation? duplicates? etc

        # upload the file to storage
        readable_file = BytesIO(request.files["file"].read())  # all goes to memory, which is fine for images
        storage_provider = StorageProvider()
        storage_file_key, size = storage_provider.upload_file(
            current_user.id,
            readable_file,
            request.files["file"].filename
        )

        # create database object if succesfull

        default_mimetype = mimetypes.guess_type(request.files["file"].filename, strict=False)[0]

        image_in_db = Image(
            mimetype=request.form.get("mimetype") or default_mimetype or "binary/octet-stream",
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
      responses:
        200:
          description: List of all images for the given user
          content:
            application/json:
              schema: ImageListSchema
    """
    with db_session() as db:
        queryset = db.query(Image).filter(
            Image.collections.any(ImageCollection.user_id == current_user.id),
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
        image_in_db = db.query(Image).filter(
            Image.id == image_id,
            Image.collections.any(ImageCollection.user_id == current_user.id),
        ).first()
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
        image_in_db = db.query(Image).filter(
            Image.id == image_id,
            Image.collections.any(ImageCollection.user_id == current_user.id),
        ).first()
        if not image_in_db:
            abort(404)
        storage_provider = StorageProvider()
        storage_provider.delete_file(image_in_db.storageKey)
        db.delete(image_in_db)
        db.commit()
        return ('', 204)


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
        image_in_db = db.query(Image).filter(
            Image.id == image_id,
            Image.collections.any(ImageCollection.user_id == current_user.id),
        ).first()

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


@app.route("/api/v0/images/<string:image_id>/annotations", methods=['GET'])
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
        image_in_db = db.query(Image).filter(
            Image.id == image_id,
            Image.collections.any(ImageCollection.user_id == current_user.id),
        ).first()

        if not image_in_db:
            abort(404)
    
        queryset = db.query(Annotation).filter(
            Annotation.image_id == image_id
        )
        total = queryset.count()
        results = queryset.order_by("id") # TODO: this will re-order the display order of the annotations.

        return schemas.AnnotationListSchema().dump(
            {
                "total": total,
                "annotations": results,
            }
        )


@app.route("/api/v0/annotations/", methods=['GET'])
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
        image_id = args.get('image_id')
        collection_id = args.get('collection_id')

        logging.info(f'GET annotations collection_id: {collection_id} image_id: {image_id}')
        queryset = db.query(Annotation).filter(
            and_(
                Image.id == image_id if image_id is not None else True,
                Annotation.image_id == Image.id,
                Image.collections.any(
                    and_(
                      ImageCollection.id == collection_id if collection_id is not None else True,
                      ImageCollection.user_id == current_user.id)
                )
            )
        )

        total = queryset.count()
        results = queryset.order_by("id") # TODO: this will re-order the display order of the annotations.

        return schemas.AnnotationListSchema().dump(
            {
                "total": total,
                "annotations": results,
            }
        )


# TODO: geometry and metadata types
# TODO: multipart/form request?
@app.route("/api/v0/annotations/", methods=['POST'])
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
        
        image_in_db = db.query(Image).filter(
            Image.id == image_id,
            Image.collections.any(ImageCollection.user_id == current_user.id),
        ).first()

        if not image_in_db:
            abort(404)
        
        # create database object if succesfull

        annotation_in_db = Annotation(
            image_id=image_id,
            geometry=json.dumps(req["geometry"]),
            annotation=req["annotation"],
            metadata_=json.dumps(req["metadata_"])
        )
        db.add(annotation_in_db)
        db.commit()
        db.refresh(annotation_in_db)        
        return schemas.AnnotationDisplaySchema().dump(annotation_in_db)


@app.route("/api/v0/annotations/<string:annotation_id>", methods=['PUT'])
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
        image_in_db = db.query(Image).filter(
            Image.id == image_id,
            Image.collections.any(ImageCollection.user_id == current_user.id),
        ).first()

        if not image_in_db:
            abort(404)
        
        # create database object if succesfull
        # TODO: test/sanity check
        annotation_in_db = db.query(Annotation).filter(
            Annotation.id == annotation_id,
            Image.id == image_id,
            Image.collections.any(ImageCollection.user_id == current_user.id)            
        ).first()
        if not annotation_in_db:
            abort(404)

        annotation_in_db.geometry = json.dumps(req["geometry"])
        annotation_in_db.annotation = req["annotation"]
        annotation_in_db.metadata_ = json.dumps(req["metadata_"]) 
        
        # db.update(annotation_in_db)
        db.commit()
        db.refresh(annotation_in_db)        
        return schemas.AnnotationDisplaySchema().dump(annotation_in_db)


@app.route("/api/v0/annotations/<string:annotation_id>", methods=['DELETE'])
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
    with db_session() as db:
        
        # TODO: test/sanity check
        annotation_in_db = db.query(Annotation).filter(
            Annotation.id == annotation_id,
            Image.id == Annotation.image_id,
            Image.collections.any(ImageCollection.user_id == current_user.id)            
        ).first()

        if not annotation_in_db:
            abort(404)

        db.delete(annotation_in_db)
        return ('', 204)


# Register the path and the entities within it
with app.test_request_context():
    spec.path(view=collections_get)
    spec.path(view=collections_post)
    spec.path(view=collection_delete)
    spec.path(view=images_list)
    spec.path(view=image_post)
    spec.path(view=image_detail)
    spec.path(view=image_retrieve)
    spec.path(view=image_delete)
    spec.path(view=image_annotations)
    spec.path(view=annotations_list)
    spec.path(view=annotation_post)
    spec.path(view=annotation_replace)
    spec.path(view=annotation_delete)
    spec.path(view=api_users.users_list)
    spec.path(view=api_users.user_create)
    spec.path(view=api_users.user_update)

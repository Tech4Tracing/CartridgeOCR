from curses import meta
from io import BytesIO
import json

from flask import jsonify, render_template, request, send_file, abort
from flask_login import login_required, current_user
from marshmallow import Schema, fields

from annotations_app import app, spec
from annotations_app.models.base import ImageCollection, Image, Annotation
from annotations_app.repos.azure_storage_provider import AzureStorageProvider as StorageProvider
from annotations_app.utils import db_session
from annotations_app.config import logging


class DemoParameter(Schema):
    gist_id = fields.Int()


class CollectionCreateSchema(Schema):
    name = fields.Str()


class CollectionDisplaySchema(Schema):
    id = fields.Str()
    # created_at = fields.DateTime()
    name = fields.Str()


class CollectionsListSchema(Schema):
    total = fields.Int()
    collections = fields.List(fields.Nested(CollectionDisplaySchema))


class ImageDisplaySchema(Schema):
    id = fields.Str()
    # created_at = fields.DateTime()
    mimetype = fields.Str()
    size = fields.Int()
    extra_data = fields.Dict()
    collections = fields.List(fields.Str())
    storageKey = fields.Str()


class ImageListSchema(Schema):
    total = fields.Int()
    images = fields.List(fields.Nested(ImageDisplaySchema))

class AnnotationDisplaySchema(Schema):
    anno_id = fields.Str()
    img_id = fields.Str()
    geometry = fields.Str()
    annotation = fields.Str()
    metadata = fields.Str()
    
class AnnotationListSchema(Schema):
    total = fields.Int()
    annotations = fields.List(fields.Nested(AnnotationDisplaySchema)) 

class ErrorSchema(Schema):
    status = fields.Int()
    title = fields.Str()
    detail = fields.Str()


class Errors(Schema):
    errors = fields.List(fields.Nested(ErrorSchema))


spec.components.schema("Collection", schema=CollectionDisplaySchema)
spec.components.schema("CollectionCreate", schema=CollectionCreateSchema)
spec.components.schema("CollectionsList", schema=CollectionsListSchema)


@app.route('/api/v0/openapi.json', methods=["GET"])
@login_required
def openapi_json():
    # current_user
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

        return CollectionsListSchema().dump(
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
        return CollectionDisplaySchema().dump(collection_in_db)


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
        return Errors().dump({"errors": [{"title": "ValidationError", "detail": "No file provided"}]})

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
                return Errors().dump({"errors": [{"title": "ValidationError", "detail": "Can't find that collection"}]})

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

        image_in_db = Image(
            mimetype=request.form["mimetype"] or "binary/octet-stream",
            size=size,
            storageKey=storage_file_key,
        )
        db.add(image_in_db)
        db.commit()
        db.refresh(image_in_db)
        collection_in_db.images.append(image_in_db)
        return ImageDisplaySchema().dump(image_in_db)


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

        return ImageListSchema().dump(
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
        return ImageDisplaySchema().dump(image_in_db)


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


@app.route("/api/v0/images/<string:img_id>/annotations", methods=['GET'])
@login_required
def image_annotations(img_id):
    """List of annotations for a given image
    ---
    get:
      responses:
        200:
          description: List of all annotations for the given image
          content:
            application/json:
              schema: AnnotationListSchema
    """
    with db_session() as db:
        image_in_db = db.query(Image).filter(
            Image.id == img_id,
            Image.collections.any(ImageCollection.user_id == current_user.id),
        ).first()

        if not image_in_db:
            abort(404)
    
        queryset = db.query(Annotation).filter(
            Annotation.img_id == img_id
        )
        total = queryset.count()
        results = queryset.order_by("id")

        return AnnotationListSchema().dump(
            {
                "total": total,
                "images": results,
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
                  img_id:
                    type: string
                  geometry: 
                    type: object
                  annotation: 
                    type: string
                  metadata: 
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
        img_id = req["img_id"] if "img_id" in req else None
        image_in_db = db.query(Image).filter(
            Image.id == img_id,
            Image.collections.any(ImageCollection.user_id == current_user.id),
        ).first()

        if not image_in_db:
            abort(404)
        
        # create database object if succesfull

        annotation_in_db = Annotation(
            img_id = img_id,
            geometry = json.dumps(req["geometry"]),
            annotation = req["annotation"],
            metadata = json.dumps(req["metadata"])            
        )
        db.add(annotation_in_db)
        db.commit()
        db.refresh(annotation_in_db)        
        return AnnotationDisplaySchema().dump(annotation_in_db)

# TODO: document this call
@app.route("/api/v0/annotations/<string:anno_id>", methods=['PUT'])
@login_required
def annotation_replace(anno_id):
    """Replace/update annotation 
    ---
    put:
        parameters:
        - in: path
          name: anno_id
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
                  img_id:
                    type: string
                  geometry: 
                    type: object
                  annotation: 
                    type: string
                  metadata: 
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
        img_id = req["img_id"] if "img_id" in req else None
        image_in_db = db.query(Image).filter(
            Image.id == img_id,
            Image.collections.any(ImageCollection.user_id == current_user.id),
        ).first()

        if not image_in_db:
            abort(404)
        
        # create database object if succesfull
        # TODO: test/sanity check
        annotation_in_db = db.query(Annotation).filter(
          Annotation.anno_id == anno_id,
          Image.id == img_id,
          Image.collections.any(ImageCollection.user_id == current_user.id)
          # OR:
          # Annotation.img_id == img_id, counting on the previous check.
          # TODO: test which is faster.
        ).first()
        if not annotation_in_db:
            abort(404)

        annotation_in_db.geometry = json.dumps(req["geometry"])
        annotation_in_db.annotation = req["annotation"]
        annotation_in_db.metadata = json.dumps(req["metadata"]) 
        
        # db.update(annotation_in_db)
        db.commit()
        db.refresh(annotation_in_db)        
        return AnnotationDisplaySchema().dump(annotation_in_db)

# TODO: document this call
@app.route("/api/v0/annotations/<string:anno_id>", methods=['DELETE'])
@login_required
def annotation_delete(anno_id):
    """Remove the annotation
    ---
    delete:
      parameters:
        - in: path
          name: anno_id
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
          Annotation.anno_id == anno_id,
          Image.id == Annotation.img_id,
          Image.collections.any(ImageCollection.user_id == current_user.id)
          # OR:
          # Annotation.img_id == img_id, counting on the previous check.
          # TODO: test which is faster.
        ).first()
        if not annotation_in_db:

            abort(404)

        db.delete(annotation_in_db)
        return ('', 204)


# Register the path and the entities within it
with app.test_request_context():
    spec.path(view=collections_get)
    spec.path(view=collections_post)
    spec.path(view=images_list)
    spec.path(view=image_post)
    spec.path(view=image_detail)
    spec.path(view=image_retrieve)
    spec.path(view=image_delete)
    spec.path(view=image_annotations)
    spec.path(view=annotation_post)
    spec.path(view=annotation_replace)
    spec.path(view=annotation_delete)

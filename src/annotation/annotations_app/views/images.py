import mimetypes
from io import BytesIO
import json
import os
from base64 import b64encode
import datetime

from flask import request, send_file, redirect, abort
from flask_login import current_user

from annotations_app.flask_app import app, db, celery
from annotations_app import schemas
from annotations_app.config import logging
from annotations_app.models.base import ImageCollection, Image, Annotation, HeadstampPrediction, Note
from annotations_app.repos.azure_storage_provider import (
    AzureStorageProvider as StorageProvider,
)
from annotations_app.tasks.predict import predict_headstamps
from annotations_app.utils import t4t_login_required, parse_boolean

from PIL import Image as PILImage
MAX_DIMENSION = 400 # for thumbnailing

from sqlalchemy import and_, desc

#assert 'PREDICTION_ENDPOINT' in os.environ
#prediction_endpoint_uri = os.environ['PREDICTION_ENDPOINT']+'/api/v0/headstamp_predict'            

@app.route("/api/v0/images", methods=["POST"])
@t4t_login_required
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
                  predict:
                    type: boolean
                    required: false
                  extra_data:
                    type: object
                  prediction_status:
                    type: object
                    required: false
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
        collection_in_db = ImageCollection.get_collection_or_abort(
          request.form["collection_id"], current_user.id, include_guest_access=True)
        
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
    image_data = request.files["file"].read()
    readable_file = BytesIO(
        image_data
    )  # all goes to memory, which is fine for images for most cases

    storage_provider = StorageProvider()
    storage_file_key, size = storage_provider.upload_file(
        current_user.id, readable_file, request.files["file"].filename
    )

    readable_file.seek(0)
    image_bits = PILImage.open(readable_file)                  # img is now PIL Image object    
    width, height = image_bits.size
    thumbnail_file_key = None
    if min(width,height) > MAX_DIMENSION:  # will need some experimentation
        if width<height:
            newsize = (MAX_DIMENSION, int(MAX_DIMENSION / width * height))
        else:
            newsize = (int(MAX_DIMENSION / height * width), MAX_DIMENSION)
        logging.info(f'Resizing thumbnail from {width,height} to {newsize}')
        thumbnail = image_bits.resize(newsize)
        thumbnail_buf = BytesIO()
        thumbnail.save(thumbnail_buf, format='JPEG')
        thumbnail_buf.seek(0)
        thumbnail_file_key, size = storage_provider.upload_file(
          current_user.id, thumbnail_buf, 'thumb_'+request.files["file"].filename
        )

        
    # create database object if succesfull

    default_mimetype = mimetypes.guess_type(
        request.files["file"].filename, strict=False
    )[0]

    mime = request.form.get("mimetype") or default_mimetype or "binary/octet-stream"
    extra_data = request.form.get("extra_data")
    extra_data = json.loads(extra_data) if extra_data else {}
    if 'filename' not in extra_data:
      extra_data['filename'] = request.files["file"].filename
    
    notes = []
    for key in extra_data:
        prediction_id = None
        if type(extra_data[key]) == dict and 'prediction_id' in extra_data['key']:
            prediction_id = extra_data[key]['prediction_id']            
        notes.append(Note(prediction_id=prediction_id, note_key=key, note_value=extra_data[key]))
    
    image_in_db = Image(
        mimetype=mime,
        size=size,
        storageKey=storage_file_key,
        thumbnailStorageKey=thumbnail_file_key,
        collection_id=collection_in_db.id,
        notes = notes,        
        #extra_data=json.dumps(extra_data),
        prediction_status=json.dumps({'status':'staging'}),
    )
    
    
    db.session.add(image_in_db)
    db.session.commit()
    db.session.refresh(image_in_db)
    logging.info(image_in_db.prediction_status)
    
    # we need an image id before we can kick off the prediction task
    # and we want a task id for future reference. Maybe we could do without it?
    # unfortunately we have to run a second transaction
    prediction_status = None
    do_prediction = parse_boolean(request.form.get('predict', 'true'))    
    logging.info(f"image upload do_prediction: {do_prediction} {type(do_prediction)}")
    if do_prediction:
        result=predict_headstamps.delay(current_user.id, image_in_db.id, b64encode(image_data).decode('utf-8'))
        logging.info(f'Prediction task: {result.task_id}')
        
        prediction_status = {
          'task_id': result.task_id,
          'status': 'pending', 
          'updated': str(datetime.datetime.utcnow()), 
          'result': 'None'
        }
    elif request.form.get('prediction_status'):
        prediction_status = json.loads(request.form.get('prediction_status'))
    else:
        prediction_status = {
          'task_id': None,
          'status': 'skipped',
          'updated': str(datetime.datetime.utcnow()),
          'result': 'None'
        }
    image_in_db.prediction_status = json.dumps(prediction_status)
    db.session.commit()
    db.session.refresh(image_in_db)
    logging.info(image_in_db.prediction_status)

    return schemas.ImageDisplaySchema().dump(image_in_db), 201


@app.route("/api/v0/images", methods=["GET"])
@t4t_login_required
def images_list():
    """List of images, optionally (TODO) filtered by collection
    ---
    get:
      parameters:
        - in: query
          name: collection_id
          schema:
            type: string
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

    this_user_collections = ImageCollection.get_collections_for_user(
        current_user.id, include_guest_access=True, include_readonly=True)

    queryset = db.session.query(Image).filter(
        Image.collection_id.in_(this_user_collections.with_entities(ImageCollection.id).distinct()),
    )
    if collection_id:
        queryset = queryset.filter(
            Image.collection_id == collection_id
        )
    total = queryset.count()
    # sort by the order they were uploaded.
    # TODO: alternate sort orders in the UI
    results = queryset.order_by("created_at")
    return schemas.ImageListSchema().dump(
        {
            "total": total,
            "images": results,
        }
    )


@app.route("/api/v0/images/<string:image_id>", methods=["GET"])
@t4t_login_required
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
    image_in_db = Image.get_image_or_abort(image_id, current_user.id, include_guest_access=True, include_readonly=True)
    return schemas.ImageDisplaySchema().dump(image_in_db)


@app.route("/api/v0/images/<string:image_id>", methods=["DELETE"])
@t4t_login_required
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
    image_in_db = Image.get_image_or_abort(image_id, current_user.id, include_guest_access=True)
    
    # Delete all notes and predictions associated with this image.
    # TODO: do we also need to do this for annotations?
    notes_in_db = db.session.query(Note).filter(
          Note.image_id == image_in_db.id,           
        ).all()

    for note in notes_in_db:
      db.session.delete(note)

    predictions_in_db = db.session.query(HeadstampPrediction).filter(
          HeadstampPrediction.image_id == image_in_db.id,           
        ).all()

    for prediction in predictions_in_db:
      db.session.delete(prediction)

    storage_provider = StorageProvider()
    storage_provider.delete_file(image_in_db.storageKey)
    if image_in_db.thumbnailStorageKey:
        storage_provider.delete_file(image_in_db.thumbnailStorageKey)

    db.session.delete(image_in_db)
    db.session.commit()
    return ("", 204)


@app.route("/api/v0/images/<string:image_id>/binary", methods=["GET"])
@t4t_login_required
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
        - in: query
          name: thumbnail
          schema:
            type: string
          required: false
          description: whether to return the thumbnail or the full image

      responses:
        200:
          description: Binary image content
    """
    image_in_db = Image.get_image_or_abort(image_id, current_user.id, include_guest_access=True, include_readonly=True)

    return_thumbnail = parse_boolean(request.args.get("thumbnail", "false"))
    return_thumbnail = return_thumbnail and image_in_db.thumbnailStorageKey

    storage_provider = StorageProvider()
    stored_file_buffer = storage_provider.retrieve_file_buffer(
        image_in_db.thumbnailStorageKey if return_thumbnail else image_in_db.storageKey
    )
    return send_file(
        BytesIO(stored_file_buffer),
        download_name=image_in_db.filename,
        mimetype="image/jpeg" if return_thumbnail else image_in_db.mimetype,
        as_attachment=False,
    )


@app.route("/api/v0/images/<string:image_id>/link", methods=["GET"])
@t4t_login_required
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
        - in: query
          name: thumbnail
          schema:
            type: string
          required: false
          description: whether to link the thumbnail or the full image

      responses:
        302:
          description: Redirect user to the real image location
    """
    image_in_db = Image.get_image_or_abort(image_id, current_user.id, include_guest_access=True, include_readonly=True)
    return_thumbnail = parse_boolean(request.args.get("thumbnail", "false"))
    return_thumbnail = return_thumbnail and image_in_db.thumbnailStorageKey

    storage_provider = StorageProvider()

    return redirect(
        storage_provider.get_file_presigned_link(
            image_in_db.thumbnailStorageKey if (return_thumbnail) else image_in_db.storageKey,
            content_type="image/jpeg" if return_thumbnail else image_in_db.mimetype,
        )
    )


@app.route("/api/v0/images/<string:image_id>/annotations", methods=["GET"])
@t4t_login_required
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
    Image.get_image_or_abort(image_id, current_user.id, include_guest_access=True, include_readonly=True)  # just to ensure the image exists

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


@app.route("/api/v0/images/<string:image_id>/predictions", methods=["GET"])
@t4t_login_required
def image_predictions(image_id):
    """List of predictions for a given image
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
          description: List of all predictions for the given image
          content:
            application/json:
              schema: HeadstampPredictionListSchema
    """
    image = Image.get_image_or_abort(image_id, current_user.id, include_guest_access=True, include_readonly=True)  # just to ensure the image exists

    queryset = db.session.query(HeadstampPrediction).filter(HeadstampPrediction.image_id == image_id)
    total = queryset.count()
    results = queryset.order_by(
        "created_at", "id"
    )  # TODO: this will re-order the display order of the annotations (use created_at datetime?)

    return schemas.HeadstampPredictionListSchema().dump(
        {
            "total": total,
            "status": image.prediction_status,
            "predictions": results,
        }
    )


@app.route("/api/v0/images/<string:image_id>", methods=["PUT"])
@t4t_login_required
def image_update(image_id: str):
    """Update image properties. The only field that can be updated is the extra_data field.
    ---
    put:
      parameters:
        - in: path
          name: image_id
          schema:
            type: string
          required: true
          description: Unique image ID
      requestBody:
        content:
          application/json:
            schema:
              type: object
              properties:
                extra_data: string

      responses:
        201:
          description: JSON with the image info
          content:
            application/json:
              schema: ImageDisplaySchema
    """
    logging.info(f"put image {image_id}")
    image_in_db = Image.get_image_or_abort(image_id, current_user.id, include_guest_access=True)

    logging.info("PUT image request for user %s", current_user.id)

    # TODO: validate the payload.
    # TODO: escape quotes and other dangerous chars
    payload = request.get_json()
    extra_data = payload['extra_data'] if 'extra_data' in payload else []
    assert isinstance(extra_data, list), "extra_data must be a list"
    if not image_id:
        abort(400, description="image_id parameter is required")

    image_in_db = Image.get_image_or_abort(image_id, current_user.id)  # ensure exists and available
    logging.info(f'updating image {image_id} with extra_data {extra_data}')
    image_in_db.notes = [Note(n) for n in extra_data]

    db.session.commit()
    db.session.refresh(image_in_db)
    return schemas.ImageDisplaySchema().dump(image_in_db)



@app.route("/api/v0/images/<string:image_id>/navigation", methods=["GET"])
@t4t_login_required
def image_navigation(image_id):
    """Get adjacent images in the database, for navigation
    ---
    get:
      parameters:
        - in: path
          name: image_id
          schema:
            type: string
          required: true
          description: Unique image ID
        - in: query
          name: sort_by
          schema:
            type: string
          required: false
          description: Sort by field (created_at, id)
      responses:
        200:
          description: Previous and next image in the database
          content:
            application/json:
              schema: NavigationSchema
    """
    image=Image.get_image_or_abort(image_id, current_user.id, include_guest_access=True, include_readonly=True)  # just to ensure the image exists

    sort_by = request.args.get("sort_by", "created_at")
    if sort_by not in ["created_at", "id"]:
        abort(400, description="Invalid sort_by parameter")

    # TODO: is there a cleaner way?
    if sort_by == "created_at":
        next_id = db.session.query(Image.id).filter(
            and_(Image.collection_id == image.collection_id, Image.created_at > image.created_at)
        ).order_by(Image.created_at).limit(1).scalar()
        prev_id = db.session.query(Image.id).filter(
            and_(Image.collection_id == image.collection_id, Image.created_at < image.created_at)
        ).order_by(desc(Image.created_at)).limit(1).scalar()
    else: # sort_by == "id"
        next_id = db.session.query(Image.id).filter(
          and_(Image.collection_id==image.collection_id, Image.id > image_id)
        ).order_by(Image.id).limit(1).scalar()
        prev_id = db.session.query(Image.id).filter(
          and_(Image.collection_id==image.collection_id, Image.id < image_id)
        ).order_by(desc(Image.id)).limit(1).scalar()
    return schemas.NavigationSchema().dump({
        "next": next_id,
        "prev": prev_id,
    }), 200

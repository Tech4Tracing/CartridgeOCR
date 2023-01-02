import mimetypes
from io import BytesIO
import json
import logging

from flask import request, abort
from flask_login import login_required, current_user

from annotations_app.flask_app import app, db, celery
from annotations_app import schemas
from annotations_app.config import logging
from annotations_app.models.base import ImageCollection, Image, HeadstampPrediction
from annotations_app.repos.azure_storage_provider import (
    AzureStorageProvider as StorageProvider,
)
from annotations_app.tasks.predict import Predict
from sqlalchemy import and_

# Needs more thinking through.
# Uploading an image should trigger prediction as a back-end task
# The prediction result should be stored in the database
# No need to monitor tasks state or result?
# This file should just be the API for accessing the predictions from the DB.

@app.route("/api/v0/predict/<string:image_id>", methods=["GET"])
@login_required
def image_predict(image_id):
  # move this method to /api/v0/predictions/<image_id> and make it a POST
  # the POST will return a 202 and the task id
  # the task itself will run prediction and update the database
  # the GET will return the status of the task
  # First publish tech4tracing.headstamp_detection.
  
    result = Predict().predict_image.delay(image_id)  
    return json.dumps({'task':result.task_id}), 202

@app.route("/api/v0/predict_status", methods=["GET"])
@login_required
def get_status():
    """Get task status
    ---
    get:
      parameters:
        - in: query
          name: task_id
          schema:
            type: string
          required: true
          description: the task id
      responses:
        200:
          description: task state
          content:
            application/json:
              schema: ImageListSchema
    """
    args = request.args
    task_id = args.get("task_id") or None
    result = celery.AsyncResult(task_id)
    if result.state == "SUCCESS":
        result = json.dumps(result.get())
    # logging.info(f'task_result: {result}')
    return json.dumps({'result':result}), 200


####

@app.route("/api/v0/predictions", methods=["GET"])
@login_required
def predictions_list():
    """List of headstamp predictions for a given user/collection/image. This endpoint is not paginated,
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
          description: List of all predictions for the given user/collection/image, depending on specificity
          content:
            application/json:
              schema: PredictionListSchema
    """
    args = request.args
    image_id = args.get("image_id") or None
    collection_id = args.get("collection_id") or None

    # retrieve image and collection (if requested) just to ensure they exist and visible
    if image_id:
        Image.get_image_or_abort(image_id, current_user.id)
    if collection_id:
        ImageCollection.get_collection_or_abort(collection_id, current_user.id)

    this_user_collections = ImageCollection.get_collections_for_user(current_user.id)

    queryset = db.session.query(HeadstampPrediction).filter(
        and_(
            # filter by image
            HeadstampPrediction.image_id == image_id if image_id else True,
            # filter by collection (including only collections visible to user if no collection is provided)
            HeadstampPrediction.image_id == Image.id,
            Image.collection_id.in_(this_user_collections.with_entities(ImageCollection.id).distinct()),
            Image.collection_id == collection_id if collection_id else True,
        )
    )

    total = queryset.count()
    results = queryset.order_by(
        "created_at", "id",
    )

    return schemas.HeadstampPredictionListSchema().dump(
        {
            "total": total,
            "predictions": results,
        }
    )


# TODO: geometry and metadata types
@app.route("/api/v0/predictions", methods=["POST"])
@login_required
def prediction_post():
    """Create headstamp prediction for image
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
                  casing_box:
                    type: object
                  casing_confidence:
                    type: number
                  primer_box:
                    type: object
                  primer_confidence:
                    type: number                  
        responses:
            201:
              description: Details about the created headstamp prediction
              content:
                application/json:
                  schema: HeadstampPredictionDisplaySchema
    """
    logging.info("Uploading headstamp prediction for user %s", current_user.id)

    req = request.get_json()

    image_id = req["image_id"] if "image_id" in req else None
    if not image_id:
        abort(400, description="image_id parameter is required")

    Image.get_image_or_abort(image_id, current_user.id)  # ensure exists and available

    # create database object if succesfull
    prediction_in_db = HeadstampPrediction(
        image_id=image_id,
        casing_box=json.dumps(req["casing_box"]),
        casing_confidence=req["casing_confidence"],
        primer_box=json.dumps(req["primer_box"]),
        primer_confidence=req["primer_confidence"],        
    )
    db.session.add(prediction_in_db)
    db.session.commit()
    db.session.refresh(prediction_in_db)
    return schemas.HeadstampPredictionDisplaySchema().dump(prediction_in_db), 201


@app.route("/api/v0/predictions/<string:prediction_id>", methods=["PUT"])
@login_required
def prediction_replace(prediction_id):
    """Replace/update annotation
    ---
    put:
        parameters:
        - in: path
          name: prediction_id
          schema:
            type: string
          required: true
          description: Unique prediction ID
        requestBody:
          content:
            application/json:
              schema:
                type: object
                properties:
                  image_id:
                    type: string
                  casing_box:
                    type: object
                  casing_confidence:
                    type: number
                  primer_box:
                    type: object
                  primer_confidence:
                    type: number                  
        responses:
            201:
              description: Details about the created headstamp prediction
              content:
                application/json:
                  schema: HeadstampPredictionDisplaySchema
          
    """
    logging.info("PUT prediction request for user %s", current_user.id)

    # TODO: validate the payload.
    # TODO: escape quotes and other dangerous chars
    req = request.get_json()

    image_id = req["image_id"] if "image_id" in req else None
    if not image_id:
        abort(400, description="image_id parameter is required")

    Image.get_image_or_abort(image_id, current_user.id)  # ensure exists and available

    # retrieve existing prediction object
    # TODO: test/sanity check
    prediction_in_db = (
        db.session.query(HeadstampPrediction)
        .filter(
            HeadstampPrediction.id == prediction_id,
            Image.id == image_id,
            # don't need image access filter while checked above
        )
        .first()
    )
    if not prediction_in_db:
        abort(404)

    prediction_in_db.primer_box = json.dumps(req["primer_box"])
    prediction_in_db.primer_confidence = req["primer_confidence"]
    prediction_in_db.casing_box = json.dumps(req["casing_box"])
    prediction_in_db.casing_confidence = req["casing_confidence"]
    db.session.commit()
    db.session.refresh(prediction_in_db)
    return schemas.HeadstampPredictionDisplaySchema().dump(prediction_in_db)


@app.route("/api/v0/predictions/<string:prediction_id>", methods=["DELETE"])
@login_required
def prediction_delete(prediction_id):
    """Remove the prediction
    ---
    delete:
      parameters:
        - in: path
          name: prediction_id
          schema:
            type: string
          required: true
          description: Unique prediction ID
      responses:
        204:
          description: Success
    """
    logging.info("DELETE prediction request for user %s", current_user.id)
    # TODO: test/sanity check
    this_user_collections = ImageCollection.get_collections_for_user(current_user.id)

    prediction_in_db = (
        db.session.query(HeadstampPrediction)
        .filter(
            HeadstampPrediction.id == prediction_id,
            Image.id == HeadstampPrediction.image_id,
            Image.collection_id.in_(this_user_collections.with_entities(ImageCollection.id).distinct()),
        )
        .first()
    )

    if not prediction_in_db:
        abort(404)

    db.session.delete(prediction_in_db)
    db.session.commit()
    return ("", 204)

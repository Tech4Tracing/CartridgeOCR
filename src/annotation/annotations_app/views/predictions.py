import mimetypes
from io import BytesIO
import json
import logging

from flask import request, send_file, redirect
from flask_login import login_required, current_user

from annotations_app.flask_app import app, db, celery
from annotations_app import schemas
from annotations_app.config import logging
from annotations_app.models.base import ImageCollection, Image, Annotation
from annotations_app.repos.azure_storage_provider import (
    AzureStorageProvider as StorageProvider,
)
from annotations_app.tasks.predict import Predict

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

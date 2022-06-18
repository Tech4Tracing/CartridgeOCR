import mimetypes
from io import BytesIO
import sys
import os
from flask import request, send_file
from flask_login import login_required, current_user

from flask_app import app
import schemas
from config import logging, Config
import base64
import json
#from annotations_app.models.base import ImageCollection, Image, Annotation
from repos.azure_storage_provider import (
    AzureStorageProvider as StorageProvider,
)

# TODO: move this code to __init__?
# TODO: use env

sys.path.append('..')
from model.predictions.inference import Inference

inf = Inference()
inf.init(modelfolder=Config.MODEL_FOLDER, checkpoint=Config.MODEL_SNAPSHOT_NAME)


@app.route("/api/v0/headstamp_predict", methods=["POST"])
#@login_required
def headstamp_predict_post():
    """Predict headstamps in image
    ---
    post:
        requestBody:
          content:
            multipart/form-data:
              schema:
                type: object
                properties:
                  mimetype:
                    type: string
                  file:
                    type: string
                    format: binary
        responses:
            201:
              description: Predictions from image
              content:
                application/json:
                  schema: HeadstampPredictionListSchema
    """
    logging.info("Predicting for user %s", current_user.id)
    if "file" not in request.files or not request.files["file"].filename:
        return (
            schemas.Errors().dump(
                {"errors": [{"title": "ValidationError", "detail": "No file provided"}]}
            ),
            400,
        )

    # TODO: file format validation? file size validation? duplicates? etc

    # upload the file to storage
    readable_file = BytesIO(
        request.files["file"].read()
    )  # all goes to memory, which is fine for images for most cases
    
     # load the image and base64 encode it.
    encoded = base64.b64encode(readable_file)
    result = inf.run(json.dumps({'image': encoded.decode()}))
     
    return result # schemas.ImageDisplaySchema().dump(image_in_db)


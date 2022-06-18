import sys
import json
import base64
import schemas
from config import Config, logging
sys.path.append('..')
from model.predictions.inference import Inference
from flask import request
from flask_app import app

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
                  render:
                    type: string
                  file:
                    type: string
                    format: binary
        responses:
            201:
              description: Predictions from image
              content:
                application/json:
                  schema: HeadstampPredictionSchema
    """
    if "file" not in request.files or not request.files["file"].filename:
        return (
            schemas.Errors().dump(
                {"errors": [{"title": "ValidationError", "detail": "No file provided"}]}
            ),
            400,
        )

    # TODO: file format validation? file size validation? duplicates? etc
    data = dict(request.form)
    logging.info(f'Data: {data}')
   
    # load the image and base64 encode it.
    encoded = base64.b64encode(request.files["file"].read())
    result = inf.run(json.dumps({'image': encoded.decode(), 'render': data.get('render',False)}))
    logging.info(result)
    return schemas.HeadstampPredictionSchema().dump(result)
     # schemas.ImageDisplaySchema().dump(image_in_db)


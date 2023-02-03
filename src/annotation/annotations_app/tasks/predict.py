from annotations_app.flask_app import celery, db
import requests
import os
import datetime
from base64 import b64encode
import json
import logging
from annotations_app.models.base import ImageCollection, Image, HeadstampPrediction



# TODO: remove or figure out subclassing
class Predict():
    """
        Worker task: receives an image id
        fetches the image from storage, and sends it to the prediction endpoint
        pushes the result to the database
    """
    def __init__(self, endpoint_uri=None):
        if endpoint_uri is None and 'PREDICTION_ENDPOINT' in os.environ:
            self.endpoint_uri = os.environ['PREDICTION_ENDPOINT']            
        else:
            self.endpoint_uri = endpoint_uri


# TODO: ignore_result=True
@celery.task(ignore_result=True) #bind=True, name="predict_image", max_retries=3, default_retry_delay=10)
def predict_headstamps(endpoint, user_id, image_id, image_base64):
    payload = {'image': image_base64, 'render':False}
    headers = {
    'x-api-key': 'xxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxx',
    'Content-Type': 'application/json'
    }
    response = requests.post(endpoint, headers=headers, json=payload)
    result = json.loads(response.text)
    # TODO: failure cases
                
    image_in_db = Image.get_image_or_abort(image_id, user_id)  # ensure exists and available

    logging.info(f"Prediction response: {response.text}")
    try:
        if 'detections' in result:
            for detection in result['detections']:
                prediction_in_db = HeadstampPrediction(
                    image_id=image_id,
                    casing_box=json.dumps(detection["casing"]["box"]),
                    casing_confidence=detection["casing"]["confidence"],
                    primer_box=json.dumps(detection["primer"]["box"]),
                    primer_confidence=detection["primer"]["confidence"],        
                )
                db.session.add(prediction_in_db)
            #'task_id': result.task_id, 'status': 'pending', 'result': 'None'
        image_in_db.prediction_status = json.dumps({
            'status': 'success', 
            'updated': str(datetime.datetime.utcnow()), 
            'detections': len(result['detections']), 
            'inference_version': result['inference_version']
        })
    
        #db.session.add(image_in_db)
        db.session.commit()
    except:
        db.session.rollback()
        image_in_db.prediction_status = {'status': 'error', 'result': response.text}
        db.session.add(image_in_db)
        db.session.commit()    
    #return response.text


# https://learn.microsoft.com/en-us/samples/azure-samples/azure-samples-python-management/appservice/
# necessary environment variables:
# export AZURE_TENANT_ID="xxx"
# export AZURE_CLIENT_ID="xxx"
# export AZURE_CLIENT_SECRET="xxx"
# export SUBSCRIPTION_ID="xxx"


def service_manage(service_name):
    """
        Scheduled task to manage the prediction service.
        If no request has come in within the last 1 hour, spin down the service.
    """
    # Authenticate service principal

    # Check last request time

    # stop the service
    # https://learn.microsoft.com/en-us/rest/api/appservice/web-apps/stop


def service_start(service_name):
    """
        Trigger to launch the service if it isn't running.
    """
    # authenticate service principal

    # check service state

    # start the service
    # https://learn.microsoft.com/en-us/rest/api/appservice/web-apps/start


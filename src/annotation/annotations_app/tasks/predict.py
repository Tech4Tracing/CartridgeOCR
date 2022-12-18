from annotations_app.flask_app import celery
import requests
import os
from base64 import b64encode

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
        
@celery.task() #bind=True, name="predict_image", max_retries=3, default_retry_delay=10)
def predict_headstamps(endpoint, imageid, image_base64):
    payload = {'image': image_base64, 'render':False}
    headers = {
    'x-api-key': 'xxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxx',
    'Content-Type': 'application/json'
    }
    response = requests.post(endpoint, headers=headers, json=payload)
    return response.text

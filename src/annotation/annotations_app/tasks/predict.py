from annotations_app.flask_app import celery

class Predict:
    def __init__(self, model_uri):
        self.model_uri = model_uri
        # TODO: fetch model
        
        

    @celery.task()
    def predict_image(x):
        return x

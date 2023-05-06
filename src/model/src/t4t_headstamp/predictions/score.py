import sys
import json
import os
from azureml.contrib.services.aml_request import rawhttp
from azureml.contrib.services.aml_response import AMLResponse
t4t_path = os.path.join(os.path.dirname(__file__), '../..')
sys.path += ['.', '..', t4t_path]
from predictions.inference import Inference

inference = Inference()


def init():
    assert(os.getenv('AZUREML_MODEL_DIR') is not None)
    model_path = os.path.join(os.getenv('AZUREML_MODEL_DIR'), 'outputData')
    checkpoint = 'best_model.pth'
    print(f'loading {model_path} / {checkpoint}')
    inference.init(modelfolder=model_path, checkpoint=checkpoint)


@rawhttp
def run(request):
    # print("This is run()")
    # print("Request: [{0}]".format(request))
    if request.method == 'GET':
        # TODO: should GET requests be serviced?  Return 502 error?
        # respBody = str.encode(request.full_path)
        respBody = str.encode(json.dumps(request.headers()))
        return AMLResponse(respBody, 200)
    elif request.method == 'POST':
        reqBody = request.get_data(False).decode('utf-8')
        print('Received POST')
        result = inference.run(reqBody)
        # result = {'image': result, 'requestheaders': request.headers()}
        # resp = AMLResponse(json.dumps(result), 200)
        resp = AMLResponse(json.dumps(result), 200)
        resp.headers['Access-Control-Allow-Origin'] = "https://web-cartridgeocr-simra.azurewebsites.net"
        resp.headers['Access-Control-Allow-Headers'] = "Origin, X-Requested-With, Content-Type, Accept"
        return resp
    elif request.method == 'OPTIONS':

        resp = AMLResponse("", 200)
        resp.headers["Allow"] = "OPTIONS, GET, POST"
        resp.headers["Access-Control-Allow-Methods"] = "OPTIONS, GET, POST"
        resp.headers['Access-Control-Allow-Origin'] = "https://web-cartridgeocr-simra.azurewebsites.net"
        resp.headers['Access-Control-Allow-Headers'] = "Origin, X-Requested-With, Content-Type, Accept"
        return resp

    else:
        return AMLResponse("bad request", 500)

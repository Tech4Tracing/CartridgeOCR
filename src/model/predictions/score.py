import sys 
import json
import io
import base64
from PIL import Image, ImageDraw
import os
import torch
import torch.utils.data
import torchvision
from azureml.core.model import Model
from azureml.contrib.services.aml_request import AMLRequest, rawhttp
from azureml.contrib.services.aml_response import AMLResponse


sys.path += ['.', '..']


class Inference():
    def __init__(self) -> None:
        pass

    def predict(self, img, prediction):
        masksout = []
        casings = []
        primers = []
        for m_i, p in enumerate(prediction):
            i2 = torchvision.transforms.ToPILImage()(img)
            imgOut = Image.new('RGB', i2.size)
            imgOut.paste(i2, (0, 0))
            canvas = ImageDraw.Draw(imgOut)
            boxes = [(b, s, l) for b, s, l in zip(p['boxes'], p['scores'], p['labels']) if b[2] < i2.width if b[3] < i2.height if b[2] - b[0] > 20 if b[3] - b[1] > 20]
            casings = [(b, s, l) for b, s, l in zip(p['boxes'], p['scores'], p['labels']) if l == 1 if b[2] < i2.width if b[3] < i2.height if b[2] - b[0] > 20 if b[3] - b[1] > 20]
            primers = [(b, s, l) for b, s, l in zip(p['boxes'], p['scores'], p['labels']) if l == 2 if b[2] < i2.width if b[3] < i2.height if b[2] - b[0] > 20 if b[3] - b[1] > 20]
            masksout.append(imgOut)
        else:
            if len(masksout) > 0:
                i1 = Image.fromarray(img.mul(255).permute(1, 2, 0).byte().numpy())
                dst = Image.new('RGB', i1.size)
                dst.paste(i1, (0, 0))
                canvas = ImageDraw.Draw(dst)
                boxesOut = []
                primersOut = []
                for box, _, label in list(sorted(casings, key=(lambda x: x[1]), reverse=True)):
                    if any(map(lambda x: isRectangleOverlap(box, x), boxesOut)):
                        pass
                    else:
                        boxesOut.append(box)
                        canvas.rectangle(box, outline='red', width=3)

                for box, _, label in list(sorted(primers, key=(lambda x: x[1]), reverse=True)):
                    if any(map(lambda x: isContained(box, x), boxesOut)):
                        if not any(map(lambda x: isRectangleOverlap(box, x), primersOut)):
                            primersOut.append(box)
                            canvas.rectangle(box, outline='yellow', width=3)
                        return dst

    def init(self):
        global model, rt, isRectangleOverlap, isContained, get_transform, load_snapshot
        print('AZURE_MODEL_DIR', os.getenv('AZUREML_MODEL_DIR'))
        model_name = os.getenv("AZUREML_MODEL_DIR").split('/')[-2]
        print('model name:', model_name)
        model_path = Model.get_model_path(model_name)
        print('model_path', model_path)
        print(sys.path)
        try:
            sys.path.append('model')
            sys.path.append('model/training')
            sys.path.append('model/dataProcessing')
            from model.training.model_utils import rt, isRectangleOverlap, isContained, get_transform, load_snapshot
        except Exception as e:
            print('Not appended', str(e))
        
        self.model = load_snapshot(model_path + '/checkpoint.pth')
        
    def run(self, request):
        print("Request:" + request)
        parsed = json.loads(request)
        encodedImage = parsed["image"]
        
        try:      
            device = torch.device('cuda') if torch.cuda.is_available() else torch.device('cpu')
            self.model.to(device)
            self.model.eval()

            # Convert request from base64 to a PIL Image
            img_bytes = base64.b64decode(encodedImage)  # img_bytes is a binary image
            img_file = io.BytesIO(img_bytes)            # convert image to file-like object
            img = Image.open(img_file)                  # img is now PIL Image object
            transform = get_transform(train=False)        
            img, _ = transform(img, {'image_id':0,  'boxes':[],  'annotations':[]})
            
            with torch.no_grad():
                prediction = self.model([img.to(device)])
                masks = [p['masks'] for p in prediction]
                prediction = [dict([(k, v.cpu().numpy().tolist()) for k, v in x.items() if k != 'masks']) for x in prediction]
                print(masks, prediction)
                dst = self.predict(img, prediction)           

                in_mem_file = io.BytesIO()
                dst.save(in_mem_file, format="JPEG")  # temporary file to store image data
                dst_bytes = in_mem_file.getvalue()      # image in binary format
                dst_b64 = base64.b64encode(dst_bytes)   # encode in base64 for response
                return dst_b64.decode()
        except Exception as ex:
            print('Exception:')
            print(ex)
            return "Failed with error: " + ex


inference = Inference()


def init():
    inference.init()


@rawhttp
def run(request):
    # print("This is run()")
    # print("Request: [{0}]".format(request))
    if request.method == 'GET':
        # TODO: should GET requests be serviced?  Return 502 error?
        respBody = str.encode(request.full_path)
        return AMLResponse(respBody, 200)
    elif request.method == 'POST':
        reqBody = request.get_data(False).decode('utf-8')
        
        result = inference.run(reqBody)
        
        resp = AMLResponse(result, 200)
        resp.headers['Access-Control-Allow-Origin'] = "https://web-cartridgeocr-simra.azurewebsites.net"
        return resp
    else:
        return AMLResponse("bad request", 500)

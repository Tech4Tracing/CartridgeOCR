import os
import sys
import io
import base64
import json
import logging
from PIL import Image, ImageDraw
import torch.utils.data
import torchvision
from azureml.core.model import Model
from t4t_headstamp.training.model_utils import rt, isEllipseOverlap, isContained, get_transform, load_snapshot


class Inference():
    def __init__(self) -> None:
        self.max_width = 1080
        # Update with any major changes to inference method.
        self.INFERENCE_VERSION = "1.0"

    def predict(self, img, prediction, threshold=0.5, render=False):
        casings = []
        primers = []
        for m_i, p in enumerate(prediction):
            # TODO: can we avoid this by just comparing with img dimensions?
            i2 = torchvision.transforms.ToPILImage()(img)
            casings += [(b, s, l) for b, s, l in zip(p['boxes'], p['scores'], p['labels']) 
                        if l == 1 
                        if s > threshold
                        if b[2] < i2.width 
                        if b[3] < i2.height 
                        if b[2] - b[0] > 20 
                        if b[3] - b[1] > 20 ]
            primers += [(b, s, l) for b, s, l in zip(p['boxes'], p['scores'], p['labels']) 
                        if l == 2 
                        if s > threshold
                        if b[2] < i2.width 
                        if b[3] < i2.height 
                        if b[2] - b[0] > 20 
                        if b[3] - b[1] > 20 ]
            # TODO: under what circumstances would there be more than one item in prediction?  
            # Maybe this would happen if img were a tensor of multiple images.          
        else:
            detectionsOut = []
            dst = None
            if len(casings) > 0:
                dst = None
                canvas = None
                if render:
                    i1 = Image.fromarray(img.mul(255).permute(1, 2, 0).byte().numpy())
                    dst = Image.new('RGBA', i1.size, (0,0,0,0))
                    # We're going to draw an overlay and paste it on top later.                    
                    canvas = ImageDraw.Draw(dst)
                casingsOut = []
                
                for casing, score, label in list(sorted(casings, key=(lambda x: x[1]), reverse=True)):
                    # Skip if it overlaps an existing output.                   
                    if any(map(lambda x: isEllipseOverlap(casing, x[0]), casingsOut)):
                        pass
                    else:
                        casingsOut.append((casing,score))                        
                
                for primer, score, label in list(sorted(primers, key=(lambda x: x[1]), reverse=True)):
                    toRemove = None
                    # Match each primer detection with an available casing.
                    # If no surrounding casing exists, reject it.
                    for casing in casingsOut:
                        if isContained(primer, casing[0]):
                            detectionsOut.append((casing, (primer,score)))
                            if canvas:
                                canvas.ellipse(casing, outline='red', fill=(255,0,0,50), width=5)
                                canvas.ellipse(primer, outline='yellow', fill=(255,255,0,50), width=5)
                            # remove the casing from casingsOut so we don't reassign it.
                            toRemove = casing
                            break
                    if toRemove:
                        casingsOut.remove(casing)

                # TODO: if any casings remain, we could optionally return them as well.

                # Draw the overlay on top of a new image
                if render:
                    dst = Image.alpha_composite(i1.convert("RGBA"), dst)
                
            return dst, detectionsOut
    def init(self, modelfolder=None, checkpoint='checkpoint.pth'):
        global model, rt, isRectangleOverlap, isContained, get_transform, load_snapshot
        if modelfolder is None:
            print('AZUREML_MODEL_DIR', os.getenv('AZUREML_MODEL_DIR'))
            model_name = os.getenv("AZUREML_MODEL_DIR").split('/')[-2]
            model_path = os.path.join(os.getenv('AZUREML_MODEL_DIR'), 'outputData')
            sys.path.append('model')
            sys.path.append('model/training')
            sys.path.append('model/dataProcessing')
        else:
            model_name = modelfolder
            model_path = model_name
            sys.path.append('..')

        print('model name:', model_name)
        print('model_path', model_path)

        self.model = load_snapshot(os.path.join(model_path, checkpoint))
        assert self.model

    def run_inference(self, img):
        device = torch.device('cuda') if torch.cuda.is_available() else torch.device('cpu')
        self.model.to(device)
        self.model.eval()
        with torch.no_grad():
            prediction = self.model([img.to(device)])
            # masks = [p['masks'] for p in prediction]
            prediction = [dict([(k, v.cpu().numpy().tolist()) for k, v in x.items() if k != 'masks']) for x in prediction]
        return prediction

    def run(self, request):
        """Processes an inference request.
        Inputs:
        request (string): a json-formatted payload:
        {
            'image': <base 64 encoded input image>,
            'render': boolean indicating whether an image with the rendered boxes should be returned.
        }
        Returns:
        Dictionary with results:
        {
            'inference_version': <inference version>,
            'image': <optional base 64 encoded output image>,
            'detections': <list of detections, each with schema:
                {'casing': {'box':<rectangle>, 'confidence': <float>},
                 'primer': {'box': <rectangle>, 'confidence': <float>}}>
        }
        bounding boxes are encoded as [x0, y0, x1, y1]
        each box coordinate is in the range [0,1)
        note for some headstamps a casing might be returned without a primer.
        """
        # print("Request" + request)
        parsed = json.loads(request)
        encodedImage = parsed["image"]
        render = parsed.get("render", False)

        try:
            # Convert request from base64 to a PIL Image
            img_bytes = base64.b64decode(encodedImage)  # img_bytes is a binary image
            img_file = io.BytesIO(img_bytes)            # convert image to file-like object
            img = Image.open(img_file)                  # img is now PIL Image object
            width, height = img.size
            if width > self.max_width:
                logging.info(f'Resizing from {width}')
                newsize = (self.max_width, int(self.max_width / width * height))
                img = img.resize(newsize)
                width, height = img.size
            logging.info(f'Image size {img.size}')
            transform = get_transform(train=False)
            img, _ = transform(img, {'image_id': 0, 'boxes': [], 'annotations': []})
            print('running inference')
            prediction = self.run_inference(img)
            # print(masks, prediction)
            dst, detections = self.predict(img, prediction, render=render)

            dst_b64 = None
            if render:
                assert dst is not None
                in_mem_file = io.BytesIO()
                dst = dst.convert("RGB")
                dst.save(in_mem_file, format="JPEG")  # temporary file to store image data
                dst_bytes = in_mem_file.getvalue()      # image in binary format
                dst_b64 = base64.b64encode(dst_bytes)   # encode in base64 for response
            logging.info(f'detected {len(detections)}')

            # TODO: this should probably move to predict() but at that point we have a tensor in hand.
            # It's easier to reliably get the image width and height here.
            def normalize(bs):
                b, score = bs
                return {
                    'confidence': score, 
                    'box': list(map(lambda x: x[0] / x[1], zip(b, [width, height, width, height]))) 
                }

            def normalize_detection(detection):
                casing, primer = detection
                return {
                    'casing': normalize(casing),
                    'primer': normalize(primer)
                }

            return {
                'image': dst_b64.decode() if dst_b64 else None,
                'detections': list(map(normalize_detection, detections)),
                'inference_version': self.INFERENCE_VERSION                
            }

        except Exception as ex:
            logging.error(f'Exception: {ex}')
            return {'error': str(ex)}

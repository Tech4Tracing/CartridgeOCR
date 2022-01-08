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


class Inference():
    def __init__(self) -> None:
        self.max_width = 1080

    def predict(self, img, prediction):
        masksout = []
        casings = []
        primers = []
        for m_i, p in enumerate(prediction):
            i2 = torchvision.transforms.ToPILImage()(img)
            imgOut = Image.new('RGB', i2.size)
            imgOut.paste(i2, (0, 0))
            canvas = ImageDraw.Draw(imgOut)
            # boxes = [(b, s, l) for b, s, l in zip(p['boxes'], p['scores'], p['labels']) if b[2] < i2.width if b[3] < i2.height if b[2] - b[0] > 20 if b[3] - b[1] > 20]
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
                return dst, boxesOut, primersOut

    def init(self, modelfolder=None, checkpoint='checkpoint.pth'):
        global model, rt, isRectangleOverlap, isContained, get_transform, load_snapshot
        if modelfolder is None:
            print('AZURE_MODEL_DIR', os.getenv('AZUREML_MODEL_DIR'))
            model_name = os.getenv("AZUREML_MODEL_DIR").split('/')[-2]
            model_path = Model.get_model_path(model_name)
            sys.path.append('model')
            sys.path.append('model/training')
            sys.path.append('model/dataProcessing')
        else:
            model_name = modelfolder
            model_path = model_name
            sys.path.append('..')

        print('model name:', model_name)
        print('model_path', model_path)
        from model.training.model_utils import rt, isRectangleOverlap, isContained, get_transform, load_snapshot

        self.model = load_snapshot(os.path.join(model_path, checkpoint))

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
            'image': <base 64 encoded input image>
        }
        Returns:
        Dictionary with results:
        {
            'image': <base 64 encoded output image>,
            'boxes': <list of casing bounding boxes>,
            'primers': <list of primer bounding boxes>
        }
        bounding boxes are encoded as [x0, y0, x1, y1]
        each box coordinate is in the range [0,1)
        """
        # print("Request" + request)
        parsed = json.loads(request)
        encodedImage = parsed["image"]

        try:
            # Convert request from base64 to a PIL Image
            img_bytes = base64.b64decode(encodedImage)  # img_bytes is a binary image
            img_file = io.BytesIO(img_bytes)            # convert image to file-like object
            # explicitly convert to RGB to ensure it's not a single channel
            img = Image.open(img_file).convert("RGB")   # img is now PIL Image object
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
            dst, boxes, primers = self.predict(img, prediction)

            in_mem_file = io.BytesIO()
            dst.save(in_mem_file, format="JPEG")  # temporary file to store image data
            dst_bytes = in_mem_file.getvalue()      # image in binary format
            dst_b64 = base64.b64encode(dst_bytes)   # encode in base64 for response
            logging.info(f'detected {len(boxes)} boxes and {len(primers)} primers')

            # TODO: this should probably move to predict() but at that point we have a tensor in hand.
            # It's easier to reliably get the image width and height here.
            def normalize(b):
                return list(map(lambda x: x[0] / x[1], zip(b, [width, height, width, height])))

            return {
                'image': dst_b64.decode(),
                'boxes': list(map(normalize, boxes)),
                'primers': list(map(normalize, primers))
            }
        except Exception as ex:
            print('Exception:')
            print(ex)
            return "Failed with error: " + ex

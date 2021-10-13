import sys
sys.path+=['.','..']
from PIL import Image
import numpy as np, os, torch, torch.utils.data, torchvision
from PIL import Image, ImageDraw
from azureml.core.model import Model
# from training.model_utils import rt, get_transform, isRectangleOverlap, isContained, get_transform, load_snapshot

def predict(img, prediction):
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

def init():
    global model, rt, isRectangleOverlap, isContained, get_transform, load_snapshot
    model_name = os.getenv("AZUREML_MODEL_DIR").split('/')[-2]
    model_path = Model.get_model_path(model_name)
    print(sys.path)
    try:
        sys.path.append('src/training')
        sys.path.append('src/dataProcessing')
        from training.model_utils import rt, isRectangleOverlap, isContained, get_transform, load_snapshot
    except:
        print('Not appended')
    
    model = load_snapshot(model_path + '/checkpoint.pth')
    
def run(image):
    # img = Image.open(image_path).convert('RGB')
    device = torch.device('cuda') if torch.cuda.is_available() else torch.device('cpu')
    transform = get_transform(train=False)
    with torch.no_grad():
        img, _ = transform(image, {'image_id':0,  'boxes':[],  'annotations':[]})
        prediction = model([img.to(device)])
        masks = [p['masks'] for p in prediction]
        prediction = [dict([(k, v.cpu().numpy().tolist()) for k, v in x.items() if k != 'masks']) for x in prediction]
        print(masks, prediction)
        dst = predict(img, prediction)
        folder = rt('outputData')
        fn = os.path.join(folder, 'predictions.png')
        dst.save(fn)
        return dst


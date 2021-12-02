import os
import torch
import torch.utils.data
import sys
sys.path += ['.', './model']
from dataProcessing.coco_utils import CocoDetection
from training.model_utils import rt, get_transform, isRectangleOverlap, isContained, get_transform
# from predictions import predict
from predictions.inference import Inference
import argparse
import tqdm

parser = argparse.ArgumentParser()
parser.add_argument('--seed', type=int, default=1)
parser.add_argument('--modelfolder', default=rt('src/outputData/'))
parser.add_argument('--checkpoint', default='checkpoint.pth')
parser.add_argument('--data', default=rt('src/data/dataset/coco_xformed.json'))
parser.add_argument('--split', type=float, default=1.0, help='fraction of examples to include as test examples')
parser.add_argument('output', default='predictions')

args = parser.parse_args()
datafolder = os.path.dirname(args.data)
dataset = CocoDetection(datafolder, args.data, get_transform(train=True))
dataset_test = CocoDetection(datafolder, args.data, get_transform(train=False))

torch.manual_seed(args.seed)
indices = torch.randperm(len(dataset)).tolist()
cutoff = int(args.split * len(dataset))
dataset = torch.utils.data.Subset(dataset, indices[:-cutoff])
dataset_test = torch.utils.data.Subset(dataset_test, indices[-cutoff:])

os.makedirs(args.output, exist_ok=True)
inference = Inference()
inference.init(modelfolder=args.modelfolder, checkpoint=args.checkpoint)

with open(os.path.join(args.output, 'predictions.txt'), 'w', encoding='utf-8') as outP:
    for ix, (img, _) in tqdm.tqdm(enumerate(dataset_test), total=len(indices[-cutoff:])):
        prediction = inference.run_inference(img)        
        (dst, boxes, primers) = inference.predict(img, prediction)
        fn = os.path.join(args.output, 'prediction_{}.png'.format(ix))
        dst.save(fn)

import os
import torch
import torch.utils.data
import json
from PIL import Image, ImageDraw
from dataProcessing.coco_utils import CocoDetection
from training.model_utils import rt, get_transform, isRectangleOverlap, isContained,get_transform, load_snapshot
from predictions import predict

folder = rt('src/outputData')
epoch = 9 #this can be changed 

dataset = CocoDetection(rt('src/data/dataset'), rt('src/data/dataset/coco_xformed.json'), get_transform(train=True))
dataset_test = CocoDetection(rt('src/data/dataset'), rt('src/data/dataset/coco_xformed.json'), get_transform(train=False))

torch.manual_seed(1)
indices = torch.randperm(len(dataset)).tolist()
cutoff = max(10,int(0.1*len(dataset)))
dataset = torch.utils.data.Subset(dataset, indices[:-cutoff])
dataset_test = torch.utils.data.Subset(dataset_test, indices[-cutoff:])

with open(os.path.join(folder,'predictions_{}.txt'.format(epoch)),'r', encoding='utf-8') as outP:
    for (ix,((img,_), line)) in enumerate(zip(dataset_test, outP)):
        prediction = json.loads(line)
        print(prediction)   
        dst = predict(img, prediction)
        fn = os.path.join(folder,'training_Predictions_{}_{}.png'.format(epoch,ix))
        dst.save(fn)
    
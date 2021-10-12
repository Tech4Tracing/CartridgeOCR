import os
import sys
sys.path += ['.', '..', './src']
import torch
import torch.utils.data
from training.engine import evaluate
import dataProcessing.utils as utils
from dataProcessing.coco_utils import CocoDetection
from training.model_utils import rt, get_transform, get_instance_segmentation_model
import sys
import torch

datapath = rt('data/dataset')
labelpath = rt('data/labeldata')
outputpath = rt('outputData')


dataset = CocoDetection(datapath, os.path.join(labelpath, 'coco_xformed.json'), get_transform(train=True))
dataset_test = CocoDetection(datapath, os.path.join(labelpath, 'coco_xformed.json'), get_transform(train=False))

# split the dataset in train and test set
torch.manual_seed(1)
indices = torch.randperm(len(dataset)).tolist()
cutoff = max(10, int(0.1 * len(dataset)))
dataset = torch.utils.data.Subset(dataset, indices[:-cutoff])
dataset_test = torch.utils.data.Subset(dataset_test, indices[-cutoff:])

# define training and validation data loaders
data_loader = torch.utils.data.DataLoader(
    dataset, batch_size=2, shuffle=True, num_workers=0,
    collate_fn=utils.collate_fn)
print(f'data loader has {len(data_loader)} batches')
data_loader_test = torch.utils.data.DataLoader(
    dataset_test, batch_size=1, shuffle=False, num_workers=0,
    collate_fn=utils.collate_fn)

device = torch.device('cuda') if torch.cuda.is_available() else torch.device('cpu')

num_classes = 3

# get the model using our helper function
model = get_instance_segmentation_model(num_classes)
# move model to the right device
# chk_path = '/mnt/c/Users/rober/Downloads/checkpoint.pth'
chk_path = r"c:\Users\rober\Downloads\checkpoint.pth"
checkpoint = torch.load(chk_path, map_location=torch.device('cpu'))
model.load_state_dict(checkpoint['model'])

model.to(device)

evaluate(model, data_loader_test, device=device)

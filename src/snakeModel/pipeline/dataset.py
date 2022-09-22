import torch
import torch.nn as nn
import os
import pandas as pd
import torchvision
import mmcv
import torch
import torch.nn as nn
import os
import pandas as pd
from torchvision.io import read_image
from torch.utils.data import Dataset
import pickle
import cv2
from PIL import Image
import torch.nn as nn
from torchvision import transforms
from mmocr.models.textdet.losses import TextSnakeLoss
import numpy as np

t = transforms.Compose([
    transforms.ToTensor(),
    transforms.Resize((800,800))]
)

lossMaskNames = ['gt_text_mask', 'gt_center_region_mask', 'gt_mask', 'gt_radius_map', 'gt_sin_map', 'gt_cos_map']

class SnakeModelDataset(Dataset):
    def __init__(self, annotationsPath, isTrain:bool):
        print(annotationsPath)
        with open(annotationsPath, 'rb') as f:
            self.data = pickle.load(f)
            if isTrain:
                self.data = self.data[0:int(len(self.data) * .7)]
            else: 
                self.data = self.data[int(len(self.data) * .7):]
        self.loss = TextSnakeLoss()

    def __len__(self):
        return len(self.data)

    def __getitem__(self, idx):
        annotation = self.data[idx]
        imgPath = annotation['file_path']
        image = Image.open(imgPath)
        image = t(image)
        target_sz = (800,800)
        masksToReturn = {}
        for key in lossMaskNames:
            masksToReturn[key] = annotation[key]
        # bitmasks = self.loss.bitmasks2tensor(masksToReturn, target_sz)
        # masksToReturn = [self.loss.bitmasks2tensor(bitmasks = annotation[key], target_sz = target_sz) for key in annotation['mask_field_names']]
        # gt_text_mask = annotation['gt_text_mask'] 'gt_center_region_mask', 'gt_mask', 'gt_radius_map', 'gt_sin_map', and 'gt_cos_map'
        print(type(masksToReturn))
        return [image, masksToReturn]
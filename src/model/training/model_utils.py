import os
import dataProcessing.utils as utils
import dataProcessing.transforms as T
from dataProcessing.coco_utils import ConvertCocoPolysToMask
from torchvision.models.detection.faster_rcnn import FastRCNNPredictor
from torchvision.models.detection.mask_rcnn import MaskRCNNPredictor
import torchvision
import torch


def rt(p):
    return os.path.join('../', p)


def get_instance_segmentation_model(num_classes):
    model = torchvision.models.detection.maskrcnn_resnet50_fpn(pretrained=True)
    in_features = model.roi_heads.box_predictor.cls_score.in_features
    model.roi_heads.box_predictor = FastRCNNPredictor(in_features, num_classes)
    in_features_mask = model.roi_heads.mask_predictor.conv5_mask.in_channels
    hidden_layer = 256
    model.roi_heads.mask_predictor = MaskRCNNPredictor(in_features_mask, hidden_layer, num_classes)
    return model


def get_transform(train):
    transforms = []
    transforms.append(T.Resize())
    transforms.append(ConvertCocoPolysToMask())
    transforms.append(T.ToTensor())
    if train:
        transforms.append(T.RandomHorizontalFlip(0.5))
    return T.Compose(transforms)


def isRectangleOverlap(R1, R2):
    if (R1[0] >= R2[2]) or (R1[2] <= R2[0]) or (R1[3] <= R2[1]) or (R1[1] >= R2[3]):
        return False
    return True


def isContained(R1, R2):
    if (R1[0] > R2[0]) and (R1[2] < R2[2]) and (R1[3] < R2[3]) and (R1[1] > R2[1]):
        return True
    return False


def save_snapshot(checkpoint, output_dir, fold, epoch):
    utils.save_on_master(checkpoint, os.path.join(output_dir, 'model_{}_{}.pth'.format(fold, epoch)))
    utils.save_on_master(checkpoint, os.path.join(output_dir, 'checkpoint.pth'))


def load_snapshot(checkpoint):
    '''Loads a snapshot. Call model.to(device) to move to GPU'''
    cp = torch.load(checkpoint, map_location=torch.device('cpu'))
    num_classes = 3
    model = get_instance_segmentation_model(num_classes)
    model.load_state_dict(cp['model'])
    return model

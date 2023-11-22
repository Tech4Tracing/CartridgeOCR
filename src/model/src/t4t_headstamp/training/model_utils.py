import os
import t4t_headstamp.dataProcessing.utils as utils
import t4t_headstamp.dataProcessing.transforms as T
from t4t_headstamp.dataProcessing.coco_utils import ConvertCocoPolysToMask
from torchvision.models.detection.faster_rcnn import FastRCNNPredictor
from torchvision.models.detection.mask_rcnn import MaskRCNNPredictor
import torchvision
import torch


def rt(p):
    return os.path.join('../', p)


def get_instance_segmentation_model(num_classes, load_pretrained=True):
    model = torchvision.models.detection.maskrcnn_resnet50_fpn(pretrained=load_pretrained, progress=False)
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

# https://github.com/NickAlger/nalger_helper_functions/blob/master/tutorial_notebooks/ellipsoid_intersection_test_tutorial.ipynb
import numpy as np
from scipy.linalg import eigh
from scipy.optimize import minimize_scalar

def ellipsoid_intersection_test(Sigma_A, Sigma_B, mu_A, mu_B, tau):
    lambdas, Phi, v_squared = ellipsoid_intersection_test_helper(Sigma_A, Sigma_B, mu_A, mu_B)
    res = minimize_scalar(ellipsoid_K_function,
                          bracket=[0.0, 0.5, 1.0],
                          args=(lambdas, v_squared, tau))
    return (res.fun[0] >= 0)


def ellipsoid_intersection_test_helper(Sigma_A, Sigma_B, mu_A, mu_B):
    lambdas, Phi = eigh(Sigma_A, b=Sigma_B)
    v_squared = np.dot(Phi.T, mu_A - mu_B) ** 2
    return lambdas, Phi, v_squared


def ellipsoid_K_function(ss, lambdas, v_squared, tau):
    ss = np.array(ss).reshape((-1,1))
    lambdas = np.array(lambdas).reshape((1,-1))
    v_squared = np.array(v_squared).reshape((1,-1))
    return 1.-(1./tau**2)*np.sum(v_squared*((ss*(1.-ss))/(1.+ss*(lambdas-1.))), axis=1)


def isEllipseOverlap(R1, R2):
    if not isRectangleOverlap(R1, R2):
        return False
    mu_A = np.array([(R1[0]+R1[2])/2, (R1[1]+R1[3])/2])
    mu_B = np.array([(R2[0]+R2[2])/2, (R2[1]+R2[3])/2])
    sigma_A = np.array([[1.0/(R1[2]-R1[0]), 0], [0, 1.0/(R1[3]-R1[1])]])
    sigma_B = np.array([[1.0/(R2[2]-R2[0]), 0], [0, 1.0/(R2[3]-R2[1])]])
    return ellipsoid_intersection_test(sigma_A, sigma_B, mu_A, mu_B, 1.0)    

def isContained(R1, R2):
    if (R1[0] > R2[0]) and (R1[2] < R2[2]) and (R1[3] < R2[3]) and (R1[1] > R2[1]):
        return True
    return False


def save_snapshot(checkpoint, output_dir, fold, epoch, is_best=False):
    utils.save_on_master(checkpoint, os.path.join(output_dir, 'model_{}_{}.pth'.format(fold, epoch)))
    utils.save_on_master(checkpoint, os.path.join(output_dir, 'checkpoint.pth'))
    if is_best:
        utils.save_on_master(checkpoint, os.path.join(output_dir, 'best_model.pth'))


def load_snapshot(checkpoint):
    '''Loads a snapshot. Call model.to(device) to move to GPU'''
    cp = torch.load(checkpoint, map_location=torch.device('cpu'))
    num_classes = 3
    model = get_instance_segmentation_model(num_classes, load_pretrained=False)
    model.load_state_dict(cp['model'])
    return model

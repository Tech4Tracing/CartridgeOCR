from cgitb import text
from json import load
import torch
import numpy as np
from mmocr.apis import init_detector
from mmocr.utils.model import revert_sync_batchnorm
import os
from mmocr.models.textdet.losses import *
from argparse import ArgumentParser, Namespace
import pickle
from pipeline.dataset import SnakeModelDataset
from torch.utils.data import DataLoader
from mmocr.datasets.pipelines.textdet_targets import TextSnakeTargets
import torch.optim as optim

class DummyObj():
    def __init__(self):
        self.masks = []

    def __str__(self) -> str:
        return str(self.masks)


textdet_models = {
            'DB_r18': {
                'config':
                'dbnet/dbnet_r18_fpnc_1200e_icdar2015.py',
                'ckpt':
                'dbnet/'
                'dbnet_r18_fpnc_sbn_1200e_icdar2015_20210329-ba3ab597.pth'
            },
            'DB_r50': {
                'config':
                'dbnet/dbnet_r50dcnv2_fpnc_1200e_icdar2015.py',
                'ckpt':
                'dbnet/'
                'dbnet_r50dcnv2_fpnc_sbn_1200e_icdar2015_20211025-9fe3b590.pth'
            },
            'DBPP_r50': {
                'config':
                'dbnetpp/dbnetpp_r50dcnv2_fpnc_1200e_icdar2015.py',
                'ckpt':
                'dbnet/'
                'dbnetpp_r50dcnv2_fpnc_1200e_icdar2015-20220502-d7a76fff.pth'
            },
            'DRRG': {
                'config':
                'drrg/drrg_r50_fpn_unet_1200e_ctw1500.py',
                'ckpt':
                'drrg/drrg_r50_fpn_unet_1200e_ctw1500_20211022-fb30b001.pth'
            },
            'FCE_IC15': {
                'config':
                'fcenet/fcenet_r50_fpn_1500e_icdar2015.py',
                'ckpt':
                'fcenet/fcenet_r50_fpn_1500e_icdar2015_20211022-daefb6ed.pth'
            },
            'FCE_CTW_DCNv2': {
                'config':
                'fcenet/fcenet_r50dcnv2_fpn_1500e_ctw1500.py',
                'ckpt':
                'fcenet/' +
                'fcenet_r50dcnv2_fpn_1500e_ctw1500_20211022-e326d7ec.pth'
            },
            'MaskRCNN_CTW': {
                'config':
                'maskrcnn/mask_rcnn_r50_fpn_160e_ctw1500.py',
                'ckpt':
                'maskrcnn/'
                'mask_rcnn_r50_fpn_160e_ctw1500_20210219-96497a76.pth'
            },
            'MaskRCNN_IC15': {
                'config':
                'maskrcnn/mask_rcnn_r50_fpn_160e_icdar2015.py',
                'ckpt':
                'maskrcnn/'
                'mask_rcnn_r50_fpn_160e_icdar2015_20210219-8eb340a3.pth'
            },
            'MaskRCNN_IC17': {
                'config':
                'maskrcnn/mask_rcnn_r50_fpn_160e_icdar2017.py',
                'ckpt':
                'maskrcnn/'
                'mask_rcnn_r50_fpn_160e_icdar2017_20210218-c6ec3ebb.pth'
            },
            'PANet_CTW': {
                'config':
                'panet/panet_r18_fpem_ffm_600e_ctw1500.py',
                'ckpt':
                'panet/'
                'panet_r18_fpem_ffm_sbn_600e_ctw1500_20210219-3b3a9aa3.pth'
            },
            'PANet_IC15': {
                'config':
                'panet/panet_r18_fpem_ffm_600e_icdar2015.py',
                'ckpt':
                'panet/'
                'panet_r18_fpem_ffm_sbn_600e_icdar2015_20210219-42dbe46a.pth'
            },
            'PS_CTW': {
                'config': 'psenet/psenet_r50_fpnf_600e_ctw1500.py',
                'ckpt':
                'psenet/psenet_r50_fpnf_600e_ctw1500_20210401-216fed50.pth'
            },
            'PS_IC15': {
                'config':
                'psenet/psenet_r50_fpnf_600e_icdar2015.py',
                'ckpt':
                'psenet/psenet_r50_fpnf_600e_icdar2015_pretrain-eefd8fe6.pth'
            },
            'TextSnake': {
                'config':
                'textsnake/textsnake_r50_fpn_unet_1200e_ctw1500.py',
                'ckpt':
                'textsnake/textsnake_r50_fpn_unet_1200e_ctw1500-27f65b64.pth'
            },
            'Tesseract': {}
        }

downloadUrlBase = 'https://download.openmmlab.com/mmocr/textdet/'
device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
img_metas = [{'dummyMetaKey': 'dummyMetaValue'}]

def parseArgs():
    parser = ArgumentParser()
    parser.add_argument(
        '--modelName',
        type=str,
        default='TextSnake',
        help='Model Name')

    parser.add_argument(
        '--inputPath',
        type=str,
        default='',
        help='Input path for the data')
    args = parser.parse_args()
    return args    

def loadModel(modelName = 'TextSnake'):
    if modelName in textdet_models:
        config_dir = os.path.join(os.path.dirname(os.path.dirname(os.getcwd())), 'mmocr', 'configs', 'textdet')  
        det_configPath = os.path.join(config_dir, textdet_models[modelName]['config'])
        det_ckpt = f'{downloadUrlBase}{textdet_models[modelName]["ckpt"]}'
        detect_model = init_detector(det_configPath, det_ckpt, device=device)
        return revert_sync_batchnorm(detect_model)
    else:
        print('Unsupported model')
        exit()

# File path of the pickle file to train from
def loadDataLoader(filePath, isTrain):
        if os.path.exists(filePath):
            dataSet =  SnakeModelDataset(filePath, isTrain)
            #TODO Figure out a way to pad the masks in a way that lets them be uniform and still pass to textsnake loss properly
            return DataLoader(dataSet, 1, shuffle=False)

def main():
    args = parseArgs()
    model = loadModel(**vars(args))
    dataLoader = loadDataLoader(args.inputPath, True)
    train(model, dataLoader)

def train(model, dataLoader, epochs = 10):
    print(f'Training on device {device}')
    optimizer = optim.SGD(model.parameters(), lr=0.001, momentum=0.9)
    targetGenerator = TextSnakeTargets()
    for e in range(epochs):
        for img, gt_masks, gt_mask_ignore in dataLoader:
            optimizer.zero_grad()
            target = {}
            target['gt_masks'] = DummyObj()
            target['gt_masks'].masks = gt_masks[0].tolist()
            target['gt_masks_ignore'] = DummyObj()
            target['gt_masks_ignore'].masks = gt_mask_ignore[0].tolist()
            target['img_shape'] = (800,800,3)
            target['mask_fields'] = []
            target = targetGenerator.generate_targets(target)
            output = model(img, img_metas, 
                gt_text_mask = [target['gt_text_mask']], 
                gt_center_region_mask = [target['gt_center_region_mask']],
                gt_mask = [target['gt_mask']],
                gt_radius_map = [target['gt_radius_map']],  
                gt_sin_map = [target['gt_sin_map']],
                gt_cos_map = [target['gt_cos_map']])
            loss = output['loss_text'] + output['loss_center'] + output['loss_radius'] + output['loss_sin'] + output['loss_cos'] 
            loss.backward()
            optimizer.step()



if __name__ == '__main__':
    main()

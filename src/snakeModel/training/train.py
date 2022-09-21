import torch
import numpy as np
from mmocr.apis import init_detector
from mmocr.utils.model import revert_sync_batchnorm

textSnakeModelWeightsPath = 'textsnake/textsnake_r50_fpn_unet_1200e_ctw1500-27f65b64.pth'
downloadUrlBase = 'https://download.openmmlab.com/mmocr/textdet/'
device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')

def train(model, criterion, epochs):
    


def loadModel(modelName = 'textsnake'):
    if modelName == 'textsnake':
        det_ckpt = f'{downloadUrlBase}{textSnakeModelWeightsPath}'
        detect_model = init_detector(
            'src\snakeModel\config\textsnake_r50_fpn_unet_1200e_ctw1500.py', det_ckpt, device=device)
        return revert_sync_batchnorm(detect_model)
    else:
        print('Unsupported model')
        exit()

def main(modelName = 'textsnake'):

from ast import parse
from math import sqrt
from re import X
from typing import final
import torch
import numpy as np
import os
import json
from mmocr.datasets.pipelines import TextSnakeTargets
from PIL import Image
import cv2

class Point():
    def __init__(self, point) -> None:
        self.x = point['x']
        self.y = point['y']
    
    def getNumpy(self):
        return np.array([self.x, self.y])

class DummyObj():
    def __init__(self):
        self.masks = []

    def __str__(self) -> str:
        return str(self.masks)

def displayRadialPolygon(center, nearPoint, farPoint, pointsList, image):
    mask = np.zeros((image.shape[0], image.shape[1], 3), dtype=np.uint8)
    # print((center.x * image.shape[1], center.y * image.shape[0]))
    toDisplay = np.array(pointsList).reshape(-1,2).astype(np.int32).reshape(1, -1, 2)
    print(toDisplay)
    cv2.fillPoly(mask, toDisplay, (255, 255, 255))
    mask = cv2.circle(mask, (int(center.x * image.shape[0]), int(center.y * image.shape[1])), 6, (255, 0, 0), 1)
    mask = cv2.circle(mask, (int(nearPoint.x * image.shape[0]), int(nearPoint.y * image.shape[1])), 6, (0, 255, 0), 1)
    mask = cv2.circle(mask, (int(farPoint.x * image.shape[0]), int(farPoint.y * image.shape[1])), 6, (0, 0, 255), 1)
    while (mask.shape[0] > 1500 or mask.shape[1] > 1500):
        mask = cv2.resize(mask, (int(mask.shape[0] * .5), int(mask.shape[1] * .5)))
    cv2.imshow('', mask)
    cv2.waitKey(0) 
    cv2.destroyAllWindows()

def extractBoxBorder(geometry, image):

    geometry = json.loads(geometry)
    x1 = geometry[0]['x']
    y1 = geometry[0]['y']
    x2 = geometry[0]['x']
    y2 = geometry[1]['y']
    x3 = geometry[1]['x']
    y3 = geometry[1]['y']
    x4 = geometry[1]['x']
    y4 = geometry[0]['y']
    pointsList = [x1, y1, x2, y2, x3, y3, x4, y4]
    for idx, x in enumerate(pointsList):
        if idx == 0: #x
            x *= image.shape[1]
        else: #y
            x *= image.shape[0]
    return np.array(pointsList)


##Todo fix order of border coords
def extractRadialBorder(geometry, image):
    """
    Input: list of 3 dictionaries of coordinates
    Output:  1d np array of coordinates
    Example: [x1, y1, x2, y2...]
    """
    geometry = json.loads(geometry)
    center = Point(geometry[0])
    point1 = Point(geometry[1])
    point2 = Point(geometry[2])
    print('-' * 100)
    print((center.x * image.shape[0], center.y * image.shape[1]))
    print((point1.x * image.shape[0], point1.y * image.shape[1]))
    print((point2.x * image.shape[0], point2.y * image.shape[1]))
    radius1 = sqrt((center.x - point1.x) ** 2 + (center.y - point1.y) ** 2)
    radius2 = sqrt((center.x - point2.x) ** 2 + (center.y - point2.y) ** 2)
    if radius1 >= radius2:
        farPoint = point1
        nearPoint = point2
        farRadius = radius1
        nearRadius = radius2
    else :
        farPoint = point2
        nearPoint = point1
        farRadius = radius2
        nearRadius = radius1

    farRadiusDelta = farPoint.getNumpy() - center.getNumpy()
    nearRadiusDelta = nearPoint.getNumpy() - center.getNumpy()

    unitVectorFarDelta = farRadiusDelta / (farRadiusDelta ** 2).sum() ** 0.5
    unitVectorNearDelta = nearRadiusDelta / (nearRadiusDelta ** 2).sum() ** 0.5

    farAngleNearRadiusPoint = center.getNumpy() + unitVectorNearDelta * farRadius
    nearAngleFarRadiusPoint = center.getNumpy() + unitVectorFarDelta * nearRadius

    averageAngleUnitVector = (unitVectorFarDelta + unitVectorNearDelta) / ((unitVectorFarDelta + unitVectorNearDelta) ** 2).sum() ** .5 
    averageAngleFarPoint = center.getNumpy() + averageAngleUnitVector * farRadius
    averageAngleNearPoint = center.getNumpy() + averageAngleUnitVector * nearRadius
    pointsList = [farPoint.x, farPoint.y, 
    nearAngleFarRadiusPoint[0],  nearAngleFarRadiusPoint[1],
    averageAngleNearPoint[0], averageAngleNearPoint[1],
    nearPoint.x, nearPoint.y, 
    farAngleNearRadiusPoint[0], farAngleNearRadiusPoint[1],
    averageAngleFarPoint[0], averageAngleFarPoint[1]]

    for idx, x in enumerate(pointsList):
        if idx % 2  == 0: #x
            pointsList[idx] *= image.shape[0]
        else: #y
            pointsList[idx] *= image.shape[1]

    # print(f'radial returning: {np.array(pointsList)} ')
    
    return np.array(pointsList)

def parseGeometries(annotation, npImage):
    geometryStr = annotation['geometry']
    regionMode = annotation['metadata']['mode']
    direction = annotation['metadata']['direction'] 
    if regionMode == 'radial':
        return extractRadialBorder(geometryStr, npImage)
    elif regionMode == 'box':
        return extractBoxBorder(geometryStr, npImage)
    else :
        print(f"unkown region mode: {regionMode}")
        exit()

# The textSnake model outputs a 5 x h x w tensor, in which the individual channels are
# text region
# center region
# cos theta
# sin theta
# radius map
# https://arxiv.org/pdf/1807.01544.pdf
def convertToSnakeFormat(root: str):
    """
    Input: root of the training data folder

    Output: List of dictionary objects with following fields
    gt_text_mask
    gt_center_region_mask
    gt_mask
    gt_radius_map
    gt_sin_map
    gt_cos_map
    """
    with open(os.path.join(root, "annotations.json")) as f:
        finalResults = []
        finalResultToDump = {}
        firstRun = True
        resultDictionary = {}#gt_masks, gt_masks_ignore, img_shape, mask_fields

        fileContent = json.load(f)
        lastFilePath = ''
        npImage = None
        for annotation in fileContent["annotations"]:
            filePath = annotation['image_id']
            filePath = os.path.join(root, f'{filePath}.jpg')
            print(filePath)
            npImage = np.asarray(Image.open(filePath))
            if len(npImage.shape) != 3:
                continue
            if filePath != lastFilePath:
                if not firstRun:
                    targets = TextSnakeTargets()
                    resultDictionary = targets.generate_targets(resultDictionary)

                    finalResultToDump = {}
                    for key in resultDictionary['mask_fields']:
                        finalResultToDump[key] = resultDictionary[key]
                    finalResults.append(finalResultToDump)
                firstRun = False
                resultDictionary = {}


                resultDictionary['img_shape'] = npImage.shape
                resultDictionary['mask_fields'] = []
                resultDictionary['gt_masks'] = DummyObj()
                resultDictionary['gt_masks_ignore'] = DummyObj()
                # resultDictionary['gt_masks_ignore'].masks = [[np.array([])]]
                resultDictionary['gt_masks_ignore'].masks = []
            lastFilePath = filePath

            masks = parseGeometries(annotation, npImage)
            if (len(resultDictionary['gt_masks'].masks) == 0):
                # print('line 133---')
                resultDictionary['gt_masks'].masks = [[masks]]
            else :
                # print('line 137---')
                resultDictionary['gt_masks'].masks.append([masks])
            # resultDictionary['gt_masks_ignore'].masks.append(masks)#do not write to gt_masks_ignore, we aren't ignoring any sections of the screen, not masking

        #final annotation hasn't been dumped yet
        targets = TextSnakeTargets()
        resultDictionary = targets.generate_targets(resultDictionary)

        finalResultToDump = {}
        for key in resultDictionary['mask_fields']:
            finalResultToDump[key] = resultDictionary[key]
        finalResults.append(finalResultToDump)
    print(finalResults)
                            
# root = "C:\\Users\\ecarlson\\Desktop\\azDest\\export_test"
# convertToSnakeFormat(root)


    # gt_masks -> dictionary with a single field masks, 
    #     masks is a (list[list[ndarray]]) where it's textSections x 1 x polygon border point list length
    # gt_masks_ignore -> dictionary with single field masks,
    #     masks is a list[[ndarray]] The list of ignored text polygons.
    # img_shape -> 3d tensor of height, width, channels
    # mask_fields -> an empty list 
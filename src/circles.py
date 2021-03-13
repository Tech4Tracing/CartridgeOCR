import cv2
import numpy as np
import sys
import os
import json
import logging
import argparse
from math import sqrt

logging.basicConfig(level=logging.INFO)

parser = argparse.ArgumentParser('Detect cartridge locations')
parser.add_argument('input', type=str, help='text file containing of files to process')
# todo: column to process
parser.add_argument('output', type=str, help='output text file containing circle positions')
parser.add_argument('--output_folder', type=str, default='outimages', help='where to save the output images')
parser.add_argument('--targetW', type=int, default=480, help='Image rescale width')
parser.add_argument('--blurRadius', type=int, default=5, help='Blur radius, in pixels, calibrated to targetW')
parser.add_argument('--edgeThreshold', type=int, default=50, help='Canny edge difference threshold')
parser.add_argument('--detectionThreshold', type=int, default=60, help='Voting threshold to be detected as a circle')
parser.add_argument('--minDist', type=int, default=50, help='minimum distance between circles')
parser.add_argument('--minRadius', type=int, default=0, help='minimum circle radius')
parser.add_argument('--maxRadius', type=int, default=0, help='maximum circle radius')

args=parser.parse_args()

def isValid(circle, priorCircles, w, h):
    (x,y,r)=map(float,list(circle))
    
    if x-r<-0.05*w or x+r>=1.05*w or y-r<-0.05*h or y+r>=1.05*h:
        return False
    for c0 in priorCircles:
        (x0,y0,r0)=map(float,list(c0))
        logging.debug((x-x0)**2+(y-y0)**2)
        rc = sqrt((x-x0)**2+(y-y0)**2)
        if rc<r+r0:
            return False
    return True

def detectCircles(filename, 
                targetW = 480, 
                blurRadius=5, 
                edgeThreshold=50, 
                detectionThreshold=60,
                minDist=50,
                minRadius=0,
                maxRadius=0):
    logging.info(f'loading {filename}')
    img = cv2.imread(filename,0)

    h, w = img.shape
    logging.info(f'width: {w} height: {h}')

    # TODO: build a pyramid and optimize

    #targetW = 480
    scale = float(targetW)/w
    logging.info(f'scaling by {scale}')

    img = cv2.resize(img, None, fx = scale, fy = scale)

    img = cv2.medianBlur(img, blurRadius)
    cimg = cv2.cvtColor(img,cv2.COLOR_GRAY2BGR)

    h2, w2 = img.shape
    # https://docs.opencv.org/3.4/dd/d1a/group__imgproc__feature.html#ga47849c3be0d0406ad3ca45db65a25d2d
    # method	Detection method, see HoughModes. Currently, the only implemented method is HOUGH_GRADIENT
    # dp	Inverse ratio of the accumulator resolution to the image resolution. For example, if dp=1 , the accumulator has the same resolution as the input image. If dp=2 , the accumulator has half as big width and height.
    # minDist	Minimum distance between the centers of the detected circles. If the parameter is too small, multiple neighbor circles may be falsely detected in addition to a true one. If it is too large, some circles may be missed.
    # param1	First method-specific parameter. In case of HOUGH_GRADIENT , it is the higher threshold of the two passed to the Canny edge detector (the lower one is twice smaller).
    # param2	Second method-specific parameter. In case of HOUGH_GRADIENT , it is the accumulator threshold for the circle centers at the detection stage. The smaller it is, the more false circles may be detected. Circles, corresponding to the larger accumulator values, will be returned first.
    # minRadius	Minimum circle radius.
    # maxRadius	Maximum circle radius. If <= 0, uses the maximum image dimension. If < 0, returns centers without finding the radius.
    logging.info('Apply Hough transform')
    #minDist = 50
    #edgeThreshold = 50
    #detectionThreshold = 60
    circles = cv2.HoughCircles(img,cv2.HOUGH_GRADIENT, 1, minDist,
                                param1=edgeThreshold, param2=detectionThreshold,
                                minRadius=minRadius, maxRadius=maxRadius)

    circles = np.uint16(np.around(circles))
    # Take the largest?
    # Eliminate circles inside?
    result = list(sorted(circles[0,:], key=lambda x: x[2], reverse=True))
    returnedResult = []
    for i in result:
        # must be fully contained in the image
        # must not be contained in another circle
        logging.info(f'circle: {i}')
        if (isValid(i, returnedResult, w2, h2)):
            # draw the outer circle
            cv2.circle(cimg,(i[0],i[1]),i[2],(0,255,0),2)
            # draw the center of the circle
            cv2.circle(cimg,(i[0],i[1]),2,(0,0,255),3)  
            returnedResult.append(i)      

    #cv2.imshow('detected circles',cimg)
    #cv2.waitKey(0)
    #cv2.destroyAllWindows()
    return(([r*scale for r in returnedResult],cimg))

if args.output_folder and not os.path.exists(args.output_folder):
    os.makedirs(args.output_folder)

with open(args.input, 'r', encoding='utf-8') as inF, \
    open(args.output, 'w', encoding='utf-8') as outF:
    for (i,l) in enumerate(inF):
        l=l.strip()
        (circles,outImg) = detectCircles(l,
            targetW = args.targetW,
            blurRadius= args.blurRadius,
            edgeThreshold= args.edgeThreshold,
            detectionThreshold = args.detectionThreshold,
            minDist = args.minDist,
            minRadius = args.minRadius,
            maxRadius=args.maxRadius
            )
        outImgPath = ''
        if args.output_folder:
            outImgPath = os.path.join(args.output_folder, f'{i}_processed.jpg')
            cv2.imwrite(outImgPath, outImg)
        outF.write(f'{l}\t{json.dumps(list([list(c) for c in circles]))}\t{outImgPath}\n')
    
    
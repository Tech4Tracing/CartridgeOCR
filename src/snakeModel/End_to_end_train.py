import os
from argparse import ArgumentParser, Namespace
from pipeline.data_convertor import *
from training.train import *
import torch


def parse_args():
    parser = ArgumentParser()
    parser.add_argument(
        '--inputPath',
        type=str,
        default='',
        help='Input path for the data')

    parser.add_argument(
        '--modelName',
        type=str,
        default='TextSnake',
        help='Input path for the data')
    parser.add_argument(
        '--outputPath',
        type=str,
        default='TextSnake',
        help='Output path for model weights')
    args = parser.parse_args()
    return args    

def main():
    args = parse_args()
    snakeFormatPath = os.path.join(args.inputPath, 'data.pkl')
    if (os.path.exists(snakeFormatPath)):
        os.remove(snakeFormatPath)
    convertToSnakeFormat(args.inputPath, snakeFormatPath)
    model = loadModel(args.modelName)
    print(model)
    dataSet = loadDataLoader(snakeFormatPath, True)
    train(model, dataSet, args.outputPath)

if __name__ == '__main__':
    main()

# Example usage: 
# python End_to_end_train.py --inputPath=C:\Users\ecarlson\Desktop\azDest\export_test --outputPath=C:\Users\ecarlson\Desktop\trainedWeights.pth
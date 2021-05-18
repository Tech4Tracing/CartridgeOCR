# CartridgeOCR

src folder contains the training code based on the AML annotations.

h4g deck is [here](https://1drv.ms/p/s!Aq_TlvfieKvqu8t5DYBMbiD91PxE6Q?e=STaglB)

## Usage

- pip install -r requirements.txt
- cd src
- python train.py

### Outputs

- data/run_data: output folder
- loss.txt: training loss
- p_[epoch]_[imageid].png: prediction overlays on image
- predictions_[epoch].txt: json dumps of raw predictions
- model_[epoch].pth: model snapshots per epoch. Pytorch format, containing {'model':model, 'optimizer': optimizer, 'lr_scheduler':lr_scheduler, 'epoch':epoch}
- checkpoint.pth: last model snapshot.

### Data prep

If you export a dataset from AML, some conversion is needed- see convert_coco_urls.py

## Roadmap

Some areas to explore:

- CNN training from a few examples.  We have several options for fine-tuning: yolo, aml resnets, torchvision
- given an extraction, unroll it to optimize OCR.
- other enhancements to improve OCR
- labeling and storage workspaces
- mobile app workflow

## Base Architecture

The following architecture diagram shows the major CartridgeOCR components from a Azure resource and network perspective.

![architecture.png](./docs/assets/architecture.png)

## Dev environment

[https://pytorch.org/tutorials/intermediate/torchvision_tutorial.html](https://pytorch.org/tutorials/intermediate/torchvision_tutorial.html)

- conda install cython
- conda install jupyter
- pip install opencv
- pip install [git+https://github.com/gautamchitnis/cocoapi.git@cocodataset-master#subdirectory=PythonAPI](git+https://github.com/gautamchitnis/cocoapi.git@cocodataset-master#subdirectory=PythonAPI)
- pip install pillow
- conda install matplotlib
- pip install azureml-sdk
- pip install azure.cli.core
- pip install azureml-contrib-dataset

## Explore yolo

- wget [https://pjreddie.com/media/files/yolov3.weights](https://pjreddie.com/media/files/yolov3.weights)

## Explore torchvision

- potentially important: [https://github.com/pytorch/vision/issues/2720](https://github.com/pytorch/vision/issues/2720)

Torchvision todo:

- move to a GPU box.
- double check batch size, epoch size
- visualize outputs
- understand evaluation outputs.

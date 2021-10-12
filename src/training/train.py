# https://colab.research.google.com/github/pytorch/vision/blob/temp-tutorial/tutorials/torchvision_finetuning_instance_segmentation.ipynb
import os
import sys
sys.path += ['.']
import logging
import numpy as np
import torch
import torch.utils.data
from training.engine import train_one_epoch, evaluate
import dataProcessing.utils as utils
from dataProcessing.coco_utils import CocoDetection
from training.model_utils import rt, get_transform, get_instance_segmentation_model, save_snapshot

logging.basicConfig(level=logging.INFO)

# TODO: output path wired up to blob storage.
# TODO: command-line parameters for these folders
datapath = rt('data/dataset')
labelpath = rt('data/labeldata')
outputpath = rt('outputData')

logging.info(f'Using pytorch version {torch.__version__}')
logging.info(f'Using numpy version {np.__version__}')

if "RUNINAZURE" in os.environ:
    from azureml.core import Workspace, Datastore, Dataset, Run

    logging.info('Downloading datasets')
    ws = Workspace.from_config()
    imagestore = Datastore.get(ws, datastore_name='images')
    labeldata = Datastore.get(ws, datastore_name='labeldata')

    imagestore_paths = [(imagestore, '/**')]
    images_ds = Dataset.File.from_files(path=imagestore_paths)
    images_ds.download(target_path=datapath, overwrite=True)

    labeldata_paths = [(labeldata, '/**')]
    labeldata_ds = Dataset.File.from_files(path=labeldata_paths)
    labeldata_ds.download(target_path=labelpath, overwrite=True)

    print(">>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>><<<<<<<<<<<<<<<<<<<<<<<<<<<<<<")

if __name__ == '__main__':
    # use our dataset and defined transformations
    label_fn = 'coco_all_annotations_xformed.json'  # coco_xformed.json
    dataset = CocoDetection(datapath, os.path.join(labelpath, label_fn), get_transform(train=True))
    dataset_test = CocoDetection(datapath, os.path.join(labelpath, label_fn), get_transform(train=False))

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

    # our dataset has three classes: background, casing, and primer
    num_classes = 3

    # get the model using our helper function
    model = get_instance_segmentation_model(num_classes)
    # move model to the right device
    model.to(device)

    # construct an optimizer
    params = [p for p in model.parameters() if p.requires_grad]
    optimizer = torch.optim.SGD(params, lr=0.005,
                                momentum=0.9, weight_decay=0.0005)

    # and a learning rate scheduler which decreases the learning rate by
    # 10x every 3 epochs
    lr_scheduler = torch.optim.lr_scheduler.StepLR(optimizer,
                                                   step_size=3,
                                                   gamma=0.1)

    num_epochs = 10
    folder = outputpath
    if not os.path.exists(folder):
        os.makedirs(folder, exist_ok=True)
    
    with open(os.path.join(folder, 'loss.txt'), 'w', encoding='utf-8') as outLoss:
        for epoch in range(num_epochs):
            # train for one epoch, printing every 10 iterations
            train_one_epoch(model, optimizer, data_loader, device, epoch, print_freq=10, outLog=outLoss)
            # update the learning rate
            lr_scheduler.step()
            # evaluate on the test dataset
            evaluate(model, data_loader_test, device=device)

            checkpoint = {
                'model': model.state_dict(),
                'optimizer': optimizer.state_dict(),
                'lr_scheduler': lr_scheduler.state_dict(),
                'epoch': epoch,
                # 'args': args
            }
            save_snapshot(checkpoint, folder, epoch)

    if "RUNINAZURE" in os.environ:
        targetpath = Run.get_context().display_name
        logging.info(f"uploading results to {targetpath}")
        files = [os.path.join(outputpath, f) for f in os.listdir(outputpath)]
        modeldata = Datastore.get(ws, datastore_name='models')
        modeldata.upload_files(files, target_path=targetpath)

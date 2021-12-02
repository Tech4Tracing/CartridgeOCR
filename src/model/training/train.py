# https://colab.research.google.com/github/pytorch/vision/blob/temp-tutorial/tutorials/torchvision_finetuning_instance_segmentation.ipynb
from azureml.core import Run
import os
import sys
sys.path += ['.']
import logging
from shutil import copy
import numpy as np
import torch
import torch.utils.data
from training.engine import train_one_epoch, evaluate
import dataProcessing.utils as utils
from dataProcessing.coco_utils import CocoDetection
from training.model_utils import rt, get_transform, get_instance_segmentation_model, save_snapshot
import argparse
from torch.optim import SGD, Adam
from sklearn.model_selection import KFold
import random

logging.basicConfig(level=logging.INFO)

# TODO: output path wired up to blob storage.
# TODO: command-line parameters for these folders
datapath = rt('data/dataset')
labelpath = rt('data/labeldata')
outputpath = rt('outputData')

logging.info(f'Using pytorch version {torch.__version__}')
logging.info(f'Using numpy version {np.__version__}')

# TODO: enable more arguments
parser = argparse.ArgumentParser()
parser.add_argument('--cv', type=int, default=1, help='cross-validation slices (<=1 for a single 90/10 split)')
parser.add_argument('--optimizer', default='sgd', help='Optimizer: sgd or adam for now')

if "RUNINAZURE" in os.environ:
    from azureml.core import Workspace, Datastore, Dataset

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
    args = parser.parse_args()

    # use our dataset and defined transformations
    label_fn = 'coco_all_annotations_xformed.json'  # coco_xformed.json
    dataset_base = CocoDetection(datapath, os.path.join(labelpath, label_fn), get_transform(train=True))
    dataset_test_base = CocoDetection(datapath, os.path.join(labelpath, label_fn), get_transform(train=False))

    seed = 42
    torch.manual_seed(seed)
    random.seed(seed)

    all_stats = {}

    def log_summary(summary, fold, epoch, best_score_key=None):
        '''
        After each epoch in each fold, compiles statistics organized by epoch
        for future collation.
        Logs current epoch result to the current fold for per-fold plotting.
        best_score_key indicates the key metric to check if we've reached the best overall score.
        '''
        run = Run.get_context()
        for k in summary:
            if epoch not in all_stats:
                all_stats[epoch] = {}
            if k not in all_stats[epoch]:
                all_stats[epoch][k] = []
            all_stats[epoch][k].append(summary[k])
            # We'll just log the raw values to a single metric to avoid clutter (they will reset on each fold)
            run.log(k, summary[k])

        return best_score_key is not None and best_score_key in summary and \
            summary[best_score_key] >= max([max(all_stats[e][best_score_key]) for e in all_stats])

    def log_final_stats():
        run = Run.get_context()
        for epoch in all_stats:
            for k in all_stats[epoch]:
                run.log(f'mean {k}', np.mean(all_stats[epoch][k]))
                run.log(f'std {k}', np.std(all_stats[epoch][k]))

    def train(fold, dataset, dataset_test, save_best=False):
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

        optimizer = None
        init_lr = 0.005
        if args.optimizer == 'sgd':
            optimizer = SGD(params, lr=init_lr,
                            momentum=0.9, weight_decay=0.0005)
        elif args.optimizer == 'adam':
            optimizer = Adam(params, lr=init_lr)  # weight_decay = ?

        # and a learning rate scheduler which decreases the learning rate by
        # 10x every 3 epochs
        lr_scheduler = torch.optim.lr_scheduler.StepLR(optimizer,
                                                       step_size=3,
                                                       gamma=0.1)

        num_epochs = 10
        folder = outputpath
        if not os.path.exists(folder):
            os.makedirs(folder, exist_ok=True)

        with open(os.path.join(folder, f'loss_{fold}.txt'), 'w', encoding='utf-8') as outLoss:
            for epoch in range(num_epochs):
                # train for one epoch, printing every 10 iterations
                train_one_epoch(model, optimizer, data_loader, device, epoch, print_freq=10, outLog=outLoss)
                # update the learning rate
                lr_scheduler.step()
                # evaluate on the test dataset
                summary = evaluate(model, data_loader_test, device=device)
                is_best = log_summary(summary, fold, epoch, best_score_key='segm F1' if save_best else None)

                checkpoint = {
                    'model': model.state_dict(),
                    'optimizer': optimizer.state_dict(),
                    'lr_scheduler': lr_scheduler.state_dict(),
                    'epoch': epoch,
                    # 'args': args
                }
                save_snapshot(checkpoint, folder, fold, epoch, is_best)

    # Run the main training part, maybe with cross-validation
    if args.cv <= 1:
        # split the dataset in train and test set
        indices = torch.randperm(len(dataset_base)).tolist()
        cutoff = max(10, int(0.1 * len(dataset_base)))
        dataset = torch.utils.data.Subset(dataset_base, indices[:-cutoff])
        dataset_test = torch.utils.data.Subset(dataset_test_base, indices[-cutoff:])
        # we only set save_best for single 90/10 split runs, not cross-validation
        train(0, dataset, dataset_test, save_best=True)
    else:
        kfold = KFold(n_splits=args.cv, shuffle=True)
        #
        # K-fold Cross Validation model evaluation
        for fold, (train_ids, test_ids) in enumerate(kfold.split(dataset_base)):
            logging.info(f'Cross-Validation fold {fold}')
            dataset = torch.utils.data.Subset(dataset_base, train_ids)
            dataset_test = torch.utils.data.Subset(dataset_test_base, test_ids)
            train(fold, dataset, dataset_test)
        log_final_stats()

    if "RUNINAZURE" in os.environ:
        folder = outputpath
        copy('training/model_utils.py', folder)
        copy('training/engine.py', folder)
        copy('dataProcessing/coco_utils.py', folder)
        copy('dataProcessing/utils.py', folder)
        copy('dataProcessing/transforms.py', folder)
        from azureml.core.model import Model

        logging.info("Registering Model")
        model = Model.register(model_name="APImodel",
                               model_path=outputpath,
                               description="",
                               workspace=ws)

        targetpath = Run.get_context().display_name
        logging.info(f"uploading results to {targetpath}")
        files = [os.path.join(outputpath, f) for f in os.listdir(outputpath)]
        modeldata = Datastore.get(ws, datastore_name='models')
        modeldata.upload_files(files, target_path=targetpath)

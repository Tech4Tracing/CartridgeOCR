# https://colab.research.google.com/github/pytorch/vision/blob/temp-tutorial/tutorials/torchvision_finetuning_instance_segmentation.ipynb
import os
import numpy as np
import torch
import torch.utils.data
import json
from PIL import Image, ImageDraw
import torchvision
from torchvision.models.detection.faster_rcnn import FastRCNNPredictor
from torchvision.models.detection.mask_rcnn import MaskRCNNPredictor
from notebooks.engine import train_one_epoch, evaluate
import notebooks.utils as utils
import notebooks.transforms as T
from notebooks.coco_utils import CocoDetection, ConvertCocoPolysToMask
from tqdm import tqdm

# TODO: how does nocrowd interact with casing and primer annotations?


def rt(p):
    return os.path.join('../',p)

      
def get_instance_segmentation_model(num_classes):
    # load an instance segmentation model pre-trained on COCO
    model = torchvision.models.detection.maskrcnn_resnet50_fpn(pretrained=True)

    # get the number of input features for the classifier
    in_features = model.roi_heads.box_predictor.cls_score.in_features
    # replace the pre-trained head with a new one
    model.roi_heads.box_predictor = FastRCNNPredictor(in_features, num_classes)

    # now get the number of input features for the mask classifier
    in_features_mask = model.roi_heads.mask_predictor.conv5_mask.in_channels
    hidden_layer = 256
    # and replace the mask predictor with a new one
    model.roi_heads.mask_predictor = MaskRCNNPredictor(in_features_mask,
                                                       hidden_layer,
                                                       num_classes)

    return model


def get_transform(train):
    transforms = []
    # converts the image, a PIL image, into a PyTorch Tensor
    transforms.append(T.Resize())
    transforms.append(ConvertCocoPolysToMask())
    transforms.append(T.ToTensor())
    if train:
        # during training, randomly flip the training images
        # and ground-truth for data augmentation
        transforms.append(T.RandomHorizontalFlip(0.5))
    
    return T.Compose(transforms)

def save_snapshot(checkpoint, output_dir, epoch ):
    utils.save_on_master(
        checkpoint,
        os.path.join(output_dir, 'model_{}.pth'.format(epoch)))
    utils.save_on_master(
        checkpoint,
        os.path.join(output_dir, 'checkpoint.pth'))

if __name__ == '__main__':
    # use our dataset and defined transformations

    dataset = CocoDetection(rt('data/dataset'), rt('data/dataset/coco_xformed.json'), get_transform(train=True))

    #dataset = PennFudanDataset('PennFudanPed', get_transform(train=True))
    dataset_test = CocoDetection(rt('data/dataset'), rt('data/dataset/coco_xformed.json'), get_transform(train=False))

    # split the dataset in train and test set
    torch.manual_seed(1)
    indices = torch.randperm(len(dataset)).tolist()
    cutoff = max(10,int(0.1*len(dataset)))
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
    folder = rt('data/run_data')
    if not os.path.exists(folder):
        os.makedirs(folder, exist_ok=True)
    
    with open(os.path.join(folder,'loss.txt'),'w', encoding='utf-8') as outLoss:
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
                #'args': args
            }
            save_snapshot(checkpoint, folder, epoch)

            # some rendering
            # pick one image from the test set
            with open(os.path.join(folder,'predictions_{}.txt'.format(epoch)),'w', encoding='utf-8') as outP:
            # put the model in evaluation mode
                model.eval()
                with torch.no_grad():
                    for ix, (img, _) in tqdm(enumerate(dataset_test)):
                        prediction = model([img.to(device)])
                        masks = [p['masks'] for p in prediction]                        
                        prediction = [
                            dict([(k, v.cpu().numpy().tolist()) for k,v in x.items() if k!='masks']) for x in prediction
                        ]                        
                        #print(prediction)
                        # TODO: clean this up.
                        masksout = []
                        casings = []
                        primers = []
                        for m_i,(m,p) in enumerate(zip(masks,prediction)):
                            #print(m.shape,p['boxes'],p['labels'])
                            if m.shape[0]==0:
                                continue
                            
                            i2 = Image.fromarray(m[0, 0].mul(255).byte().cpu().numpy())         
                            imgOut = Image.new("RGB", i2.size)                      
                            imgOut.paste(i2, (0,0))
                            canvas = ImageDraw.Draw(imgOut)
                            boxes = [(b,s,l) for (b,s,l) in zip(p['boxes'],p['scores'],p['labels']) if b[2]<i2.width and b[3]<i2.height and b[2]-b[0]>20 and b[3]-b[1]>20]
                            casings = [(b,s,l) for (b,s,l) in zip(p['boxes'],p['scores'],p['labels']) if l==1 and b[2]<i2.width and b[3]<i2.height and b[2]-b[0]>20 and b[3]-b[1]>20]
                            primers = [(b,s,l) for (b,s,l) in zip(p['boxes'],p['scores'],p['labels']) if l==2 and b[2]<i2.width and b[3]<i2.height and b[2]-b[0]>20 and b[3]-b[1]>20]

                            #for box,_ in list(sorted(zip(p['boxes'],p['scores']), key=lambda x: x[1], reverse=True))[:3]:
                            for box,_,label in list(sorted(boxes, key=lambda x: x[1], reverse=True))[:3]:
                                #print(label)
                                canvas.rectangle(box, outline="red" if label==1 else "yellow")
                            masksout.append(imgOut)
                                         
                        if len(masksout)>0:
                            i1 = Image.fromarray(img.mul(255).permute(1, 2, 0).byte().numpy())                            
                            #dst = Image.new('RGB', (i1.width + sum([m.width for m in masksout]), i1.height))
                            dst = Image.new('RGB', i1.size)
                            dst.paste(i1, (0, 0))
                            canvas = ImageDraw.Draw(dst)
                            for box,_,label in list(sorted(casings, key=lambda x: x[1], reverse=True))[:3]:
                                #print(label)
                                canvas.rectangle(box, outline="red", width=3)
                            for box,_,label in list(sorted(primers, key=lambda x: x[1], reverse=True))[:3]:
                                #print(label)
                                canvas.rectangle(box, outline="yellow", width=3)

                            #x = i1.width
                            #for m2 in masksout:
                            #    dst.paste(m2, (x, 0))
                            #    x += m2.width
                            fn = os.path.join(folder,'p_{}_{}.png'.format(epoch,ix))
                            dst.save(fn)
                        outP.write(json.dumps(prediction)+'\n')
                        


    #Image.fromarray(img.mul(255).permute(1, 2, 0).byte().numpy())
    # visualized segmentation mask
    #Image.fromarray(prediction[0]['masks'][0, 0].mul(255).byte().cpu().numpy())


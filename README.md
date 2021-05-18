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

## Deployment

### Clone the repository

Clone the repository to your local machine (`git clone https://github.com/Tech4Tracing/CartridgeOCR.git`)

### Pre-requisites

You will require the following pre-requisites installed.

- Terraform >= v0.15.3. The following instructions use local terraform state, you may want to consider [storing you state remotely in Azure](https://docs.microsoft.com/en-us/azure/developer/terraform/store-state-in-azure-storage)
- Azure CLI >= 2.21.0
- An Azure Subscription

### Configuring variables

The environment is going to be provisioned using Terraform scripts. In order to run Terraform, you need to set the environment variables in [/terraform/terraform.tfvars.tmpl](../templates/core/terraform/terraform.tfvars.tmpl).

Rename the `terraform.tfvars.tmpl` to `terraform.tfvars`

Edit the terraform.tfvars as required. As `resource_name_prefix` and `environment` are used in Azure resource names they must be alpha numeric `(a-z,0-9)`. The defaults are as follows:

```hcl
resource_name_prefix     = "cartridgeocr"
environment              = "dev"
location                 = "westeurope"
```

Notice that some resources require a globally unique name, so make sure that resource name prefix makes the generated resource name unique.

### Log into your Azure subscription

[Login and select the azure subscription you wish to deploy to](https://docs.microsoft.com/en-us/azure/developer/terraform/get-started-cloud-shell#set-the-current-azure-subscription):

```cmd
az login
az account set -s <subscription_name_or_id>
```

### Initialize Terraform and deploy

To run terraform, from the ./terraform folder run:

```cmd
terraform init
terraform apply
```

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

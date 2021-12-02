#!/bin/bash

sudo apt install zip
sudo apt install jq
sudo apt install npm
sudo npm install -g @ionic/cli
pip install azureml-dataset-runtime --upgrade

homedir=`pwd`

env_file="$homedir/.env"

export $(cat $env_file | xargs)

cd $homedir/src/webapp/CartridgeOCRApp

ionic build

cd $homedir/src/webapp/CartridgeOCRApp/build

zip build.zip -r *

az webapp deployment source config-zip --src build.zip -g $resourceGroup -n $webappName

echo "Web App URL: https://$webappName.azurewebsites.net/"

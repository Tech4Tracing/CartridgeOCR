#!/bin/bash

#load env file
if [ -f ".env" ]
then
  export $(cat .env | xargs)
fi

az storage blob directory upload --container $imagesContainer \
                                 --destination-path "." \
                                 --source "data/dataset/*" \
                                 --account-name $storageAccountName \
                                 --account-key $storageAccountKey  


az storage blob directory upload --container $labelDataContainer \
                                 --destination-path "." \
                                 --source "data/labeldata/*" \
                                 --account-name $storageAccountName \
                                 --account-key $storageAccountKey  

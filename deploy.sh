#!/bin/bash

sudo apt install zip
sudo apt install jq

$homedir=`pwd`

cd $homedir/terraform

terraform init
terraform apply -auto-approve

tfoutput=$(terraform output -json)
cosmosEndpoint=$(echo $tfoutput | jq -r '.cosmosEndpoint.value')
cosmosKey=$(echo $tfoutput | jq -r '.cosmosKey.value')
cosmosDatabaseId=$(echo $tfoutput | jq -r '.cosmosDatabaseId.value')
storageAccount=$(echo $tfoutput | jq -r '.storageAccount.value')
resourceGroup=$(echo $tfoutput | jq -r '.resourceGroup.value')
functionName=$(echo $tfoutput | jq -r '.functionName.value')
webappName=$(echo $tfoutput | jq -r '.webappName.value')

cd $homedir/src/webapp/api

settings_file="local.settings.json"
cat <<EOF > $settings_file
{
  "IsEncrypted": false,
  "Values": {
    "AzureWebJobsStorage": "",
    "FUNCTIONS_WORKER_RUNTIME": "node",
    "cosmosEndpoint": "$cosmosEndpoint",
    "cosmosKey": "$cosmosKey",
    "cosmosDatabaseId": "$cosmosDatabaseId",
    "cosmosContainerId": "Images",
    "cosmosPartitionKey": "{ kind: \"Hash\", paths: [\"/category\"] }",
    "storageAccount": "$storageAccount",
    "storageContainer": "images"
  }
}
EOF

zip api.zip -r *

az functionapp deployment source config-zip --src api.zip -g $resourceGroup -n $functionName --build-remote true

az functionapp config appsettings set -g $resourceGroup -n $functionName --settings \
                "cosmosEndpoint=$cosmosEndpoint" \
                "cosmosKey=$cosmosKey" \
                "cosmosDatabaseId=$cosmosDatabaseId" \
                "CosmosContainerId=Images" \
                "cosmosPartitionKey={kind:\"Hash\",paths:[\"/category\"]}" \
                "storageAccount=$storageAccount" \
                "storageContainer=images"


cd $homedir/src/webapp/CartridgeOCRApp

ionic build

cd $homedir/src/webapp/CartridgeOCRApp/build

zip build.zip -r *

az webapp deployment source config-zip --src build.zip -g $resourceGroup -n $webappName

echo "Image Upload API URL: https://$functionName.azurewebsites.net/api/image-upload"
echo "Web App URL: https://$webappName.azurewebsites.net/"

#!/bin/bash

sudo apt install zip
sudo apt install jq
pip install azureml-dataset-runtime --upgrade

$homedir=`pwd`

cd $homedir/terraform

terraform init
terraform apply -auto-approve

tfoutput=$(terraform output -json)

env_file="$homedir/.env"
cat <<EOF > $env_file
cosmosEndpoint=$(echo $tfoutput | jq -r '.cosmosEndpoint.value')
cosmosKey=$(echo $tfoutput | jq -r '.cosmosKey.value')
cosmosDatabaseId=$(echo $tfoutput | jq -r '.cosmosDatabaseId.value')
storageAccount=$(echo $tfoutput | jq -r '.storageAccount.value')
storageAccountName=$(echo $tfoutput | jq -r '.storageAccountName.value')
storageAccountKey=$(echo $tfoutput | jq -r '.storageAccountKey.value')
resourceGroup=$(echo $tfoutput | jq -r '.resourceGroup.value')
functionName=$(echo $tfoutput | jq -r '.functionName.value')
webappName=$(echo $tfoutput | jq -r '.webappName.value')
AMLWorkspaceName=$(echo $tfoutput | jq -r '.AMLWorkspaceName.value')
subscriptionId=$(echo $tfoutput | jq -r '.subscriptionId.value')
imagesContainer=$(echo $tfoutput | jq -r '.imagesContainer.value')
labelDataContainer=$(echo $tfoutput | jq -r '.labelDataContainer.value')
computeCluster='cpucluster'
EOF

export $(cat $env_file | xargs)

# Install az extensions without prompt
az config set extension.use_dynamic_install=yes_without_prompt

# Install AML extenstion
az extension add -n azure-cli-ml

# Create compute cluster
az ml computetarget create amlcompute --max-nodes 4 --name $computeCluster --vm-size 'Standard_DS12_v2' -w $AMLWorkspaceName -g $resourceGroup

# Set system managed identity to cluster and permission for AML 
az ml computetarget amlcompute identity assign --identities '[system]' --name $computeCluster -w $AMLWorkspaceName -g $resourceGroup
computeMSI=$(az ml computetarget amlcompute identity show  --name $computeCluster -w $AMLWorkspaceName -g $resourceGroup | jq -r '.principalId')
acrScope=$(az resource show -n $AMLWorkspaceName -g $resourceGroup --resource-type 'Microsoft.MachineLearningServices/workspaces' | jq -r '.id')
az role assignment create --assignee-object-id $computeMSI --role Owner --scope $acrScope

# Create datastore in AML for images
az ml datastore attach-blob --account-name $storageAccountName \
                            --container-name $imagesContainer \
                            --name $imagesContainer \
                            --account-key $storageAccountKey  \
                            -w $AMLWorkspaceName \
                            -g $resourceGroup

# Create datastore in AML for datalabels
az ml datastore attach-blob --account-name $storageAccountName \
                            --container-name $labelDataContainer \
                            --name $labelDataContainer \
                            --account-key $storageAccountKey  \
                            -w $AMLWorkspaceName \
                            -g $resourceGroup


AML_settings_file="$homedir/src/config.json"
cat <<EOF > $AML_settings_file
{
    "subscription_id": "$subscriptionId",
    "resource_group": "$resourceGroup",
    "workspace_name": "$AMLWorkspaceName"
}
EOF

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
    "cosmosContainerId": "$imagesContainer",
    "cosmosPartitionKey": "{ kind: \"Hash\", paths: [\"/category\"] }",
    "storageAccount": "$storageAccount",
    "storageContainer": "$imagesContainer"
  }
}
EOF

zip api.zip -r *

az functionapp deployment source config-zip --src api.zip -g $resourceGroup -n $functionName --build-remote true

az functionapp config appsettings set -g $resourceGroup -n $functionName --settings \
                "cosmosEndpoint=$cosmosEndpoint" \
                "cosmosKey=$cosmosKey" \
                "cosmosDatabaseId=$cosmosDatabaseId" \
                "CosmosContainerId=$imagesContainer" \
                "cosmosPartitionKey={kind:\"Hash\",paths:[\"/category\"]}" \
                "storageAccount=$storageAccount" \
                "storageContainer=$imagesContainer"

cd $homedir/src/webapp/CartridgeOCRApp

ionic build

cd $homedir/src/webapp/CartridgeOCRApp/build

zip build.zip -r *

az webapp deployment source config-zip --src build.zip -g $resourceGroup -n $webappName

echo "Image Upload API URL: https://$functionName.azurewebsites.net/api/image-upload"
echo "Web App URL: https://$webappName.azurewebsites.net/"

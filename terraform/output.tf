output "resourceGroup" {
  value = azurerm_resource_group.core.name
}

output "functionName" {
  value = azurerm_function_app.API.name
}

output "cosmosEndpoint" {
  value = azurerm_cosmosdb_account.cosmos.endpoint
}

output "cosmosKey" {
  value = azurerm_cosmosdb_account.cosmos.primary_key
  sensitive = true
}

output "cosmosDatabaseId" {
  value = azurerm_cosmosdb_sql_database.cosmos-sql-db.name
}

output "storageAccount" {
  value = azurerm_storage_account.stg.primary_connection_string
  sensitive = true
}

output "storageAccountName" {
  value = azurerm_storage_account.stg.name
}

output "storageAccountKey" {
  value = azurerm_storage_account.stg.primary_access_key
  sensitive = true
}

output "webappName" {
  value = azurerm_app_service.webapp.name
}

output "AMLWorkspaceName" {
  value = azurerm_machine_learning_workspace.ml.name
}

output "subscriptionId" {
  value = data.azurerm_subscription.current.subscription_id
}

output "imagesContainer" {
  value = azurerm_storage_container.images.name
}

output "labelDataContainer" {
  value = azurerm_storage_container.labeldata.name
}

output "modelContainer" {
  value = azurerm_storage_container.models.name
}
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
}

output "cosmosDatabaseId" {
  value = azurerm_cosmosdb_sql_database.cosmos-sql-db.name
}

output "storageAccount" {
  value = azurerm_storage_account.stg.primary_connection_string
}

output "webappName" {
  value = azurerm_app_service.webapp.name
}

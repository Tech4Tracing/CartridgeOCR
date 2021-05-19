terraform {
  required_providers {
    azurerm = {
      source  = "hashicorp/azurerm"
      version = "=2.58.0"
    }
  }
}

provider "azurerm" {
  features {}
}

data "azurerm_client_config" "current" {}

resource "azurerm_resource_group" "core" {
  location = var.location
  name     = "rg-${var.resource_name_prefix}-${var.environment}"
  tags = {
    project     = "CartridgeOCR"
    environment = var.environment
    source      = "https://github.com/Tech4Tracing/CartridgeOCR"
  }
}

resource "azurerm_application_insights" "ai" {
  name                = "ai${var.resource_name_prefix}"
  location            = azurerm_resource_group.core.location
  resource_group_name = azurerm_resource_group.core.name
  application_type    = "web"
}

resource "azurerm_container_registry" "acr" {
  name                     = "acr${var.resource_name_prefix}${var.environment}"
  resource_group_name      = azurerm_resource_group.core.name
  location                 = var.location
  sku                      = "Premium"
  admin_enabled            = false
}

resource "azurerm_cosmosdb_account" "cosmos" {
  name                = "cosmos-${var.resource_name_prefix}-${var.environment}"
  location            = var.location
  resource_group_name = azurerm_resource_group.core.name
  offer_type          = "Standard"
  kind                = "GlobalDocumentDB"

  enable_automatic_failover = false
 
  consistency_policy {
    consistency_level       = "BoundedStaleness"
    max_interval_in_seconds = 10
    max_staleness_prefix    = 200
  }

  geo_location {
    location          = var.location
    failover_priority = 0
  }
}

resource "azurerm_cosmosdb_sql_database" "cosmos-sql-db" {
  name                = "cosmos-sql-${var.resource_name_prefix}-${var.environment}"
  resource_group_name = azurerm_resource_group.core.name
  account_name        = azurerm_cosmosdb_account.cosmos.name
  throughput          = 400
}

resource "azurerm_key_vault" "kv" {
  name                = "kv-${var.resource_name_prefix}-${var.environment}"
  location            = var.location
  resource_group_name = azurerm_resource_group.core.name
  sku_name            = "standard"
  purge_protection_enabled = true
  tenant_id           = data.azurerm_client_config.current.tenant_id
}

resource "azurerm_storage_account" "stg" {
  name                     = "stg${var.resource_name_prefix}${var.environment}"
  resource_group_name      = azurerm_resource_group.core.name
  location                 = var.location
  account_tier             = "Standard"
  account_replication_type = "LRS"
}

resource "azurerm_storage_container" "images" {
  name                  = "images"
  storage_account_name  = azurerm_storage_account.stg.name
  container_access_type = "private"
}

resource "azurerm_machine_learning_workspace" "ml" {
  name                    = "ml-${var.resource_name_prefix}-${var.environment}"
  location                = azurerm_resource_group.core.location
  resource_group_name     = azurerm_resource_group.core.name
  application_insights_id = azurerm_application_insights.ai.id
  key_vault_id            = azurerm_key_vault.kv.id
  storage_account_id      = azurerm_storage_account.stg.id

  identity {
    type = "SystemAssigned"
  }
}

resource "azurerm_app_service_plan" "plan" {
  name                = "plan-${var.resource_name_prefix}-${var.environment}"
  resource_group_name = azurerm_resource_group.core.name
  location            = var.location
  reserved            = true
  kind                = "linux"
  sku {
    tier     = "PremiumV3"
    capacity = 1
    size     = "P1v3"
  }
}

resource "azurerm_app_service" "webapp" {
  name                = "web-${var.resource_name_prefix}-${var.environment}"
  resource_group_name = azurerm_resource_group.core.name
  location            = var.location
  app_service_plan_id = azurerm_app_service_plan.plan.id


  https_only = true
  app_settings = {
    "APPINSIGHTS_INSTRUMENTATIONKEY" = azurerm_application_insights.ai.instrumentation_key
  }

  site_config {
    remote_debugging_enabled    = false
    scm_use_main_ip_restriction = true
    cors {
      allowed_origins     = []
      support_credentials = false
    }
    always_on       = true
    min_tls_version = "1.2"
    websockets_enabled = true
  }

  logs {
    application_logs {
      file_system_level = "Information"
    }

    http_logs {
      file_system {
        retention_in_days = 7
        retention_in_mb   = 100
      }
    }
  }
}

resource "azurerm_function_app" "API" {
  name                       = "api-${var.resource_name_prefix}-${var.environment}"
  location                   = var.location
  resource_group_name        = azurerm_resource_group.core.name
  app_service_plan_id        = azurerm_app_service_plan.plan.id
  storage_account_name       = azurerm_storage_account.stg.name
  storage_account_access_key = azurerm_storage_account.stg.primary_access_key
  version = "~3"
  
  app_settings = {
        https_only = true
        FUNCTIONS_WORKER_RUNTIME = "node"
        WEBSITE_NODE_DEFAULT_VERSION = "~14"
        FUNCTION_APP_EDIT_MODE = "readonly"
    }
}

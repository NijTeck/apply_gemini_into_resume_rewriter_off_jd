provider "azurerm" {
  features {}
  subscription_id = var.subscription_id
  tenant_id       = var.tenant_id
}

resource "azurerm_resource_group" "resume_optimizer" {
  name     = var.resource_group_name
  location = var.location
}

# Storage Account for resumes and function app
resource "azurerm_storage_account" "storage" {
  name                     = var.storage_account_name
  resource_group_name      = azurerm_resource_group.resume_optimizer.name
  location                 = azurerm_resource_group.resume_optimizer.location
  account_tier             = "Standard"
  account_replication_type = "LRS"
}

# Create blob container for storing resumes
resource "azurerm_storage_container" "resume_repo" {
  name                  = var.storage_container_name
  storage_account_name  = azurerm_storage_account.storage.name
  container_access_type = "private"
}

# App Service Plan for Function App
resource "azurerm_service_plan" "function_plan" {
  name                = "resume-optimizer-plan"
  resource_group_name = azurerm_resource_group.resume_optimizer.name
  location            = azurerm_resource_group.resume_optimizer.location
  os_type             = "Linux"
  sku_name            = "EP1"
}

# Application Insights
resource "azurerm_application_insights" "insights" {
  name                = "resume-optimizer-insights"
  location            = azurerm_resource_group.resume_optimizer.location
  resource_group_name = azurerm_resource_group.resume_optimizer.name
  application_type    = "web"
}

# Key Vault for storing secrets
resource "azurerm_key_vault" "vault" {
  name                        = var.key_vault_name
  location                    = azurerm_resource_group.resume_optimizer.location
  resource_group_name         = azurerm_resource_group.resume_optimizer.name
  enabled_for_disk_encryption = true
  tenant_id                   = var.tenant_id
  soft_delete_retention_days  = 7
  purge_protection_enabled    = false
  sku_name                    = "standard"
}

# Store Gemini API key in Key Vault
resource "azurerm_key_vault_secret" "gemini_api_key" {
  name         = "gemini-api-key"
  value        = var.gemini_api_key
  key_vault_id = azurerm_key_vault.vault.id
}

# Document Intelligence Service
resource "azurerm_cognitive_account" "document_intelligence" {
  name                = var.document_intelligence_name
  location            = azurerm_resource_group.resume_optimizer.location
  resource_group_name = azurerm_resource_group.resume_optimizer.name
  kind                = "FormRecognizer"
  sku_name            = "S0"
}

# Function App
resource "azurerm_linux_function_app" "function_app" {
  name                       = var.function_app_name
  location                   = azurerm_resource_group.resume_optimizer.location
  resource_group_name        = azurerm_resource_group.resume_optimizer.name
  service_plan_id            = azurerm_service_plan.function_plan.id
  storage_account_name       = azurerm_storage_account.storage.name
  storage_account_access_key = azurerm_storage_account.storage.primary_access_key

  site_config {
    application_stack {
      python_version = "3.11"
    }
  }

  app_settings = {
    "APPINSIGHTS_INSTRUMENTATIONKEY"    = azurerm_application_insights.insights.instrumentation_key
    "AzureWebJobsStorage"               = azurerm_storage_account.storage.primary_connection_string
    "FUNCTIONS_WORKER_RUNTIME"          = "python"
    "DOCUMENT_INTELLIGENCE_ENDPOINT"    = azurerm_cognitive_account.document_intelligence.endpoint
    "DOCUMENT_INTELLIGENCE_KEY"         = azurerm_cognitive_account.document_intelligence.primary_access_key
    "GEMINI_API_KEY"                    = "@Microsoft.KeyVault(SecretUri=${azurerm_key_vault_secret.gemini_api_key.id})"
    "BLOB_CONNECTION_STRING"            = azurerm_storage_account.storage.primary_connection_string
    "RESUME_CONTAINER_NAME"             = azurerm_storage_container.resume_repo.name
  }

  identity {
    type = "SystemAssigned"
  }
}

# Grant Function App access to Key Vault
resource "azurerm_key_vault_access_policy" "function_app_policy" {
  key_vault_id = azurerm_key_vault.vault.id
  tenant_id    = var.tenant_id
  object_id    = azurerm_linux_function_app.function_app.identity[0].principal_id

  secret_permissions = [
    "Get", "List"
  ]
} 
output "function_app_url" {
  description = "The URL of the deployed function app"
  value       = "https://${azurerm_linux_function_app.function_app.default_hostname}/api/optimize"
}

output "storage_account_name" {
  description = "The name of the storage account"
  value       = azurerm_storage_account.storage.name
}

output "resource_group_name" {
  description = "The name of the resource group"
  value       = azurerm_resource_group.resume_optimizer.name
}

output "key_vault_name" {
  description = "The name of the key vault"
  value       = azurerm_key_vault.vault.name
}

output "application_insights_name" {
  description = "The name of the Application Insights resource"
  value       = azurerm_application_insights.insights.name
}

output "document_intelligence_name" {
  description = "The name of the Document Intelligence resource"
  value       = azurerm_cognitive_account.document_intelligence.name
}

output "application_insights_instrumentation_key" {
  description = "The instrumentation key for Application Insights"
  value       = azurerm_application_insights.insights.instrumentation_key
  sensitive   = true
} 
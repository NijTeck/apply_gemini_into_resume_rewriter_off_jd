variable "tenant_id" {
  description = "Azure tenant ID"
  type        = string
}

variable "subscription_id" {
  description = "Azure subscription ID"
  type        = string
}

variable "gemini_api_key" {
  description = "Google Gemini API key"
  type        = string
  sensitive   = true
}

variable "location" {
  description = "Azure region to deploy resources"
  type        = string
  default     = "eastus"
}

variable "resource_group_name" {
  description = "Name of the resource group"
  type        = string
  default     = "your-resource-group"
}

variable "storage_account_name" {
  description = "Name of the storage account"
  type        = string
  default     = "yourstorageaccountname"
}

variable "function_app_name" {
  description = "Name of the function app"
  type        = string
  default     = "your-function-app-name"
}

variable "key_vault_name" {
  description = "Name of the key vault"
  type        = string
  default     = "your-key-vault-name"
}

variable "document_intelligence_name" {
  description = "Name of the document intelligence resource"
  type        = string
  default     = "your-docintel-name"
}

variable "storage_container_name" {
  description = "Name of the resume blob storage container"
  type        = string
  default     = "resumes"
}
# GitHub Actions Setup Guide

This guide will help you migrate from Azure DevOps to GitHub Actions and configure it for your new Azure tenant.

## 🚀 Quick Setup Steps

### 1. Update Tenant Configuration

First, update your tenant-specific information:

**File: `terraform.tfvars`**
```hcl
# Replace these with your new tenant values
tenant_id = "YOUR_NEW_TENANT_ID"
subscription_id = "YOUR_NEW_SUBSCRIPTION_ID"
```

### 2. Create Azure Service Principal

Run this command in Azure Cloud Shell or Azure CLI:

```bash
# Replace YOUR_SUBSCRIPTION_ID with your actual subscription ID
az ad sp create-for-rbac --name "GitHubActions-JobApplier" \
  --role contributor \
  --scopes /subscriptions/YOUR_SUBSCRIPTION_ID \
  --sdk-auth
```

**Important**: Save the JSON output - you'll need it for GitHub secrets!

### 3. Grant Additional Permissions

```bash
# Get your service principal ID
SP_ID=$(az ad sp list --display-name "GitHubActions-JobApplier" --query "[0].id" -o tsv)

# Grant Container Registry permissions
az role assignment create --assignee $SP_ID \
  --role "AcrPush" \
  --scope /subscriptions/YOUR_SUBSCRIPTION_ID

# Grant Key Vault permissions (if using)
az role assignment create --assignee $SP_ID \
  --role "Key Vault Administrator" \
  --scope /subscriptions/YOUR_SUBSCRIPTION_ID

# Grant Storage permissions
az role assignment create --assignee $SP_ID \
  --role "Storage Blob Data Contributor" \
  --scope /subscriptions/YOUR_SUBSCRIPTION_ID
```

### 4. Set Up GitHub Secrets

In your GitHub repository, go to **Settings** → **Secrets and variables** → **Actions** and add:

| Secret Name | Value | Description |
|-------------|-------|-------------|
| `AZURE_CREDENTIALS` | JSON from step 2 | Service principal credentials |
| `AZURE_SUBSCRIPTION_ID` | Your subscription ID | Azure subscription |
| `AZURE_TENANT_ID` | Your tenant ID | Azure tenant |
| `GEMINI_API_KEY` | Your Gemini API key | Google Gemini API |
| `BLOB_CONNECTION_STRING` | Your storage connection string | Azure Storage |

### 5. Get Your Blob Connection String

```bash
# Replace with your actual storage account name and resource group
   az storage account show-connection-string \
  --name <your-storage-account> \
  --resource-group <your-resource-group> \
  --query connectionString -o tsv
```

## 🔧 Configuration Details

### Available Workflows

1. **Container Deploy** (`.github/workflows/container-deploy.yml`):
   - Use this for regular deployments
   - Assumes infrastructure exists
   - Faster builds

2. **Terraform Deploy** (`.github/workflows/terraform-deploy.yml`):
   - Use this for infrastructure changes
   - Deploys Terraform first, then container
   - Longer but more complete

### Workflow Triggers

Both workflows trigger on:
- Push to `main` branch
- Changes to specific files
- Manual workflow dispatch

### Environment Variables

The workflows use these environment variables (configured in the workflow files):

```yaml
env:
  CONTAINER_REGISTRY: '<your-acr-name>.azurecr.io'
  ACR_NAME: '<your-acr-name>'
  IMAGE_REPOSITORY: 'resume-optimizer'
  RESOURCE_GROUP: '<your-resource-group>'
  CONTAINER_APP_NAME: '<your-container-app-name>'
```

## 🐛 Troubleshooting

### Common Issues

1. **Authentication Errors**
   - Verify `AZURE_CREDENTIALS` is valid JSON
   - Check service principal permissions

2. **Resource Not Found**
   - Ensure resources exist in the correct subscription
   - Verify resource group and names match

3. **Permission Denied**
   - Grant additional roles to service principal
   - Check subscription-level permissions

### Debug Commands

```bash
# Test your service principal locally
az login --service-principal \
  --username "YOUR_CLIENT_ID" \
  --password "YOUR_CLIENT_SECRET" \
  --tenant "YOUR_TENANT_ID"

# List your resources
az resource list --resource-group <your-resource-group>

# Check container app status
az containerapp show \
  --name <your-container-app-name> \
  --resource-group <your-resource-group>
```

## 🗑️ Cleanup Old Azure DevOps

Once GitHub Actions is working:

1. **Disable Azure DevOps pipeline**
2. **Remove service connection** (if not needed elsewhere)
3. **Delete pipeline files** (optional):
   - `azure-pipelines.yml`
   - `terraform-pipeline.yml`
   - `azure-pipeline-instructions.md`

## ✅ Testing Your Setup

1. **Push a small change** to trigger the workflow
2. **Check GitHub Actions tab** for build status
3. **Verify deployment** in Azure Portal
4. **Test your application URL**

## 🆘 Getting Help

If you encounter issues:

1. **Check GitHub Actions logs** - they're very detailed
2. **Verify all secrets are set** correctly
3. **Test Azure CLI commands** locally first
4. **Check Azure resource status** in the portal

## 📝 Quick Reference

### Required Information

- ✅ Azure Tenant ID
- ✅ Azure Subscription ID  
- ✅ Service Principal JSON
- ✅ Gemini API Key
- ✅ Storage Connection String

### Key Files Updated

- ✅ `.github/workflows/container-deploy.yml` (created)
- ✅ `.github/workflows/terraform-deploy.yml` (created)
- ✅ `terraform.tfvars` (updated)
- ✅ `README.md` (updated)

You're all set! 🎉 
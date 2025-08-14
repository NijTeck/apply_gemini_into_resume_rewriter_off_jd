# Setting Up Azure DevOps Pipeline for Resume Optimizer

This document explains how to set up the Azure DevOps pipeline to automate deployment of the Resume Optimizer application.

## Prerequisites

1. Azure DevOps organization and project
2. Azure Subscription
3. Service Principal with permissions to create resources in your Azure subscription

## Setup Steps

### 1. Create Azure DevOps Service Connection

1. In your Azure DevOps project, go to **Project Settings** > **Service Connections** > **New Service Connection**
2. Select **Azure Resource Manager**
3. Choose **Service Principal (automatic)** 
4. Name the connection `AzureServiceConnection`
5. Select your subscription and click **Save**

### 2. Create Pipeline Variable Group

1. Go to **Pipelines** > **Library** > **+ Variable Group**
2. Create a variable group named `ResumeOptimizerVars`
3. Add the following secret variables:
   - `GEMINI_API_KEY`: Your Google Gemini API key 
   - `TENANT_ID`: Your Azure tenant ID
   - `SUBSCRIPTION_ID`: Your Azure subscription ID

### 3. Create Azure Container Registry Service Connection (if needed)

1. In **Project Settings** > **Service Connections** > **New Service Connection**, select **Docker Registry**
2. Choose **Azure Container Registry**
3. Select your subscription and your Azure Container Registry
4. Name it `ACRConnection`

### 4. Create terraform.tfvars File

Create a `terraform.tfvars` file in your repository with:

```hcl
tenant_id       = "YOUR_TENANT_ID"
subscription_id = "YOUR_SUBSCRIPTION_ID"
gemini_api_key  = "YOUR_GEMINI_API_KEY"
```

**Note:** It's better to use pipeline variables for sensitive values instead of storing them in the repo.

### 5. Create the Pipeline

1. Go to **Pipelines** > **New Pipeline**
2. Select **Azure Repos Git** or your source control
3. Select your repository
4. Choose **Existing Azure Pipelines YAML file**
5. Select `/azure-pipelines.yml` for container-only deployment or `/terraform-pipeline.yml` for full infrastructure deployment
6. Click **Continue** and then **Run**

## Pipeline Options

Two pipeline options are available:

1. **azure-pipelines.yml**: Assumes infrastructure is already created, only builds and deploys the container
2. **terraform-pipeline.yml**: Deploys infrastructure with Terraform, then builds and deploys the container

Choose the appropriate option based on your needs.

## Pipeline Stages

The pipeline includes the following stages:

1. **Terraform** (optional): Deploy infrastructure using Terraform
2. **Build**: Build and push Docker image
3. **Deploy**: Deploy container to Azure Container Apps
4. **Test**: Test the deployed application

## Customizing the Pipeline

You can customize the pipeline by:

1. Modifying variable values in the YAML file
2. Adding additional stages/tasks
3. Configuring environment-specific deployments
4. Adding more comprehensive tests

## Troubleshooting

- **Permission errors**: Ensure your Service Principal has the necessary permissions
- **Connection errors**: Verify that service connections are correctly configured
- **Build failures**: Check Docker build logs for issues
- **Deployment failures**: Check Azure CLI output in the pipeline logs

## Security Considerations

- Store sensitive values like API keys in Azure DevOps variable groups or Azure Key Vault
- Consider using managed identities for Azure resources
- Scan container images for vulnerabilities before deployment 
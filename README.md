# Resume Optimizer

A web application that optimizes resumes for specific job descriptions using AI.

## Production-grade Azure AI workload (at a glance)

This repository is a practical, production-ready reference for Azure engineers and Azure ML engineers to:

- Integrate AI into an existing Azure application
- Build a new AI-powered application on Azure

What it demonstrates:

- **Azure services used**: Azure Container Apps (deployment path), Azure Container Registry, Azure Blob Storage, Azure Key Vault, Azure Application Insights, and Azure AI Document Intelligence (Form Recognizer)
- **Infrastructure as Code**: Terraform definitions for core resources and app configuration
- **AI integration**: Google Gemini for resume analysis and rewriting (model configurable via environment variables)
- **DevOps practices**: CI/CD guidance with GitHub Actions and example Azure Pipelines, containerization, secret management, RBAC, and observability

Workload patterns supported:

- **Containerized web app** (recommended): Deployed to Azure Container Apps with CI/CD
- **Serverless processing**: Azure Functions path defined in Terraform for event-driven scenarios

Architecture (high level):

1. User uploads a resume (PDF/DOCX)
2. Text extraction via built-in parsers or Azure AI Document Intelligence
3. AI analysis and rewrite via Google Gemini
4. Tailored DOCX generated and stored in Azure Blob Storage
5. Tracking data persisted in Blob Storage (CSV)
6. Telemetry available via Application Insights; secrets managed in Key Vault

## Features

- Upload resume in PDF or DOCX format
- Analyze job descriptions and requirements
- Generate optimized resumes tailored to specific jobs
- Track resume modifications and applications
- Store resumes in Azure Blob Storage

## Prerequisites

- Azure subscription with the following resources:
  - Azure Container Apps
  - Azure Container Registry
  - Azure Blob Storage
  - Azure Key Vault (optional)
  - Azure Document Intelligence (optional)
- Google Gemini API key (store in .env or CI secrets; do not commit)
- GitHub repository with GitHub Actions enabled

## Environment Variables

The application requires the following environment variables (never commit real values to the repo):

- `GEMINI_API_KEY`: Your Google Gemini API key
- `BLOB_CONNECTION_STRING`: Azure Blob Storage connection string
- `RESUME_CONTAINER_NAME`: Container name for original resumes
- `TAILORED_RESUME_CONTAINER_NAME`: Container name for tailored resumes 
- `TRACKING_CONTAINER_NAME`: Container name for tracking information
- `TRACKING_FILE_NAME`: Filename for tracking CSV
- `DOCUMENT_INTELLIGENCE_ENDPOINT`: Azure Document Intelligence endpoint (optional)
- `DOCUMENT_INTELLIGENCE_KEY`: Azure Document Intelligence key (optional)

## Deployment

### GitHub Actions Setup

The application uses GitHub Actions for CI/CD deployment to Azure Container Apps.

#### Required GitHub Secrets

Set up the following secrets in your GitHub repository (Settings → Secrets and variables → Actions):

```
AZURE_CREDENTIALS              # Azure service principal credentials (JSON)
AZURE_SUBSCRIPTION_ID          # Your Azure subscription ID
AZURE_TENANT_ID               # Your Azure tenant ID
GEMINI_API_KEY                # Google Gemini API key
BLOB_CONNECTION_STRING        # Azure Blob Storage connection string
```

#### Azure Service Principal Setup

1. Create a service principal for GitHub Actions:
   ```bash
   az ad sp create-for-rbac --name "GitHubActions-ResumeOptimizer" \
     --role contributor \
     --scopes /subscriptions/YOUR_SUBSCRIPTION_ID \
     --sdk-auth
   ```

2. Copy the JSON output and add it as the `AZURE_CREDENTIALS` secret in GitHub.

3. Grant additional permissions to the service principal:
   ```bash
   # For Key Vault access (if using)
   az role assignment create --assignee YOUR_SERVICE_PRINCIPAL_ID \
     --role "Key Vault Administrator" \
     --scope /subscriptions/YOUR_SUBSCRIPTION_ID
   
   # For Container Registry access
   az role assignment create --assignee YOUR_SERVICE_PRINCIPAL_ID \
     --role "AcrPush" \
     --scope /subscriptions/YOUR_SUBSCRIPTION_ID
   ```

#### Available Workflows

1. **Container Deployment** (`.github/workflows/container-deploy.yml`):
   - Assumes infrastructure already exists
   - Builds and deploys container only
   - Faster deployment for code changes

2. **Terraform + Container Deployment** (`.github/workflows/terraform-deploy.yml`):
   - Deploys infrastructure using Terraform
   - Then builds and deploys container
   - Use for infrastructure changes

### Local Development

1. Create a `.env` file based on `.env.example` and fill in your values.

2. Build and run the Docker container:
   ```bash
   docker build -t resume-optimizer .
   docker run -p 8000:8000 \
      -e GEMINI_API_KEY=your-gemini-api-key \
      -e BLOB_CONNECTION_STRING=your-azure-blob-connection-string \
     -e RESUME_CONTAINER_NAME=resumes \
     resume-optimizer
   ```

2. Access the application at http://localhost:8000

### Manual Azure Deployment

If you prefer manual deployment:

1. Copy `terraform.tfvars.example` to `terraform.tfvars` and update with your tenant and subscription IDs. Do not commit `terraform.tfvars`.
2. Run Terraform:
   ```bash
   terraform init
   terraform plan
   terraform apply
   ```
3. Build and push Docker image:
   ```bash
   az acr login --name <your-acr-name>
   docker build -t <your-acr-name>.azurecr.io/resume-optimizer .
   docker push <your-acr-name>.azurecr.io/resume-optimizer
   ```

## Migration from Azure DevOps

If migrating from Azure DevOps:

1. Update tenant and subscription IDs in `terraform.tfvars`
2. Set up GitHub secrets as described above
3. Push code to trigger GitHub Actions deployment
4. Remove Azure DevOps pipeline files if no longer needed

## Troubleshooting

### Common Issues

1. **Permission errors**: Ensure your service principal has the necessary permissions
2. **Container registry access**: Verify ACR permissions for the service principal
3. **Environment variables**: Check that all required secrets are set in GitHub
4. **Terraform backend**: Ensure Terraform state storage account exists

### Debug Steps

1. Check GitHub Actions logs for detailed error messages
2. Verify Azure resources exist in the correct subscription
3. Test authentication with Azure CLI locally
4. Validate environment variables are set correctly

### Support

For issues with:
- **GitHub Actions**: Check the Actions tab in your repository
- **Azure resources**: Use Azure CLI to verify resource status
- **Container deployment**: Check Container Apps logs in Azure Portal

- Let me know if you have any questions ( write a discussion ) 

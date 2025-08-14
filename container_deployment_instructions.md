# Resume Optimizer Container Deployment

We've successfully set up Azure Container Apps as an alternative to Azure Functions. Here's a summary of the resources created:

1. **Azure Storage Account:** `yourstorageaccountname`
2. **Storage Container:** `resumes`
3. **Application Insights:** `resume-optimizer-insights`
4. **Key Vault:** `your-key-vault-name`
5. **Azure Container Registry:** `<your-acr-name>`
6. **Container App Environment:** `<your-containerapp-env>`
7. **Container App:** `<your-container-app-name>` 

## How to Build and Push the Docker Image

To complete deployment, follow these steps:

1. **Build the Docker image locally**:
   ```bash
   docker build -t resume-optimizer .
   ```

2. **Tag the image for the Azure Container Registry**:
   ```bash
   docker tag resume-optimizer <your-acr-name>.azurecr.io/resume-optimizer:latest
   ```

3. **Login to the Container Registry**:
   ```bash
   az acr login --name <your-acr-name>
   ```

4. **Push the image to the registry**:
   ```bash
   docker push <your-acr-name>.azurecr.io/resume-optimizer:latest
   ```

5. **Update the Container App to use your image**:
   ```bash
   az containerapp update --name <your-container-app-name> --resource-group <your-resource-group> --image <your-acr-name>.azurecr.io/resume-optimizer:latest
   ```

## Access Your Application

Your application is accessible at:
https://<your-container-app-fqdn>/api/optimize

## Environment Variables

The following environment variables have been set in the Container App:
- GEMINI_API_KEY
- BLOB_CONNECTION_STRING
- RESUME_CONTAINER_NAME

## Testing Your Application

Once deployed, you can test your application with:

```bash
curl -X POST https://<your-container-app-fqdn>/api/optimize \
  -F "resume=@path/to/your/resume.pdf" \
  -F "job_description=Your job description text here"
```

## Advantages of Container Apps vs. Functions

- Fully supports Linux containers without quota restrictions
- More flexibility in runtime environment and dependencies
- Can run any containerized application, not just functions
- Similar serverless scaling capabilities
- Support for custom domains and SSL
- Direct integration with Azure Container Registry

## Monitoring

You can monitor your application using the Azure Portal. Navigate to the Container App resource and select the "Monitoring" section to view logs and metrics. 
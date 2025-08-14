#!/bin/bash

# Variables
RESOURCE_GROUP="<your-resource-group>"
CONTAINER_APP_NAME="<your-container-app-name>"

# Display current environment variables
echo "Current environment variables in Container App:"
az containerapp show --name $CONTAINER_APP_NAME --resource-group $RESOURCE_GROUP \
  --query "properties.template.containers[0].env" -o table

# Define environment variables (replace with your own values)
GEMINI_API_KEY="your-gemini-api-key"
BLOB_CONNECTION_STRING="your-blob-connection-string"
RESUME_CONTAINER_NAME="resumes"
TAILORED_RESUME_CONTAINER_NAME="tailored-resumes"
TRACKING_CONTAINER_NAME="tracking"
TRACKING_FILE_NAME="resume_tracking.csv"
DOCUMENT_INTELLIGENCE_ENDPOINT="your-document-intelligence-endpoint"
DOCUMENT_INTELLIGENCE_KEY="your-document-intelligence-key"

# Update environment variables with retry logic
MAX_RETRIES=5
RETRY_DELAY=30
ATTEMPT=1

function wait_for_operation_completion() {
    echo "Waiting for any ongoing operations to complete..."
    local start_time=$(date +%s)
    local timeout=300  # 5 minutes timeout
    
    while true; do
        local status=$(az containerapp show --name $CONTAINER_APP_NAME --resource-group $RESOURCE_GROUP \
            --query "properties.provisioningState" -o tsv)
        
        if [[ "$status" == "Succeeded" ]]; then
            echo "Container App is in 'Succeeded' state, ready for updates."
            return 0
        fi
        
        local current_time=$(date +%s)
        if (( current_time - start_time >= timeout )); then
            echo "Timeout waiting for operations to complete."
            return 1
        fi
        
        echo "Current state: $status. Waiting $RETRY_DELAY seconds..."
        sleep $RETRY_DELAY
    done
}

while [ $ATTEMPT -le $MAX_RETRIES ]; do
    echo "Attempt $ATTEMPT of $MAX_RETRIES to update environment variables..."
    
    # Wait for any ongoing operations to complete
    wait_for_operation_completion
    
    # Update the environment variables
    echo "Updating environment variables..."
    az containerapp update --name $CONTAINER_APP_NAME --resource-group $RESOURCE_GROUP \
        --set-env-vars \
        GEMINI_API_KEY=$GEMINI_API_KEY \
        BLOB_CONNECTION_STRING=$BLOB_CONNECTION_STRING \
        RESUME_CONTAINER_NAME=$RESUME_CONTAINER_NAME \
        TAILORED_RESUME_CONTAINER_NAME=$TAILORED_RESUME_CONTAINER_NAME \
        TRACKING_CONTAINER_NAME=$TRACKING_CONTAINER_NAME \
        TRACKING_FILE_NAME=$TRACKING_FILE_NAME \
        DOCUMENT_INTELLIGENCE_ENDPOINT=$DOCUMENT_INTELLIGENCE_ENDPOINT \
        DOCUMENT_INTELLIGENCE_KEY=$DOCUMENT_INTELLIGENCE_KEY \
        DEBUG=true \
        PYTHONUNBUFFERED=1
    
    if [ $? -eq 0 ]; then
        echo "Environment variables updated successfully!"
        
        # Verify the environment variables were set correctly
        echo "Verifying environment variables..."
        az containerapp show --name $CONTAINER_APP_NAME --resource-group $RESOURCE_GROUP \
            --query "properties.template.containers[0].env" -o table
        exit 0
    else
        echo "Failed to update environment variables."
        if [ $ATTEMPT -lt $MAX_RETRIES ]; then
            echo "Retrying in $RETRY_DELAY seconds..."
            sleep $RETRY_DELAY
        fi
    fi
    
    ATTEMPT=$((ATTEMPT+1))
done

echo "Failed to update environment variables after $MAX_RETRIES attempts."
exit 1 
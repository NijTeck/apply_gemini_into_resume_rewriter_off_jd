import os
import logging
import csv
import io
import tempfile
from typing import Dict, Any, List
from azure.storage.blob import BlobServiceClient, ContentSettings

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("azure-storage-manager")

class AzureStorageManager:
    """Class to handle all Azure storage operations"""
    
    def __init__(self):
        """Initialize the storage manager with connection string from environment variables"""
        self.connection_string = os.environ.get("BLOB_CONNECTION_STRING")
        self.resume_container_name = os.environ.get("RESUME_CONTAINER_NAME")
        self.tailored_container_name = os.environ.get("TAILORED_RESUME_CONTAINER_NAME", "tailored-resumes")
        self.tracking_container_name = os.environ.get("TRACKING_CONTAINER_NAME", "tracking")
        self.tracking_file_name = os.environ.get("TRACKING_FILE_NAME", "resume_tracking.csv")
        
        # Initialize the blob service client
        self.blob_service_client = BlobServiceClient.from_connection_string(self.connection_string)
        
        # Ensure containers exist
        self._ensure_container_exists(self.resume_container_name)
        self._ensure_container_exists(self.tailored_container_name)
        self._ensure_container_exists(self.tracking_container_name)
    
    def _ensure_container_exists(self, container_name: str):
        """Ensure the specified container exists, create it if it doesn't"""
        try:
            self.blob_service_client.get_container_client(container_name).get_container_properties()
        except Exception:
            logger.info(f"Container {container_name} does not exist, creating it")
            self.blob_service_client.create_container(container_name)
    
    def upload_tailored_resume(self, resume_data: bytes, filename: str) -> str:
        """
        Upload a tailored resume to Azure storage
        
        Args:
            resume_data: The resume document as bytes
            filename: The filename to use for storage
            
        Returns:
            URL of the uploaded blob
        """
        try:
            # Get a blob client
            blob_client = self.blob_service_client.get_blob_client(
                container=self.tailored_container_name, 
                blob=filename
            )
            
            # Set the content settings for a DOCX file
            content_settings = ContentSettings(
                content_type="application/vnd.openxmlformats-officedocument.wordprocessingml.document"
            )
            
            # Upload the resume
            blob_client.upload_blob(
                resume_data, 
                content_settings=content_settings,
                overwrite=True
            )
            
            # Return the URL
            return blob_client.url
            
        except Exception as e:
            logger.error(f"Error uploading tailored resume: {str(e)}")
            raise
    
    def update_tracking_file(self, tracking_entry: Dict[str, str]) -> bool:
        """
        Update the tracking file with a new entry
        
        Args:
            tracking_entry: Dictionary containing the tracking information
                - job_title: The job title
                - company: The company name
                - role: The role
                - tailored_resume_identifier: The filename of the tailored resume
                - date_modified: The date of modification
                
        Returns:
            True if successful, False otherwise
        """
        try:
            # Get a blob client for the tracking file
            blob_client = self.blob_service_client.get_blob_client(
                container=self.tracking_container_name, 
                blob=self.tracking_file_name
            )
            
            # Check if the tracking file exists
            try:
                # Download the existing tracking file
                existing_data = blob_client.download_blob().readall()
                existing_data_str = existing_data.decode('utf-8')
            except Exception:
                # File doesn't exist, create a new one
                existing_data_str = ""
            
            # Create a new CSV file with the existing data and the new entry
            output = io.StringIO()
            
            # Determine the fieldnames
            fieldnames = ["job_title", "company", "role", "tailored_resume_identifier", "date_modified"]
            
            # Create a CSV writer
            writer = csv.DictWriter(output, fieldnames=fieldnames)
            
            # If the file is empty, write the header first
            if not existing_data_str:
                writer.writeheader()
            
            # Read the existing entries
            if existing_data_str:
                reader = csv.DictReader(io.StringIO(existing_data_str))
                # Copy existing entries
                for row in reader:
                    writer.writerow(row)
            
            # Add the new entry
            writer.writerow(tracking_entry)
            
            # Upload the updated file
            blob_client.upload_blob(
                output.getvalue().encode('utf-8'),
                content_settings=ContentSettings(content_type="text/csv"),
                overwrite=True
            )
            
            return True
            
        except Exception as e:
            logger.error(f"Error updating tracking file: {str(e)}")
            raise
    
    def delete_original_resume(self, filename: str) -> bool:
        """
        Delete the original resume file
        
        Args:
            filename: The filename of the original resume
            
        Returns:
            True if successful, False otherwise
        """
        try:
            # Get a blob client
            blob_client = self.blob_service_client.get_blob_client(
                container=self.resume_container_name, 
                blob=filename
            )
            
            # Delete the blob
            blob_client.delete_blob()
            
            return True
            
        except Exception as e:
            logger.error(f"Error deleting original resume: {str(e)}")
            raise 
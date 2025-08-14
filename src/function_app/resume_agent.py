import os
import logging
import re
from typing import Dict, Any

from .resume_rewriter import rewrite_resume, extract_job_details, generate_unique_identifier
from .docx_generator import text_to_docx
from .azure_storage_manager import AzureStorageManager
from . import extract_text_from_file

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("jobapplier-agent")

class ResumeAgent:
    """
    Resume optimization and processing agent
    
    This agent processes a resume and job description to create a tailored resume,
    store it in Azure storage, and track the changes.
    """
    
    def __init__(self):
        """Initialize the resume agent"""
        self.storage_manager = AzureStorageManager()
    
    def process_resume(self, resume_file_path: str, job_description: str, 
                       user_name: str, original_filename: str) -> Dict[str, Any]:
        """
        Process a resume and job description to create a tailored resume
        
        Args:
            resume_file_path: Path to the original resume file
            job_description: The job description text
            user_name: The name of the user
            original_filename: The original filename of the resume
            
        Returns:
            A dictionary containing the results of the operation:
            - status: "success" or "error"
            - message: A message describing the result
            - data: Additional data about the operation (if successful)
            - error: Error details (if failed)
        """
        try:
            logger.info(f"Processing resume for user: {user_name}")
            
            # Validate inputs
            if not resume_file_path or not os.path.exists(resume_file_path):
                raise ValueError(f"Invalid resume file path: {resume_file_path}")
            if not job_description:
                raise ValueError("Job description is required")
            if not user_name:
                raise ValueError("User name is required")
            if not original_filename:
                raise ValueError("Original filename is required")
            
            # Step 1: Extract text from the resume file
            logger.info("Extracting text from resume file...")
            try:
                resume_text = extract_text_from_file(resume_file_path, original_filename)
                if not resume_text or not resume_text.strip():
                    raise ValueError("No text could be extracted from the resume file")
            except Exception as e:
                logger.error(f"Failed to extract text from resume: {str(e)}")
                return {
                    "status": "error",
                    "message": "Failed to extract text from resume",
                    "error": str(e)
                }
            
            # Step 2: Rewrite the resume to match the job description
            logger.info("Rewriting resume to match job description...")
            try:
                rewrite_result = rewrite_resume(resume_text, job_description)
                if not rewrite_result or "error" in rewrite_result:
                    error_msg = rewrite_result.get("error", "Unknown error") if rewrite_result else "No result from resume rewriter"
                    raise ValueError(f"Failed to rewrite resume: {error_msg}")
            except Exception as e:
                logger.error(f"Failed to rewrite resume: {str(e)}")
                return {
                    "status": "error",
                    "message": "Failed to rewrite resume",
                    "error": str(e)
                }
            
            # Step 3: Generate a DOCX file from the rewritten resume
            logger.info("Generating DOCX file...")
            try:
                rewritten_text = rewrite_result.get("rewritten_resume_text")
                if not rewritten_text:
                    raise ValueError("No rewritten text available")
                docx_data = text_to_docx(rewritten_text)
            except Exception as e:
                logger.error(f"Failed to generate DOCX file: {str(e)}")
                return {
                    "status": "error",
                    "message": "Failed to generate DOCX file",
                    "error": str(e)
                }
            
            # Step 4: Generate a unique filename for the tailored resume
            job_title = rewrite_result.get("job_title", "Not Specified")
            company_name = rewrite_result.get("company_name", "Not Specified")
            role = rewrite_result.get("role", "Not Specified")
            tailored_filename = generate_unique_identifier(user_name, job_title, company_name)
            
            # Step 5: Upload the tailored resume to Azure storage
            logger.info(f"Uploading tailored resume: {tailored_filename}")
            try:
                resume_url = self.storage_manager.upload_tailored_resume(docx_data, tailored_filename)
            except Exception as e:
                logger.error(f"Failed to upload tailored resume: {str(e)}")
                return {
                    "status": "error",
                    "message": "Failed to upload tailored resume",
                    "error": str(e)
                }
            
            # Step 6: Update the tracking file
            logger.info("Updating tracking file...")
            try:
                tracking_entry = {
                    "job_title": job_title,
                    "company": company_name,
                    "role": role,
                    "tailored_resume_identifier": tailored_filename,
                    "date_modified": rewrite_result.get("date_modified", "")
                }
                self.storage_manager.update_tracking_file(tracking_entry)
            except Exception as e:
                logger.warning(f"Failed to update tracking file: {str(e)}")
                # Don't fail the whole operation if tracking update fails
            
            # Step 7: Try to delete the original resume file, but don't fail if it doesn't exist
            logger.info(f"Attempting to delete original resume: {original_filename}")
            try:
                self.storage_manager.delete_original_resume(original_filename)
            except Exception as e:
                logger.warning(f"Failed to delete original resume: {str(e)}")
                # Don't fail the whole operation if delete fails
            
            # Step 8: Return success with tracking information
            return {
                "status": "success",
                "message": "Resume successfully tailored and stored",
                "data": {
                    "tailored_resume_url": resume_url,
                    "tailored_resume_filename": tailored_filename,
                    "job_title": job_title,
                    "company_name": company_name,
                    "role": role,
                    "integration_percentage": rewrite_result.get("integration_percentage", "80-95%"),
                    "changes_summary": rewrite_result.get("changes_summary", []),
                    "highlighted_skills": rewrite_result.get("highlighted_skills", []),
                    "gap_analysis": rewrite_result.get("gap_analysis", [])
                }
            }
            
        except Exception as e:
            logger.error(f"Error processing resume: {str(e)}")
            return {
                "status": "error",
                "message": "Failed to process resume",
                "error": str(e)
            } 
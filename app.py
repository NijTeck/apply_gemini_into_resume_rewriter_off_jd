from flask import Flask, jsonify, request, render_template, send_from_directory
import logging
import tempfile
import os
from dotenv import load_dotenv
import traceback
from werkzeug.utils import secure_filename
from flask_cors import CORS
import datetime
import sys
from azure.storage.blob import BlobServiceClient

# Configure logging first
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger("jobapplier")

# Load environment variables from .env file
load_dotenv()

# Validate required environment variables
required_env_vars = [
    'GEMINI_API_KEY',
    'BLOB_CONNECTION_STRING',
    'RESUME_CONTAINER_NAME',
    'TAILORED_RESUME_CONTAINER_NAME',
    'TRACKING_CONTAINER_NAME'
]

# Set default values for missing environment variables (for development/testing)
default_values = {
    'RESUME_CONTAINER_NAME': 'resume',
    'TAILORED_RESUME_CONTAINER_NAME': 'tailoredresumecontainer',
    'TRACKING_CONTAINER_NAME': 'trackingcontainer',
    'TRACKING_FILE_NAME': 'resume_tracking.csv',
    'GEMINI_MODEL_ID': 'gemini-1.5-pro'
}

# Check for missing variables but don't exit
missing_vars = []
for var in required_env_vars:
    if not os.environ.get(var):
        missing_vars.append(var)
        # Set default values for non-sensitive variables
        if var in default_values:
            os.environ[var] = default_values[var]
            logger.warning(f"Using default value for {var}: {default_values[var]}")

if missing_vars:
    logger.warning(f"Missing environment variables: {', '.join(missing_vars)}")
    if 'GEMINI_API_KEY' in missing_vars or 'BLOB_CONNECTION_STRING' in missing_vars:
        logger.warning("Some sensitive environment variables are missing. Some features may not work properly.")
else:
    logger.info("All required environment variables are set")

# Import the real function_app functions
try:
    from src.function_app import (
        extract_text_from_file,
        upload_to_blob_storage,
        get_gemini_recommendations,
        ResumeAgent
    )
    logger.info("Successfully imported function_app modules")
except Exception as e:
    logger.error(f"Failed to import function_app modules: {str(e)}")
    logger.error(traceback.format_exc())
    sys.exit(1)

app = Flask(__name__)
CORS(app)  # Enable CORS for all routes

@app.route("/")
@app.route("/index")
@app.route("/index.html")
@app.route("/home")
def index():
    return render_template("index.html")

@app.route("/static/<path:path>")
def serve_static(path):
    return send_from_directory("static", path)

@app.route("/api/optimize", methods=["POST", "GET"])
def optimize():
    logger.info(f"Received {request.method} request to /api/optimize")
    
    # Handle GET requests with instructions
    if request.method == "GET":
        return jsonify({
            "message": "This endpoint requires a POST request with a resume file and job description",
            "usage": {
                "method": "POST",
                "content_type": "multipart/form-data",
                "parameters": {
                    "resume": "PDF or DOCX file",
                    "job_description": "Text of the job description"
                }
            }
        })
    
    try:
        logger.info(f"Request form data keys: {list(request.form.keys())}")
        logger.info(f"Request files keys: {list(request.files.keys())}")
        
        # Get the resume file from the request
        if 'resume' not in request.files:
            logger.error("No resume file in request")
            return jsonify({"error": "No resume file provided"}), 400
            
        resume_file = request.files['resume']
        job_description = request.form.get('job_description')
        
        logger.info(f"Resume filename: {resume_file.filename}")
        logger.info(f"Job description length: {len(job_description) if job_description else 0}")
        
        if not job_description:
            return jsonify({"error": "No job description provided"}), 400
        
        # Process and save the resume
        temp_file = tempfile.NamedTemporaryFile(delete=False)
        filename = secure_filename(resume_file.filename)
        file_path = temp_file.name
        resume_file.save(file_path)
        temp_file.close()
        
        logger.info(f"Resume saved to temporary file: {file_path}")
        
        # Check if environment variables are set
        logger.info(f"GEMINI_API_KEY set: {'Yes' if os.environ.get('GEMINI_API_KEY') else 'No'}")
        logger.info(f"BLOB_CONNECTION_STRING set: {'Yes' if os.environ.get('BLOB_CONNECTION_STRING') else 'No'}")
        logger.info(f"RESUME_CONTAINER_NAME set: {'Yes' if os.environ.get('RESUME_CONTAINER_NAME') else 'No'}")
        
        # Extract text from the resume
        logger.info("Extracting text from resume...")
        resume_text = extract_text_from_file(file_path, filename)
        logger.info(f"Extracted {len(resume_text)} characters from resume")
        
        # Upload the resume to blob storage
        logger.info("Uploading resume to blob storage...")
        blob_url = upload_to_blob_storage(file_path, filename)
        logger.info(f"Resume uploaded to {blob_url}")
        
        # Get optimization recommendations using Google Gemini API
        logger.info("Getting recommendations from Gemini API...")
        recommendations = get_gemini_recommendations(resume_text, job_description)
        logger.info("Recommendations received from Gemini API")
        
        # Clean up the temporary file
        os.remove(file_path)
        
        # Check if recommendations contains an error message
        if isinstance(recommendations, dict) and "error" in recommendations:
            logger.error(f"Error in Gemini recommendations: {recommendations['error']}")
            # The get_gemini_recommendations function now returns structured data even with errors
        
        # Return the results
        response_data = {
            "original_resume_url": blob_url,
            "recommendations": recommendations
        }
        
        logger.info("Returning successful response")
        return jsonify(response_data)
        
    except Exception as e:
        logger.error(f"Error in optimize: {str(e)}")
        logger.error(traceback.format_exc())
        
        # Create structured error response that will render properly in UI
        error_response = {
            "original_resume_url": "",
            "recommendations": {
                "matching_skills": [
                    {"skill": "System Error", "strength": 3, "importance": 5, "notes": f"An error occurred: {str(e)}"}
                ],
                "missing_skills": [
                    {"skill": "Error Recovery", "importance": 5, "suggestion": "Please try again or contact support if the issue persists."}
                ],
                "improvement_suggestions": [
                    "Our system encountered an error processing your request. Please try again with a different resume or job description."
                ],
                "potential_red_flags": [
                    "No analysis available due to system error."
                ],
                "experience_tailoring": [
                    "No tailoring suggestions available due to system error."
                ],
                "gap_analysis": {"overall_match": "N/A", "technical_match": "N/A", "experience_match": "N/A", "critical_gaps": ["Unable to analyze"]}
            }
        }
        
        return jsonify(error_response), 500

@app.route("/api/rewrite-resume", methods=["POST", "GET"])
def rewrite_resume():
    logger.info(f"Received {request.method} request to /api/rewrite-resume")
    
    # Handle GET requests with instructions
    if request.method == "GET":
        return jsonify({
            "message": "This endpoint requires a POST request with a resume file and job description",
            "usage": {
                "method": "POST",
                "content_type": "multipart/form-data",
                "parameters": {
                    "resume": "PDF or DOCX file",
                    "job_description": "Text of the job description",
                    "user_name": "Name of the user"
                }
            }
        })
    
    try:
        logger.info(f"Request form data keys: {list(request.form.keys())}")
        logger.info(f"Request files keys: {list(request.files.keys())}")
        
        # Get the resume file from the request
        if 'resume' not in request.files:
            logger.error("No resume file in request")
            return jsonify({"error": "No resume file provided"}), 400
            
        resume_file = request.files['resume']
        job_description = request.form.get('job_description')
        user_name = request.form.get('user_name', "User")
        
        logger.info(f"Resume filename: {resume_file.filename}")
        logger.info(f"Job description length: {len(job_description) if job_description else 0}")
        logger.info(f"User name: {user_name}")
        
        if not job_description:
            return jsonify({"error": "No job description provided"}), 400
        
        # Process and save the resume
        temp_file = tempfile.NamedTemporaryFile(delete=False)
        filename = secure_filename(resume_file.filename)
        file_path = temp_file.name
        resume_file.save(file_path)
        temp_file.close()
        
        logger.info(f"Resume saved to temporary file: {file_path}")
        
        # Extract text from the resume
        logger.info("Extracting text from resume...")
        resume_text = extract_text_from_file(file_path, filename)
        logger.info(f"Extracted {len(resume_text)} characters from resume")
        
        # Check if environment variables are set
        logger.info(f"GEMINI_API_KEY set: {'Yes' if os.environ.get('GEMINI_API_KEY') else 'No'}")
        logger.info(f"BLOB_CONNECTION_STRING set: {'Yes' if os.environ.get('BLOB_CONNECTION_STRING') else 'No'}")
        
        # Initialize the ResumeAgent
        logger.info("Initializing ResumeAgent...")
        resume_agent = ResumeAgent()
        
        # Process the resume
        logger.info("Processing resume...")
        result = resume_agent.process_resume(file_path, job_description, user_name, filename)
        
        # Upload the original resume to blob storage for reference
        logger.info("Uploading original resume to blob storage...")
        try:
            original_blob_url = upload_to_blob_storage(file_path, filename)
            logger.info(f"Original resume uploaded to {original_blob_url}")
            result["original_resume_url"] = original_blob_url
        except Exception as upload_error:
            logger.error(f"Error uploading original resume: {str(upload_error)}")
            result["original_resume_url"] = ""
        
        # Clean up the temporary file
        os.remove(file_path)
        
        # Check if result contains an error
        if "error" in result:
            logger.warning(f"Resume rewriting returned an error: {result.get('error')}")
            
            # Even with an error, if we have a rewritten_resume_text, we can still generate a document
            if "rewritten_resume_text" in result and result["rewritten_resume_text"]:
                logger.info("Using fallback resume text to generate document despite error")
                try:
                    # Continue with document generation even if there was an API error
                    from src.function_app.docx_generator import text_to_docx
                    
                    # Generate the DOCX from the fallback text
                    logger.info("Generating DOCX from fallback text...")
                    docx_data = text_to_docx(result["rewritten_resume_text"])
                    
                    # Save to temporary file
                    logger.info("Saving generated DOCX to temporary file...")
                    output_path = os.path.join(tempfile.gettempdir(), f"Tailored_Resume_{datetime.datetime.now().strftime('%Y%m%d%H%M%S')}.docx")
                    with open(output_path, "wb") as f:
                        f.write(docx_data)
                    
                    # Upload to blob storage
                    logger.info("Uploading generated DOCX to blob storage...")
                    try:
                        # Get the identifiers for the filename
                        from src.function_app.resume_rewriter import generate_unique_identifier
                        unique_filename = generate_unique_identifier(user_name, "Senior Position", "Company")
                        
                        # Upload to the tailored resume container
                        container_name = os.environ.get("TAILORED_RESUME_CONTAINER_NAME", "tailoredresumecontainer")
                        blob_service_client = BlobServiceClient.from_connection_string(os.environ["BLOB_CONNECTION_STRING"])
                        container_client = blob_service_client.get_container_client(container_name)
                        blob_client = container_client.get_blob_client(unique_filename)
                        
                        with open(output_path, "rb") as data:
                            blob_client.upload_blob(data, overwrite=True)
                        
                        # Add blob URL to the result
                        result["tailored_resume_url"] = blob_client.url
                        
                        # Update the error to indicate fallback was used
                        result["error"] = f"Warning: {result.get('error')}. A fallback resume was generated instead."
                        
                        logger.info(f"Tailored resume uploaded successfully to {blob_client.url}")
                    except Exception as blob_error:
                        logger.error(f"Error uploading tailored resume: {str(blob_error)}")
                        result["tailored_resume_url"] = ""
                    
                    # Clean up
                    os.remove(output_path)
                except Exception as docx_error:
                    logger.error(f"Error generating fallback document: {str(docx_error)}")
            
        # Return the results
        logger.info("Returning response for resume rewriting")
        return jsonify(result)
        
    except Exception as e:
        logger.error(f"Error in rewrite_resume: {str(e)}")
        logger.error(traceback.format_exc())
        return jsonify({
            "error": f"An error occurred while processing your resume: {str(e)}",
            "details": traceback.format_exc()
        }), 500

@app.route("/health")
def health():
    return "OK"

@app.route("/api/check-env")
def check_env():
    """Debug endpoint to check environment variables"""
    env_vars = {
        "GEMINI_API_KEY": bool(os.environ.get("GEMINI_API_KEY")),
        "GEMINI_API_VERSION": os.environ.get("GEMINI_API_VERSION", "v1"),
        "BLOB_CONNECTION_STRING": bool(os.environ.get("BLOB_CONNECTION_STRING")),
        "RESUME_CONTAINER_NAME": os.environ.get("RESUME_CONTAINER_NAME"),
        "TAILORED_RESUME_CONTAINER_NAME": os.environ.get("TAILORED_RESUME_CONTAINER_NAME"),
        "TRACKING_CONTAINER_NAME": os.environ.get("TRACKING_CONTAINER_NAME"),
        "TRACKING_FILE_NAME": os.environ.get("TRACKING_FILE_NAME"),
        "PYTHONPATH": os.environ.get("PYTHONPATH")
    }
    return jsonify(env_vars)

@app.route("/api/test", methods=["GET"])
def test_api():
    """Simple test endpoint to check if API is functioning"""
    return jsonify({
        "status": "success",
        "message": "API is working correctly",
        "time": str(datetime.datetime.now())
    })

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8000, debug=True) 
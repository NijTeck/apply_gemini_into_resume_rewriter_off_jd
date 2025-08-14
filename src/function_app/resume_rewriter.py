import os
import json
import logging
import datetime
import re
import time
from typing import Dict, List, Any
import google.generativeai as genai

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("resume-rewriter")

def rewrite_resume(resume_text: str, job_description: str) -> Dict[str, Any]:
    """Rewrite a resume to align with a job description using Google Gemini API"""
    try:
        # Get API key from environment
        api_key = os.environ.get("GEMINI_API_KEY")
        if not api_key:
            raise EnvironmentError("GEMINI_API_KEY environment variable is not set.")

        # Configure with the API key
        genai.configure(api_key=api_key)
        
        # Align with Analyze Resume settings
        model_id = os.environ.get("GEMINI_MODEL_ID", "gemini-1.5-pro")
        model = genai.GenerativeModel(model_id)
        
        # Adjust generation config to slow down generation
        generation_config = {
            "temperature": 0.5,  # Lower temperature for slower, more deterministic generation
            "top_k": 40,
            "top_p": 0.8,  # Lower top_p to reduce randomness
            "max_output_tokens": 1024,  # Keep output size manageable
            "candidate_count": 1
        }
        
        # Extract job details first
        job_title, company_name, role = extract_job_details(job_description)
        
        # Prepare the enhanced prompt with formatting instructions
        prompt = f"""
            You are an expert resume writer tasked with rewriting a resume for a specific job, focusing on content alignment, professional formatting for a DOCX document, and meeting specific header and space requirements.

            ## CRITICAL REQUIREMENTS:
            - The rewritten resume MUST be extremely detailed, with expansive content that fills exactly TWO FULL PAGES when formatted in a standard resume layout.
            - DO NOT be concise - you MUST be verbose and thorough in describing each role, responsibility, and achievement.
            - Create AT LEAST 5-7 detailed bullet points for EVERY job position (more for recent positions).
            - Each bullet point MUST be multi-sentence and comprehensive (3-4 lines of text each minimum).
            - The professional summary section MUST be 6-8 lines minimum with extensive details about expertise.
            - Include ALL original job positions, skills, and experiences from the original resume WITHOUT omitting any.
            - Maintain the exact formatting of the header seen in the original resume including citizenship, clearance, and contact details.

            ## Header Requirements (EXACT FORMAT):
            Include the following at the top of the resume in the header (use placeholders if not provided in the original resume):
            - Optional summary line (e.g., Citizenship | Clearance) IF PRESENT in the user's original resume
            - 555-555-5555 | you@example.com | https://example.com | City, State

            ## Content Expansion Guidelines:
            1. For EVERY bullet point from the original resume, expand it to 3-5 sentences that elaborate on:
               - The specific architectural challenge or business problem
               - Your detailed solution approach and methodologies used
               - The exact technologies, frameworks, and tools leveraged
               - Cross-functional teams involved and your leadership role
               - Quantifiable business impact and results achieved
               - Any optimization, cost-saving, or compliance aspects

            2. For EACH job position, include:
               - A 2-3 sentence role introduction paragraph before bullets
               - 5-7 comprehensive bullet points minimum (more for recent positions)
               - Additional details on projects, responsibilities, and achievements
               - Specific technology stacks, architectures, and methodologies used

            3. For the skills section:
               - Organize into clear categories exactly matching the original resume
               - Maintain ALL skills from the original resume
               - Add relevant skills from the job description only if you have genuine experience with them

            ## Job Description:
            {job_description}

            ## Original Resume:
            {resume_text}

            ## FORMATTING INSTRUCTIONS:
            Use these exact markers for formatting:
            - `[NAME] Your Name`
            - `[CONTACT] 555-555-5555 | you@example.com | https://example.com | City, State`
            - `[SUMMARY] Professional summary with key qualifications and expertise...` (expand this to 6-8 detailed lines)
            - `[SECTION_HEADER] PROFESSIONAL EXPERIENCE`
            - `[JOB_TITLE] Senior Cloud Engineer`
            - `[COMPANY] ExampleCorp`
            - `[DATES] Jan 2022 – Present`
            - `[LOCATION] City, State`
            - Paragraph text for role overview (2-3 sentences)
            - `[BULLET] Extensive bullet point with multiple sentences and specific details...`
            - `[SECTION_HEADER] SKILLS`
            - `[SKILL_CATEGORY] Configuration & Deployment`
            - `[SKILLS] Microsoft Autopilot, Microsoft Intune, Active Directory, Azure Active Directory, Windows 10, Windows 11`

            ## CRITICAL LENGTH REQUIREMENT:
            The final resume MUST provide enough detailed content to fill TWO COMPLETE PAGES when formatted. This requires approximately 700-1000 words of expanded text with multiple detailed bullet points for every position.

            ## Output Format:
            Respond ONLY with a JSON object containing the rewritten resume text structured with the markers above, plus metadata. Use this exact structure:
            {{
                "rewritten_resume_text": "[NAME] Your Name\\n[CONTACT] 555-555-5555 | you@example.com | https://example.com | City, State\\n\\n[SUMMARY] Highly experienced Cloud Professional with 6+ years of expertise in architecting, engineering, and securing cloud solutions... (expanded to 6-8 lines)\\n\\n[SECTION_HEADER] PROFESSIONAL EXPERIENCE\\n\\n[JOB_TITLE] Senior Cloud Engineer\\n[COMPANY] ExampleCorp\\n[DATES] Jan 2022 – Present\\n[LOCATION] City, State\\nComprehensive 2-3 sentence role introduction explaining overall responsibilities and scope...\\n[BULLET] Expanded first bullet with 3-4 sentences covering the architectural challenge, solution approach, technologies used, and measurable impact...\\n[BULLET] Expanded second bullet with 3-4 sentences about another key achievement...\\n... (repeat with 5+ bullets per position) ...\\n\\n[JOB_TITLE] Systems Administrator\\n[COMPANY] Example Company\\n[DATES] Sep 2020 – Jan 2022\\n... (repeat same detailed format for ALL positions) ...\\n\\n[SECTION_HEADER] SKILLS\\n\\n[SKILL_CATEGORY] Configuration & Deployment\\n[SKILLS] Microsoft Intune, Active Directory, Azure Active Directory, Windows 10, Windows 11\\n\\n[SKILL_CATEGORY] Scripting & Automation\\n[SKILLS] PowerShell\\n\\n... (continue with all categories from original resume) ...\\n",
                "changes_summary": ["Expanded each bullet to provide comprehensive context and details", "Added quantifiable achievements and specific technologies", "Enhanced professional summary to highlight key qualifications", "Maintained all original experience while providing more context"],
                "integration_percentage": "90%",
                "highlighted_skills": ["Cloud Platforms", "Security", "Automation", "Infrastructure Management"],
                "gap_analysis": ["Any requirements from job description not addressed"]
            }}

            Ensure the `rewritten_resume_text` strictly follows the marker format. The rewritten text MUST be significantly longer and more detailed than the original to fill exactly TWO PAGES. No extra text outside the JSON.
        """
        
        # Configure safety settings
        safety_settings = [
            {
                "category": "HARM_CATEGORY_HARASSMENT",
                "threshold": "BLOCK_MEDIUM_AND_ABOVE"
            },
            {
                "category": "HARM_CATEGORY_HATE_SPEECH",
                "threshold": "BLOCK_MEDIUM_AND_ABOVE"
            },
            {
                "category": "HARM_CATEGORY_SEXUALLY_EXPLICIT",
                "threshold": "BLOCK_MEDIUM_AND_ABOVE"
            },
            {
                "category": "HARM_CATEGORY_DANGEROUS_CONTENT",
                "threshold": "BLOCK_MEDIUM_AND_ABOVE"
            }
        ]
        
        # Log detailed configuration for debugging
        logger.info("API Key: %s", api_key[:4] + "****")
        logger.info("Model ID: %s", model_id)
        logger.info("Prompt Length: %d", len(prompt))
        logger.info("Generation Config: %s", generation_config)
        logger.info("Safety Settings: %s", safety_settings)
        
        # Make the API request with retries
        max_retries = 3
        retry_delay = 10
        last_error = None
        
        for attempt in range(1, max_retries + 1):
            try:
                logger.info(f"Sending request to Gemini API for structured resume rewriting (attempt {attempt}/{max_retries})")
                # Log generation configuration
                logger.info(f"Using model: {model_id} with output tokens: {generation_config['max_output_tokens']}")
                
                # Make the request with safety settings
                response = model.generate_content(
                    contents=prompt,
                    generation_config=generation_config,
                    safety_settings=safety_settings
                )
                
                # Log the API response
                logger.info("API Response: %s", response.text if response else "No response")
                
                # Process the response
                if response and hasattr(response, "text"):
                    try:
                        # Look for JSON content in the response
                        json_start = response.text.find('{')
                        json_end = response.text.rfind('}') + 1
                        
                        if json_start >= 0 and json_end > json_start:
                            json_text = response.text[json_start:json_end]
                            rewrite_result = json.loads(json_text)
                            
                            # Verify content length - if too short, reject and add error
                            rewritten_text = rewrite_result.get("rewritten_resume_text", "")
                            # At least 4000 chars to fill 2 pages with detailed content
                            if len(rewritten_text) < 4000:
                                logger.warning(f"Generated resume too short ({len(rewritten_text)} chars), needs at least 4000 chars for 2 pages")
                                if attempt < max_retries:
                                    logger.info(f"Retrying to get longer content (attempt {attempt}/{max_retries})")
                                    time.sleep(retry_delay)
                                    continue
                                else:
                                    return {
                                        "error": "Generated resume content insufficient to fill two pages. Please try again.",
                                        "rewritten_resume_text": rewritten_text
                                    }
                            
                            # Add job details to the result
                            rewrite_result["job_title"] = job_title
                            rewrite_result["company_name"] = company_name
                            rewrite_result["role"] = role
                            rewrite_result["date_modified"] = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                            
                            logger.info(f"Successfully parsed structured resume from Gemini response: {len(rewritten_text)} characters")
                            return rewrite_result
                        else:
                            logger.error("JSON content not found in the structured response")
                            if attempt < max_retries:
                                logger.info(f"Retrying due to missing JSON (attempt {attempt}/{max_retries})")
                                time.sleep(retry_delay)
                                continue
                            else:
                                return {
                                    "error": "JSON content not found in the response", 
                                    "raw_response": response.text,
                                    "rewritten_resume_text": generate_fallback_resume(resume_text, job_description)
                                }
                                
                    except json.JSONDecodeError as e:
                        logger.error(f"Failed to parse structured JSON response: {e}")
                        if attempt < max_retries:
                            logger.info(f"Retrying due to JSON parse error (attempt {attempt}/{max_retries})")
                            time.sleep(retry_delay)
                            continue
                        else:
                            return {
                                "error": "Failed to parse JSON response", 
                                "raw_response": response.text,
                                "rewritten_resume_text": generate_fallback_resume(resume_text, job_description)
                            }
                else:
                    logger.error("Empty response from Gemini API for structured rewrite")
                    if attempt < max_retries:
                        logger.info(f"Retrying due to empty response (attempt {attempt}/{max_retries})")
                        time.sleep(retry_delay)
                        continue
                    else:
                        return {
                            "error": "Empty response from API",
                            "rewritten_resume_text": generate_fallback_resume(resume_text, job_description)
                        }
            except Exception as retry_error:
                import traceback
                except_message = str(retry_error)
                logger.error(f"Error during resume rewriting attempt {attempt}: {except_message}\n{traceback.format_exc()}")
                last_error = retry_error
                if attempt < max_retries:
                    logger.info(f"Retrying after error (attempt {attempt}/{max_retries})")
                    time.sleep(retry_delay)
                    continue

        # Add explicit logging for rate limit issues
        if last_error and (
            'quota' in str(last_error).lower() or
            'rate limit' in str(last_error).lower() or
            '429' in str(last_error) or
            'exceeded' in str(last_error).lower()
        ):
            logger.error("Rate limit or quota issue detected: %s", last_error)
            return {
                "error": str(last_error),
                "rewritten_resume_text": generate_fallback_resume(resume_text, job_description)
            }

        # Attempt to use a more stable API version
        try:
            model = genai.GenerativeModel("v1main")
            response = model.generate_content(
                contents=prompt,
                generation_config=generation_config,
                safety_settings=safety_settings
            )
        except Exception as stable_api_error:
            logger.error(f"Fallback to v1main API failed: {stable_api_error}")
            raise
        
        # If we made it here, all retries failed
        error_msg = str(last_error) if last_error else "Unknown error after all retry attempts"
        
        # Check for quota/rate limit error
        if last_error and (
            'quota' in error_msg.lower() or
            'rate limit' in error_msg.lower() or
            '429' in error_msg or
            'exceeded' in error_msg.lower()
        ):
            user_msg = (
                "The resume rewriting service is temporarily unavailable due to high demand or quota limits. "
                "Please try again in a few minutes. If the problem persists, contact support."
            )
            logger.error(f"Quota/rate limit error: {error_msg}")
            return {
                "error": error_msg, 
                "rewritten_resume_text": generate_fallback_resume(resume_text, job_description)
            }
        
        logger.error(f"Error rewriting resume with structure after all retries: {error_msg}")
        return {
            "error": error_msg,
            "rewritten_resume_text": generate_fallback_resume(resume_text, job_description)
        }
    
    except Exception as e:
        import traceback
        except_message = str(e)
        logger.error(f"Exception in rewrite_resume: {except_message}\n{traceback.format_exc()}")
        return {
            "error": except_message,
            "rewritten_resume_text": generate_fallback_resume(resume_text, job_description)
        }

def extract_job_details(job_description: str) -> tuple:
    """Extract job title, company name, and role from the job description"""
    try:
        # Initialize the Gemini API
        genai.configure(api_key=os.environ["GEMINI_API_KEY"])
        # Use a compatible model like gemini-1.5-pro-latest
        model_id = os.environ.get("GEMINI_MODEL_ID", "gemini-1.5-pro-latest")
        model = genai.GenerativeModel(model_id)
        
        # Prepare the prompt
        prompt = f"""
        Extract the following information from this job description:
        1. Job Title (the specific position being advertised)
        2. Company Name (the organization offering the job)
        3. Role (the general role category, like "Engineering", "Marketing", "Finance", etc.)
        
        If any of these cannot be clearly determined, use "Not Specified".
        
        Job Description:
        {job_description}
        
        Respond only with a JSON object in this exact format:
        {{
            "job_title": "extracted job title",
            "company_name": "extracted company name",
            "role": "extracted role category"
        }}
        """
        
        # Create generation config
        generation_config = {
            "temperature": 0.1,
            "top_k": 40,
            "top_p": 0.95,
            "max_output_tokens": 1024,
        }
        
        # Make the API request
        response = model.generate_content(
            contents=prompt,
            generation_config=generation_config
        )
        
        # Process the response
        if response and response.text:
            try:
                # Look for JSON content in the response
                json_start = response.text.find('{')
                json_end = response.text.rfind('}') + 1
                
                if json_start >= 0 and json_end > json_start:
                    json_text = response.text[json_start:json_end]
                    details = json.loads(json_text)
                    return (
                        details.get("job_title", "Not Specified"),
                        details.get("company_name", "Not Specified"),
                        details.get("role", "Not Specified")
                    )
            except json.JSONDecodeError:
                pass # Fallback to regex if JSON parsing fails
        
        # Fall back to simple regex extraction if API fails or JSON parsing fails
        job_title = "Not Specified"
        company_name = "Not Specified"
        role = "Not Specified"
        
        # Simple regex patterns (these are basic and would need refinement)
        title_patterns = [
            r"(?:Job Title|Position|Title):\s*([^\n]+)",
            r"(?:hiring|seeking|looking for|recruiting) (?:a|an) ([^\n.]+)"
        ]
        
        company_patterns = [
            r"(?:Company|Organization|Employer):\s*([^\n]+)",
            r"([A-Z][a-zA-Z0-9\s&]+) is seeking",
            r"About ([A-Z][a-zA-Z0-9\s&]+)"
        ]
        
        for pattern in title_patterns:
            match = re.search(pattern, job_description, re.IGNORECASE)
            if match:
                job_title = match.group(1).strip()
                break
                
        for pattern in company_patterns:
            match = re.search(pattern, job_description, re.IGNORECASE)
            if match:
                company_name = match.group(1).strip()
                break
                
        # Role is often harder to extract with regex
        # For simplicity, use the job title if available
        if job_title != "Not Specified":
            role_words = job_title.split()
            if len(role_words) > 0:
                role = role_words[0]  # Just use the first word as a simple fallback
        
        return job_title, company_name, role
    
    except Exception as e:
        logger.error(f"Error extracting job details: {str(e)}")
        return "Not Specified", "Not Specified", "Not Specified"

def generate_unique_identifier(name: str, job_title: str, company: str) -> str:
    """Generate a unique identifier for the tailored resume file"""
    def sanitize(text):
        return re.sub(r'[^\w\s-]', '', text).strip().replace(' ', '_')
    
    sanitized_name = sanitize(name)
    sanitized_job = sanitize(job_title)
    sanitized_company = sanitize(company)
    timestamp = datetime.datetime.now().strftime("%Y%m%d%H%M%S")
    
    return f"Resume_{sanitized_name}_{sanitized_job}_{sanitized_company}_{timestamp}.docx"

def generate_fallback_resume(resume_text: str, job_description: str) -> str:
    """Generate a fallback formatted resume when the API fails"""
    try:
        # Extract name and contact info from the resume if possible (fallback to placeholder)
        name = "Your Name"
        
        # Extract basic job details
        job_lines = job_description.split('\n')
        job_title = "Senior Cloud Engineer"  # Default
        company = "Not Specified"
        
        # Look for company name in job description
        company_match = re.search(r"(?:at|for|with|@)\s+([A-Z][A-Za-z\s&]+)", job_description)
        if company_match:
            company = company_match.group(1).strip()
        
        # Look for job title in job description
        title_match = re.search(r"(Senior|Sr\.?|Lead|Principal|Cloud|Azure|AWS|DevOps|Engineer|Architect|Developer)[\s\w]+(?:Engineer|Architect|Developer|Professional|Consultant|Specialist)", job_description)
        if title_match:
            job_title = title_match.group(0).strip()
        
        # Create a basic formatted resume that will work with the docx generator
        fallback_text = f"""[NAME] {name}
[CONTACT] 555-555-5555 | you@example.com | https://example.com | City, State

US Citizen | Active DoD Secret Clearance

[SUMMARY] Highly experienced Cloud Professional with 6+ years of expertise in architecting, engineering, and securing Microsoft Azure solutions. Committed to delivering robust infrastructure with a focus on automation, security compliance, and operational excellence. Demonstrated success in implementing scalable cloud architectures and DevOps practices across enterprise environments. Skilled in designing and implementing secure, cost-effective cloud solutions that meet business requirements while ensuring compliance with regulatory standards.

[SECTION_HEADER] PROFESSIONAL EXPERIENCE

[JOB_TITLE] Senior Cloud Engineer
[COMPANY] ExampleCorp
[DATES] Jan 2022 – Present
[LOCATION] City, State
Serve as a technical leader for enterprise cloud infrastructure, responsible for designing, implementing and managing Microsoft Azure solutions across multiple business units while ensuring security compliance and operational efficiency.
[BULLET] Architected and implemented comprehensive Azure landing zones and governance frameworks that ensured security compliance while enabling development teams to deploy resources efficiently. This involved creating custom RBAC roles, implementing Azure Policy initiatives, and establishing resource organization structures that balanced security with operational agility, resulting in 40% faster resource provisioning while maintaining 100% compliance with organizational security standards.
[BULLET] Led the migration of critical on-premises applications to Azure, developing detailed assessment frameworks, migration strategies, and validation processes that ensured minimal business disruption. This involved comprehensive application dependency mapping, performance baseline establishment, and post-migration validation procedures, resulting in successful migration of 25+ applications with 99.9% uptime during transition.
[BULLET] Designed and implemented robust disaster recovery and business continuity solutions utilizing Azure Site Recovery, Azure Backup, and geo-redundant storage options that ensured critical systems could be recovered within defined RPO/RTO requirements. This included automated recovery testing procedures, documentation of recovery processes, and regular disaster simulation exercises, which reduced potential recovery time from days to hours.
[BULLET] Established comprehensive monitoring solutions using Azure Monitor, Log Analytics, and Application Insights that provided real-time visibility into infrastructure health, application performance, and security posture. This solution incorporated custom dashboard creation, automated alerting mechanisms, and integration with incident management systems, resulting in 60% faster incident detection and resolution.
[BULLET] Implemented Azure DevOps CI/CD pipelines for infrastructure deployment that enabled consistent, repeatable, and auditable infrastructure changes across environments. This included creating reusable ARM and Bicep templates, implementing approval gates, and integrating security scanning tools, which reduced deployment errors by 75% while increasing deployment frequency.
[BULLET] Conducted technical mentoring and knowledge transfer sessions for junior engineers, developing comprehensive training materials and hands-on workshops focused on Azure technologies and best practices. These initiatives improved team capabilities, decreased knowledge silos, and established consistent technical approaches across the organization.

[JOB_TITLE] Systems Administrator
[COMPANY] Example Company
[DATES] Sep 2020 – Jan 2022
[LOCATION] Dallas, Texas
Managed enterprise-wide infrastructure systems with primary responsibility for Microsoft technologies, including Active Directory, Exchange, and Windows Server environments, while driving automation initiatives to improve operational efficiency.
[BULLET] Designed and implemented comprehensive Active Directory and Azure AD infrastructure that supported over 5,000 users across multiple business units while ensuring security compliance and operational efficiency. This involved restructuring OU hierarchies, implementing group policy frameworks, and establishing identity synchronization mechanisms, resulting in 30% reduction in user access issues and improved security posture.
[BULLET] Led the migration from on-premises Exchange to Exchange Online, developing detailed migration strategies, coexistence architectures, and cutover processes that minimized business disruption. This project included comprehensive discovery of existing mail flows, third-party integrations, and compliance requirements, resulting in successful migration of 5,000+ mailboxes with minimal user impact.
[BULLET] Architected and deployed Windows Virtual Desktop (now Azure Virtual Desktop) infrastructure that enabled secure remote work capabilities for the entire organization during COVID-19 pandemic response. This solution incorporated multi-session host pools, FSLogix profile containers, and conditional access policies, providing secure, performant desktop experiences that supported business continuity.
[BULLET] Implemented comprehensive automation frameworks using PowerShell, creating reusable modules and scripts for common administrative tasks, user onboarding/offboarding, and compliance reporting. These automation initiatives reduced administrative overhead by 40% while improving consistency and reducing human error in system administration tasks.
[BULLET] Established robust backup and disaster recovery solutions for critical infrastructure components, implementing multi-tiered backup strategies with clear retention policies and regular recovery testing. This comprehensive approach ensured business continuity capabilities with defined recovery point and recovery time objectives for all critical systems.
[BULLET] Led the implementation of Microsoft Endpoint Configuration Manager (MECM) for enterprise-wide device management, creating standardized deployment packages, compliance policies, and reporting frameworks. This centralized management solution improved security posture, reduced support incidents, and enabled consistent software delivery across the organization.

[SECTION_HEADER] SKILLS

[SKILL_CATEGORY] Configuration & Deployment
[SKILLS] Microsoft Autopilot, Microsoft Intune, Active Directory, Azure Active Directory, Windows 10, Windows 11

[SKILL_CATEGORY] Scripting & Automation
[SKILLS] PowerShell, Desired State Configuration, Azure Resource Manager Templates, Bicep, Azure CLI, GitHub Actions, Azure DevOps Pipelines

[SKILL_CATEGORY] Cloud & Virtualization
[SKILLS] Microsoft Azure, Azure Virtual Desktop, Hyper-V, VMware vSphere, Azure Kubernetes Service, Azure Container Instances

[SKILL_CATEGORY] Monitoring & Management
[SKILLS] Azure Monitor, Log Analytics, Application Insights, System Center Operations Manager, Azure Automation, Azure Update Management

[SKILL_CATEGORY] Security & Compliance
[SKILLS] Microsoft Defender for Cloud, Microsoft Sentinel, Azure Key Vault, Microsoft Information Protection, Azure Policy, Regulatory Compliance Frameworks

[SKILL_CATEGORY] Networking
[SKILLS] Azure Virtual Networks, ExpressRoute, VPN Gateway, Network Security Groups, Azure Firewall, Azure Front Door, Azure Application Gateway
"""
        
        # Log the fallback resume output
        logger.info("Fallback Resume Output: %s", fallback_text)
        
        return fallback_text
    except Exception as e:
        logger.error(f"Error generating fallback resume: {str(e)}")
        # Return absolute minimal fallback
        return """[NAME] Your Name
[CONTACT] 555-555-5555 | you@example.com | https://example.com | City, State

US Citizen | Active DoD Secret Clearance

[SUMMARY] Highly experienced Cloud Professional with expertise in Azure cloud solutions.

[SECTION_HEADER] PROFESSIONAL EXPERIENCE

[JOB_TITLE] Senior Cloud Engineer
[COMPANY] ExampleCorp
[DATES] Jan 2022 – Present
[BULLET] Designed and implemented Azure cloud solutions.
[BULLET] Managed cloud infrastructure and security compliance.

[SECTION_HEADER] SKILLS

[SKILL_CATEGORY] Cloud Technologies
[SKILLS] Microsoft Azure, Active Directory, PowerShell, Azure DevOps"""


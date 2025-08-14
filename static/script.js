// Tab switching functionality
function openTab(evt, tabName) {
    // Hide all tab content
    var tabContents = document.getElementsByClassName("tab-content");
    for (var i = 0; i < tabContents.length; i++) {
        tabContents[i].classList.remove("active");
    }
    
    // Remove "active" class from all tab buttons
    var tabButtons = document.getElementsByClassName("tab-button");
    for (var i = 0; i < tabButtons.length; i++) {
        tabButtons[i].classList.remove("active");
    }
    
    // Show the selected tab content and add "active" class to the button
    document.getElementById(tabName).classList.add("active");
    evt.currentTarget.classList.add("active");
}

// Resume Analysis Form Handler
document.getElementById("analyzeForm").addEventListener("submit", function(e) {
    e.preventDefault();
    
    const formData = new FormData();
    formData.append("resume", document.getElementById("resumeAnalyze").files[0]);
    formData.append("job_description", document.getElementById("jobDescriptionAnalyze").value);
    
    // Show loading indicator
    document.getElementById("analyzeResults").innerHTML = "<p>Analyzing your resume... This may take a minute.</p>";
    document.getElementById("analyzeResults").style.display = "block";
    
    fetch("/api/optimize", {
        method: "POST",
        body: formData
    })
    .then(response => response.json())
    .then(data => {
        console.log("API Response:", data); // Debug: Log full response data
        document.getElementById("analyzeResults").innerHTML = ""; // Clear loading indicator
        document.getElementById("analyzeResults").style.display = "block";
        
        // Add the heading back
        const heading = document.createElement("h2");
        heading.textContent = "Recommendations";
        document.getElementById("analyzeResults").appendChild(heading);
        
        // Check for errors first
        if (data.error) {
            const errorDiv = document.createElement("div");
            errorDiv.className = "error-message";
            errorDiv.textContent = `Error: ${data.error}`;
            document.getElementById("analyzeResults").appendChild(errorDiv);
            return;
        }

        // Check if recommendations object exists
        if (!data.recommendations) {
            const errorDiv = document.createElement("div");
            errorDiv.className = "error-message";
            errorDiv.textContent = "No recommendations found in the API response.";
            document.getElementById("analyzeResults").appendChild(errorDiv);
            return;
        }

        // Check if recommendations contains an error message
        if (data.recommendations.error) {
            const errorDiv = document.createElement("div");
            errorDiv.className = "error-message";
            errorDiv.textContent = `API Error: ${data.recommendations.error}`;
            // Add "Please try again later or contact support" to be more user-friendly
            const helpText = document.createElement("p");
            helpText.className = "error-help";
            helpText.textContent = "Please try again later or contact support if the issue persists.";
            errorDiv.appendChild(helpText);
            document.getElementById("analyzeResults").appendChild(errorDiv);
            return;
        }

        // If there's a raw_response, show it and return
        if (data.recommendations.raw_response) {
            const rawDiv = document.createElement("div");
            rawDiv.className = "raw-response";
            rawDiv.innerHTML = "<h3>API returned an unstructured response:</h3>";
            
            const rawContent = document.createElement("pre");
            rawContent.textContent = data.recommendations.raw_response;
            rawDiv.appendChild(rawContent);
            
            document.getElementById("analyzeResults").appendChild(rawDiv);
            return;
        }
        
        // Recreate all the sections
        const sections = [
            { id: "matching-skills", title: "Matching Skills" },
            { id: "missing-skills", title: "Missing Skills" },
            { id: "improvement-suggestions", title: "Improvement Suggestions" },
            { id: "potential-red-flags", title: "Potential Red Flags" },
            { id: "experience-tailoring", title: "Experience Tailoring" },
            { id: "gap-analysis", title: "Gap Analysis" }
        ];
        
        sections.forEach(section => {
            const sectionDiv = document.createElement("div");
            sectionDiv.className = "section";
            
            const titleDiv = document.createElement("div");
            titleDiv.className = "section-title";
            titleDiv.textContent = section.title;
            sectionDiv.appendChild(titleDiv);
            
            const contentDiv = document.createElement("div");
            contentDiv.id = section.id;
            sectionDiv.appendChild(contentDiv);
            
            document.getElementById("analyzeResults").appendChild(sectionDiv);
        });
        
        // Now populate the sections
        // Handle matching skills with ratings
        const matchingSkillsContainer = document.getElementById("matching-skills");
        
        if (data.recommendations.matching_skills && Array.isArray(data.recommendations.matching_skills)) {
            // Check if we have the detailed format with objects
            if (typeof data.recommendations.matching_skills[0] === "object" && data.recommendations.matching_skills[0].hasOwnProperty("skill")) {
                data.recommendations.matching_skills.forEach(item => {
                    const skillDiv = document.createElement("div");
                    skillDiv.className = "skill-item";
                    
                    const skillHeader = document.createElement("div");
                    skillHeader.className = "skill-header";
                    skillHeader.innerHTML = `${item.skill} <span class="skill-rating">Strength: ${item.strength}/5</span> <span class="skill-importance">Importance: ${item.importance}/5</span>`;
                    
                    const skillNotes = document.createElement("div");
                    skillNotes.className = "skill-notes";
                    skillNotes.textContent = item.notes;
                    
                    skillDiv.appendChild(skillHeader);
                    skillDiv.appendChild(skillNotes);
                    matchingSkillsContainer.appendChild(skillDiv);
                });
            } else {
                // Handle old format (simple strings)
                const ul = document.createElement("ul");
                data.recommendations.matching_skills.forEach(item => {
                    const li = document.createElement("li");
                    li.textContent = item;
                    ul.appendChild(li);
                });
                matchingSkillsContainer.appendChild(ul);
            }
        }
        
        // Handle missing skills with importance
        const missingSkillsContainer = document.getElementById("missing-skills");
        
        if (data.recommendations.missing_skills && Array.isArray(data.recommendations.missing_skills)) {
            // Check if we have the detailed format with objects
            if (typeof data.recommendations.missing_skills[0] === "object" && data.recommendations.missing_skills[0].hasOwnProperty("skill")) {
                data.recommendations.missing_skills.forEach(item => {
                    const skillDiv = document.createElement("div");
                    skillDiv.className = "skill-item";
                    
                    const skillHeader = document.createElement("div");
                    skillHeader.className = "skill-header";
                    skillHeader.innerHTML = `${item.skill} <span class="skill-importance">Importance: ${item.importance}/5</span>`;
                    
                    const skillNotes = document.createElement("div");
                    skillNotes.className = "skill-notes";
                    skillNotes.textContent = item.suggestion;
                    
                    skillDiv.appendChild(skillHeader);
                    skillDiv.appendChild(skillNotes);
                    missingSkillsContainer.appendChild(skillDiv);
                });
            } else {
                // Handle old format (simple strings)
                const ul = document.createElement("ul");
                data.recommendations.missing_skills.forEach(item => {
                    const li = document.createElement("li");
                    li.textContent = item;
                    ul.appendChild(li);
                });
                missingSkillsContainer.appendChild(ul);
            }
        }
        
        // Populate regular lists
        function populateList(id, items) {
            const list = document.createElement("ul");
            if (Array.isArray(items)) {
                items.forEach(item => {
                    const li = document.createElement("li");
                    li.textContent = item;
                    list.appendChild(li);
                });
                document.getElementById(id).appendChild(list);
            }
        }
        
        populateList("improvement-suggestions", data.recommendations.improvement_suggestions);
        populateList("potential-red-flags", data.recommendations.potential_red_flags);
        populateList("experience-tailoring", data.recommendations.experience_tailoring);
        
        // Handle Gap Analysis
        const gapAnalysisContainer = document.getElementById("gap-analysis");
        
        if (data.recommendations.gap_analysis) {
            const gap = data.recommendations.gap_analysis;
            const stats = document.createElement("div");
            
            if (gap.overall_match) {
                const overallMatch = document.createElement("div");
                overallMatch.className = "gap-stat";
                overallMatch.innerHTML = "Overall Match: <span class='gap-value'>" + gap.overall_match + "</span>";
                stats.appendChild(overallMatch);
            }
            
            if (gap.technical_match) {
                const techMatch = document.createElement("div");
                techMatch.className = "gap-stat";
                techMatch.innerHTML = "Technical Match: <span class='gap-value'>" + gap.technical_match + "</span>";
                stats.appendChild(techMatch);
            }
            
            if (gap.experience_match) {
                const expMatch = document.createElement("div");
                expMatch.className = "gap-stat";
                expMatch.innerHTML = "Experience Match: <span class='gap-value'>" + gap.experience_match + "</span>";
                stats.appendChild(expMatch);
            }
            
            gapAnalysisContainer.appendChild(stats);
            
            if (gap.critical_gaps && gap.critical_gaps.length > 0) {
                const criticalTitle = document.createElement("div");
                criticalTitle.innerHTML = "<strong>Critical Gaps:</strong>";
                criticalTitle.className = "critical-gaps";
                gapAnalysisContainer.appendChild(criticalTitle);
                
                const gapsList = document.createElement("ul");
                gap.critical_gaps.forEach(item => {
                    const li = document.createElement("li");
                    li.textContent = item;
                    gapsList.appendChild(li);
                });
                gapAnalysisContainer.appendChild(gapsList);
            }
        }
    })
    .catch(error => {
        console.error("Error:", error);
        document.getElementById("analyzeResults").innerHTML = "<p>An error occurred while analyzing your resume. Please try again.</p>";
        document.getElementById("analyzeResults").style.display = "block";
    });
});

// Resume Rewrite Form Handler
document.getElementById("rewriteForm").addEventListener("submit", function(e) {
    e.preventDefault();
    
    const formData = new FormData();
    formData.append("resume", document.getElementById("resumeRewrite").files[0]);
    formData.append("job_description", document.getElementById("jobDescriptionRewrite").value);
    formData.append("user_name", document.getElementById("userName").value);
    
    // Show loading indicator
    document.getElementById("rewriteResults").innerHTML = "<p>Rewriting your resume... This may take 1-2 minutes.</p>";
    document.getElementById("rewriteResults").style.display = "block";
    
    fetch("/api/rewrite-resume", {
        method: "POST",
        body: formData
    })
    .then(response => response.json())
    .then(data => {
        console.log("API Response:", data); // Debug: Log full response data
        document.getElementById("rewriteResults").innerHTML = ""; // Clear loading indicator
        
        // Check for errors
        if (data.error) {
            const errorDiv = document.createElement("div");
            errorDiv.className = "error-message";
            errorDiv.textContent = data.error;
            
            // Add a helpful message for the user 
            const helpText = document.createElement("p");
            helpText.className = "error-help";
            helpText.textContent = "Please try again later or contact support if the issue persists. The API may be experiencing temporary issues.";
            errorDiv.appendChild(helpText);
            
            document.getElementById("rewriteResults").appendChild(errorDiv);
            
            // If we still have a tailored resume despite the error, show the link
            if (data.tailored_resume_url) {
                const successDiv = document.createElement("div");
                successDiv.className = "success-message";
                successDiv.innerHTML = `<p>A resume was still created for you despite the error. <a href="${data.tailored_resume_url}" target="_blank">Download your tailored resume</a></p>`;
                document.getElementById("rewriteResults").appendChild(successDiv);
            }
            
            return;
        }
        
        // Handle success case
        const successDiv = document.createElement("div");
        successDiv.className = "success-message";
        successDiv.innerHTML = `
            <h3>Resume successfully rewritten!</h3>
            <p><a href="${data.rewritten_resume_url}" target="_blank">Download your tailored resume</a></p>
        `;
        document.getElementById("rewriteResults").appendChild(successDiv);
    })
    .catch(error => {
        console.error("Error:", error);
        document.getElementById("rewriteResults").innerHTML = `
            <div class="error-message">
                <p>An error occurred while rewriting your resume. Please try again.</p>
                <p class="error-help">The system might be experiencing temporary issues. Please try again later or contact support if the problem persists.</p>
            </div>
        `;
    });
}); 
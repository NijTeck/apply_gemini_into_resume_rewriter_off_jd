FROM python:3.11-slim

WORKDIR /app

# Install curl for healthcheck
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Install required packages
RUN pip install --no-cache-dir \
    flask \
    flask-cors \
    gunicorn \
    requests \
    PyPDF2 \
    python-docx \
    azure-storage-blob \
    azure-ai-formrecognizer \
    python-dotenv \
    google-generativeai>=0.3.0

# Create directory structure
RUN mkdir -p /app/templates /app/static /app/src/function_app

# Copy static files and templates
COPY templates/ /app/templates/
COPY static/ /app/static/

# Copy function_app module properly
COPY src/function_app/*.py /app/src/function_app/
RUN touch /app/src/function_app/__init__.py

# Copy app.py
COPY app.py /app/app.py

# Create startup script
RUN echo '#!/bin/bash\n\
echo "Starting application..."\n\
echo "Python version: $(python --version)"\n\
echo "Current directory: $(pwd)"\n\
echo "Directory contents:"\n\
ls -la\n\
echo "PYTHONPATH: $PYTHONPATH"\n\
echo "Starting Gunicorn..."\n\
exec gunicorn --bind 0.0.0.0:8000 --log-level debug --error-logfile - --access-logfile - app:app\n\
' > /app/start.sh && chmod +x /app/start.sh

# Expose port
EXPOSE 8000

# Health check
HEALTHCHECK --interval=30s --timeout=30s --start-period=5s --retries=3 \
  CMD curl -f http://localhost:8000/health || exit 1

# Set environment variables
ENV PYTHONPATH=/app \
    PYTHONUNBUFFERED=1

# Start the app
CMD ["/app/start.sh"] 
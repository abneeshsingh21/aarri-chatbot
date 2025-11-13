FROM python:3.12-slim

WORKDIR /app

# Cache buster: force fresh build (numpy 1.x compatibility fix)
# Updated 2025-11-12T17:05:00Z

# Copy the entire backend first to ensure all files are in the build context
COPY backend/ .

# Install dependencies (requirements.txt is now at /app/requirements.txt)
RUN pip install --no-cache-dir -r requirements.txt

# Expose the port the app listens on
EXPOSE 5000

# Health check (runs at container runtime; requests is installed from requirements)
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD python -c "import requests, sys; r=requests.get('http://localhost:5000/health', timeout=5); sys.exit(0 if r.status_code==200 else 1)"

# Run the Flask app with gunicorn (increased timeout for FAISS initialization)
CMD ["gunicorn", "-w", "2", "-b", "0.0.0.0:5000", "--timeout", "120", "app:app"]

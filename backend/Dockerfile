# backend/Dockerfile
FROM python:3.11-slim

# Prevents python from writing .pyc files and buffers stdout/stderr (good for logs)
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV PORT=8080

# Create a non-root user for safety
RUN groupadd -r aarii && useradd -r -g aarii aarii

# system deps commonly needed by Python packages (add/remove as needed)
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    gcc \
    git \
    curl \
  && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Copy only dependency files first for better caching
COPY backend/requirements.txt backend/requirements-dev.txt* /app/

# Upgrade pip & install runtime (and gunicorn)
RUN python -m pip install --upgrade pip setuptools wheel \
 && python -m pip install --no-cache-dir -r requirements.txt \
 && python -m pip install --no-cache-dir gunicorn

# Optional: install dev requirements if file exists
# (this won't fail if requirements-dev.txt doesn't exist thanks to the wildcard usage)
RUN if [ -f requirements-dev.txt ]; then python -m pip install --no-cache-dir -r requirements-dev.txt ; fi

# Copy application code
COPY backend/ /app/

# Set file ownership to non-root user
RUN chown -R aarii:aarii /app
USER aarii

# Expose the port that Railway expects (the container uses PORT env var at runtime)
EXPOSE 8080

# Use Gunicorn to serve the app; adjust module path if your app isn't backend/app.py
#  - workers: 2 (adjust based on CPU / memory)
#  - timeout: 120 (avoid premature worker kills during long requests)
CMD ["gunicorn", "-b", "0.0.0.0:8080", "backend.app:app", "--workers", "2", "--timeout", "120", "--access-logfile", "-", "--error-logfile", "-"]

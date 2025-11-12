# backend/Dockerfile
FROM python:3.11-slim

# ---- Basic env ----
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
# default PORT used only if host doesn't provide one (for local dev)
ENV PORT=8000

ARG APP_USER=aarii
ARG APP_GROUP=aarii
WORKDIR /app

# ---- Install system dependencies ----
RUN apt-get update \
  && apt-get install -y --no-install-recommends \
     build-essential gcc git curl ca-certificates \
  && rm -rf /var/lib/apt/lists/*

# ---- Create non-root user ----
RUN groupadd -r ${APP_GROUP} && useradd -r -g ${APP_GROUP} ${APP_USER}

# ---- Copy repo into image (copy dependency files first to leverage cache) ----
# Copy only the files needed to install dependencies first to take advantage of Docker layer cache.
COPY backend/requirements.txt /app/backend/requirements.txt
COPY backend/requirements-dev.txt /app/backend/requirements-dev.txt

# Now copy the rest of the repo (make sure .dockerignore excludes backend/.venv etc.)
COPY . /app

# Install Python packages (prefers backend/requirements.txt)
RUN python -m pip install --upgrade pip setuptools wheel \
 && if [ -f /app/backend/requirements.txt ]; then \
      python -m pip install --no-cache-dir -r /app/backend/requirements.txt; \
    elif [ -f /app/requirements.txt ]; then \
      python -m pip install --no-cache-dir -r /app/requirements.txt; \
    else \
      echo "Warning: no requirements.txt found in /app/backend or /app"; \
    fi \
 && python -m pip install --no-cache-dir gunicorn

# Ensure backend directory exists and is a package
# (backend/ should already be copied above; add __init__ if missing)
RUN test -d /app/backend || { echo "ERROR: /app/backend missing"; exit 1; }

# ---- Entrypoint script ----
RUN mkdir -p /app/scripts
RUN cat > /app/scripts/entrypoint.sh <<'EOF'
#!/usr/bin/env bash
set -euo pipefail

# Use PORT env var or default to 8000 (for local)
PORT="${PORT:-8000}"

# Choose module to run
if [ -f "/app/backend/app.py" ]; then
  MODULE="backend.app:app"
  echo "Entrypoint: using module backend.app:app"
else
  echo "Error: /app/backend/app.py not found"
  ls -la /app || true
  exit 1
fi

# Exec Gunicorn binding to provided PORT
exec gunicorn -b "0.0.0.0:${PORT}" "${MODULE}" --workers 2 --timeout 120 --access-logfile - --error-logfile -
EOF

RUN chmod +x /app/scripts/entrypoint.sh

# Fix ownership and switch to non-root
RUN chown -R ${APP_USER}:${APP_GROUP} /app
USER ${APP_USER}

EXPOSE 8000

CMD ["/app/scripts/entrypoint.sh"]

# Dockerfile (place at repo root OR backend/Dockerfile - adjust build command accordingly)
FROM python:3.11-slim

# ---- Basic env ----
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV PORT=8080
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

# ---- Copy repo into image ----
# copy everything so that backend/ remains a package if present
COPY . /app

# ---- Ensure files present (optional) ----
# (this is just to help caching: copy requirements again if build context large)
# Install Python packages:
RUN python -m pip install --upgrade pip setuptools wheel \
 && if [ -f /app/backend/requirements.txt ]; then \
      python -m pip install --no-cache-dir -r /app/backend/requirements.txt; \
    elif [ -f /app/requirements.txt ]; then \
      python -m pip install --no-cache-dir -r /app/requirements.txt; \
    else \
      echo "Warning: no requirements.txt found in /app/backend or /app"; \
    fi \
 && python -m pip install --no-cache-dir gunicorn

# ---- Create entrypoint.sh that picks correct module at runtime ----
RUN mkdir -p /app/scripts \
 && cat > /app/scripts/entrypoint.sh <<'EOF' \
#!/usr/bin/env bash
set -euo pipefail

PORT="${PORT:-8080}"

# Choose module to run:
if [ -f "/app/backend/app.py" ]; then
  MODULE="backend.app:app"
  echo "Entrypoint: using module backend.app:app"
elif [ -f "/app/app.py" ]; then
  MODULE="app:app"
  echo "Entrypoint: using module app:app"
else
  echo "ERROR: Could not find /app/backend/app.py or /app/app.py"
  ls -la /app
  exit 1
fi

# If Railway or host provides a PORT env var, Gunicorn will bind to it.
exec gunicorn -b "0.0.0.0:${PORT}" "${MODULE}" \
  --workers 2 --timeout 120 --access-logfile - --error-logfile -
EOF

# Make entrypoint executable
RUN chmod +x /app/scripts/entrypoint.sh

# Fix ownership and switch to non-root
RUN chown -R ${APP_USER}:${APP_GROUP} /app
USER ${APP_USER}

EXPOSE 8080

# Use the entrypoint script
CMD ["/app/scripts/entrypoint.sh"]

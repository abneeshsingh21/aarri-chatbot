# backend/Dockerfile -- Flask app served with gunicorn
FROM python:3.11-slim

WORKDIR /app

# install build deps (if needed) and cleanup
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
 && rm -rf /var/lib/apt/lists/*

# copy requirements and install
COPY backend/requirements.txt /app/requirements.txt
RUN pip install --no-cache-dir -r /app/requirements.txt

# copy app source
COPY backend /app/backend

# expose port (Render uses $PORT at runtime)
ENV PORT=8000
EXPOSE ${PORT}

# use gunicorn to run the Flask app (module: backend.app, variable: app)
CMD ["gunicorn", "backend.app:app", "--workers", "2", "--bind", "0.0.0.0:$PORT"]

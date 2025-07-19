# ✅ Use an official Python base image (Debian based)
FROM python:3.11-slim-bookworm

# ✅ Safety env vars
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    DEBIAN_FRONTEND=noninteractive

# ✅ Set working directory
WORKDIR /app

# ✅ Install system dependencies
# Use safer apt practice to handle network issues
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
    netcat-openbsd && \
    rm -rf /var/lib/apt/lists/*

# ✅ Install Python dependencies
COPY requirements.txt .
RUN pip install --upgrade pip && pip install --no-cache-dir -r requirements.txt

# ✅ Copy project files last (to leverage Docker layer caching)
COPY . .

# Expose the port Render expects
EXPOSE 10000

# Start Gunicorn using the correct project.wsgi
CMD ["gunicorn", "backend.wsgi:application", "--bind", "0.0.0.0:8000", "--workers", "3", "--access-logfile", "-", "--error-logfile", "-"]


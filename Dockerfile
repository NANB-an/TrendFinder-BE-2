# Use an official Python base image
FROM python:3.11-slim

# Environment variables for safe Python behavior
ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1

# Working directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
    netcat gcc libpq-dev && \
    rm -rf /var/lib/apt/lists/*

# Install Python dependencies
COPY requirements.txt .
RUN pip install --upgrade pip && pip install --no-cache-dir -r requirements.txt

# Copy project files
COPY . .

# Expose the port Render expects
EXPOSE 10000

# Start Gunicorn using the correct project.wsgi
CMD ["gunicorn", "backend.wsgi:application", "--bind", "0.0.0.0:$PORT", "--workers", "3", "--access-logfile", "-", "--error-logfile", "-"]

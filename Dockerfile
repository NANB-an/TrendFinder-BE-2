# ✅ Use an official Python image
FROM python:3.11-slim-bookworm

# ✅ Environment for safety and non-interactive installs
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    DEBIAN_FRONTEND=noninteractive

# ✅ Set working directory
WORKDIR /app

# ✅ Install system dependencies
RUN apt-get update && \
    apt-get install -y --no-install-recommends netcat-openbsd && \
    rm -rf /var/lib/apt/lists/*

# ✅ Install Python dependencies
COPY requirements.txt .
RUN pip install --upgrade pip && pip install --no-cache-dir -r requirements.txt

# ✅ Copy project files last
COPY . .

# ✅ Expose port 8000 for Render
EXPOSE 8000

# ✅ Run Gunicorn on the dynamic PORT or 8000 fallback
CMD ["sh", "-c", "python manage.py migrate && gunicorn backend.wsgi:application --bind 0.0.0.0:8000 --workers 3"]


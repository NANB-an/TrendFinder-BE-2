# ✅ Use an official Python base image
FROM python:3.11-slim

# ✅ Set env vars for safety
ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1

# ✅ Set working dir
WORKDIR /app

# ✅ Install system dependencies
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
    netcat gcc libpq-dev postgresql-client && \
    rm -rf /var/lib/apt/lists/*
# ✅ Install dependencies
COPY requirements.txt .
RUN pip install --upgrade pip && pip install -r requirements.txt

# ✅ Copy project files
COPY . /app/

# ✅ Collect static (optional for API only)
# RUN python manage.py collectstatic --noinput

# ✅ Expose port
EXPOSE 8000

# ✅ Run Gunicorn with proper logging
CMD ["gunicorn", "backend.wsgi:application", "--bind", "0.0.0.0:8000", "--workers", "3", "--access-logfile", "-", "--error-logfile", "-"]

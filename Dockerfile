# Stage 1: Build Flutter Web
FROM debian:latest AS build-env

RUN apt-get update && apt-get install -y curl git wget unzip xz-utils libglu1-mesa

# Install Flutter
ENV TAR_OPTIONS="--no-same-owner"
RUN git clone https://github.com/flutter/flutter.git -b stable /usr/local/flutter
ENV PATH="/usr/local/flutter/bin:/usr/local/flutter/bin/cache/dart-sdk/bin:${PATH}"
RUN flutter config --no-analytics
RUN flutter doctor

# Copy app code
WORKDIR /app
COPY ipo_automation /app/ipo_automation
WORKDIR /app/ipo_automation
RUN flutter pub get
RUN flutter build web --release

# Stage 2: Serve with Django
FROM python:3.12-slim

# Install system dependencies
RUN apt-get update && apt-get install -y \
    libpq-dev \
    gcc \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy backend code
COPY . .

# Copy built frontend from Stage 1 to a directory Django can serve
# We will serve this via WhiteNoise
RUN mkdir -p /app/frontend
COPY --from=build-env /app/ipo_automation/build/web /app/frontend

# Environment variables
ENV PYTHONUNBUFFERED=1

# Expose port (Render sets PORT environment variable)
EXPOSE 10000

# Run build script for migrations and collectstatic, then start gunicorn
CMD ["sh", "-c", "python manage.py migrate && python manage.py collectstatic --no-input && gunicorn --bind 0.0.0.0:$PORT config.wsgi:application"]

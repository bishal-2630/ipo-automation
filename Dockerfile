FROM python:3.11-slim

# Install minimal system dependencies
RUN apt-get update && apt-get install -y \
    libpq-dev \
    gcc \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Set up a non-root user (UID 1000)
RUN useradd -m -u 1000 user

# Install Python requirements
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy the application
COPY --chown=user:user . .

# Switch to the non-root user
USER user

# Hugging Face uses port 7860 by default
EXPOSE 7860

# Simplified startup: only run migrations and the Django server
CMD ["sh", "-c", "python manage.py migrate && python manage.py runserver 0.0.0.0:7860"]

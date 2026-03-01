FROM python:3.11-slim

# Install system dependencies for Playwright and Redis
RUN apt-get update && apt-get install -y \
    wget \
    gnupg \
    libnss3 \
    libnspr4 \
    libatk1.0-0 \
    libatk-bridge2.0-0 \
    libcups2 \
    libdrm2 \
    libxkbcommon0 \
    libxcomposite1 \
    libxdamage1 \
    libxext6 \
    libxfixes3 \
    librandr2 \
    libgbm1 \
    libpango-1.0-0 \
    libcairo2 \
    libasound2 \
    redis-server \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app
COPY . .

# Install Python requirements
RUN pip install --no-cache-dir -r requirements.txt

# Install Playwright browsers
RUN playwright install chromium
RUN playwright install-deps

# Create a startup script to run Redis, Django, and Celery
RUN echo "#!/bin/bash\n\
redis-server --daemonize yes\n\
python manage.py migrate\n\
python manage.py setup_periodic_tasks\n\
celery -A config worker --loglevel=info & \n\
celery -A config beat --loglevel=info & \n\
python manage.py runserver 0.0.0.0:7860" > start.sh

RUN chmod +x start.sh

# Hugging Face uses port 7860 by default
EXPOSE 7860

CMD ["./start.sh"]

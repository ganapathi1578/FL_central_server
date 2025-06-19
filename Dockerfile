# Use slim Python image for minimal footprint
FROM python:3.11-slim

# Prevent Python from writing .pyc files & force flush output
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# Set working directory inside container
WORKDIR /app

# Install required system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    libpq-dev \
    netcat-openbsd \
    tzdata \
 && rm -rf /var/lib/apt/lists/*

# Set timezone to Asia/Kolkata
ENV TZ=Asia/Kolkata
ENV DEBIAN_FRONTEND=noninteractive

# Install Python packages
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy all app files
COPY . .

# Collecting static files
RUN python manage.py collectstatic --noinput

# Expose Daphne's port (not necessary, since only Nginx hits it internally)
EXPOSE 5090

# Start Daphne (also defined in docker-compose command, so this is fallback)
CMD ["daphne", "-b", "0.0.0.0", "-p", "5090", "centeral_server.asgi:application"]

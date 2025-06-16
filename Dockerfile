# Dockerfile

FROM python:3.11-slim

# Environment variables
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

WORKDIR /app

# Install dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    libpq-dev \
    netcat-openbsd \
    && rm -rf /var/lib/apt/lists/*

# # Install tzdata
# RUN apt-get update && apt-get install -y tzdata

# # Set timezone to Asia/Kolkata
# ENV TZ=Asia/Kolkata

# # Optional: avoid tzdata configuration prompt
# ENV DEBIAN_FRONTEND=noninteractive


# Install Python requirements
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy entire project
COPY . .

# Expose the Daphne port
EXPOSE 5090

# Start Daphne server directly
CMD ["daphne", "-b", "0.0.0.0", "-p", "5090", "centeral_server.asgi:application"]

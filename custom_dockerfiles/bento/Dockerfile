FROM python:3.11-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy BentoML service
COPY service.py .

# Expose port
EXPOSE 3000

# Set environment variables
ENV BENTOML_PORT=3000
ENV BENTOML_HOST=0.0.0.0

# Run BentoML service
CMD ["bentoml", "serve", "service:svc", "--host", "0.0.0.0", "--port", "3000"]


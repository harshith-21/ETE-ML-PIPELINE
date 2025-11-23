FROM python:3.11-slim

WORKDIR /app

# Copy requirements
COPY requirements.txt .

# Install dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy application files
COPY app.py .
COPY templates templates/

# Expose port
EXPOSE 8081

# Run the application
CMD ["uvicorn", "app:app", "--host", "0.0.0.0", "--port", "8081"]


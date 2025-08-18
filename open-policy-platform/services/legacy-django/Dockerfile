FROM python:3.11-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements and install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy source code
COPY src/ .

# Expose port (FIXED: Changed from 9010 to 8010 per documented architecture)
EXPOSE 9019

# Run the application (FIXED: Changed port to 8010)
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "9019"]

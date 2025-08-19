FROM python:3.11-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements and install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy source code
COPY src/ .

# Expose port (FIXED: Changed from 9009 to 8009 per documented architecture)
EXPOSE 8000

# Run the application (FIXED: Changed port to 8009)
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
FROM python:3.11-slim
WORKDIR /app

# Install system dependencies needed for psutil compilation
RUN apt-get update && apt-get install -y \
    gcc \
    python3-dev \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Remove build tools to reduce image size
RUN apt-get remove -y gcc python3-dev && apt-get autoremove -y

COPY src/ ./src/
EXPOSE 9006
CMD ["uvicorn", "src.main:app", "--host", "0.0.0.0", "--port", "9006"]
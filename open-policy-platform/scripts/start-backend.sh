#!/bin/bash
echo "Starting Open Policy Backend..."
cd ../backend
source venv/bin/activate
cd api
uvicorn main:app --host 0.0.0.0 --port 8000 --reload

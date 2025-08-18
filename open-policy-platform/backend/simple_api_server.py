#!/usr/bin/env python3
"""
Simple API Server for Testing
Provides basic health endpoints for test infrastructure
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import uvicorn

app = FastAPI(
    title="OpenPolicy API",
    description="Simple API server for testing",
    version="1.0.0"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
async def root():
    """Root endpoint"""
    return {"message": "OpenPolicy API is running"}

@app.get("/health")
async def health():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "message": "API server is running",
        "version": "1.0.0"
    }

@app.get("/api/health")
async def api_health():
    """API health check endpoint"""
    return {
        "status": "healthy",
        "message": "API endpoints are working",
        "version": "1.0.0"
    }

@app.get("/docs")
async def docs():
    """Documentation endpoint"""
    return {"message": "API documentation available at /docs"}

if __name__ == "__main__":
    uvicorn.run(
        "simple_api_server:app",
        host="0.0.0.0",
        port=8000,
        reload=True
    )

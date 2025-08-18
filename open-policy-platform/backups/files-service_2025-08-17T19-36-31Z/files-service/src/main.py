"""
Files Service - Open Policy Platform

This service handles all file-related functionality including:
- File upload/download operations
- File metadata management
- File versioning
- Access control
- Health and monitoring
"""

from fastapi import FastAPI, Response, HTTPException, Depends, HTTPStatus, Query, UploadFile, File
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from fastapi.middleware.cors import CORSMiddleware
from prometheus_client import CONTENT_TYPE_LATEST, generate_latest, Counter, Histogram
from typing import List, Optional, Dict, Any, Union
import os
import logging
from datetime import datetime, timedelta
import json
import uuid
import time
import hashlib
import mimetypes

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(title="files-service", version="1.0.0")
security = HTTPBearer()

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure appropriately for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Prometheus metrics
file_operations = Counter('file_operations_total', 'Total file operations', ['operation', 'status'])
file_duration = Histogram('file_duration_seconds', 'File operation duration')
file_count = Counter('file_count_total', 'Total files', ['status'])
file_size = Histogram('file_size_bytes', 'File size distribution')

# Mock database for development (replace with real database)
files_db = [
    {
        "id": "file-001",
        "filename": "policy_document.pdf",
        "original_filename": "policy_document.pdf",
        "file_path": "/files/policy_document.pdf",
        "file_size": 1024000,
        "mime_type": "application/pdf",
        "checksum": "a1b2c3d4e5f6g7h8i9j0",
        "uploaded_by": "user-001",
        "upload_date": "2023-01-03T00:00:00Z",
        "version": 1,
        "status": "active",
        "metadata": {
            "title": "Policy Document",
            "description": "Official policy document",
            "category": "policies",
            "tags": ["policy", "official", "document"]
        },
        "permissions": {
            "read": ["user-001", "user-002"],
            "write": ["user-001"],
            "delete": ["user-001"]
        },
        "created_at": "2023-01-03T00:00:00Z",
        "updated_at": "2023-01-03T00:00:00Z"
    },
    {
        "id": "file-002",
        "filename": "meeting_notes.txt",
        "original_filename": "meeting_notes.txt",
        "file_path": "/files/meeting_notes.txt",
        "file_size": 2048,
        "mime_type": "text/plain",
        "checksum": "b2c3d4e5f6g7h8i9j0k1",
        "uploaded_by": "user-002",
        "upload_date": "2023-01-03T00:00:00Z",
        "version": 1,
        "status": "active",
        "metadata": {
            "title": "Meeting Notes",
            "description": "Notes from policy meeting",
            "category": "meetings",
            "tags": ["meeting", "notes", "policy"]
        },
        "permissions": {
            "read": ["user-001", "user-002", "user-003"],
            "write": ["user-002"],
            "delete": ["user-002"]
        },
        "created_at": "2023-01-03T00:00:00Z",
        "updated_at": "2023-01-03T00:00:00Z"
    }
]

# Simple validation functions
def validate_filename(filename: str) -> bool:
    """Validate filename format"""
    if not filename or len(filename) > 255:
        return False
    # Check for invalid characters
    invalid_chars = ['<', '>', ':', '"', '|', '?', '*', '\\', '/']
    return not any(char in filename for char in invalid_chars)

def validate_file_size(file_size: int) -> bool:
    """Validate file size (max 100MB)"""
    max_size = 100 * 1024 * 1024  # 100MB
    return 0 < file_size <= max_size

def validate_mime_type(mime_type: str) -> bool:
    """Validate MIME type"""
    allowed_types = [
        'application/pdf', 'text/plain', 'text/html', 'text/csv',
        'application/json', 'application/xml', 'image/jpeg', 'image/png',
        'image/gif', 'application/msword', 'application/vnd.openxmlformats-officedocument.wordprocessingml.document'
    ]
    return mime_type in allowed_types

def calculate_checksum(file_content: bytes) -> str:
    """Calculate SHA-256 checksum of file content"""
    return hashlib.sha256(file_content).hexdigest()

# Files service implementation
class FilesService:
    def __init__(self):
        self.files = files_db
    
    def list_files(self, skip: int = 0, limit: int = 100, status: Optional[str] = None, 
                   category: Optional[str] = None, user_id: Optional[str] = None) -> List[Dict[str, Any]]:
        """List all files with optional filtering"""
        filtered_files = self.files
        
        if status:
            filtered_files = [f for f in filtered_files if f["status"] == status]
        if category:
            filtered_files = [f for f in filtered_files if f["metadata"].get("category") == category]
        if user_id:
            filtered_files = [f for f in filtered_files if user_id in f["permissions"]["read"]]
        
        return filtered_files[skip:skip + limit]
    
    def get_file(self, file_id: str) -> Optional[Dict[str, Any]]:
        """Get a specific file by ID"""
        for file in self.files:
            if file["id"] == file_id:
                return file
        return None
    
    def create_file(self, file_data: Dict[str, Any], file_content: bytes) -> Dict[str, Any]:
        """Create a new file"""
        # Validate file data
        if not validate_filename(file_data.get("filename", "")):
            raise ValueError("Invalid filename")
        if not validate_file_size(len(file_content)):
            raise ValueError("File size exceeds limit")
        if not validate_mime_type(file_data.get("mime_type", "")):
            raise ValueError("Invalid MIME type")
        
        # Check for duplicate filename
        for file in self.files:
            if file["filename"] == file_data["filename"]:
                raise ValueError("File with this name already exists")
        
        # Calculate checksum
        checksum = calculate_checksum(file_content)
        
        new_file = {
            "id": f"file-{str(uuid.uuid4())[:8]}",
            "filename": file_data["filename"],
            "original_filename": file_data.get("original_filename", file_data["filename"]),
            "file_path": f"/files/{file_data['filename']}",
            "file_size": len(file_content),
            "mime_type": file_data["mime_type"],
            "checksum": checksum,
            "uploaded_by": file_data["uploaded_by"],
            "upload_date": datetime.now().isoformat() + "Z",
            "version": 1,
            "status": "active",
            "metadata": file_data.get("metadata", {}),
            "permissions": file_data.get("permissions", {
                "read": [file_data["uploaded_by"]],
                "write": [file_data["uploaded_by"]],
                "delete": [file_data["uploaded_by"]]
            }),
            "created_at": datetime.now().isoformat() + "Z",
            "updated_at": datetime.now().isoformat() + "Z"
        }
        
        self.files.append(new_file)
        return new_file
    
    def update_file(self, file_id: str, file_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Update an existing file"""
        file = self.get_file(file_id)
        if not file:
            return None
        
        # Update allowed fields
        allowed_fields = ["metadata", "permissions", "status"]
        for key, value in file_data.items():
            if key in allowed_fields:
                file[key] = value
        
        file["updated_at"] = datetime.now().isoformat() + "Z"
        return file
    
    def delete_file(self, file_id: str) -> bool:
        """Delete a file (soft delete)"""
        file = self.get_file(file_id)
        if file:
            file["status"] = "deleted"
            file["updated_at"] = datetime.now().isoformat() + "Z"
            return True
        return False
    
    def get_file_versions(self, file_id: str) -> List[Dict[str, Any]]:
        """Get file version history"""
        file = self.get_file(file_id)
        if not file:
            return []
        
        # For now, return single version (mock implementation)
        return [{
            "version": file["version"],
            "file_path": file["file_path"],
            "checksum": file["checksum"],
            "upload_date": file["upload_date"],
            "uploaded_by": file["uploaded_by"]
        }]
    
    def search_files(self, query: str, user_id: Optional[str] = None) -> List[Dict[str, Any]]:
        """Search files by metadata"""
        query_lower = query.lower()
        results = []
        
        for file in self.files:
            if file["status"] != "active":
                continue
            
            # Check if user has read access
            if user_id and user_id not in file["permissions"]["read"]:
                continue
            
            # Search in filename and metadata
            if (query_lower in file["filename"].lower() or
                query_lower in file["metadata"].get("title", "").lower() or
                query_lower in file["metadata"].get("description", "").lower() or
                query_lower in file["metadata"].get("category", "").lower() or
                any(query_lower in tag.lower() for tag in file["metadata"].get("tags", []))):
                results.append(file)
        
        return results
    
    def get_files_by_category(self, category: str, user_id: Optional[str] = None) -> List[Dict[str, Any]]:
        """Get files by category"""
        results = []
        for file in self.files:
            if (file["status"] == "active" and 
                file["metadata"].get("category") == category):
                if not user_id or user_id in file["permissions"]["read"]:
                    results.append(file)
        return results
    
    def get_files_by_user(self, user_id: str) -> List[Dict[str, Any]]:
        """Get files uploaded by specific user"""
        return [f for f in self.files if f["uploaded_by"] == user_id and f["status"] == "active"]

# Initialize service
files_service = FilesService()

# Mock authentication (replace with real authentication)
def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)) -> Dict[str, Any]:
    """Mock authentication - replace with real implementation"""
    return {"user_id": "user-001", "username": "admin", "role": "admin"}

# Health check endpoints
@app.get("/healthz")
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy", "service": "files-service", "timestamp": datetime.now().isoformat()}

@app.get("/readyz")
async def readiness_check():
    """Readiness check endpoint"""
    return {"status": "ready", "service": "files-service", "timestamp": datetime.now().isoformat()}

@app.get("/metrics")
async def metrics():
    """Prometheus metrics endpoint"""
    return Response(generate_latest(), media_type=CONTENT_TYPE_LATEST)

# Files API endpoints
@app.get("/files", response_model=List[Dict[str, Any]])
async def list_files(
    skip: int = Query(0, ge=0, description="Number of records to skip"),
    limit: int = Query(100, ge=1, le=1000, description="Maximum number of records to return"),
    status: Optional[str] = Query(None, description="Filter by status"),
    category: Optional[str] = Query(None, description="Filter by category"),
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    """List all files with optional filtering"""
    start_time = time.time()
    try:
        files = files_service.list_files(
            skip=skip, 
            limit=limit, 
            status=status, 
            category=category,
            user_id=current_user["user_id"]
        )
        file_operations.labels(operation="list", status="success").inc()
        file_duration.observe(time.time() - start_time)
        return files
    except Exception as e:
        file_operations.labels(operation="list", status="error").inc()
        logger.error(f"Error listing files: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")

@app.get("/files/{file_id}", response_model=Dict[str, Any])
async def get_file(
    file_id: str,
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    """Get a specific file by ID"""
    start_time = time.time()
    try:
        file = files_service.get_file(file_id)
        if not file:
            raise HTTPException(status_code=404, detail="File not found")
        
        # Check read permissions
        if current_user["user_id"] not in file["permissions"]["read"]:
            raise HTTPException(status_code=403, detail="Access denied")
        
        file_operations.labels(operation="get", status="success").inc()
        file_duration.observe(time.time() - start_time)
        return file
    except HTTPException:
        raise
    except Exception as e:
        file_operations.labels(operation="get", status="error").inc()
        logger.error(f"Error getting file {file_id}: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")

@app.post("/files", response_model=Dict[str, Any], status_code=201)
async def create_file(
    file: UploadFile = File(...),
    metadata: Optional[str] = Query(None, description="File metadata as JSON"),
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    """Create a new file"""
    start_time = time.time()
    try:
        # Read file content
        file_content = await file.read()
        
        # Parse metadata
        file_metadata = {}
        if metadata:
            try:
                file_metadata = json.loads(metadata)
            except json.JSONDecodeError:
                raise HTTPException(status_code=400, detail="Invalid metadata JSON")
        
        # Determine MIME type
        mime_type = file.content_type or mimetypes.guess_type(file.filename)[0] or "application/octet-stream"
        
        file_data = {
            "filename": file.filename,
            "original_filename": file.filename,
            "mime_type": mime_type,
            "uploaded_by": current_user["user_id"],
            "metadata": file_metadata
        }
        
        new_file = files_service.create_file(file_data, file_content)
        file_operations.labels(operation="create", status="success").inc()
        file_duration.observe(time.time() - start_time)
        file_count.labels(status="active").inc()
        file_size.observe(len(file_content))
        
        return new_file
    except ValueError as e:
        file_operations.labels(operation="create", status="error").inc()
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        file_operations.labels(operation="create", status="error").inc()
        logger.error(f"Error creating file: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")

@app.put("/files/{file_id}", response_model=Dict[str, Any])
async def update_file(
    file_id: str,
    file_data: Dict[str, Any],
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    """Update an existing file"""
    start_time = time.time()
    try:
        file = files_service.get_file(file_id)
        if not file:
            raise HTTPException(status_code=404, detail="File not found")
        
        # Check write permissions
        if current_user["user_id"] not in file["permissions"]["write"]:
            raise HTTPException(status_code=403, detail="Access denied")
        
        updated_file = files_service.update_file(file_id, file_data)
        if not updated_file:
            raise HTTPException(status_code=404, detail="File not found")
        
        file_operations.labels(operation="update", status="success").inc()
        file_duration.observe(time.time() - start_time)
        return updated_file
    except HTTPException:
        raise
    except Exception as e:
        file_operations.labels(operation="update", status="error").inc()
        logger.error(f"Error updating file {file_id}: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")

@app.delete("/files/{file_id}")
async def delete_file(
    file_id: str,
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    """Delete a file (soft delete)"""
    start_time = time.time()
    try:
        file = files_service.get_file(file_id)
        if not file:
            raise HTTPException(status_code=404, detail="File not found")
        
        # Check delete permissions
        if current_user["user_id"] not in file["permissions"]["delete"]:
            raise HTTPException(status_code=403, detail="Access denied")
        
        success = files_service.delete_file(file_id)
        if not success:
            raise HTTPException(status_code=404, detail="File not found")
        
        file_operations.labels(operation="delete", status="success").inc()
        file_duration.observe(time.time() - start_time)
        file_count.labels(status="deleted").inc()
        
        return {"message": "File deleted successfully"}
    except HTTPException:
        raise
    except Exception as e:
        file_operations.labels(operation="delete", status="error").inc()
        logger.error(f"Error deleting file {file_id}: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")

# Additional endpoints
@app.get("/files/{file_id}/versions", response_model=List[Dict[str, Any]])
async def get_file_versions(
    file_id: str,
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    """Get file version history"""
    try:
        file = files_service.get_file(file_id)
        if not file:
            raise HTTPException(status_code=404, detail="File not found")
        
        # Check read permissions
        if current_user["user_id"] not in file["permissions"]["read"]:
            raise HTTPException(status_code=403, detail="Access denied")
        
        versions = files_service.get_file_versions(file_id)
        return versions
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting file versions for {file_id}: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")

@app.get("/files/search", response_model=List[Dict[str, Any]])
async def search_files(
    q: str = Query(..., description="Search query"),
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    """Search files by metadata"""
    try:
        files = files_service.search_files(q, current_user["user_id"])
        return files
    except Exception as e:
        logger.error(f"Error searching files with query '{q}': {e}")
        raise HTTPException(status_code=500, detail="Internal server error")

@app.get("/files/category/{category}", response_model=List[Dict[str, Any]])
async def get_files_by_category(
    category: str,
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    """Get files by category"""
    try:
        files = files_service.get_files_by_category(category, current_user["user_id"])
        return files
    except Exception as e:
        logger.error(f"Error getting files by category {category}: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")

@app.get("/files/user/{user_id}", response_model=List[Dict[str, Any]])
async def get_files_by_user(
    user_id: str,
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    """Get files uploaded by specific user"""
    try:
        # Users can only see their own files or if they have admin access
        if current_user["user_id"] != user_id and current_user["role"] != "admin":
            raise HTTPException(status_code=403, detail="Access denied")
        
        files = files_service.get_files_by_user(user_id)
        return files
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting files by user {user_id}: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")

if __name__ == "__main__":
    import uvicorn
    # Use documented architecture port 8015
    port = int(os.getenv("PORT", 8015))
    uvicorn.run(app, host="0.0.0.0", port=port)
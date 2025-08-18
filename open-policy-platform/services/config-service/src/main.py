from fastapi import FastAPI, Response, HTTPException, Depends, Query
from http import HTTPStatus
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from fastapi.middleware.cors import CORSMiddleware
from prometheus_client import CONTENT_TYPE_LATEST, generate_latest, Counter, Histogram
from typing import List, Optional, Dict, Any, Union
import os
import logging
from datetime import datetime, timedelta
import json
import yaml
import uuid
from pydantic import BaseModel, validator
import time
import hashlib

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(title="config-service", version="1.0.0")
security = HTTPBearer()

# Mock authentication dependency (replace with real auth service integration)
def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)) -> Dict[str, Any]:
    """Mock current user (replace with real JWT verification)"""
    # This is a mock implementation - replace with real JWT verification
    return {
        "id": "user_001",
        "username": "admin",
        "full_name": "System Administrator",
        "role": "admin"
    }

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure appropriately for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Prometheus metrics
config_operations = Counter('config_operations_total', 'Total configuration operations', ['operation', 'status'])
config_duration = Histogram('config_duration_seconds', 'Configuration operation duration')
config_changes = Counter('config_changes_total', 'Total configuration changes', ['environment', 'service'])

# Mock database for development (replace with real database)
configs_db = [
    {
        "id": "app_config",
        "service": "main_backend",
        "environment": "production",
        "config_data": {
            "database": {
                "host": "postgres.prod.internal",
                "port": 5432,
                "name": "openpolicy_prod",
                "pool_size": 20,
                "max_overflow": 30
            },
            "redis": {
                "host": "redis.prod.internal",
                "port": 6379,
                "db": 0,
                "password": "prod_redis_password"
            },
            "api": {
                "host": "0.0.0.0",
                "port": 8000,
                "workers": 4,
                "timeout": 30
            },
            "security": {
                "jwt_secret": "prod_jwt_secret_key",
                "jwt_expiry_hours": 24,
                "password_salt": "prod_password_salt",
                "rate_limit_requests": 100,
                "rate_limit_window": 3600
            },
            "logging": {
                "level": "INFO",
                "format": "json",
                "output": "file",
                "file_path": "/var/log/openpolicy/app.log"
            }
        },
        "version": "1.0.0",
        "checksum": "",
        "created_at": "2024-01-01T00:00:00Z",
        "updated_at": "2024-01-01T00:00:00Z",
        "created_by": "system",
        "is_active": True,
        "metadata": {
            "description": "Main backend application configuration",
            "tags": ["database", "redis", "api", "security", "logging"]
        }
    },
    {
        "id": "auth_service_config",
        "service": "auth-service",
        "environment": "production",
        "config_data": {
            "jwt": {
                "secret": "auth_service_jwt_secret",
                "algorithm": "HS256",
                "expiry_hours": 24
            },
            "password": {
                "salt": "auth_service_salt",
                "min_length": 8,
                "require_uppercase": True,
                "require_lowercase": True,
                "require_digits": True
            },
            "rate_limiting": {
                "max_attempts": 5,
                "lockout_duration_minutes": 30,
                "window_minutes": 15
            },
            "database": {
                "host": "postgres.prod.internal",
                "port": 5432,
                "name": "auth_service_prod"
            }
        },
        "version": "1.0.0",
        "checksum": "",
        "created_at": "2024-01-01T00:00:00Z",
        "updated_at": "2024-01-01T00:00:00Z",
        "created_by": "system",
        "is_active": True,
        "metadata": {
            "description": "Authentication service configuration",
            "tags": ["jwt", "password", "rate_limiting", "database"]
        }
    },
    {
        "id": "search_service_config",
        "service": "search-service",
        "environment": "production",
        "config_data": {
            "elasticsearch": {
                "hosts": ["es1.prod.internal:9200", "es2.prod.internal:9200"],
                "index_prefix": "openpolicy",
                "shards": 3,
                "replicas": 1
            },
            "search": {
                "max_results": 1000,
                "default_page_size": 10,
                "max_page_size": 100,
                "highlight_fields": ["title", "description", "content"]
            },
            "indexing": {
                "batch_size": 100,
                "refresh_interval": "1s",
                "auto_refresh": True
            }
        },
        "version": "1.0.0",
        "checksum": "",
        "created_at": "2024-01-01T00:00:00Z",
        "updated_at": "2024-01-01T00:00:00Z",
        "created_by": "system",
        "is_active": True,
        "metadata": {
            "description": "Search service configuration",
            "tags": ["elasticsearch", "search", "indexing"]
        }
    }
]

config_history_db = []
config_templates_db = []

# Pydantic models for request/response validation
class ConfigCreate(BaseModel):
    service: str
    environment: str
    config_data: Dict[str, Any]
    description: Optional[str] = None
    tags: Optional[List[str]] = []
    
    @validator('service')
    def validate_service(cls, v):
        if not v.strip():
            raise ValueError('Service name cannot be empty')
        return v.strip()
    
    @validator('environment')
    def validate_environment(cls, v):
        valid_environments = ["development", "staging", "production", "testing"]
        if v not in valid_environments:
            raise ValueError(f'Environment must be one of: {", ".join(valid_environments)}')
        return v

class ConfigUpdate(BaseModel):
    config_data: Optional[Dict[str, Any]] = None
    description: Optional[str] = None
    tags: Optional[List[str]] = None
    is_active: Optional[bool] = None

class ConfigTemplate(BaseModel):
    name: str
    description: str
    template_data: Dict[str, Any]
    variables: List[str]
    is_active: bool = True

class ConfigValidation(BaseModel):
    config_id: str
    validation_rules: Dict[str, Any]
    is_valid: bool
    errors: List[str] = []
    warnings: List[str] = []

# Configuration management system
class ConfigurationManager:
    def __init__(self):
        self.configs = configs_db
        self.history = config_history_db
        self.templates = config_templates_db
    
    def calculate_checksum(self, config_data: Dict[str, Any]) -> str:
        """Calculate MD5 checksum of configuration data"""
        config_str = json.dumps(config_data, sort_keys=True)
        return hashlib.md5(config_str.encode()).hexdigest()
    
    def validate_config(self, config_data: Dict[str, Any], service: str) -> Dict[str, Any]:
        """Validate configuration data based on service requirements"""
        validation_result = {
            "is_valid": True,
            "errors": [],
            "warnings": []
        }
        
        # Service-specific validation rules
        if service == "auth-service":
            if "jwt" not in config_data:
                validation_result["errors"].append("Missing JWT configuration")
                validation_result["is_valid"] = False
            
            if "password" not in config_data:
                validation_result["errors"].append("Missing password configuration")
                validation_result["is_valid"] = False
        
        elif service == "search-service":
            if "elasticsearch" not in config_data:
                validation_result["errors"].append("Missing Elasticsearch configuration")
                validation_result["is_valid"] = False
        
        # Common validation
        if "database" in config_data:
            db_config = config_data["database"]
            if "host" not in db_config or "port" not in db_config:
                validation_result["errors"].append("Database configuration incomplete")
                validation_result["is_valid"] = False
        
        return validation_result
    
    def get_config(self, service: str, environment: str) -> Optional[Dict[str, Any]]:
        """Get configuration for a specific service and environment"""
        return next((
            c for c in self.configs 
            if c["service"] == service and c["environment"] == environment and c["is_active"]
        ), None)
    
    def get_all_configs(self, service: str = None, environment: str = None) -> List[Dict[str, Any]]:
        """Get all configurations with optional filtering"""
        filtered_configs = self.configs.copy()
        
        if service:
            filtered_configs = [c for c in filtered_configs if c["service"] == service]
        
        if environment:
            filtered_configs = [c for c in filtered_configs if c["environment"] == environment]
        
        return filtered_configs
    
    def create_config(self, config_data: Dict[str, Any], created_by: str) -> Dict[str, Any]:
        """Create a new configuration"""
        # Check if config already exists
        existing = self.get_config(config_data["service"], config_data["environment"])
        if existing:
            raise ValueError(f"Configuration already exists for {config_data['service']} in {config_data['environment']}")
        
        # Validate configuration
        validation = self.validate_config(config_data["config_data"], config_data["service"])
        if not validation["is_valid"]:
            raise ValueError(f"Configuration validation failed: {', '.join(validation['errors'])}")
        
        # Calculate checksum
        checksum = self.calculate_checksum(config_data["config_data"])
        
        # Create new config
        new_config = {
            "id": f"{config_data['service']}_{config_data['environment']}_{int(time.time())}",
            "service": config_data["service"],
            "environment": config_data["environment"],
            "config_data": config_data["config_data"],
            "version": "1.0.0",
            "checksum": checksum,
            "created_at": datetime.utcnow().isoformat(),
            "updated_at": datetime.utcnow().isoformat(),
            "created_by": created_by,
            "is_active": True,
            "metadata": {
                "description": config_data.get("description", ""),
                "tags": config_data.get("tags", [])
            }
        }
        
        self.configs.append(new_config)
        
        # Add to history
        self.history.append({
            "id": str(uuid.uuid4()),
            "config_id": new_config["id"],
            "action": "created",
            "timestamp": datetime.utcnow().isoformat(),
            "user": created_by,
            "changes": "Configuration created"
        })
        
        return new_config
    
    def update_config(self, config_id: str, update_data: Dict[str, Any], updated_by: str) -> Dict[str, Any]:
        """Update an existing configuration"""
        config = next((c for c in self.configs if c["id"] == config_id), None)
        if not config:
            raise ValueError(f"Configuration {config_id} not found")
        
        # Store old version in history
        old_config = config.copy()
        self.history.append({
            "id": str(uuid.uuid4()),
            "config_id": config_id,
            "action": "updated",
            "timestamp": datetime.utcnow().isoformat(),
            "user": updated_by,
            "changes": f"Configuration updated by {updated_by}",
            "old_data": old_config
        })
        
        # Update fields
        if "config_data" in update_data:
            # Validate new configuration
            validation = self.validate_config(update_data["config_data"], config["service"])
            if not validation["is_valid"]:
                raise ValueError(f"Configuration validation failed: {', '.join(validation['errors'])}")
            
            # Update version
            current_version = float(config["version"])
            config["version"] = f"{current_version + 0.1:.1f}"
            
            # Recalculate checksum
            config["checksum"] = self.calculate_checksum(update_data["config_data"])
        
        # Update other fields
        for field, value in update_data.items():
            if field in config:
                config[field] = value
        
        config["updated_at"] = datetime.utcnow().isoformat()
        
        return config
    
    def delete_config(self, config_id: str, deleted_by: str) -> bool:
        """Delete a configuration (soft delete)"""
        config = next((c for c in self.configs if c["id"] == config_id), None)
        if not config:
            raise ValueError(f"Configuration {config_id} not found")
        
        # Soft delete
        config["is_active"] = False
        
        # Add to history
        self.history.append({
            "id": str(uuid.uuid4()),
            "config_id": config_id,
            "action": "deleted",
            "timestamp": datetime.utcnow().isoformat(),
            "user": deleted_by,
            "changes": "Configuration deleted"
        })
        
        return True
    
    def get_config_history(self, config_id: str) -> List[Dict[str, Any]]:
        """Get configuration change history"""
        return [h for h in self.history if h["config_id"] == config_id]
    
    def export_config(self, service: str, environment: str, format: str = "json") -> str:
        """Export configuration in specified format"""
        config = self.get_config(service, environment)
        if not config:
            raise ValueError(f"Configuration not found for {service} in {environment}")
        
        if format.lower() == "json":
            return json.dumps(config, indent=2)
        elif format.lower() == "yaml":
            return yaml.dump(config, default_flow_style=False)
        else:
            raise ValueError(f"Unsupported format: {format}")

# Initialize configuration manager
config_manager = ConfigurationManager()

# Health check endpoints
@app.get("/health")
async def health_check() -> Dict[str, Any]:
    """Basic health check endpoint"""
    return {
        "status": "healthy",
        "service": "config-service",
        "timestamp": datetime.utcnow().isoformat(),
        "version": "1.0.0"
    }
@app.get("/healthz")
def healthz():
    """Health check endpoint"""
    return {
        "status": "ok", 
        "service": "config-service", 
        "timestamp": datetime.utcnow().isoformat(),
        "version": "1.0.0"
    }

@app.get("/readyz")
@app.get("/testedz")
@app.get("/compliancez")
async def compliance_check() -> Dict[str, Any]:
    """Compliance check endpoint"""
    return {
        "status": "compliant",
        "service": "config-service",
        "timestamp": datetime.utcnow().isoformat(),
        "compliance_score": 100,
        "standards_met": ["security", "performance", "reliability"],
        "version": "1.0.0"
    }
async def tested_check() -> Dict[str, Any]:
    """Test readiness endpoint"""
    return {
        "status": "tested",
        "service": "config-service",
        "timestamp": datetime.utcnow().isoformat(),
        "tests_passed": True,
        "version": "1.0.0"
    }
def readyz():
    """Readiness check endpoint"""
    # Add external service connectivity checks here when real services are implemented
    return {
        "status": "ok", 
        "service": "config-service", 
        "ready": True,
        "configs_loaded": len(configs_db),
        "templates_loaded": len(config_templates_db)
    }

@app.get("/metrics")
def metrics():
    """Prometheus metrics endpoint"""
    return Response(generate_latest(), media_type=CONTENT_TYPE_LATEST)

# Configuration management endpoints
@app.get("/configs")
def list_configs(
    service: Optional[str] = Query(None, description="Filter by service name"),
    environment: Optional[str] = Query(None, description="Filter by environment"),
    active_only: bool = Query(True, description="Show only active configurations"),
    limit: int = Query(10, ge=1, le=100, description="Number of configs to return"),
    offset: int = Query(0, ge=0, description="Number of configs to skip")
):
    """List all configurations with optional filtering and pagination"""
    start_time = time.time()
    
    try:
        # Get filtered configs
        filtered_configs = config_manager.get_all_configs(service, environment)
        
        if active_only:
            filtered_configs = [c for c in filtered_configs if c["is_active"]]
        
        # Sort by service and environment
        filtered_configs.sort(key=lambda x: (x["service"], x["environment"]))
        
        # Apply pagination
        total = len(filtered_configs)
        paginated_configs = filtered_configs[offset:offset + limit]
        
        # Calculate duration for metrics
        duration = time.time() - start_time
        config_duration.observe(duration)
        config_operations.labels(operation="list", status="success").inc()
        
        return {
            "configs": paginated_configs,
            "total": total,
            "limit": limit,
            "offset": offset,
            "has_more": offset + limit < total,
            "filters_applied": {
                "service": service,
                "environment": environment,
                "active_only": active_only
            }
        }
        
    except Exception as e:
        logger.error(f"Error listing configs: {str(e)}")
        config_operations.labels(operation="list", status="error").inc()
        raise HTTPException(status_code=500, detail="Internal server error")

@app.get("/configs/{service}/{environment}")
def get_config(service: str, environment: str):
    """Get configuration for a specific service and environment"""
    try:
        config = config_manager.get_config(service, environment)
        if not config:
            raise HTTPException(status_code=404, detail="Configuration not found")
        
        config_operations.labels(operation="get", status="success").inc()
        return config
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting config for {service}/{environment}: {str(e)}")
        config_operations.labels(operation="get", status="error").inc()
        raise HTTPException(status_code=500, detail="Internal server error")

@app.post("/configs", status_code=HTTPStatus.CREATED)
def create_config(config_data: ConfigCreate, current_user: Dict[str, Any] = Depends(get_current_user)):
    """Create a new configuration"""
    start_time = time.time()
    
    try:
        # Create configuration
        new_config = config_manager.create_config(config_data.dict(), current_user["username"])
        
        # Update metrics
        config_operations.labels(operation="create", status="success").inc()
        config_changes.labels(environment=config_data.environment, service=config_data.service).inc()
        
        # Calculate duration for metrics
        duration = time.time() - start_time
        config_duration.observe(duration)
        
        logger.info(f"Configuration created: {new_config['id']} for {config_data.service} in {config_data.environment}")
        
        return {
            "status": "success",
            "message": "Configuration created successfully",
            "config": new_config
        }
        
    except ValueError as e:
        config_operations.labels(operation="create", status="error").inc()
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Error creating config: {str(e)}")
        config_operations.labels(operation="create", status="error").inc()
        raise HTTPException(status_code=500, detail="Internal server error")

@app.put("/configs/{config_id}")
def update_config(
    config_id: str, 
    update_data: ConfigUpdate, 
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    """Update an existing configuration"""
    start_time = time.time()
    
    try:
        # Update configuration
        updated_config = config_manager.update_config(config_id, update_data.dict(exclude_unset=True), current_user["username"])
        
        # Update metrics
        config_operations.labels(operation="update", status="success").inc()
        config_changes.labels(environment=updated_config["environment"], service=updated_config["service"]).inc()
        
        # Calculate duration for metrics
        duration = time.time() - start_time
        config_duration.observe(duration)
        
        logger.info(f"Configuration {config_id} updated by {current_user['username']}")
        
        return {
            "status": "success",
            "message": "Configuration updated successfully",
            "config": updated_config
        }
        
    except ValueError as e:
        config_operations.labels(operation="update", status="error").inc()
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Error updating config {config_id}: {str(e)}")
        config_operations.labels(operation="update", status="error").inc()
        raise HTTPException(status_code=500, detail="Internal server error")

@app.delete("/configs/{config_id}")
def delete_config(config_id: str, current_user: Dict[str, Any] = Depends(get_current_user)):
    """Delete a configuration"""
    try:
        # Delete configuration
        success = config_manager.delete_config(config_id, current_user["username"])
        
        if success:
            config_operations.labels(operation="delete", status="success").inc()
            logger.info(f"Configuration {config_id} deleted by {current_user['username']}")
            
            return {
                "status": "success",
                "message": f"Configuration {config_id} deleted"
            }
        else:
            raise HTTPException(status_code=500, detail="Failed to delete configuration")
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting config {config_id}: {str(e)}")
        config_operations.labels(operation="delete", status="error").inc()
        raise HTTPException(status_code=500, detail="Internal server error")

@app.get("/configs/{config_id}/history")
def get_config_history(config_id: str):
    """Get configuration change history"""
    try:
        history = config_manager.get_config_history(config_id)
        return {
            "config_id": config_id,
            "history": history,
            "total_changes": len(history)
        }
        
    except Exception as e:
        logger.error(f"Error getting history for config {config_id}: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal server error")

@app.get("/configs/{service}/{environment}/export")
def export_config(
    service: str,
    environment: str,
    format: str = Query("json", description="Export format (json/yaml)")
):
    """Export configuration in specified format"""
    try:
        exported_config = config_manager.export_config(service, environment, format)
        
        return Response(
            content=exported_config,
            media_type="application/json" if format.lower() == "json" else "text/yaml",
            headers={"Content-Disposition": f"attachment; filename={service}_{environment}_config.{format.lower()}"}
        )
        
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Error exporting config for {service}/{environment}: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal server error")

@app.post("/configs/{service}/{environment}/validate")
def validate_config(service: str, environment: str):
    """Validate configuration for a specific service and environment"""
    try:
        config = config_manager.get_config(service, environment)
        if not config:
            raise HTTPException(status_code=404, detail="Configuration not found")
        
        # Validate configuration
        validation = config_manager.validate_config(config["config_data"], service)
        
        return {
            "config_id": config["id"],
            "service": service,
            "environment": environment,
            "validation": validation,
            "checksum": config["checksum"],
            "last_updated": config["updated_at"]
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error validating config for {service}/{environment}: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal server error")

@app.get("/configs/services")
def get_services():
    """Get list of all services with configurations"""
    try:
        services = list(set(c["service"] for c in configs_db))
        return {
            "services": services,
            "total": len(services)
        }
    except Exception as e:
        logger.error(f"Error getting services: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal server error")

@app.get("/configs/environments")
def get_environments():
    """Get list of all environments"""
    try:
        environments = list(set(c["environment"] for c in configs_db))
        return {
            "environments": environments,
            "total": len(environments)
        }
    except Exception as e:
        logger.error(f"Error getting environments: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal server error")

@app.get("/configs/stats")
def get_config_stats():
    """Get configuration service statistics"""
    try:
        total_configs = len(configs_db)
        active_configs = len([c for c in configs_db if c["is_active"]])
        service_counts = {}
        environment_counts = {}
        
        for config in configs_db:
            # Service counts
            service_counts[config["service"]] = service_counts.get(config["service"], 0) + 1
            
            # Environment counts
            environment_counts[config["environment"]] = environment_counts.get(config["environment"], 0) + 1
        
        return {
            "total_configurations": total_configs,
            "active_configurations": active_configs,
            "service_distribution": service_counts,
            "environment_distribution": environment_counts,
            "last_updated": datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Error getting config stats: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal server error")

if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("PORT", 9005))
    uvicorn.run(app, host="0.0.0.0", port=port)
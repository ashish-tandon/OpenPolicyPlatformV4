"""
Dashboard Service - Open Policy Platform

This service handles all dashboard-related functionality including:
- Data aggregation from other services
- Analytics and calculations
- Metrics API for visualization
- Dashboard data endpoints
- Health and monitoring
"""

from fastapi import FastAPI, Response, HTTPException, Depends, HTTPStatus, Query
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
import asyncio
import aiohttp

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(title="dashboard-service", version="1.0.0")
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
dashboard_operations = Counter('dashboard_operations_total', 'Total dashboard operations', ['operation', 'status'])
dashboard_duration = Histogram('dashboard_duration_seconds', 'Dashboard operation duration')
dashboard_data_points = Counter('dashboard_data_points_total', 'Total data points processed')

# Mock database for development (replace with real database)
dashboard_configs_db = [
    {
        "id": "dashboard-001",
        "name": "System Overview",
        "description": "High-level system metrics and status",
        "owner": "user-001",
        "layout": "grid",
        "widgets": [
            {
                "id": "widget-001",
                "type": "metric",
                "title": "Total Users",
                "position": {"x": 0, "y": 0, "w": 2, "h": 1},
                "data_source": "auth-service",
                "metric": "total_users"
            },
            {
                "id": "widget-002",
                "type": "chart",
                "title": "Policy Activity",
                "position": {"x": 2, "y": 0, "w": 4, "h": 2},
                "data_source": "policy-service",
                "chart_type": "line",
                "metric": "policies_created"
            }
        ],
        "created_at": "2023-01-03T00:00:00Z",
        "updated_at": "2023-01-03T00:00:00Z"
    },
    {
        "id": "dashboard-002",
        "name": "Analytics Dashboard",
        "description": "Detailed analytics and insights",
        "owner": "user-002",
        "layout": "flexible",
        "widgets": [
            {
                "id": "widget-003",
                "type": "table",
                "title": "Recent Activities",
                "position": {"x": 0, "y": 0, "w": 6, "h": 3},
                "data_source": "monitoring-service",
                "metric": "recent_activities"
            }
        ],
        "created_at": "2023-01-03T00:00:00Z",
        "updated_at": "2023-01-03T00:00:00Z"
    }
]

# Mock data cache for development
data_cache = {
    "system_metrics": {
        "total_users": 1250,
        "active_users": 890,
        "total_policies": 456,
        "total_files": 1234,
        "system_uptime": "99.8%",
        "last_updated": datetime.now().isoformat() + "Z"
    },
    "policy_metrics": {
        "policies_created": [45, 52, 38, 67, 89, 76, 54],
        "policies_updated": [12, 15, 8, 23, 34, 28, 19],
        "policies_deleted": [2, 1, 3, 0, 1, 2, 1],
        "categories": ["Education", "Healthcare", "Transportation", "Environment", "Security"],
        "category_counts": [89, 67, 45, 78, 56]
    },
    "file_metrics": {
        "total_files": 1234,
        "files_uploaded": [23, 45, 67, 89, 123, 156, 189],
        "file_types": ["PDF", "DOC", "TXT", "CSV", "JSON"],
        "type_counts": [456, 234, 189, 156, 89],
        "storage_used": "2.3 GB",
        "storage_limit": "10 GB"
    },
    "user_metrics": {
        "total_users": 1250,
        "active_users": 890,
        "new_users": [12, 23, 34, 45, 56, 67, 78],
        "user_roles": ["Admin", "User", "Moderator", "Guest"],
        "role_counts": [15, 1100, 89, 46]
    }
}

# Simple validation functions
def validate_dashboard_name(name: str) -> bool:
    """Validate dashboard name"""
    return name and len(name) <= 100 and not any(char in name for char in ['<', '>', ':', '"', '|', '?', '*', '\\', '/'])

def validate_widget_config(widget: Dict[str, Any]) -> List[str]:
    """Validate widget configuration"""
    errors = []
    if not widget.get("type"): errors.append("Widget type is required")
    if not widget.get("title"): errors.append("Widget title is required")
    if not widget.get("position"): errors.append("Widget position is required")
    if not widget.get("data_source"): errors.append("Data source is required")
    return errors

# Dashboard service implementation
class DashboardService:
    def __init__(self):
        self.dashboards = dashboard_configs_db
        self.cache = data_cache
    
    def list_dashboards(self, skip: int = 0, limit: int = 100, owner: Optional[str] = None) -> List[Dict[str, Any]]:
        """List all dashboards with optional filtering"""
        filtered_dashboards = self.dashboards
        
        if owner:
            filtered_dashboards = [d for d in filtered_dashboards if d["owner"] == owner]
        
        return filtered_dashboards[skip:skip + limit]
    
    def get_dashboard(self, dashboard_id: str) -> Optional[Dict[str, Any]]:
        """Get a specific dashboard by ID"""
        for dashboard in self.dashboards:
            if dashboard["id"] == dashboard_id:
                return dashboard
        return None
    
    def create_dashboard(self, dashboard_data: Dict[str, Any]) -> Dict[str, Any]:
        """Create a new dashboard"""
        # Validate dashboard data
        if not validate_dashboard_name(dashboard_data.get("name", "")):
            raise ValueError("Invalid dashboard name")
        
        # Validate widgets if provided
        if "widgets" in dashboard_data:
            for widget in dashboard_data["widgets"]:
                widget_errors = validate_widget_config(widget)
                if widget_errors:
                    raise ValueError(f"Widget validation errors: {', '.join(widget_errors)}")
        
        new_dashboard = {
            "id": f"dashboard-{str(uuid.uuid4())[:8]}",
            "name": dashboard_data["name"],
            "description": dashboard_data.get("description", ""),
            "owner": dashboard_data["owner"],
            "layout": dashboard_data.get("layout", "grid"),
            "widgets": dashboard_data.get("widgets", []),
            "created_at": datetime.now().isoformat() + "Z",
            "updated_at": datetime.now().isoformat() + "Z"
        }
        
        self.dashboards.append(new_dashboard)
        return new_dashboard
    
    def update_dashboard(self, dashboard_id: str, dashboard_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Update an existing dashboard"""
        dashboard = self.get_dashboard(dashboard_id)
        if not dashboard:
            return None
        
        # Update allowed fields
        allowed_fields = ["name", "description", "layout", "widgets"]
        for key, value in dashboard_data.items():
            if key in allowed_fields:
                if key == "name" and not validate_dashboard_name(value):
                    raise ValueError("Invalid dashboard name")
                if key == "widgets":
                    for widget in value:
                        widget_errors = validate_widget_config(widget)
                        if widget_errors:
                            raise ValueError(f"Widget validation errors: {', '.join(widget_errors)}")
                dashboard[key] = value
        
        dashboard["updated_at"] = datetime.now().isoformat() + "Z"
        return dashboard
    
    def delete_dashboard(self, dashboard_id: str) -> bool:
        """Delete a dashboard"""
        dashboard = self.get_dashboard(dashboard_id)
        if dashboard:
            self.dashboards.remove(dashboard)
            return True
        return False
    
    def get_dashboard_data(self, dashboard_id: str) -> Dict[str, Any]:
        """Get data for a specific dashboard"""
        dashboard = self.get_dashboard(dashboard_id)
        if not dashboard:
            return {}
        
        dashboard_data = {
            "dashboard": dashboard,
            "data": {},
            "last_updated": datetime.now().isoformat() + "Z"
        }
        
        # Collect data for each widget
        for widget in dashboard.get("widgets", []):
            data_source = widget.get("data_source")
            metric = widget.get("metric")
            
            if data_source and metric:
                widget_data = self.get_metric_data(data_source, metric)
                dashboard_data["data"][widget["id"]] = widget_data
        
        return dashboard_data
    
    def get_metric_data(self, data_source: str, metric: str) -> Dict[str, Any]:
        """Get metric data from cache or external service"""
        # For now, return cached data
        if data_source in self.cache and metric in self.cache[data_source]:
            return {
                "value": self.cache[data_source][metric],
                "source": data_source,
                "metric": metric,
                "timestamp": datetime.now().isoformat() + "Z"
            }
        
        return {
            "value": None,
            "source": data_source,
            "metric": metric,
            "error": "Metric not found",
            "timestamp": datetime.now().isoformat() + "Z"
        }
    
    def get_system_overview(self) -> Dict[str, Any]:
        """Get system overview metrics"""
        return {
            "system_metrics": self.cache["system_metrics"],
            "policy_metrics": self.cache["policy_metrics"],
            "file_metrics": self.cache["file_metrics"],
            "user_metrics": self.cache["user_metrics"],
            "last_updated": datetime.now().isoformat() + "Z"
        }
    
    def get_analytics_data(self, metric_type: str, time_range: str = "7d") -> Dict[str, Any]:
        """Get analytics data for specific metric type"""
        if metric_type == "policies":
            return {
                "metric_type": "policies",
                "time_range": time_range,
                "data": self.cache["policy_metrics"],
                "last_updated": datetime.now().isoformat() + "Z"
            }
        elif metric_type == "files":
            return {
                "metric_type": "files",
                "time_range": time_range,
                "data": self.cache["file_metrics"],
                "last_updated": datetime.now().isoformat() + "Z"
            }
        elif metric_type == "users":
            return {
                "metric_type": "users",
                "time_range": time_range,
                "data": self.cache["user_metrics"],
                "last_updated": datetime.now().isoformat() + "Z"
            }
        else:
            return {
                "metric_type": metric_type,
                "time_range": time_range,
                "error": "Unknown metric type",
                "last_updated": datetime.now().isoformat() + "Z"
            }
    
    def search_dashboards(self, query: str) -> List[Dict[str, Any]]:
        """Search dashboards by name or description"""
        query_lower = query.lower()
        results = []
        
        for dashboard in self.dashboards:
            if (query_lower in dashboard["name"].lower() or
                query_lower in dashboard.get("description", "").lower()):
                results.append(dashboard)
        
        return results

# Initialize service
dashboard_service = DashboardService()

# Mock authentication (replace with real authentication)
def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)) -> Dict[str, Any]:
    """Mock authentication - replace with real implementation"""
    return {"user_id": "user-001", "username": "admin", "role": "admin"}

# Health check endpoints
@app.get("/healthz")
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy", "service": "dashboard-service", "timestamp": datetime.now().isoformat()}

@app.get("/readyz")
async def readiness_check():
    """Readiness check endpoint"""
    return {"status": "ready", "service": "dashboard-service", "timestamp": datetime.now().isoformat()}

@app.get("/metrics")
async def metrics():
    """Prometheus metrics endpoint"""
    return Response(generate_latest(), media_type=CONTENT_TYPE_LATEST)

# Dashboard API endpoints
@app.get("/dashboards", response_model=List[Dict[str, Any]])
async def list_dashboards(
    skip: int = Query(0, ge=0, description="Number of records to skip"),
    limit: int = Query(100, ge=1, le=1000, description="Maximum number of records to return"),
    owner: Optional[str] = Query(None, description="Filter by owner"),
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    """List all dashboards with optional filtering"""
    start_time = time.time()
    try:
        dashboards = dashboard_service.list_dashboards(skip=skip, limit=limit, owner=owner)
        dashboard_operations.labels(operation="list", status="success").inc()
        dashboard_duration.observe(time.time() - start_time)
        return dashboards
    except Exception as e:
        dashboard_operations.labels(operation="list", status="error").inc()
        logger.error(f"Error listing dashboards: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")

@app.get("/dashboards/{dashboard_id}", response_model=Dict[str, Any])
async def get_dashboard(
    dashboard_id: str,
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    """Get a specific dashboard by ID"""
    start_time = time.time()
    try:
        dashboard = dashboard_service.get_dashboard(dashboard_id)
        if not dashboard:
            raise HTTPException(status_code=404, detail="Dashboard not found")
        
        dashboard_operations.labels(operation="get", status="success").inc()
        dashboard_duration.observe(time.time() - start_time)
        return dashboard
    except HTTPException:
        raise
    except Exception as e:
        dashboard_operations.labels(operation="get", status="error").inc()
        logger.error(f"Error getting dashboard {dashboard_id}: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")

@app.post("/dashboards", response_model=Dict[str, Any], status_code=201)
async def create_dashboard(
    dashboard_data: Dict[str, Any],
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    """Create a new dashboard"""
    start_time = time.time()
    try:
        # Set owner to current user
        dashboard_data["owner"] = current_user["user_id"]
        
        new_dashboard = dashboard_service.create_dashboard(dashboard_data)
        dashboard_operations.labels(operation="create", status="success").inc()
        dashboard_duration.observe(time.time() - start_time)
        return new_dashboard
    except ValueError as e:
        dashboard_operations.labels(operation="create", status="error").inc()
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        dashboard_operations.labels(operation="create", status="error").inc()
        logger.error(f"Error creating dashboard: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")

@app.put("/dashboards/{dashboard_id}", response_model=Dict[str, Any])
async def update_dashboard(
    dashboard_id: str,
    dashboard_data: Dict[str, Any],
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    """Update an existing dashboard"""
    start_time = time.time()
    try:
        dashboard = dashboard_service.get_dashboard(dashboard_id)
        if not dashboard:
            raise HTTPException(status_code=404, detail="Dashboard not found")
        
        # Check ownership
        if dashboard["owner"] != current_user["user_id"] and current_user["role"] != "admin":
            raise HTTPException(status_code=403, detail="Access denied")
        
        updated_dashboard = dashboard_service.update_dashboard(dashboard_id, dashboard_data)
        if not updated_dashboard:
            raise HTTPException(status_code=404, detail="Dashboard not found")
        
        dashboard_operations.labels(operation="update", status="success").inc()
        dashboard_duration.observe(time.time() - start_time)
        return updated_dashboard
    except HTTPException:
        raise
    except ValueError as e:
        dashboard_operations.labels(operation="update", status="error").inc()
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        dashboard_operations.labels(operation="update", status="error").inc()
        logger.error(f"Error updating dashboard {dashboard_id}: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")

@app.delete("/dashboards/{dashboard_id}")
async def delete_dashboard(
    dashboard_id: str,
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    """Delete a dashboard"""
    start_time = time.time()
    try:
        dashboard = dashboard_service.get_dashboard(dashboard_id)
        if not dashboard:
            raise HTTPException(status_code=404, detail="Dashboard not found")
        
        # Check ownership
        if dashboard["owner"] != current_user["user_id"] and current_user["role"] != "admin":
            raise HTTPException(status_code=403, detail="Access denied")
        
        success = dashboard_service.delete_dashboard(dashboard_id)
        if not success:
            raise HTTPException(status_code=404, detail="Dashboard not found")
        
        dashboard_operations.labels(operation="delete", status="success").inc()
        dashboard_duration.observe(time.time() - start_time)
        
        return {"message": "Dashboard deleted successfully"}
    except HTTPException:
        raise
    except Exception as e:
        dashboard_operations.labels(operation="delete", status="error").inc()
        logger.error(f"Error deleting dashboard {dashboard_id}: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")

# Dashboard data endpoints
@app.get("/dashboards/{dashboard_id}/data", response_model=Dict[str, Any])
async def get_dashboard_data(
    dashboard_id: str,
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    """Get data for a specific dashboard"""
    start_time = time.time()
    try:
        dashboard_data = dashboard_service.get_dashboard_data(dashboard_id)
        if not dashboard_data:
            raise HTTPException(status_code=404, detail="Dashboard not found")
        
        dashboard_operations.labels(operation="get_data", status="success").inc()
        dashboard_duration.observe(time.time() - start_time)
        dashboard_data_points.inc()
        
        return dashboard_data
    except HTTPException:
        raise
    except Exception as e:
        dashboard_operations.labels(operation="get_data", status="error").inc()
        logger.error(f"Error getting dashboard data for {dashboard_id}: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")

@app.get("/system/overview", response_model=Dict[str, Any])
async def get_system_overview(
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    """Get system overview metrics"""
    start_time = time.time()
    try:
        overview_data = dashboard_service.get_system_overview()
        dashboard_operations.labels(operation="system_overview", status="success").inc()
        dashboard_duration.observe(time.time() - start_time)
        return overview_data
    except Exception as e:
        dashboard_operations.labels(operation="system_overview", status="error").inc()
        logger.error(f"Error getting system overview: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")

@app.get("/analytics/{metric_type}", response_model=Dict[str, Any])
async def get_analytics_data(
    metric_type: str,
    time_range: str = Query("7d", description="Time range for analytics"),
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    """Get analytics data for specific metric type"""
    start_time = time.time()
    try:
        analytics_data = dashboard_service.get_analytics_data(metric_type, time_range)
        dashboard_operations.labels(operation="analytics", status="success").inc()
        dashboard_duration.observe(time.time() - start_time)
        return analytics_data
    except Exception as e:
        dashboard_operations.labels(operation="analytics", status="error").inc()
        logger.error(f"Error getting analytics data for {metric_type}: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")

# Additional endpoints
@app.get("/dashboards/search", response_model=List[Dict[str, Any]])
async def search_dashboards(
    q: str = Query(..., description="Search query"),
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    """Search dashboards by name or description"""
    try:
        dashboards = dashboard_service.search_dashboards(q)
        return dashboards
    except Exception as e:
        logger.error(f"Error searching dashboards with query '{q}': {e}")
        raise HTTPException(status_code=500, detail="Internal server error")

@app.get("/metrics/{data_source}/{metric}", response_model=Dict[str, Any])
async def get_metric_data(
    data_source: str,
    metric: str,
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    """Get specific metric data from a data source"""
    try:
        metric_data = dashboard_service.get_metric_data(data_source, metric)
        return metric_data
    except Exception as e:
        logger.error(f"Error getting metric {metric} from {data_source}: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")

if __name__ == "__main__":
    import uvicorn
    # Use documented architecture port 8016
    port = int(os.getenv("PORT", 8016))
    uvicorn.run(app, host="0.0.0.0", port=port)
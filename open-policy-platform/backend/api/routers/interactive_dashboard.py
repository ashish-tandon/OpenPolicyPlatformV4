"""
Open Policy Platform V4 - Interactive Dashboard Router
Real-time dashboards, customizable widgets, and advanced data visualization
"""

from fastapi import APIRouter, Depends, HTTPException, Query, WebSocket, WebSocketDisconnect
from fastapi.responses import StreamingResponse, JSONResponse
from pydantic import BaseModel
from sqlalchemy.orm import Session
from typing import List, Optional, Dict, Any, AsyncGenerator
import json
import asyncio
import logging
from datetime import datetime, timedelta
import random
import uuid
from enum import Enum

from ..dependencies import get_db

router = APIRouter()
logger = logging.getLogger(__name__)

# Dashboard Models
class WidgetType(str, Enum):
    CHART = "chart"
    METRIC = "metric"
    TABLE = "table"
    GAUGE = "gauge"
    TIMELINE = "timeline"
    MAP = "map"
    HEATMAP = "heatmap"

class ChartType(str, Enum):
    LINE = "line"
    BAR = "bar"
    PIE = "pie"
    SCATTER = "scatter"
    AREA = "area"
    CANDLESTICK = "candlestick"
    RADAR = "radar"

class DashboardWidget(BaseModel):
    id: str
    name: str
    type: WidgetType
    chart_type: Optional[ChartType] = None
    position: Dict[str, int]  # x, y, width, height
    data_source: str
    refresh_interval: int  # seconds
    config: Dict[str, Any]
    is_active: bool = True
    created_at: datetime
    updated_at: datetime

class Dashboard(BaseModel):
    id: str
    name: str
    description: str
    user_id: str
    widgets: List[DashboardWidget]
    layout: Dict[str, Any]
    theme: str = "light"
    is_public: bool = False
    created_at: datetime
    updated_at: datetime

class WidgetData(BaseModel):
    widget_id: str
    data: Dict[str, Any]
    timestamp: datetime
    metadata: Optional[Dict[str, Any]] = None

class DashboardPreferences(BaseModel):
    user_id: str
    default_dashboard: str
    theme: str = "light"
    refresh_rate: int = 30
    notifications_enabled: bool = True
    auto_save: bool = True

# Mock Dashboard Database
DASHBOARDS = {
    "main_dashboard": {
        "id": "main_dashboard",
        "name": "Main Platform Dashboard",
        "description": "Comprehensive overview of platform performance and metrics",
        "user_id": "admin",
        "widgets": [
            {
                "id": "widget_001",
                "name": "Platform Performance",
                "type": "chart",
                "chart_type": "line",
                "position": {"x": 0, "y": 0, "width": 6, "height": 4},
                "data_source": "performance_metrics",
                "refresh_interval": 30,
                "config": {
                    "title": "Platform Performance Over Time",
                    "y_axis_label": "Response Time (ms)",
                    "color_scheme": "blue",
                    "show_legend": True
                },
                "is_active": True,
                "created_at": datetime.now() - timedelta(days=7),
                "updated_at": datetime.now()
            },
            {
                "id": "widget_002",
                "name": "User Activity",
                "type": "metric",
                "position": {"x": 6, "y": 0, "width": 3, "height": 2},
                "data_source": "user_metrics",
                "refresh_interval": 60,
                "config": {
                    "title": "Active Users",
                    "unit": "users",
                    "color": "green",
                    "icon": "users"
                },
                "is_active": True,
                "created_at": datetime.now() - timedelta(days=7),
                "updated_at": datetime.now()
            },
            {
                "id": "widget_003",
                "name": "System Health",
                "type": "gauge",
                "position": {"x": 9, "y": 0, "width": 3, "height": 2},
                "data_source": "system_health",
                "refresh_interval": 45,
                "config": {
                    "title": "System Uptime",
                    "min_value": 0,
                    "max_value": 100,
                    "unit": "%",
                    "thresholds": {"warning": 95, "critical": 90}
                },
                "is_active": True,
                "created_at": datetime.now() - timedelta(days=7),
                "updated_at": datetime.now()
            }
        ],
        "layout": {"grid": "responsive", "columns": 12},
        "theme": "light",
        "is_public": True,
        "created_at": datetime.now() - timedelta(days=30),
        "updated_at": datetime.now()
    }
}

USER_PREFERENCES = {
    "admin": {
        "user_id": "admin",
        "default_dashboard": "main_dashboard",
        "theme": "light",
        "refresh_rate": 30,
        "notifications_enabled": True,
        "auto_save": True
    }
}

# Active WebSocket connections for real-time updates
active_connections: List[WebSocket] = []

# Interactive Dashboard Endpoints
@router.get("/dashboards")
async def list_dashboards(
    user_id: Optional[str] = Query(None, description="Filter by user ID"),
    is_public: Optional[bool] = Query(None, description="Filter by public status"),
    limit: int = Query(50, description="Maximum dashboards to return")
):
    """List available dashboards"""
    try:
        dashboards = list(DASHBOARDS.values())
        
        # Apply filters
        if user_id:
            dashboards = [d for d in dashboards if d["user_id"] == user_id]
        if is_public is not None:
            dashboards = [d for d in dashboards if d["is_public"] == is_public]
        
        # Apply limit
        dashboards = dashboards[:limit]
        
        return {
            "status": "success",
            "dashboards": dashboards,
            "total_dashboards": len(dashboards),
            "filters_applied": {
                "user_id": user_id,
                "is_public": is_public,
                "limit": limit
            }
        }
        
    except Exception as e:
        logger.error(f"Error listing dashboards: {e}")
        raise HTTPException(status_code=500, detail=f"Dashboard listing error: {str(e)}")

@router.get("/dashboards/{dashboard_id}")
async def get_dashboard(dashboard_id: str):
    """Get specific dashboard with widgets and layout"""
    try:
        if dashboard_id not in DASHBOARDS:
            raise HTTPException(status_code=404, detail="Dashboard not found")
        
        dashboard = DASHBOARDS[dashboard_id]
        
        # Add widget data for each widget
        for widget in dashboard["widgets"]:
            widget["data"] = await generate_widget_data(widget)
        
        return {
            "status": "success",
            "dashboard": dashboard
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting dashboard: {e}")
        raise HTTPException(status_code=500, detail=f"Dashboard retrieval error: {str(e)}")

@router.post("/dashboards")
async def create_dashboard(
    name: str,
    description: str,
    user_id: str,
    theme: str = "light",
    is_public: bool = False
):
    """Create a new dashboard"""
    try:
        dashboard_id = f"dashboard_{uuid.uuid4().hex[:8]}"
        
        new_dashboard = Dashboard(
            id=dashboard_id,
            name=name,
            description=description,
            user_id=user_id,
            widgets=[],
            layout={"grid": "responsive", "columns": 12},
            theme=theme,
            is_public=is_public,
            created_at=datetime.now(),
            updated_at=datetime.now()
        )
        
        DASHBOARDS[dashboard_id] = new_dashboard.dict()
        
        return {
            "status": "success",
            "message": f"Dashboard '{name}' created successfully",
            "dashboard_id": dashboard_id,
            "dashboard": new_dashboard
        }
        
    except Exception as e:
        logger.error(f"Error creating dashboard: {e}")
        raise HTTPException(status_code=500, detail=f"Dashboard creation error: {str(e)}")

@router.post("/dashboards/{dashboard_id}/widgets")
async def add_widget(
    dashboard_id: str,
    name: str,
    widget_type: WidgetType,
    position: Dict[str, int],
    data_source: str,
    chart_type: Optional[ChartType] = None,
    refresh_interval: int = 60,
    config: Dict[str, Any] = {}
):
    """Add a new widget to a dashboard"""
    try:
        if dashboard_id not in DASHBOARDS:
            raise HTTPException(status_code=404, detail="Dashboard not found")
        
        dashboard = DASHBOARDS[dashboard_id]
        
        # Create new widget
        widget_id = f"widget_{uuid.uuid4().hex[:8]}"
        new_widget = DashboardWidget(
            id=widget_id,
            name=name,
            type=widget_type,
            chart_type=chart_type,
            position=position,
            data_source=data_source,
            refresh_interval=refresh_interval,
            config=config,
            created_at=datetime.now(),
            updated_at=datetime.now()
        )
        
        # Add widget to dashboard
        dashboard["widgets"].append(new_widget.dict())
        dashboard["updated_at"] = datetime.now()
        
        return {
            "status": "success",
            "message": f"Widget '{name}' added to dashboard",
            "widget_id": widget_id,
            "widget": new_widget
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error adding widget: {e}")
        raise HTTPException(status_code=500, detail=f"Widget creation error: {str(e)}")

@router.get("/widgets/{widget_id}/data")
async def get_widget_data(
    widget_id: str,
    refresh: bool = Query(False, description="Force data refresh")
):
    """Get data for a specific widget"""
    try:
        # Find widget in dashboards
        widget = None
        for dashboard in DASHBOARDS.values():
            for w in dashboard["widgets"]:
                if w["id"] == widget_id:
                    widget = w
                    break
            if widget:
                break
        
        if not widget:
            raise HTTPException(status_code=404, detail="Widget not found")
        
        # Generate widget data
        data = await generate_widget_data(widget, force_refresh=refresh)
        
        return {
            "status": "success",
            "widget_id": widget_id,
            "data": data,
            "timestamp": datetime.now(),
            "next_refresh": datetime.now() + timedelta(seconds=widget["refresh_interval"])
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting widget data: {e}")
        raise HTTPException(status_code=500, detail=f"Widget data error: {str(e)}")

@router.get("/widgets/{widget_id}/config")
async def get_widget_config(widget_id: str):
    """Get configuration for a specific widget"""
    try:
        # Find widget in dashboards
        widget = None
        for dashboard in DASHBOARDS.values():
            for w in dashboard["widgets"]:
                if w["id"] == widget_id:
                    widget = w
                    break
            if widget:
                break
        
        if not widget:
            raise HTTPException(status_code=404, detail="Widget not found")
        
        return {
            "status": "success",
            "widget_id": widget_id,
            "config": widget["config"],
            "type": widget["type"],
            "chart_type": widget["chart_type"],
            "position": widget["position"],
            "refresh_interval": widget["refresh_interval"]
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting widget config: {e}")
        raise HTTPException(status_code=500, detail=f"Widget config error: {str(e)}")

@router.put("/widgets/{widget_id}/config")
async def update_widget_config(
    widget_id: str,
    config: Dict[str, Any]
):
    """Update configuration for a specific widget"""
    try:
        # Find and update widget in dashboards
        widget_updated = False
        for dashboard in DASHBOARDS.values():
            for w in dashboard["widgets"]:
                if w["id"] == widget_id:
                    w["config"].update(config)
                    w["updated_at"] = datetime.now()
                    dashboard["updated_at"] = datetime.now()
                    widget_updated = True
                    break
            if widget_updated:
                break
        
        if not widget_updated:
            raise HTTPException(status_code=404, detail="Widget not found")
        
        return {
            "status": "success",
            "message": f"Widget {widget_id} configuration updated",
            "widget_id": widget_id,
            "updated_config": config
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating widget config: {e}")
        raise HTTPException(status_code=500, detail=f"Widget config update error: {str(e)}")

@router.get("/preferences/{user_id}")
async def get_user_preferences(user_id: str):
    """Get user dashboard preferences"""
    try:
        if user_id not in USER_PREFERENCES:
            # Create default preferences
            USER_PREFERENCES[user_id] = {
                "user_id": user_id,
                "default_dashboard": "main_dashboard",
                "theme": "light",
                "refresh_rate": 30,
                "notifications_enabled": True,
                "auto_save": True
            }
        
        return {
            "status": "success",
            "preferences": USER_PREFERENCES[user_id]
        }
        
    except Exception as e:
        logger.error(f"Error getting user preferences: {e}")
        raise HTTPException(status_code=500, detail=f"Preferences retrieval error: {str(e)}")

@router.put("/preferences/{user_id}")
async def update_user_preferences(
    user_id: str,
    preferences: DashboardPreferences
):
    """Update user dashboard preferences"""
    try:
        USER_PREFERENCES[user_id] = preferences.dict()
        
        return {
            "status": "success",
            "message": f"Preferences updated for user {user_id}",
            "preferences": USER_PREFERENCES[user_id]
        }
        
    except Exception as e:
        logger.error(f"Error updating user preferences: {e}")
        raise HTTPException(status_code=500, detail=f"Preferences update error: {str(e)}")

@router.get("/themes")
async def get_available_themes():
    """Get available dashboard themes"""
    try:
        themes = [
            {
                "id": "light",
                "name": "Light Theme",
                "description": "Clean, bright interface for daytime use",
                "colors": {
                    "primary": "#007bff",
                    "secondary": "#6c757d",
                    "background": "#ffffff",
                    "text": "#212529"
                }
            },
            {
                "id": "dark",
                "name": "Dark Theme",
                "description": "Easy on the eyes for nighttime use",
                "colors": {
                    "primary": "#0d6efd",
                    "secondary": "#6c757d",
                    "background": "#212529",
                    "text": "#f8f9fa"
                }
            },
            {
                "id": "blue",
                "name": "Blue Theme",
                "description": "Professional blue color scheme",
                "colors": {
                    "primary": "#0056b3",
                    "secondary": "#495057",
                    "background": "#f8f9fa",
                    "text": "#212529"
                }
            }
        ]
        
        return {
            "status": "success",
            "themes": themes,
            "total_themes": len(themes)
        }
        
    except Exception as e:
        logger.error(f"Error getting themes: {e}")
        raise HTTPException(status_code=500, detail=f"Themes retrieval error: {str(e)}")

@router.get("/data-sources")
async def get_available_data_sources():
    """Get available data sources for widgets"""
    try:
        data_sources = [
            {
                "id": "performance_metrics",
                "name": "Performance Metrics",
                "description": "System performance and response time data",
                "type": "time_series",
                "update_frequency": "30s",
                "endpoint": "/api/v1/analytics/real-time-metrics"
            },
            {
                "id": "user_metrics",
                "name": "User Metrics",
                "description": "User activity and engagement data",
                "type": "aggregated",
                "update_frequency": "60s",
                "endpoint": "/api/v1/analytics/business-metrics"
            },
            {
                "id": "system_health",
                "name": "System Health",
                "description": "System uptime and health indicators",
                "type": "status",
                "update_frequency": "45s",
                "endpoint": "/api/v1/health"
            },
            {
                "id": "ml_insights",
                "name": "ML Insights",
                "description": "Machine learning generated insights",
                "type": "insights",
                "update_frequency": "300s",
                "endpoint": "/api/v1/analytics/ml-insights"
            }
        ]
        
        return {
            "status": "success",
            "data_sources": data_sources,
            "total_sources": len(data_sources)
        }
        
    except Exception as e:
        logger.error(f"Error getting data sources: {e}")
        raise HTTPException(status_code=500, detail=f"Data sources retrieval error: {str(e)}")

@router.websocket("/ws/dashboard/{dashboard_id}")
async def websocket_dashboard(websocket: WebSocket, dashboard_id: str):
    """WebSocket endpoint for real-time dashboard updates"""
    await websocket.accept()
    active_connections.append(websocket)
    
    try:
        # Send initial dashboard data
        if dashboard_id in DASHBOARDS:
            dashboard = DASHBOARDS[dashboard_id]
            await websocket.send_text(json.dumps({
                "type": "dashboard_data",
                "dashboard_id": dashboard_id,
                "data": dashboard
            }))
        
        # Keep connection alive and send updates
        while True:
            # Wait for client messages
            data = await websocket.receive_text()
            message = json.loads(data)
            
            if message["type"] == "subscribe_widget":
                # Subscribe to specific widget updates
                widget_id = message["widget_id"]
                await send_widget_updates(websocket, widget_id)
            elif message["type"] == "ping":
                # Respond to ping
                await websocket.send_text(json.dumps({"type": "pong"}))
                
    except WebSocketDisconnect:
        active_connections.remove(websocket)
    except Exception as e:
        logger.error(f"WebSocket error: {e}")
        if websocket in active_connections:
            active_connections.remove(websocket)

# Helper Functions
async def generate_widget_data(widget: Dict[str, Any], force_refresh: bool = False) -> Dict[str, Any]:
    """Generate data for a specific widget based on its type and data source"""
    try:
        widget_type = widget["type"]
        data_source = widget["data_source"]
        
        if widget_type == "chart":
            if widget.get("chart_type") == "line":
                # Generate time series data
                data = {
                    "labels": [f"{(datetime.now() - timedelta(minutes=i)).strftime('%H:%M')}" for i in range(20, 0, -1)],
                    "datasets": [{
                        "label": "Response Time",
                        "data": [round(random.uniform(0.1, 0.5), 3) for _ in range(20)],
                        "borderColor": "#007bff",
                        "backgroundColor": "rgba(0, 123, 255, 0.1)"
                    }]
                }
            elif widget.get("chart_type") == "bar":
                # Generate bar chart data
                data = {
                    "labels": ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"],
                    "datasets": [{
                        "label": "User Activity",
                        "data": [random.randint(80, 150) for _ in range(7)],
                        "backgroundColor": "rgba(0, 123, 255, 0.8)"
                    }]
                }
            else:
                data = {"message": "Chart type not implemented yet"}
        
        elif widget_type == "metric":
            if data_source == "user_metrics":
                data = {
                    "value": random.randint(100, 200),
                    "unit": "users",
                    "trend": random.choice(["up", "down", "stable"]),
                    "change": round(random.uniform(-15, 20), 1)
                }
            else:
                data = {
                    "value": random.randint(50, 100),
                    "unit": "units",
                    "trend": "stable",
                    "change": 0.0
                }
        
        elif widget_type == "gauge":
            data = {
                "value": round(random.uniform(85, 100), 1),
                "min": 0,
                "max": 100,
                "unit": "%",
                "status": "good"
            }
        
        elif widget_type == "table":
            data = {
                "headers": ["Metric", "Value", "Status", "Trend"],
                "rows": [
                    ["Response Time", "0.15s", "Good", "↓"],
                    ["Error Rate", "0.02%", "Good", "→"],
                    ["CPU Usage", "45%", "Good", "↑"],
                    ["Memory Usage", "67%", "Warning", "↑"]
                ]
            }
        
        else:
            data = {"message": "Widget type not implemented yet"}
        
        return data
        
    except Exception as e:
        logger.error(f"Error generating widget data: {e}")
        return {"error": str(e)}

async def send_widget_updates(websocket: WebSocket, widget_id: str):
    """Send periodic updates for a specific widget"""
    try:
        # Find widget
        widget = None
        for dashboard in DASHBOARDS.values():
            for w in dashboard["widgets"]:
                if w["id"] == widget_id:
                    widget = w
                    break
            if widget:
                break
        
        if not widget:
            return
        
        # Send updates based on refresh interval
        while True:
            await asyncio.sleep(widget["refresh_interval"])
            
            # Generate new data
            data = await generate_widget_data(widget)
            
            # Send update
            await websocket.send_text(json.dumps({
                "type": "widget_update",
                "widget_id": widget_id,
                "data": data,
                "timestamp": datetime.now().isoformat()
            }))
            
    except Exception as e:
        logger.error(f"Error sending widget updates: {e}")

async def broadcast_dashboard_update(dashboard_id: str, update_type: str, data: Dict[str, Any]):
    """Broadcast dashboard updates to all connected clients"""
    try:
        message = {
            "type": update_type,
            "dashboard_id": dashboard_id,
            "data": data,
            "timestamp": datetime.now().isoformat()
        }
        
        # Send to all active connections
        for connection in active_connections:
            try:
                await connection.send_text(json.dumps(message))
            except Exception as e:
                logger.error(f"Error broadcasting to connection: {e}")
                # Remove failed connection
                active_connections.remove(connection)
                
    except Exception as e:
        logger.error(f"Error broadcasting dashboard update: {e}")

"""
Open Policy Platform V4 - Data Visualization Router
Advanced charting, graphing, and interactive visualization capabilities
"""

from fastapi import APIRouter, Depends, HTTPException, Query, BackgroundTasks
from fastapi.responses import StreamingResponse, JSONResponse
from pydantic import BaseModel
from sqlalchemy.orm import Session
from typing import List, Optional, Dict, Any, AsyncGenerator, Union
import json
import asyncio
import logging
from datetime import datetime, timedelta
import random
import math
import uuid
from enum import Enum

from ..dependencies import get_db

router = APIRouter()
logger = logging.getLogger(__name__)

# Visualization Models
class ChartType(str, Enum):
    LINE = "line"
    BAR = "bar"
    PIE = "pie"
    SCATTER = "scatter"
    AREA = "area"
    CANDLESTICK = "candlestick"
    RADAR = "radar"
    HEATMAP = "heatmap"
    TREEMAP = "treemap"
    SANKEY = "sankey"
    BUBBLE = "bubble"
    POLAR = "polar"

class DataAggregation(str, Enum):
    SUM = "sum"
    AVERAGE = "average"
    COUNT = "count"
    MIN = "min"
    MAX = "max"
    MEDIAN = "median"

class VisualizationConfig(BaseModel):
    chart_type: ChartType
    title: str
    x_axis_label: Optional[str] = None
    y_axis_label: Optional[str] = None
    color_scheme: str = "default"
    show_legend: bool = True
    show_grid: bool = True
    animation: bool = True
    responsive: bool = True
    height: int = 400
    width: Optional[int] = None
    theme: str = "light"

class DataSeries(BaseModel):
    name: str
    data: List[Union[float, int, str]]
    color: Optional[str] = None
    type: Optional[str] = None
    y_axis: Optional[int] = None

class ChartData(BaseModel):
    labels: List[str]
    series: List[DataSeries]
    config: VisualizationConfig
    metadata: Optional[Dict[str, Any]] = None

class InteractiveChart(BaseModel):
    id: str
    name: str
    description: str
    chart_data: ChartData
    filters: Dict[str, Any]
    drill_down_enabled: bool = False
    export_enabled: bool = True
    created_at: datetime
    updated_at: datetime

# Mock Chart Database
CHARTS = {
    "platform_performance": {
        "id": "platform_performance",
        "name": "Platform Performance Overview",
        "description": "Comprehensive view of system performance metrics",
        "chart_data": {
            "labels": [],
            "series": [],
            "config": {
                "chart_type": "line",
                "title": "Platform Performance Over Time",
                "x_axis_label": "Time",
                "y_axis_label": "Response Time (ms)",
                "color_scheme": "blue",
                "show_legend": True,
                "show_grid": True,
                "animation": True,
                "responsive": True,
                "height": 400
            }
        },
        "filters": {
            "time_range": "24h",
            "metrics": ["response_time", "error_rate", "cpu_usage"]
        },
        "drill_down_enabled": True,
        "export_enabled": True,
        "created_at": datetime.now() - timedelta(days=7),
        "updated_at": datetime.now()
    }
}

# Data Visualization Endpoints
@router.get("/charts")
async def list_charts(
    chart_type: Optional[ChartType] = Query(None, description="Filter by chart type"),
    limit: int = Query(50, description="Maximum charts to return")
):
    """List available charts and visualizations"""
    try:
        charts = list(CHARTS.values())
        
        # Apply filters
        if chart_type:
            charts = [c for c in charts if c["chart_data"]["config"]["chart_type"] == chart_type]
        
        # Apply limit
        charts = charts[:limit]
        
        return {
            "status": "success",
            "charts": charts,
            "total_charts": len(charts),
            "filters_applied": {
                "chart_type": chart_type,
                "limit": limit
            }
        }
        
    except Exception as e:
        logger.error(f"Error listing charts: {e}")
        raise HTTPException(status_code=500, detail=f"Chart listing error: {str(e)}")

@router.get("/charts/{chart_id}")
async def get_chart(chart_id: str):
    """Get specific chart with data and configuration"""
    try:
        if chart_id not in CHARTS:
            raise HTTPException(status_code=404, detail="Chart not found")
        
        chart = CHARTS[chart_id]
        
        # Generate chart data
        chart["chart_data"] = await generate_chart_data(chart["chart_data"]["config"], chart["filters"])
        
        return {
            "status": "success",
            "chart": chart
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting chart: {e}")
        raise HTTPException(status_code=500, detail=f"Chart retrieval error: {str(e)}")

@router.post("/charts")
async def create_chart(
    name: str,
    description: str,
    chart_type: ChartType,
    title: str,
    x_axis_label: Optional[str] = None,
    y_axis_label: Optional[str] = None,
    color_scheme: str = "default",
    height: int = 400
):
    """Create a new chart"""
    try:
        chart_id = f"chart_{uuid.uuid4().hex[:8]}"
        
        config = VisualizationConfig(
            chart_type=chart_type,
            title=title,
            x_axis_label=x_axis_label,
            y_axis_label=y_axis_label,
            color_scheme=color_scheme,
            height=height
        )
        
        chart_data = ChartData(
            labels=[],
            series=[],
            config=config
        )
        
        new_chart = InteractiveChart(
            id=chart_id,
            name=name,
            description=description,
            chart_data=chart_data,
            filters={},
            created_at=datetime.now(),
            updated_at=datetime.now()
        )
        
        CHARTS[chart_id] = new_chart.dict()
        
        return {
            "status": "success",
            "message": f"Chart '{name}' created successfully",
            "chart_id": chart_id,
            "chart": new_chart
        }
        
    except Exception as e:
        logger.error(f"Error creating chart: {e}")
        raise HTTPException(status_code=500, detail=f"Chart creation error: {str(e)}")

@router.post("/charts/{chart_id}/data")
async def generate_chart_data_endpoint(
    chart_id: str,
    filters: Dict[str, Any],
    aggregation: DataAggregation = DataAggregation.AVERAGE
):
    """Generate chart data with custom filters and aggregation"""
    try:
        if chart_id not in CHARTS:
            raise HTTPException(status_code=404, detail="Chart not found")
        
        chart = CHARTS[chart_id]
        config = chart["chart_data"]["config"]
        
        # Generate data based on chart type and filters
        chart_data = await generate_chart_data(config, filters, aggregation)
        
        return {
            "status": "success",
            "chart_id": chart_id,
            "chart_data": chart_data,
            "filters_applied": filters,
            "aggregation": aggregation,
            "generated_at": datetime.now()
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error generating chart data: {e}")
        raise HTTPException(status_code=500, detail=f"Chart data generation error: {str(e)}")

@router.get("/chart-types")
async def get_available_chart_types():
    """Get available chart types with descriptions and use cases"""
    try:
        chart_types = [
            {
                "type": "line",
                "name": "Line Chart",
                "description": "Shows trends over time or continuous data",
                "best_for": ["Time series data", "Trends", "Continuous variables"],
                "example": "Platform performance over time"
            },
            {
                "type": "bar",
                "name": "Bar Chart",
                "description": "Compares quantities across categories",
                "best_for": ["Categorical data", "Comparisons", "Discrete values"],
                "example": "User activity by day of week"
            },
            {
                "type": "pie",
                "name": "Pie Chart",
                "description": "Shows parts of a whole",
                "best_for": ["Proportions", "Percentages", "Composition"],
                "example": "User engagement distribution"
            },
            {
                "type": "scatter",
                "name": "Scatter Plot",
                "description": "Shows relationship between two variables",
                "best_for": ["Correlations", "Outliers", "Two variables"],
                "example": "Response time vs. user count"
            },
            {
                "type": "area",
                "name": "Area Chart",
                "description": "Shows cumulative data over time",
                "best_for": ["Cumulative data", "Stacked values", "Time series"],
                "example": "Total users over time"
            },
            {
                "type": "heatmap",
                "name": "Heatmap",
                "description": "Shows data density in a matrix",
                "best_for": ["Matrix data", "Density patterns", "Two dimensions"],
                "example": "User activity by hour and day"
            }
        ]
        
        return {
            "status": "success",
            "chart_types": chart_types,
            "total_types": len(chart_types)
        }
        
    except Exception as e:
        logger.error(f"Error getting chart types: {e}")
        raise HTTPException(status_code=500, detail=f"Chart types retrieval error: {str(e)}")

@router.get("/color-schemes")
async def get_available_color_schemes():
    """Get available color schemes for charts"""
    try:
        color_schemes = [
            {
                "id": "default",
                "name": "Default",
                "description": "Standard color palette",
                "colors": ["#007bff", "#6c757d", "#28a745", "#dc3545", "#ffc107", "#17a2b8"]
            },
            {
                "id": "blue",
                "name": "Blue Theme",
                "description": "Professional blue color scheme",
                "colors": ["#0056b3", "#007bff", "#3399ff", "#66b3ff", "#99ccff", "#cce6ff"]
            },
            {
                "id": "green",
                "name": "Green Theme",
                "description": "Nature-inspired green palette",
                "colors": ["#155724", "#28a745", "#40c057", "#69db7c", "#8ce99a", "#b2f2bb"]
            },
            {
                "id": "warm",
                "name": "Warm Theme",
                "description": "Warm and energetic colors",
                "colors": ["#d63384", "#fd7e14", "#ffc107", "#20c997", "#6f42c1", "#e83e8c"]
            },
            {
                "id": "grayscale",
                "name": "Grayscale",
                "description": "Professional monochrome scheme",
                "colors": ["#212529", "#495057", "#6c757d", "#adb5bd", "#ced4da", "#e9ecef"]
            }
        ]
        
        return {
            "status": "success",
            "color_schemes": color_schemes,
            "total_schemes": len(color_schemes)
        }
        
    except Exception as e:
        logger.error(f"Error getting color schemes: {e}")
        raise HTTPException(status_code=500, detail=f"Color schemes retrieval error: {str(e)}")

@router.post("/export/{chart_id}")
async def export_chart(
    chart_id: str,
    format: str = Query("png", description="Export format (png, svg, pdf, csv, json)"),
    width: int = Query(800, description="Export width in pixels"),
    height: int = Query(600, description="Export height in pixels")
):
    """Export chart in various formats"""
    try:
        if chart_id not in CHARTS:
            raise HTTPException(status_code=404, detail="Chart not found")
        
        chart = CHARTS[chart_id]
        
        # Generate export data
        export_data = await generate_export_data(chart, format, width, height)
        
        if format in ["png", "svg", "pdf"]:
            # Return file response
            return StreamingResponse(
                iter([export_data]),
                media_type=f"image/{format}" if format != "pdf" else "application/pdf",
                headers={"Content-Disposition": f"attachment; filename={chart_id}.{format}"}
            )
        else:
            # Return data response
            return {
                "status": "success",
                "chart_id": chart_id,
                "format": format,
                "data": export_data,
                "exported_at": datetime.now()
            }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error exporting chart: {e}")
        raise HTTPException(status_code=500, detail=f"Chart export error: {str(e)}")

@router.get("/templates")
async def get_chart_templates():
    """Get pre-built chart templates for common use cases"""
    try:
        templates = [
            {
                "id": "performance_overview",
                "name": "Performance Overview",
                "description": "Standard performance monitoring dashboard",
                "chart_type": "line",
                "config": {
                    "title": "System Performance Overview",
                    "x_axis_label": "Time",
                    "y_axis_label": "Response Time (ms)",
                    "color_scheme": "blue",
                    "height": 400
                },
                "data_sources": ["performance_metrics", "system_health"],
                "use_case": "System monitoring and performance tracking"
            },
            {
                "id": "user_analytics",
                "name": "User Analytics",
                "description": "User behavior and engagement analysis",
                "chart_type": "bar",
                "config": {
                    "title": "User Engagement Analysis",
                    "x_axis_label": "Metric",
                    "y_axis_label": "Value",
                    "color_scheme": "green",
                    "height": 400
                },
                "data_sources": ["user_metrics", "analytics"],
                "use_case": "User behavior analysis and engagement tracking"
            },
            {
                "id": "business_metrics",
                "name": "Business Metrics",
                "description": "Key business indicators and KPIs",
                "chart_type": "area",
                "config": {
                    "title": "Business Metrics Overview",
                    "x_axis_label": "Time Period",
                    "y_axis_label": "Metric Value",
                    "color_scheme": "warm",
                    "height": 400
                },
                "data_sources": ["business_metrics", "ml_insights"],
                "use_case": "Business intelligence and KPI tracking"
            }
        ]
        
        return {
            "status": "success",
            "templates": templates,
            "total_templates": len(templates)
        }
        
    except Exception as e:
        logger.error(f"Error getting chart templates: {e}")
        raise HTTPException(status_code=500, detail=f"Chart templates retrieval error: {str(e)}")

@router.post("/templates/{template_id}/instantiate")
async def instantiate_chart_template(
    template_id: str,
    name: str = Query(..., description="Chart name"),
    description: str = Query(..., description="Chart description"),
    custom_config: Optional[Dict[str, Any]] = None
):
    """Create a new chart from a template"""
    try:
        # Get template
        templates = await get_chart_templates()
        template = None
        for t in templates["templates"]:
            if t["id"] == template_id:
                template = t
                break
        
        if not template:
            raise HTTPException(status_code=404, detail="Template not found")
        
        # Create chart from template
        chart_id = f"chart_{uuid.uuid4().hex[:8]}"
        
        config = VisualizationConfig(
            chart_type=template["chart_type"],
            title=name,
            x_axis_label=template["config"]["x_axis_label"],
            y_axis_label=template["config"]["y_axis_label"],
            color_scheme=template["config"]["color_scheme"],
            height=template["config"]["height"]
        )
        
        # Apply custom configuration if provided
        if custom_config:
            config_dict = config.dict()
            config_dict.update(custom_config)
            config = VisualizationConfig(**config_dict)
        
        chart_data = ChartData(
            labels=[],
            series=[],
            config=config
        )
        
        new_chart = InteractiveChart(
            id=chart_id,
            name=name,
            description=description,
            chart_data=chart_data,
            filters={},
            created_at=datetime.now(),
            updated_at=datetime.now()
        )
        
        CHARTS[chart_id] = new_chart.dict()
        
        return {
            "status": "success",
            "message": f"Chart '{name}' created from template",
            "chart_id": chart_id,
            "template_id": template_id,
            "chart": new_chart
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error instantiating template: {e}")
        raise HTTPException(status_code=500, detail=f"Template instantiation error: {str(e)}")

# Helper Functions
async def generate_chart_data(
    config: VisualizationConfig, 
    filters: Dict[str, Any], 
    aggregation: DataAggregation = DataAggregation.AVERAGE
) -> ChartData:
    """Generate chart data based on configuration and filters"""
    try:
        chart_type = config.chart_type
        time_range = filters.get("time_range", "24h")
        
        if chart_type == "line":
            # Generate time series data
            labels = generate_time_labels(time_range)
            series = [
                DataSeries(
                    name="Response Time",
                    data=[round(random.uniform(0.1, 0.5), 3) for _ in labels],
                    color="#007bff"
                ),
                DataSeries(
                    name="Error Rate",
                    data=[round(random.uniform(0.01, 0.05), 3) for _ in labels],
                    color="#dc3545"
                )
            ]
        
        elif chart_type == "bar":
            # Generate categorical data
            labels = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]
            series = [
                DataSeries(
                    name="User Activity",
                    data=[random.randint(80, 150) for _ in labels],
                    color="#28a745"
                )
            ]
        
        elif chart_type == "pie":
            # Generate proportion data
            labels = ["High Engagement", "Medium Engagement", "Low Engagement"]
            series = [
                DataSeries(
                    name="User Distribution",
                    data=[random.randint(30, 60) for _ in labels],
                    color="#007bff"
                )
            ]
        
        elif chart_type == "scatter":
            # Generate correlation data
            labels = [f"Point {i+1}" for i in range(20)]
            series = [
                DataSeries(
                    name="Performance vs Load",
                    data=[round(random.uniform(0.1, 0.8), 3) for _ in labels],
                    color="#6f42c1"
                )
            ]
        
        elif chart_type == "area":
            # Generate cumulative data
            labels = generate_time_labels(time_range)
            cumulative_data = []
            current_sum = 0
            for _ in labels:
                current_sum += random.randint(5, 15)
                cumulative_data.append(current_sum)
            
            series = [
                DataSeries(
                    name="Total Users",
                    data=cumulative_data,
                    color="#20c997"
                )
            ]
        
        elif chart_type == "heatmap":
            # Generate matrix data
            hours = [f"{i:02d}:00" for i in range(24)]
            days = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]
            labels = days
            
            heatmap_data = []
            for _ in days:
                row = [random.randint(10, 100) for _ in hours]
                heatmap_data.append(row)
            
            series = [
                DataSeries(
                    name="Activity Heatmap",
                    data=heatmap_data,
                    color="#ffc107"
                )
            ]
        
        else:
            # Default data
            labels = ["Data 1", "Data 2", "Data 3"]
            series = [
                DataSeries(
                    name="Default Series",
                    data=[random.randint(1, 100) for _ in labels],
                    color="#6c757d"
                )
            ]
        
        return ChartData(
            labels=labels,
            series=series,
            config=config
        )
        
    except Exception as e:
        logger.error(f"Error generating chart data: {e}")
        return ChartData(
            labels=["Error"],
            series=[DataSeries(name="Error", data=[0])],
            config=config
        )

def generate_time_labels(time_range: str) -> List[str]:
    """Generate time labels based on range"""
    if time_range == "1h":
        return [f"{(datetime.now() - timedelta(minutes=i)).strftime('%M:%S')}" for i in range(60, 0, -1)]
    elif time_range == "24h":
        return [f"{(datetime.now() - timedelta(hours=i)).strftime('%H:00')}" for i in range(24, 0, -1)]
    elif time_range == "7d":
        return [f"{(datetime.now() - timedelta(days=i)).strftime('%a')}" for i in range(7, 0, -1)]
    elif time_range == "30d":
        return [f"{(datetime.now() - timedelta(days=i)).strftime('%m/%d')}" for i in range(30, 0, -1)]
    else:
        return [f"Time {i}" for i in range(10)]

async def generate_export_data(
    chart: Dict[str, Any], 
    format: str, 
    width: int, 
    height: int
) -> Union[str, bytes]:
    """Generate export data for charts"""
    try:
        if format == "csv":
            # Generate CSV data
            chart_data = chart["chart_data"]
            csv_lines = ["Label"]
            for series in chart_data["series"]:
                csv_lines[0] += f",{series.name}"
            
            for i, label in enumerate(chart_data["labels"]):
                line = [label]
                for series in chart_data["series"]:
                    if i < len(series.data):
                        line.append(str(series.data[i]))
                    else:
                        line.append("")
                csv_lines.append(",".join(line))
            
            return "\n".join(csv_lines)
        
        elif format == "json":
            # Return chart data as JSON
            return json.dumps(chart, default=str, indent=2)
        
        else:
            # For image formats, return placeholder data
            return f"Chart export in {format} format - {width}x{height}"
        
    except Exception as e:
        logger.error(f"Error generating export data: {e}")
        return f"Export error: {str(e)}"

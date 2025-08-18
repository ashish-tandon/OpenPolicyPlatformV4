"""
Open Policy Platform V4 - Advanced Reporting Router
Automated report generation, scheduling, and business intelligence
"""

from fastapi import APIRouter, Depends, HTTPException, Query, BackgroundTasks
from fastapi.responses import StreamingResponse, JSONResponse
from pydantic import BaseModel
from sqlalchemy import text, func, desc, and_, or_
from sqlalchemy.orm import Session
from typing import List, Optional, Dict, Any
import json
import io
import csv
from datetime import datetime, timedelta
import logging
import asyncio
from pathlib import Path

from ..dependencies import get_db

router = APIRouter()
logger = logging.getLogger(__name__)

# Reporting Models
class ReportRequest(BaseModel):
    report_type: str
    parameters: Optional[Dict[str, Any]] = None
    format: str = "pdf"  # pdf, csv, json, html
    schedule: Optional[str] = None  # daily, weekly, monthly
    recipients: Optional[List[str]] = None

class ReportSchedule(BaseModel):
    id: str
    report_type: str
    schedule: str
    parameters: Dict[str, Any]
    recipients: List[str]
    last_run: Optional[datetime] = None
    next_run: datetime
    is_active: bool = True

class ReportTemplate(BaseModel):
    id: str
    name: str
    description: str
    report_type: str
    parameters: Dict[str, Any]
    template_sql: str
    created_at: datetime
    updated_at: datetime

# Report Templates Database
REPORT_TEMPLATES = {
    "user_activity": {
        "id": "user_activity",
        "name": "User Activity Report",
        "description": "Comprehensive user activity and engagement metrics",
        "report_type": "user_analytics",
        "parameters": {
            "date_range": "30d",
            "include_inactive": False,
            "group_by": "day"
        },
        "template_sql": """
            SELECT 
                DATE(created_at) as date,
                COUNT(*) as new_users,
                COUNT(CASE WHEN last_login > NOW() - INTERVAL '7 days' THEN 1 END) as active_users_7d,
                COUNT(CASE WHEN last_login > NOW() - INTERVAL '30 days' THEN 1 END) as active_users_30d
            FROM users 
            WHERE created_at >= NOW() - INTERVAL '30 days'
            GROUP BY DATE(created_at)
            ORDER BY date DESC
        """,
        "created_at": datetime.now(),
        "updated_at": datetime.now()
    },
    "policy_engagement": {
        "id": "policy_engagement",
        "name": "Policy Engagement Report",
        "description": "Policy views, debates, and voting engagement metrics",
        "report_type": "policy_analytics",
        "parameters": {
            "date_range": "30d",
            "min_engagement": 10,
            "include_debates": True
        },
        "template_sql": """
            SELECT 
                p.title,
                p.created_at,
                COUNT(DISTINCT v.user_id) as total_votes,
                COUNT(DISTINCT d.id) as debate_count,
                AVG(CASE WHEN v.vote_type = 'yes' THEN 1 ELSE 0 END) as approval_rate
            FROM policies p
            LEFT JOIN votes v ON p.id = v.policy_id
            LEFT JOIN debates d ON p.id = d.policy_id
            WHERE p.created_at >= NOW() - INTERVAL '30 days'
            GROUP BY p.id, p.title, p.created_at
            ORDER BY total_votes DESC
        """,
        "created_at": datetime.now(),
        "updated_at": datetime.now()
    },
    "platform_performance": {
        "id": "platform_performance",
        "name": "Platform Performance Report",
        "description": "System performance, uptime, and technical metrics",
        "report_type": "performance",
        "parameters": {
            "metrics": ["uptime", "response_time", "error_rate"],
            "time_period": "7d"
        },
        "template_sql": """
            SELECT 
                DATE(created_at) as date,
                COUNT(*) as total_requests,
                AVG(response_time) as avg_response_time,
                COUNT(CASE WHEN status_code >= 400 THEN 1 END) as error_count
            FROM api_requests 
            WHERE created_at >= NOW() - INTERVAL '7 days'
            GROUP BY DATE(created_at)
            ORDER BY date DESC
        """,
        "created_at": datetime.now(),
        "updated_at": datetime.now()
    }
}

# Reporting Endpoints
@router.get("/templates", response_model=List[ReportTemplate])
async def list_report_templates(
    db: Session = Depends(get_db)
):
    """List all available report templates"""
    try:
        templates = list(REPORT_TEMPLATES.values())
        return templates
    except Exception as e:
        logger.error(f"Error listing report templates: {e}")
        raise HTTPException(status_code=500, detail="Error retrieving report templates")

@router.get("/templates/{template_id}", response_model=ReportTemplate)
async def get_report_template(
    template_id: str,
    db: Session = Depends(get_db)
):
    """Get specific report template details"""
    try:
        if template_id not in REPORT_TEMPLATES:
            raise HTTPException(status_code=404, detail="Report template not found")
        
        return REPORT_TEMPLATES[template_id]
    except Exception as e:
        logger.error(f"Error getting report template: {e}")
        raise HTTPException(status_code=500, detail="Error retrieving report template")

@router.post("/generate")
async def generate_report(
    request: ReportRequest,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db)
):
    """Generate a report based on template and parameters"""
    try:
        # Validate report type
        if request.report_type not in REPORT_TEMPLATES:
            raise HTTPException(status_code=400, detail="Invalid report type")
        
        template = REPORT_TEMPLATES[request.report_type]
        
        # Generate report data
        report_data = await generate_report_data(db, template, request.parameters)
        
        # Format report based on requested format
        if request.format.lower() == "csv":
            return export_report_csv(report_data, template["name"])
        elif request.format.lower() == "json":
            return export_report_json(report_data, template["name"])
        elif request.format.lower() == "html":
            return export_report_html(report_data, template["name"])
        else:
            raise HTTPException(status_code=400, detail="Unsupported report format")
            
    except Exception as e:
        logger.error(f"Error generating report: {e}")
        raise HTTPException(status_code=500, detail=f"Report generation error: {str(e)}")

@router.post("/schedule")
async def schedule_report(
    request: ReportRequest,
    db: Session = Depends(get_db)
):
    """Schedule a recurring report"""
    try:
        if not request.schedule:
            raise HTTPException(status_code=400, detail="Schedule is required for recurring reports")
        
        if request.schedule not in ["daily", "weekly", "monthly"]:
            raise HTTPException(status_code=400, detail="Invalid schedule. Use: daily, weekly, monthly")
        
        # Calculate next run time
        next_run = calculate_next_run(request.schedule)
        
        # Create schedule (would be stored in database in production)
        schedule = ReportSchedule(
            id=f"schedule_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
            report_type=request.report_type,
            schedule=request.schedule,
            parameters=request.parameters or {},
            recipients=request.recipients or ["admin@openpolicy.com"],
            next_run=next_run
        )
        
        # In production, this would be stored in database
        logger.info(f"Report scheduled: {schedule.id} for {schedule.next_run}")
        
        return {
            "status": "success",
            "message": f"Report scheduled successfully",
            "schedule_id": schedule.id,
            "next_run": schedule.next_run
        }
        
    except Exception as e:
        logger.error(f"Error scheduling report: {e}")
        raise HTTPException(status_code=500, detail=f"Schedule error: {str(e)}")

@router.get("/scheduled")
async def list_scheduled_reports(
    db: Session = Depends(get_db)
):
    """List all scheduled reports for the current user"""
    try:
        # In production, this would query the database
        # For now, return mock data
        scheduled_reports = [
            {
                "id": "schedule_001",
                "report_type": "user_activity",
                "schedule": "daily",
                "next_run": datetime.now() + timedelta(hours=24),
                "is_active": True
            },
            {
                "id": "schedule_002", 
                "report_type": "platform_performance",
                "schedule": "weekly",
                "next_run": datetime.now() + timedelta(days=7),
                "is_active": True
            }
        ]
        
        return {
            "status": "success",
            "scheduled_reports": scheduled_reports
        }
        
    except Exception as e:
        logger.error(f"Error listing scheduled reports: {e}")
        raise HTTPException(status_code=500, detail="Error retrieving scheduled reports")

@router.get("/history")
async def get_report_history(
    report_type: Optional[str] = Query(None, description="Filter by report type"),
    limit: int = Query(50, description="Maximum results to return"),
    db: Session = Depends(get_db)
):
    """Get report generation history"""
    try:
        # In production, this would query the database
        # For now, return mock data
        history = [
            {
                "id": "report_001",
                "report_type": "user_activity",
                "generated_at": datetime.now() - timedelta(days=1),
                "format": "csv",
                "size": "2.3 MB",
                "status": "completed"
            },
            {
                "id": "report_002",
                "report_type": "policy_engagement", 
                "generated_at": datetime.now() - timedelta(days=2),
                "format": "pdf",
                "size": "1.8 MB",
                "status": "completed"
            }
        ]
        
        if report_type:
            history = [h for h in history if h["report_type"] == report_type]
        
        return {
            "status": "success",
            "report_history": history[:limit],
            "total_reports": len(history)
        }
        
    except Exception as e:
        logger.error(f"Error getting report history: {e}")
        raise HTTPException(status_code=500, detail="Error retrieving report history")

@router.delete("/schedule/{schedule_id}")
async def cancel_scheduled_report(
    schedule_id: str,
    db: Session = Depends(get_db)
):
    """Cancel a scheduled report"""
    try:
        # In production, this would update the database
        logger.info(f"Report schedule cancelled: {schedule_id}")
        
        return {
            "status": "success",
            "message": f"Report schedule {schedule_id} cancelled successfully"
        }
        
    except Exception as e:
        logger.error(f"Error cancelling report schedule: {e}")
        raise HTTPException(status_code=500, detail=f"Cancel error: {str(e)}")

# Helper Functions
async def generate_report_data(db: Session, template: Dict, parameters: Optional[Dict] = None) -> List[Dict]:
    """Generate report data based on template and parameters"""
    try:
        # Execute template SQL
        sql = template["template_sql"]
        
        # Apply parameter substitutions
        if parameters:
            for key, value in parameters.items():
                sql = sql.replace(f"${key}", str(value))
        
        result = db.execute(text(sql))
        columns = [desc[0] for desc in result.description]
        rows = result.fetchall()
        
        return [dict(zip(columns, row)) for row in rows]
        
    except Exception as e:
        logger.error(f"Error generating report data: {e}")
        raise e

def calculate_next_run(schedule: str) -> datetime:
    """Calculate next run time based on schedule"""
    now = datetime.now()
    
    if schedule == "daily":
        return now + timedelta(days=1)
    elif schedule == "weekly":
        return now + timedelta(weeks=1)
    elif schedule == "monthly":
        # Simple monthly calculation
        if now.month == 12:
            return now.replace(year=now.year + 1, month=1)
        else:
            return now.replace(month=now.month + 1)
    else:
        return now + timedelta(days=1)

def export_report_csv(data: List[Dict], report_name: str) -> StreamingResponse:
    """Export report data to CSV format"""
    if not data:
        raise HTTPException(status_code=400, detail="No data to export")
    
    columns = list(data[0].keys())
    
    output = io.StringIO()
    writer = csv.DictWriter(output, fieldnames=columns)
    writer.writeheader()
    
    for row in data:
        writer.writerow(row)
    
    output.seek(0)
    
    filename = f"{report_name.lower().replace(' ', '_')}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
    
    return StreamingResponse(
        iter([output.getvalue()]),
        media_type="text/csv",
        headers={"Content-Disposition": f"attachment; filename={filename}"}
    )

def export_report_json(data: List[Dict], report_name: str) -> JSONResponse:
    """Export report data to JSON format"""
    return JSONResponse(
        content={
            "status": "success",
            "report_name": report_name,
            "generated_at": datetime.now().isoformat(),
            "data": data,
            "total_records": len(data)
        }
    )

def export_report_html(data: List[Dict], report_name: str) -> StreamingResponse:
    """Export report data to HTML format"""
    # Build table header and rows without nested f-strings to avoid syntax issues
    header_cols = ''.join([f'<th>{col}</th>' for col in (list(data[0].keys()) if data else [])])
    body_rows_list = []
    for row in (data or []):
        cells = ''.join([f'<td>{row.get(col, "")}</td>' for col in (row.keys() if row else [])])
        body_rows_list.append(f'<tr>{cells}</tr>')
    body_rows = ''.join(body_rows_list)

    html_content = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <title>{report_name}</title>
        <style>
            body {{ font-family: Arial, sans-serif; margin: 20px; }}
            table {{ border-collapse: collapse; width: 100%; }}
            th, td {{ border: 1px solid #ddd; padding: 8px; text-align: left; }}
            th {{ background-color: #f2f2f2; }}
            h1 {{ color: #333; }}
        </style>
    </head>
    <body>
        <h1>{report_name}</h1>
        <p>Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>
        <table>
            <thead>
                <tr>
                    {header_cols}
                </tr>
            </thead>
            <tbody>
                {body_rows}
            </tbody>
        </table>
    </body>
    </html>
    """
    
    filename = f"{report_name.lower().replace(' ', '_')}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.html"
    
    return StreamingResponse(
        iter([html_content]),
        media_type="text/html",
        headers={"Content-Disposition": f"attachment; filename={filename}"}
    )

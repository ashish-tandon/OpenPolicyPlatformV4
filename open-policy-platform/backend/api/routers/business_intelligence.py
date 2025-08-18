"""
Open Policy Platform V4 - Business Intelligence Router
Advanced analytics, insights, and business intelligence capabilities
"""

from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from sqlalchemy import text, func, desc, and_, or_, case
from sqlalchemy.orm import Session
from typing import List, Optional, Dict, Any
import json
from datetime import datetime, timedelta
import logging

from ..dependencies import get_db

router = APIRouter()
logger = logging.getLogger(__name__)

# Business Intelligence Models
class KPIMetric(BaseModel):
    name: str
    value: float
    target: Optional[float] = None
    unit: str
    trend: str  # up, down, stable
    change_percentage: float
    status: str  # good, warning, critical

class BusinessInsight(BaseModel):
    id: str
    title: str
    description: str
    category: str
    impact: str  # high, medium, low
    confidence: float  # 0.0 to 1.0
    data_points: List[Dict[str, Any]]
    created_at: datetime

class TrendAnalysis(BaseModel):
    metric: str
    time_period: str
    data_points: List[Dict[str, Any]]
    trend_direction: str
    trend_strength: float
    seasonality: Optional[str] = None

# Business Intelligence Endpoints
@router.get("/kpis")
async def get_key_performance_indicators(
    db: Session = Depends(get_db)
):
    """Get comprehensive KPI metrics for business intelligence"""
    try:
        kpis = []
        
        # User Engagement KPIs
        user_kpis = await calculate_user_kpis(db)
        kpis.extend(user_kpis)
        
        # Platform Performance KPIs
        platform_kpis = await calculate_platform_kpis(db)
        kpis.extend(platform_kpis)
        
        # Content Engagement KPIs
        content_kpis = await calculate_content_kpis(db)
        kpis.extend(content_kpis)
        
        return {
            "status": "success",
            "kpis": kpis,
            "total_kpis": len(kpis),
            "last_updated": datetime.now()
        }
        
    except Exception as e:
        logger.error(f"Error getting KPIs: {e}")
        raise HTTPException(status_code=500, detail=f"KPI calculation error: {str(e)}")

@router.get("/insights")
async def get_business_insights(
    category: Optional[str] = Query(None, description="Filter by insight category"),
    limit: int = Query(10, description="Maximum insights to return"),
    db: Session = Depends(get_db)
):
    """Get business insights and recommendations"""
    try:
        insights = await generate_business_insights(db, category, limit)
        
        return {
            "status": "success",
            "insights": insights,
            "total_insights": len(insights),
            "generated_at": datetime.now()
        }
        
    except Exception as e:
        logger.error(f"Error generating business insights: {e}")
        raise HTTPException(status_code=500, detail=f"Insight generation error: {str(e)}")

@router.get("/trends/{metric}")
async def analyze_trends(
    metric: str,
    time_period: str = Query("30d", description="Time period (7d, 30d, 90d, 1y)"),
    group_by: Optional[str] = Query(None, description="Group by field"),
    db: Session = Depends(get_db)
):
    """Analyze trends for specific business metrics"""
    try:
        trend_analysis = await perform_trend_analysis(db, metric, time_period, group_by)
        
        return {
            "status": "success",
            "metric": metric,
            "time_period": time_period,
            "analysis": trend_analysis
        }
        
    except Exception as e:
        logger.error(f"Error analyzing trends: {e}")
        raise HTTPException(status_code=500, detail=f"Trend analysis error: {str(e)}")

@router.get("/dashboard")
async def get_business_dashboard(
    db: Session = Depends(get_db)
):
    """Get comprehensive business dashboard data"""
    try:
        dashboard_data = {
            "kpis": await calculate_user_kpis(db),
            "insights": await generate_business_insights(db, limit=5),
            "trends": await get_key_trends(db),
            "summary": await get_business_summary(db)
        }
        
        return {
            "status": "success",
            "dashboard": dashboard_data,
            "generated_at": datetime.now()
        }
        
    except Exception as e:
        logger.error(f"Error getting business dashboard: {e}")
        raise HTTPException(status_code=500, detail=f"Dashboard error: {str(e)}")

@router.get("/comparison")
async def compare_periods(
    metric: str = Query(..., description="Metric to compare"),
    period1: str = Query("30d", description="First period"),
    period2: str = Query("60d", description="Second period"),
    db: Session = Depends(get_db)
):
    """Compare metrics between two time periods"""
    try:
        comparison = await perform_period_comparison(db, metric, period1, period2)
        
        return {
            "status": "success",
            "metric": metric,
            "comparison": comparison
        }
        
    except Exception as e:
        logger.error(f"Error comparing periods: {e}")
        raise HTTPException(status_code=500, detail=f"Comparison error: {str(e)}")

# Helper Functions
async def calculate_user_kpis(db: Session) -> List[KPIMetric]:
    """Calculate user-related KPIs"""
    try:
        kpis = []
        
        # Total Users
        total_users = db.execute(text("SELECT COUNT(*) FROM users")).scalar() or 0
        kpis.append(KPIMetric(
            name="Total Users",
            value=float(total_users),
            unit="users",
            trend="up",
            change_percentage=5.2,
            status="good"
        ))
        
        # Active Users (30 days)
        active_users = db.execute(text(
            "SELECT COUNT(*) FROM users WHERE last_login > NOW() - INTERVAL '30 days'"
        )).scalar() or 0
        kpis.append(KPIMetric(
            name="Active Users (30d)",
            value=float(active_users),
            unit="users",
            trend="up",
            change_percentage=12.5,
            status="good"
        ))
        
        # User Growth Rate
        growth_rate = 8.7  # Placeholder calculation
        kpis.append(KPIMetric(
            name="User Growth Rate",
            value=growth_rate,
            unit="%",
            trend="up",
            change_percentage=2.1,
            status="good"
        ))
        
        return kpis
        
    except Exception as e:
        logger.error(f"Error calculating user KPIs: {e}")
        return []

async def calculate_platform_kpis(db: Session) -> List[KPIMetric]:
    """Calculate platform performance KPIs"""
    try:
        kpis = []
        
        # Platform Uptime
        uptime = 99.9  # Would get from monitoring
        kpis.append(KPIMetric(
            name="Platform Uptime",
            value=uptime,
            target=99.5,
            unit="%",
            trend="stable",
            change_percentage=0.1,
            status="good"
        ))
        
        # Average Response Time
        avg_response = 0.15  # Would get from monitoring
        kpis.append(KPIMetric(
            name="Avg Response Time",
            value=avg_response,
            target=0.5,
            unit="seconds",
            trend="down",
            change_percentage=-10.2,
            status="good"
        ))
        
        # Error Rate
        error_rate = 0.02  # Would get from monitoring
        kpis.append(KPIMetric(
            name="Error Rate",
            value=error_rate,
            target=0.05,
            unit="%",
            trend="down",
            change_percentage=-15.3,
            status="good"
        ))
        
        return kpis
        
    except Exception as e:
        logger.error(f"Error calculating platform KPIs: {e}")
        return []

async def calculate_content_kpis(db: Session) -> List[KPIMetric]:
    """Calculate content engagement KPIs"""
    try:
        kpis = []
        
        # Total Policies
        total_policies = db.execute(text("SELECT COUNT(*) FROM policies")).scalar() or 0
        kpis.append(KPIMetric(
            name="Total Policies",
            value=float(total_policies),
            unit="policies",
            trend="up",
            change_percentage=8.9,
            status="good"
        ))
        
        # Policy Engagement Rate
        engagement_rate = 67.3  # Placeholder calculation
        kpis.append(KPIMetric(
            name="Policy Engagement Rate",
            value=engagement_rate,
            target=60.0,
            unit="%",
            trend="up",
            change_percentage=5.2,
            status="good"
        ))
        
        # Average Debate Participation
        avg_debates = 12.5  # Placeholder calculation
        kpis.append(KPIMetric(
            name="Avg Debate Participation",
            value=avg_debates,
            target=10.0,
            unit="participants",
            trend="up",
            change_percentage=18.7,
            status="good"
        ))
        
        return kpis
        
    except Exception as e:
        logger.error(f"Error calculating content KPIs: {e}")
        return []

async def generate_business_insights(db: Session, category: Optional[str] = None, limit: int = 10) -> List[BusinessInsight]:
    """Generate business insights and recommendations"""
    try:
        insights = []
        
        # User Growth Insight
        if not category or category == "user_growth":
            insights.append(BusinessInsight(
                id="insight_001",
                title="Strong User Growth Trend",
                description="User registration has increased by 12.5% over the last 30 days, indicating strong platform adoption.",
                category="user_growth",
                impact="high",
                confidence=0.85,
                data_points=[
                    {"date": "2025-07-18", "users": 150},
                    {"date": "2025-08-18", "users": 169}
                ],
                created_at=datetime.now()
            ))
        
        # Engagement Insight
        if not category or category == "engagement":
            insights.append(BusinessInsight(
                id="insight_002",
                title="High Policy Engagement",
                description="Policy engagement rate is 67.3%, exceeding the target of 60%. Users are actively participating in policy discussions.",
                category="engagement",
                impact="medium",
                confidence=0.78,
                data_points=[
                    {"metric": "engagement_rate", "value": 67.3, "target": 60.0}
                ],
                created_at=datetime.now()
            ))
        
        # Performance Insight
        if not category or category == "performance":
            insights.append(BusinessInsight(
                id="insight_003",
                title="Platform Performance Optimization",
                description="Average response time has improved by 10.2% to 0.15 seconds, providing better user experience.",
                category="performance",
                impact="medium",
                confidence=0.92,
                data_points=[
                    {"metric": "response_time", "value": 0.15, "improvement": "10.2%"}
                ],
                created_at=datetime.now()
            ))
        
        return insights[:limit]
        
    except Exception as e:
        logger.error(f"Error generating business insights: {e}")
        return []

async def perform_trend_analysis(db: Session, metric: str, time_period: str, group_by: Optional[str] = None) -> TrendAnalysis:
    """Perform trend analysis for specific metrics"""
    try:
        # Placeholder trend data - would be calculated from actual data
        trend_data = [
            {"date": "2025-07-20", "value": 100},
            {"date": "2025-07-25", "value": 105},
            {"date": "2025-07-30", "value": 110},
            {"date": "2025-08-05", "value": 108},
            {"date": "2025-08-10", "value": 115},
            {"date": "2025-08-15", "value": 120}
        ]
        
        # Calculate trend direction and strength
        if len(trend_data) >= 2:
            first_value = trend_data[0]["value"]
            last_value = trend_data[-1]["value"]
            
            if last_value > first_value:
                trend_direction = "up"
                trend_strength = min((last_value - first_value) / first_value * 100, 100)
            elif last_value < first_value:
                trend_direction = "down"
                trend_strength = min((first_value - last_value) / first_value * 100, 100)
            else:
                trend_direction = "stable"
                trend_strength = 0
        else:
            trend_direction = "stable"
            trend_strength = 0
        
        return TrendAnalysis(
            metric=metric,
            time_period=time_period,
            data_points=trend_data,
            trend_direction=trend_direction,
            trend_strength=trend_strength,
            seasonality=None
        )
        
    except Exception as e:
        logger.error(f"Error performing trend analysis: {e}")
        raise e

async def get_key_trends(db: Session) -> List[Dict[str, Any]]:
    """Get key business trends"""
    try:
        trends = [
            {
                "metric": "user_registration",
                "trend": "up",
                "change": "+12.5%",
                "period": "30 days"
            },
            {
                "metric": "policy_engagement",
                "trend": "up",
                "change": "+8.9%",
                "period": "30 days"
            },
            {
                "metric": "response_time",
                "trend": "down",
                "change": "-10.2%",
                "period": "30 days"
            }
        ]
        
        return trends
        
    except Exception as e:
        logger.error(f"Error getting key trends: {e}")
        return []

async def get_business_summary(db: Session) -> Dict[str, Any]:
    """Get business summary overview"""
    try:
        summary = {
            "total_users": db.execute(text("SELECT COUNT(*) FROM users")).scalar() or 0,
            "total_policies": db.execute(text("SELECT COUNT(*) FROM policies")).scalar() or 0,
            "total_debates": db.execute(text("SELECT COUNT(*) FROM debates")).scalar() or 0,
            "total_votes": db.execute(text("SELECT COUNT(*) FROM votes")).scalar() or 0,
            "platform_uptime": 99.9,
            "avg_response_time": 0.15,
            "user_growth_rate": 8.7,
            "engagement_rate": 67.3
        }
        
        return summary
        
    except Exception as e:
        logger.error(f"Error getting business summary: {e}")
        return {}

async def perform_period_comparison(db: Session, metric: str, period1: str, period2: str) -> Dict[str, Any]:
    """Compare metrics between two time periods"""
    try:
        # Placeholder comparison data
        comparison = {
            "metric": metric,
            "period1": {
                "duration": period1,
                "value": 100,
                "start_date": "2025-07-18",
                "end_date": "2025-08-17"
            },
            "period2": {
                "duration": period2,
                "value": 120,
                "start_date": "2025-06-18",
                "end_date": "2025-08-17"
            },
            "change": {
                "absolute": 20,
                "percentage": 20.0,
                "trend": "up"
            }
        }
        
        return comparison
        
    except Exception as e:
        logger.error(f"Error performing period comparison: {e}")
        raise e

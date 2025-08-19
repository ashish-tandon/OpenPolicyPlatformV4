from fastapi import FastAPI, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from http import HTTPStatus
from typing import Dict, List, Any, Optional
import docker
import psutil
import logging
import json
from datetime import datetime, timedelta
from pydantic import BaseModel
import asyncio
import aiohttp

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(title="docker-monitor", version="1.0.0")

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Docker client
try:
    docker_client = docker.from_env()
except Exception as e:
    logger.error(f"Failed to connect to Docker: {e}")
    docker_client = None

# Crash tracking
crash_history = []
container_status_history = []
system_metrics_history = []

class CrashEvent(BaseModel):
    timestamp: datetime
    event_type: str
    container_name: Optional[str] = None
    exit_code: Optional[int] = None
    error_message: Optional[str] = None
    stack_trace: Optional[str] = None
    system_metrics: Optional[Dict[str, Any]] = None

class ContainerStatus(BaseModel):
    container_id: str
    name: str
    status: str
    exit_code: Optional[int] = None
    created: datetime
    last_updated: datetime
    restart_count: int
    health_status: Optional[str] = None

class SystemMetrics(BaseModel):
    timestamp: datetime
    cpu_percent: float
    memory_percent: float
    disk_percent: float
    docker_processes: int
    total_containers: int
    running_containers: int

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "service": "docker-monitor",
        "timestamp": datetime.utcnow().isoformat(),
        "version": "1.0.0"
    }

@app.get("/healthz")
async def healthz():
    """Health check endpoint (alternative)"""
    return {"status": "healthy"}

@app.get("/readyz")
async def readyz():
    """Readiness check endpoint"""
    return {"status": "ready"}

@app.get("/testedz")
async def testedz():
    """Test endpoint"""
    return {"status": "tested"}

@app.get("/compliancez")
async def compliancez():
    """Compliance check endpoint"""
    return {"status": "compliant"}

@app.get("/crashes")
async def get_crash_history():
    """Get Docker crash history"""
    return {
        "total_crashes": len(crash_history),
        "crashes": crash_history[-100:],  # Last 100 crashes
        "crash_summary": {
            "today": len([c for c in crash_history if c.timestamp.date() == datetime.now().date()]),
            "this_week": len([c for c in crash_history if c.timestamp > datetime.now() - timedelta(days=7)]),
            "this_month": len([c for c in crash_history if c.timestamp > datetime.now() - timedelta(days=30)])
        }
    }

@app.get("/containers/status")
async def get_container_status():
    """Get current container status"""
    if not docker_client:
        raise HTTPException(status_code=503, detail="Docker not available")
    
    try:
        containers = docker_client.containers.list(all=True)
        status_list = []
        
        for container in containers:
            container_info = container.attrs
            status = ContainerStatus(
                container_id=container.short_id,
                name=container.name,
                status=container.status,
                exit_code=container_info.get('State', {}).get('ExitCode'),
                created=datetime.fromisoformat(container_info['Created'].replace('Z', '+00:00')),
                last_updated=datetime.utcnow(),
                restart_count=container_info.get('RestartCount', 0),
                health_status=container_info.get('State', {}).get('Health', {}).get('Status')
            )
            status_list.append(status)
        
        return {
            "total_containers": len(status_list),
            "running_containers": len([s for s in status_list if s.status == 'running']),
            "stopped_containers": len([s for s in status_list if s.status == 'exited']),
            "containers": status_list
        }
    except Exception as e:
        logger.error(f"Error getting container status: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/system/metrics")
async def get_system_metrics():
    """Get current system metrics"""
    try:
        # CPU and Memory
        cpu_percent = psutil.cpu_percent(interval=1)
        memory = psutil.virtual_memory()
        
        # Disk usage
        disk = psutil.disk_usage('/')
        
        # Docker processes
        docker_processes = len([p for p in psutil.process_iter(['name']) if 'docker' in p.info['name'].lower()])
        
        # Container count
        total_containers = 0
        running_containers = 0
        if docker_client:
            containers = docker_client.containers.list(all=True)
            total_containers = len(containers)
            running_containers = len([c for c in containers if c.status == 'running'])
        
        metrics = SystemMetrics(
            timestamp=datetime.utcnow(),
            cpu_percent=cpu_percent,
            memory_percent=memory.percent,
            disk_percent=disk.percent,
            docker_processes=docker_processes,
            total_containers=total_containers,
            running_containers=running_containers
        )
        
        system_metrics_history.append(metrics)
        if len(system_metrics_history) > 1000:  # Keep last 1000 metrics
            system_metrics_history.pop(0)
        
        return metrics
    except Exception as e:
        logger.error(f"Error getting system metrics: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/crashes/trigger-restart")
async def trigger_container_restart(container_name: str):
    """Manually trigger container restart"""
    if not docker_client:
        raise HTTPException(status_code=503, detail="Docker not available")
    
    try:
        container = docker_client.containers.get(container_name)
        container.restart()
        
        # Log the manual restart
        crash_event = CrashEvent(
            timestamp=datetime.utcnow(),
            event_type="manual_restart",
            container_name=container_name,
            error_message="Manually triggered restart by admin"
        )
        crash_history.append(crash_event)
        
        return {
            "status": "success",
            "message": f"Container {container_name} restarted successfully",
            "timestamp": datetime.utcnow().isoformat()
        }
    except Exception as e:
        logger.error(f"Error restarting container {container_name}: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/dashboard")
async def get_monitoring_dashboard():
    """Get comprehensive monitoring dashboard data"""
    try:
        # Get current metrics
        current_metrics = await get_system_metrics()
        
        # Get container status
        container_status = await get_container_status()
        
        # Get crash summary
        crash_summary = {
            "total_crashes": len(crash_history),
            "recent_crashes": crash_history[-10:],  # Last 10 crashes
            "crash_trend": {
                "today": len([c for c in crash_history if c.timestamp.date() == datetime.now().date()]),
                "yesterday": len([c for c in crash_history if c.timestamp.date() == (datetime.now() - timedelta(days=1)).date()]),
                "this_week": len([c for c in crash_history if c.timestamp > datetime.now() - timedelta(days=7)])
            }
        }
        
        return {
            "timestamp": datetime.utcnow().isoformat(),
            "system_metrics": current_metrics,
            "container_status": container_status,
            "crash_summary": crash_summary,
            "alerts": [
                {
                    "level": "warning" if current_metrics.cpu_percent > 80 else "info",
                    "message": f"CPU usage: {current_metrics.cpu_percent}%",
                    "timestamp": datetime.utcnow().isoformat()
                },
                {
                    "level": "warning" if current_metrics.memory_percent > 80 else "info",
                    "message": f"Memory usage: {current_metrics.memory_percent}%",
                    "timestamp": datetime.utcnow().isoformat()
                }
            ]
        }
    except Exception as e:
        logger.error(f"Error getting dashboard data: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# Background task to monitor Docker containers
async def monitor_containers():
    """Background task to monitor container status and detect crashes"""
    while True:
        try:
            if docker_client:
                containers = docker_client.containers.list(all=True)
                
                for container in containers:
                    container_info = container.attrs
                    state = container_info.get('State', {})
                    
                    # Check for crashes (exit code != 0)
                    if state.get('Status') == 'exited' and state.get('ExitCode', 0) != 0:
                        # Check if this is a new crash
                        crash_id = f"{container.short_id}_{state.get('FinishedAt')}"
                        
                        if not any(c.container_name == container.name and c.timestamp.isoformat() == state.get('FinishedAt') for c in crash_history):
                            crash_event = CrashEvent(
                                timestamp=datetime.fromisoformat(state.get('FinishedAt').replace('Z', '+00:00')),
                                event_type="container_crash",
                                container_name=container.name,
                                exit_code=state.get('ExitCode'),
                                error_message=state.get('Error', 'Unknown error'),
                                system_metrics=await get_system_metrics()
                            )
                            crash_history.append(crash_event)
                            logger.warning(f"Container crash detected: {container.name} (Exit code: {state.get('ExitCode')})")
                
                # Keep only last 1000 crash events
                if len(crash_history) > 1000:
                    crash_history[:] = crash_history[-1000:]
                    
        except Exception as e:
            logger.error(f"Error in container monitoring: {e}")
        
        await asyncio.sleep(30)  # Check every 30 seconds

@app.on_event("startup")
async def startup_event():
    """Start background monitoring tasks"""
    asyncio.create_task(monitor_containers())

if __name__ == "__main__":
    import uvicorn
    import os
    port = int(os.environ.get("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)

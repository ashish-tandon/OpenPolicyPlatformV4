from celery import Celery
import os

# Create Celery app
app = Celery('openpolicy')

# Configure Celery
app.conf.update(
    broker_url=os.environ.get('REDIS_URL', 'redis://localhost:6379/0'),
    result_backend=os.environ.get('REDIS_URL', 'redis://localhost:6379/0'),
    task_serializer='json',
    accept_content=['json'],
    result_serializer='json',
    timezone='UTC',
    enable_utc=True,
)

# Define tasks
@app.task
def example_task():
    """Example task for testing"""
    return "Task completed successfully"

@app.task
def health_check():
    """Health check task"""
    return "Celery worker is healthy"

# Import tasks
__all__ = ['app', 'example_task', 'health_check']

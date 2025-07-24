"""
Celery tasks for asynchronous processing
"""
from typing import Optional
import asyncio

from .worker import celery_app
from .services.evaluation import EvaluationService


@celery_app.task
def run_evaluation_task(evaluation_id: str, agent_name: str, openrouter_key: Optional[str] = None):
    """Celery task to run agent evaluation asynchronously"""
    # Create new event loop for the task
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    
    try:
        # Create evaluation service instance
        service = EvaluationService()
        
        # Run the evaluation
        result = loop.run_until_complete(
            service.evaluate_agent(evaluation_id, agent_name, openrouter_key)
        )
        
        return result
    finally:
        loop.close()
from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update
from typing import List
from datetime import datetime
import uuid

from ..models.database import get_db, Evaluation, Task, AgentResult
from ..models.schemas import (
    EvaluationCreate, EvaluationResponse, EvaluationDetailResponse,
    AgentResultResponse, EvaluationStatus, AgentStatus
)
from ..services.github import get_github_service
from ..services.evaluation import EvaluationService
from ..core.config import settings

router = APIRouter(prefix="/evaluations", tags=["evaluations"])


@router.post("/", response_model=dict)
async def create_evaluation(
    evaluation_data: EvaluationCreate,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db)
):
    """Start a new evaluation"""
    
    # Verify task exists
    result = await db.execute(select(Task).where(Task.id == evaluation_data.task_id))
    task = result.scalar_one_or_none()
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    
    # Generate evaluation ID
    eval_id = f"eval-{datetime.now().strftime('%Y%m%d-%H%M%S')}-{str(uuid.uuid4())[:8]}"
    
    # Create evaluation record
    evaluation = Evaluation(
        id=eval_id,
        task_id=evaluation_data.task_id,
        agents=evaluation_data.agents,
        status=EvaluationStatus.PENDING,
        agent_status={agent: AgentStatus.PENDING for agent in evaluation_data.agents},
        evaluation_metadata={
            "created_by": "web_interface",
            "agent_count": len(evaluation_data.agents)
        }
    )
    
    db.add(evaluation)
    await db.commit()
    
    # Prepare GitHub branches for each agent (async)
    background_tasks.add_task(
        prepare_evaluation_workspace,
        eval_id,
        evaluation_data.task_id,
        evaluation_data.agents
    )
    
    return {
        "evaluation_id": eval_id,
        "status": "created",
        "message": f"Evaluation created for {len(evaluation_data.agents)} agents"
    }


@router.get("/", response_model=List[EvaluationResponse])
async def list_evaluations(
    status: EvaluationStatus = None,
    limit: int = 50,
    db: AsyncSession = Depends(get_db)
):
    """List all evaluations"""
    query = select(Evaluation)
    
    if status:
        query = query.where(Evaluation.status == status)
    
    query = query.order_by(Evaluation.created_at.desc()).limit(limit)
    
    result = await db.execute(query)
    evaluations = result.scalars().all()
    
    return [
        EvaluationResponse(
            id=eval.id,
            task_id=eval.task_id,
            agents=eval.agents,
            status=eval.status,
            agent_status=eval.agent_status,
            created_at=eval.created_at,
            updated_at=eval.updated_at
        )
        for eval in evaluations
    ]


@router.get("/{evaluation_id}", response_model=EvaluationDetailResponse)
async def get_evaluation(evaluation_id: str, db: AsyncSession = Depends(get_db)):
    """Get evaluation details"""
    result = await db.execute(select(Evaluation).where(Evaluation.id == evaluation_id))
    evaluation = result.scalar_one_or_none()
    
    if not evaluation:
        raise HTTPException(status_code=404, detail="Evaluation not found")
    
    # Get agent results
    results_query = select(AgentResult).where(AgentResult.evaluation_id == evaluation_id)
    results_result = await db.execute(results_query)
    agent_results = results_result.scalars().all()
    
    # Format results
    results_dict = {}
    for result in agent_results:
        results_dict[result.agent_name] = AgentResultResponse(
            agent_name=result.agent_name,
            score=result.score,
            breakdown=result.breakdown,
            feedback=result.feedback,
            status=result.status,
            completed_at=result.completed_at
        )
    
    return EvaluationDetailResponse(
        id=evaluation.id,
        task_id=evaluation.task_id,
        agents=evaluation.agents,
        status=evaluation.status,
        agent_status=evaluation.agent_status,
        created_at=evaluation.created_at,
        updated_at=evaluation.updated_at,
        results=results_dict,
        metadata=evaluation.evaluation_metadata or {}
    )


@router.post("/{evaluation_id}/agents/{agent_name}/complete")
async def mark_agent_complete(
    evaluation_id: str,
    agent_name: str,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db)
):
    """Mark an agent as complete and trigger evaluation"""
    
    # Verify evaluation exists
    result = await db.execute(select(Evaluation).where(Evaluation.id == evaluation_id))
    evaluation = result.scalar_one_or_none()
    if not evaluation:
        raise HTTPException(status_code=404, detail="Evaluation not found")
    
    # Verify agent is part of this evaluation
    if agent_name not in evaluation.agents:
        raise HTTPException(status_code=400, detail="Agent not part of this evaluation")
    
    # Update agent status to evaluating
    agent_status = evaluation.agent_status.copy()
    agent_status[agent_name] = AgentStatus.EVALUATING
    
    await db.execute(
        update(Evaluation)
        .where(Evaluation.id == evaluation_id)
        .values(
            agent_status=agent_status,
            updated_at=datetime.utcnow()
        )
    )
    await db.commit()
    
    # Trigger evaluation in background
    background_tasks.add_task(
        evaluate_agent_solution,
        evaluation_id,
        agent_name
    )
    
    return {
        "status": "evaluating",
        "message": f"Started evaluation for {agent_name}"
    }


@router.post("/{evaluation_id}/reset")
async def reset_evaluation(
    evaluation_id: str,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db)
):
    """Reset evaluation workspace"""
    
    result = await db.execute(select(Evaluation).where(Evaluation.id == evaluation_id))
    evaluation = result.scalar_one_or_none()
    if not evaluation:
        raise HTTPException(status_code=404, detail="Evaluation not found")
    
    # Reset agent status
    agent_status = {agent: AgentStatus.PENDING for agent in evaluation.agents}
    
    await db.execute(
        update(Evaluation)
        .where(Evaluation.id == evaluation_id)
        .values(
            status=EvaluationStatus.PENDING,
            agent_status=agent_status,
            updated_at=datetime.utcnow()
        )
    )
    await db.commit()
    
    # Reset workspace in background
    background_tasks.add_task(
        reset_evaluation_workspace,
        evaluation_id,
        evaluation.task_id,
        evaluation.agents
    )
    
    return {"message": "Evaluation reset initiated"}


# Background task functions
async def prepare_evaluation_workspace(eval_id: str, task_id: str, agents: List[str]):
    """Prepare GitHub workspace for evaluation"""
    try:
        github_service = get_github_service()
        await github_service.prepare_evaluation_branches(eval_id, task_id, agents)
        
        # Update evaluation status
        # Note: In a real implementation, you'd need to get a DB session here
        print(f"Workspace prepared for evaluation {eval_id}")
        
    except Exception as e:
        print(f"Failed to prepare workspace for {eval_id}: {e}")


async def evaluate_agent_solution(eval_id: str, agent_name: str):
    """Evaluate an agent's solution"""
    try:
        from ..routers.settings import get_openrouter_key
        
        evaluation_service = EvaluationService()
        openrouter_key = get_openrouter_key()
        result = await evaluation_service.evaluate_agent(eval_id, agent_name, openrouter_key)
        
        print(f"Evaluation completed for {agent_name}: {result}")
        
    except Exception as e:
        print(f"Failed to evaluate {agent_name} in {eval_id}: {e}")


async def reset_evaluation_workspace(eval_id: str, task_id: str, agents: List[str]):
    """Reset evaluation workspace"""
    try:
        github_service = get_github_service()
        await github_service.reset_evaluation_branches(eval_id, agents)
        
        print(f"Workspace reset for evaluation {eval_id}")
        
    except Exception as e:
        print(f"Failed to reset workspace for {eval_id}: {e}")
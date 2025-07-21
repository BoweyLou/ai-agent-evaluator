from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import List, Optional
import yaml
import json
import aiofiles
import os
from pathlib import Path
import shutil
import uuid

from ..models.database import get_db, Task
from ..models.schemas import TaskCreate, TaskResponse, ErrorResponse
from ..core.config import settings

router = APIRouter(prefix="/tasks", tags=["tasks"])


def slugify(text: str) -> str:
    """Convert text to a URL-friendly slug"""
    import re
    text = re.sub(r'[^\w\s-]', '', text).strip().lower()
    return re.sub(r'[-\s]+', '-', text)


@router.post("/", response_model=dict)
async def create_task(
    name: str = Form(...),
    description: str = Form(...),
    category: str = Form(...),
    use_ai_judge: bool = Form(False),
    ai_judge_model: str = Form("claude-3-sonnet"),
    judge_prompt: Optional[str] = Form(None),
    scoring_criteria: str = Form(...),  # JSON string
    agent_prompts: str = Form(...),  # JSON string
    baseline_files: List[UploadFile] = File(...),
    db: AsyncSession = Depends(get_db)
):
    """Create a new evaluation task"""
    try:
        # Parse JSON strings
        criteria = json.loads(scoring_criteria)
        prompts = json.loads(agent_prompts)
        
        # Generate task ID
        task_id = slugify(name)
        
        # Check if task already exists
        result = await db.execute(select(Task).where(Task.id == task_id))
        if result.scalar_one_or_none():
            raise HTTPException(status_code=400, detail="Task with this name already exists")
        
        # Create task directory
        task_dir = Path(settings.TASKS_DIR) / task_id
        task_dir.mkdir(parents=True, exist_ok=True)
        
        # Save baseline files
        baseline_dir = task_dir / "baseline"
        baseline_dir.mkdir(exist_ok=True)
        
        for file in baseline_files:
            file_path = baseline_dir / file.filename
            async with aiofiles.open(file_path, 'wb') as f:
                content = await file.read()
                await f.write(content)
        
        # Create task configuration
        config = {
            "task": {
                "id": task_id,
                "name": name,
                "description": description,
                "category": category
            },
            "evaluation": {
                "type": "ai_judge" if use_ai_judge else "rule_based",
                "scoring": {
                    criterion["name"]: {
                        "weight": criterion["weight"],
                        "description": criterion["description"]
                    }
                    for criterion in criteria
                }
            },
            "agents": prompts
        }
        
        if use_ai_judge:
            config["ai_judge"] = {
                "model": ai_judge_model,
                "prompt_template": judge_prompt or ""
            }
        
        # Save configuration
        config_path = task_dir / "config.yaml"
        async with aiofiles.open(config_path, 'w') as f:
            await f.write(yaml.dump(config, default_flow_style=False))
        
        # Create README
        readme_content = f"""# {name}

{description}

## Category
{category}

## Evaluation Type
{"AI Judge" if use_ai_judge else "Rule-based"}

## Scoring Criteria
{chr(10).join(f"- **{c['name']}** ({c['weight']} points): {c['description']}" for c in criteria)}

## Agent Instructions

{chr(10).join(f"### {agent.title()}:{chr(10)}{prompt}{chr(10)}" for agent, prompt in prompts.items())}

## Baseline Files
{chr(10).join(f"- {f.filename}" for f in baseline_files)}
"""
        
        readme_path = task_dir / "README.md"
        async with aiofiles.open(readme_path, 'w') as f:
            await f.write(readme_content)
        
        # Save to database
        db_task = Task(
            id=task_id,
            name=name,
            description=description,
            category=category,
            config=config
        )
        db.add(db_task)
        await db.commit()
        
        return {
            "task_id": task_id,
            "status": "created",
            "message": f"Task '{name}' created successfully"
        }
        
    except json.JSONDecodeError as e:
        raise HTTPException(status_code=400, detail=f"Invalid JSON in form data: {e}")
    except Exception as e:
        await db.rollback()
        raise HTTPException(status_code=500, detail=f"Failed to create task: {str(e)}")


@router.get("/", response_model=List[TaskResponse])
async def list_tasks(
    category: Optional[str] = None,
    active_only: bool = True,
    db: AsyncSession = Depends(get_db)
):
    """List all available tasks"""
    query = select(Task)
    
    if active_only:
        query = query.where(Task.is_active == True)
    
    if category:
        query = query.where(Task.category == category)
    
    query = query.order_by(Task.created_at.desc())
    
    result = await db.execute(query)
    tasks = result.scalars().all()
    
    return [
        TaskResponse(
            id=task.id,
            name=task.name,
            description=task.description,
            category=task.category,
            has_ai_judge="ai_judge" in (task.config or {}),
            created_at=task.created_at,
            is_active=task.is_active
        )
        for task in tasks
    ]


@router.get("/{task_id}", response_model=dict)
async def get_task(task_id: str, db: AsyncSession = Depends(get_db)):
    """Get task details"""
    result = await db.execute(select(Task).where(Task.id == task_id))
    task = result.scalar_one_or_none()
    
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    
    # Get baseline files
    baseline_dir = Path(settings.TASKS_DIR) / task_id / "baseline"
    baseline_files = []
    if baseline_dir.exists():
        baseline_files = [f.name for f in baseline_dir.iterdir() if f.is_file()]
    
    return {
        "id": task.id,
        "name": task.name,
        "description": task.description,
        "category": task.category,
        "config": task.config,
        "baseline_files": baseline_files,
        "created_at": task.created_at,
        "is_active": task.is_active
    }


@router.delete("/{task_id}")
async def delete_task(task_id: str, db: AsyncSession = Depends(get_db)):
    """Delete a task (soft delete)"""
    result = await db.execute(select(Task).where(Task.id == task_id))
    task = result.scalar_one_or_none()
    
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    
    task.is_active = False
    await db.commit()
    
    return {"message": f"Task '{task_id}' deleted successfully"}
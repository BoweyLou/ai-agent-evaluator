from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from typing import List, Dict, Any
from datetime import datetime, timedelta

from ..models.database import get_db, Evaluation, Task, AgentResult
from ..models.schemas import EvaluationStatus

router = APIRouter(prefix="/results", tags=["results"])


@router.get("/summary", response_model=Dict[str, Any])
async def get_results_summary(db: AsyncSession = Depends(get_db)):
    """Get overall results summary and statistics"""
    
    # Total evaluations
    total_evals = await db.scalar(select(func.count(Evaluation.id)))
    
    # Completed evaluations
    completed_evals = await db.scalar(
        select(func.count(Evaluation.id)).where(Evaluation.status == EvaluationStatus.COMPLETED)
    )
    
    # Active evaluations
    active_evals = await db.scalar(
        select(func.count(Evaluation.id)).where(Evaluation.status == EvaluationStatus.ACTIVE)
    )
    
    # Recent evaluations (last 7 days)
    recent_date = datetime.utcnow() - timedelta(days=7)
    recent_evals = await db.scalar(
        select(func.count(Evaluation.id)).where(Evaluation.created_at >= recent_date)
    )
    
    # Agent performance summary
    agent_results = await db.execute(
        select(AgentResult.agent_name, func.avg(AgentResult.score), func.count(AgentResult.id))
        .where(AgentResult.score.isnot(None))
        .group_by(AgentResult.agent_name)
    )
    
    agent_performance = {}
    for agent_name, avg_score, count in agent_results:
        agent_performance[agent_name] = {
            "average_score": round(float(avg_score), 1) if avg_score else 0,
            "total_evaluations": count
        }
    
    # Task category distribution
    task_distribution = await db.execute(
        select(Task.category, func.count(Evaluation.id))
        .join(Evaluation, Task.id == Evaluation.task_id)
        .group_by(Task.category)
    )
    
    category_stats = {}
    for category, count in task_distribution:
        category_stats[category] = count
    
    return {
        "total_evaluations": total_evals,
        "completed_evaluations": completed_evals,
        "active_evaluations": active_evals,
        "recent_evaluations": recent_evals,
        "agent_performance": agent_performance,
        "task_categories": category_stats
    }


@router.get("/comparison/{evaluation_id}", response_model=Dict[str, Any])
async def get_evaluation_comparison(evaluation_id: str, db: AsyncSession = Depends(get_db)):
    """Get detailed comparison for a specific evaluation"""
    
    # Get evaluation
    eval_result = await db.execute(select(Evaluation).where(Evaluation.id == evaluation_id))
    evaluation = eval_result.scalar_one_or_none()
    if not evaluation:
        raise HTTPException(status_code=404, detail="Evaluation not found")
    
    # Get task details
    task_result = await db.execute(select(Task).where(Task.id == evaluation.task_id))
    task = task_result.scalar_one_or_none()
    
    # Get all agent results
    results_query = select(AgentResult).where(AgentResult.evaluation_id == evaluation_id)
    results_result = await db.execute(results_query)
    agent_results = results_result.scalars().all()
    
    # Sort agents by score
    sorted_results = sorted(
        [r for r in agent_results if r.score is not None],
        key=lambda x: x.score,
        reverse=True
    )
    
    # Calculate rankings and performance metrics
    comparison_data = {
        "evaluation_id": evaluation_id,
        "task": {
            "id": task.id,
            "name": task.name,
            "category": task.category
        } if task else None,
        "rankings": [],
        "score_distribution": {},
        "criteria_breakdown": {},
        "summary": {}
    }
    
    total_score = 0
    score_counts = {}
    criteria_totals = {}
    
    for rank, result in enumerate(sorted_results, 1):
        medal = "🥇" if rank == 1 else "🥈" if rank == 2 else "🥉" if rank == 3 else ""
        
        comparison_data["rankings"].append({
            "rank": rank,
            "agent": result.agent_name,
            "score": result.score,
            "medal": medal,
            "breakdown": result.breakdown or {},
            "feedback": result.feedback,
            "completed_at": result.completed_at
        })
        
        # Score distribution
        score_range = f"{(result.score // 10) * 10}-{(result.score // 10) * 10 + 9}"
        score_counts[score_range] = score_counts.get(score_range, 0) + 1
        
        # Criteria breakdown
        if result.breakdown:
            for criterion, score in result.breakdown.items():
                if criterion not in criteria_totals:
                    criteria_totals[criterion] = []
                criteria_totals[criterion].append(score)
        
        total_score += result.score
    
    # Calculate averages and statistics
    if sorted_results:
        comparison_data["summary"] = {
            "average_score": round(total_score / len(sorted_results), 1),
            "highest_score": sorted_results[0].score,
            "lowest_score": sorted_results[-1].score,
            "score_range": sorted_results[0].score - sorted_results[-1].score,
            "total_agents": len(sorted_results)
        }
    
    comparison_data["score_distribution"] = score_counts
    
    # Criteria averages
    for criterion, scores in criteria_totals.items():
        comparison_data["criteria_breakdown"][criterion] = {
            "average": round(sum(scores) / len(scores), 1),
            "max": max(scores),
            "min": min(scores),
            "scores": scores
        }
    
    return comparison_data


@router.get("/leaderboard", response_model=List[Dict[str, Any]])
async def get_agent_leaderboard(
    limit: int = 10,
    category: str = None,
    db: AsyncSession = Depends(get_db)
):
    """Get agent leaderboard across all evaluations"""
    
    query = select(
        AgentResult.agent_name,
        func.avg(AgentResult.score).label('avg_score'),
        func.count(AgentResult.id).label('total_evals'),
        func.max(AgentResult.score).label('best_score'),
        func.min(AgentResult.score).label('worst_score')
    ).where(AgentResult.score.isnot(None))
    
    if category:
        query = query.join(Evaluation, AgentResult.evaluation_id == Evaluation.id)\
                    .join(Task, Evaluation.task_id == Task.id)\
                    .where(Task.category == category)
    
    query = query.group_by(AgentResult.agent_name)\
                 .order_by(func.avg(AgentResult.score).desc())\
                 .limit(limit)
    
    result = await db.execute(query)
    
    leaderboard = []
    for rank, (agent, avg_score, total, best, worst) in enumerate(result, 1):
        medal = "🥇" if rank == 1 else "🥈" if rank == 2 else "🥉" if rank == 3 else ""
        
        leaderboard.append({
            "rank": rank,
            "agent": agent,
            "medal": medal,
            "average_score": round(float(avg_score), 1),
            "total_evaluations": total,
            "best_score": best,
            "worst_score": worst,
            "consistency": round(float(avg_score) / best * 100, 1) if best > 0 else 0
        })
    
    return leaderboard


@router.get("/trends", response_model=Dict[str, Any])
async def get_performance_trends(
    days: int = 30,
    agent: str = None,
    db: AsyncSession = Depends(get_db)
):
    """Get performance trends over time"""
    
    # Get date range
    end_date = datetime.utcnow()
    start_date = end_date - timedelta(days=days)
    
    # Base query for results in date range
    query = select(
        AgentResult.agent_name,
        AgentResult.score,
        AgentResult.completed_at,
        func.date(AgentResult.completed_at).label('eval_date')
    ).where(
        AgentResult.completed_at >= start_date,
        AgentResult.score.isnot(None)
    )
    
    if agent:
        query = query.where(AgentResult.agent_name == agent)
    
    query = query.order_by(AgentResult.completed_at)
    
    result = await db.execute(query)
    results = result.all()
    
    # Group by date and agent
    trends_data = {}
    daily_averages = {}
    
    for row in results:
        agent_name = row.agent_name
        eval_date = row.eval_date.isoformat()
        score = row.score
        
        if agent_name not in trends_data:
            trends_data[agent_name] = []
        
        trends_data[agent_name].append({
            "date": eval_date,
            "score": score
        })
        
        # Daily averages
        if eval_date not in daily_averages:
            daily_averages[eval_date] = []
        daily_averages[eval_date].append(score)
    
    # Calculate daily averages
    daily_avg_scores = {}
    for date, scores in daily_averages.items():
        daily_avg_scores[date] = round(sum(scores) / len(scores), 1)
    
    return {
        "date_range": {
            "start": start_date.date().isoformat(),
            "end": end_date.date().isoformat()
        },
        "agent_trends": trends_data,
        "daily_averages": daily_avg_scores,
        "total_evaluations": len(results)
    }
"""
Main evaluation service that coordinates rule-based and AI judge evaluation
"""

from typing import Dict, Any, Optional
from pathlib import Path
import yaml
import json
from datetime import datetime
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update

from ..models.database import AsyncSessionLocal, Evaluation, AgentResult, Task
from ..core.evaluators.css_evaluator import EnhancedCSSEvaluator
from ..services.openrouter import OpenRouterJudge
from ..services.github import GitHubService, MockGitHubService
from ..core.config import settings


class EvaluationService:
    """Main service for coordinating evaluations"""
    
    def __init__(self):
        self.evaluators = {
            "enhanced_css": EnhancedCSSEvaluator(),
            "rule_based": EnhancedCSSEvaluator(),  # Alias for CSS evaluator
        }
        
        # Use mock GitHub service if no token provided
        if settings.GITHUB_TOKEN:
            self.github_service = GitHubService()
        else:
            self.github_service = MockGitHubService()
        
        # Initialize OpenRouter if API key provided
        self.openrouter_judge = None
        if settings.OPENROUTER_API_KEY:
            try:
                self.openrouter_judge = OpenRouterJudge()
            except Exception as e:
                print(f"Warning: Failed to initialize OpenRouter: {e}")
    
    async def evaluate_agent(self, evaluation_id: str, agent_name: str) -> Dict[str, Any]:
        """Evaluate a single agent's solution"""
        
        async with AsyncSessionLocal() as db:
            # Get evaluation details
            eval_result = await db.execute(select(Evaluation).where(Evaluation.id == evaluation_id))
            evaluation = eval_result.scalar_one_or_none()
            
            if not evaluation:
                raise ValueError(f"Evaluation {evaluation_id} not found")
            
            # Get task configuration
            task_result = await db.execute(select(Task).where(Task.id == evaluation.task_id))
            task = task_result.scalar_one_or_none()
            
            if not task:
                raise ValueError(f"Task {evaluation.task_id} not found")
            
            task_config = task.config or {}
            
            # Get baseline and solution files
            baseline_files = await self._load_baseline_files(evaluation.task_id)
            solution_files = await self._load_solution_files(evaluation_id, agent_name)
            
            # Run evaluation based on task configuration
            evaluation_type = task_config.get("evaluation", {}).get("type", "rule_based")
            
            if evaluation_type == "ai_judge" and self.openrouter_judge:
                result = await self._run_ai_judge_evaluation(
                    task_config, baseline_files, solution_files, agent_name
                )
            elif evaluation_type == "hybrid":
                # Run both rule-based and AI judge, then combine
                rule_result = await self._run_rule_based_evaluation(
                    task_config, baseline_files, solution_files, agent_name
                )
                
                if self.openrouter_judge:
                    ai_result = await self._run_ai_judge_evaluation(
                        task_config, baseline_files, solution_files, agent_name
                    )
                    result = self._combine_evaluations(rule_result, ai_result)
                else:
                    result = rule_result
            else:
                # Default to rule-based evaluation
                result = await self._run_rule_based_evaluation(
                    task_config, baseline_files, solution_files, agent_name
                )
            
            # Save result to database
            await self._save_agent_result(db, evaluation_id, agent_name, result)
            
            # Update evaluation status if all agents are complete
            await self._check_evaluation_completion(db, evaluation_id)
            
            return result
    
    async def _load_baseline_files(self, task_id: str) -> Dict[str, str]:
        """Load baseline files for a task"""
        baseline_dir = Path(settings.TASKS_DIR) / task_id / "baseline"
        files = {}
        
        if baseline_dir.exists():
            for file_path in baseline_dir.rglob("*"):
                if file_path.is_file():
                    try:
                        with open(file_path, 'r', encoding='utf-8') as f:
                            relative_path = file_path.relative_to(baseline_dir)
                            files[str(relative_path)] = f.read()
                    except UnicodeDecodeError:
                        # Skip binary files
                        pass
        
        return files
    
    async def _load_solution_files(self, evaluation_id: str, agent_name: str) -> Dict[str, str]:
        """Load solution files from GitHub branch"""
        branch_name = f"{settings.GITHUB_BRANCH_PREFIX}-{evaluation_id}-{agent_name}"
        
        try:
            return await self.github_service.get_branch_files(branch_name)
        except Exception as e:
            print(f"Warning: Failed to load solution files from GitHub: {e}")
            return {}
    
    async def _run_rule_based_evaluation(
        self, 
        task_config: Dict[str, Any], 
        baseline_files: Dict[str, str], 
        solution_files: Dict[str, str], 
        agent_name: str
    ) -> Dict[str, Any]:
        """Run rule-based evaluation"""
        
        # Determine evaluator type from task config
        eval_type = task_config.get("evaluation", {}).get("type", "rule_based")
        
        # Use appropriate evaluator
        if eval_type in self.evaluators:
            evaluator = self.evaluators[eval_type]
        else:
            # Default to CSS evaluator for now
            evaluator = self.evaluators["enhanced_css"]
        
        result = evaluator.evaluate(baseline_files, solution_files)
        
        # Add metadata
        result.update({
            "agent": agent_name,
            "evaluation_type": "rule_based",
            "completed_at": datetime.utcnow().isoformat()
        })
        
        return result
    
    async def _run_ai_judge_evaluation(
        self, 
        task_config: Dict[str, Any], 
        baseline_files: Dict[str, str], 
        solution_files: Dict[str, str], 
        agent_name: str
    ) -> Dict[str, Any]:
        """Run AI judge evaluation"""
        
        if not self.openrouter_judge:
            raise ValueError("OpenRouter judge not configured")
        
        result = await self.openrouter_judge.evaluate_solution(
            task_config, baseline_files, solution_files, agent_name
        )
        
        # Add metadata
        result.update({
            "completed_at": datetime.utcnow().isoformat()
        })
        
        return result
    
    def _combine_evaluations(self, rule_result: Dict[str, Any], ai_result: Dict[str, Any]) -> Dict[str, Any]:
        """Combine rule-based and AI judge evaluations"""
        
        # Weight the scores (70% rule-based, 30% AI judge)
        rule_weight = 0.7
        ai_weight = 0.3
        
        combined_score = (
            rule_result.get("total_score", 0) * rule_weight +
            ai_result.get("total_score", 0) * ai_weight
        )
        
        return {
            "agent": rule_result.get("agent"),
            "total_score": round(combined_score),
            "scores": {
                "rule_based": rule_result.get("scores", {}),
                "ai_judge": ai_result.get("scores", {})
            },
            "feedback": f"Rule-based: {rule_result.get('total_score', 0)}/100, AI Judge: {ai_result.get('total_score', 0)}/100",
            "breakdown": {
                "rule_based_score": rule_result.get("total_score", 0),
                "ai_judge_score": ai_result.get("total_score", 0),
                "combined_score": round(combined_score)
            },
            "strengths": ai_result.get("strengths", []),
            "improvements": (
                rule_result.get("improvements", []) + 
                ai_result.get("improvements", [])
            ),
            "evaluation_type": "hybrid",
            "completed_at": datetime.utcnow().isoformat(),
            "details": {
                "rule_based": rule_result,
                "ai_judge": ai_result
            }
        }
    
    async def _save_agent_result(
        self, 
        db: AsyncSession, 
        evaluation_id: str, 
        agent_name: str, 
        result: Dict[str, Any]
    ):
        """Save agent result to database"""
        
        # Check if result already exists
        existing_result = await db.execute(
            select(AgentResult).where(
                AgentResult.evaluation_id == evaluation_id,
                AgentResult.agent_name == agent_name
            )
        )
        existing = existing_result.scalar_one_or_none()
        
        if existing:
            # Update existing result
            await db.execute(
                update(AgentResult)
                .where(
                    AgentResult.evaluation_id == evaluation_id,
                    AgentResult.agent_name == agent_name
                )
                .values(
                    score=result.get("total_score"),
                    breakdown=result.get("scores") or result.get("breakdown"),
                    feedback=result.get("feedback"),
                    outputs=result,
                    completed_at=datetime.utcnow(),
                    status="completed"
                )
            )
        else:
            # Create new result
            agent_result = AgentResult(
                evaluation_id=evaluation_id,
                agent_name=agent_name,
                score=result.get("total_score"),
                breakdown=result.get("scores") or result.get("breakdown"),
                feedback=result.get("feedback"),
                outputs=result,
                started_at=datetime.utcnow(),
                completed_at=datetime.utcnow(),
                status="completed"
            )
            db.add(agent_result)
        
        # Update evaluation agent status
        eval_result = await db.execute(select(Evaluation).where(Evaluation.id == evaluation_id))
        evaluation = eval_result.scalar_one_or_none()
        
        if evaluation:
            agent_status = evaluation.agent_status.copy()
            agent_status[agent_name] = "completed"
            
            await db.execute(
                update(Evaluation)
                .where(Evaluation.id == evaluation_id)
                .values(
                    agent_status=agent_status,
                    updated_at=datetime.utcnow()
                )
            )
        
        await db.commit()
    
    async def _check_evaluation_completion(self, db: AsyncSession, evaluation_id: str):
        """Check if evaluation is complete and update status"""
        
        eval_result = await db.execute(select(Evaluation).where(Evaluation.id == evaluation_id))
        evaluation = eval_result.scalar_one_or_none()
        
        if not evaluation:
            return
        
        # Check if all agents are completed
        all_completed = all(
            status == "completed" 
            for status in evaluation.agent_status.values()
        )
        
        if all_completed and evaluation.status != "completed":
            await db.execute(
                update(Evaluation)
                .where(Evaluation.id == evaluation_id)
                .values(
                    status="completed",
                    updated_at=datetime.utcnow()
                )
            )
            await db.commit()
            
            # Generate comparison report
            await self._generate_comparison_report(evaluation_id)
    
    async def _generate_comparison_report(self, evaluation_id: str):
        """Generate comparison report for completed evaluation"""
        
        async with AsyncSessionLocal() as db:
            # Get all results for this evaluation
            results_query = select(AgentResult).where(AgentResult.evaluation_id == evaluation_id)
            results_result = await db.execute(results_query)
            agent_results = results_result.scalars().all()
            
            if not agent_results:
                return
            
            # Sort by score
            sorted_results = sorted(
                [r for r in agent_results if r.score is not None],
                key=lambda x: x.score,
                reverse=True
            )
            
            # Generate markdown report
            report_content = f"""# Evaluation Results: {evaluation_id}

## Rankings

"""
            
            for rank, result in enumerate(sorted_results, 1):
                medal = "🥇" if rank == 1 else "🥈" if rank == 2 else "🥉" if rank == 3 else ""
                report_content += f"{rank}. {medal} **{result.agent_name}**: {result.score}/100\n"
                
                if result.feedback:
                    report_content += f"   - {result.feedback}\n"
                
                report_content += "\n"
            
            # Save report
            results_dir = Path(settings.RESULTS_DIR) / evaluation_id
            results_dir.mkdir(parents=True, exist_ok=True)
            
            with open(results_dir / "comparison_report.md", "w") as f:
                f.write(report_content)
            
            print(f"Generated comparison report for {evaluation_id}")
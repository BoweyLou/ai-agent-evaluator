import httpx
import json
from typing import Dict, Any, List
from pathlib import Path
from ..core.config import settings


class OpenRouterJudge:
    """OpenRouter integration for AI-powered evaluation"""
    
    def __init__(self, api_key: str = None):
        self.api_key = api_key or settings.OPENROUTER_API_KEY
        self.base_url = "https://openrouter.ai/api/v1"
        
        if not self.api_key:
            raise ValueError("OpenRouter API key is required")
    
    async def evaluate_solution(
        self,
        task_config: Dict[str, Any],
        baseline_files: Dict[str, str],
        solution_files: Dict[str, str],
        agent_name: str
    ) -> Dict[str, Any]:
        """Use AI to evaluate a solution"""
        
        try:
            # Build evaluation prompt
            prompt = self._build_prompt(
                task_config,
                baseline_files,
                solution_files,
                agent_name
            )
            
            # Get model from config or use default
            model = task_config.get("ai_judge", {}).get("model", settings.DEFAULT_AI_JUDGE_MODEL)
            
            # Call OpenRouter API
            async with httpx.AsyncClient(timeout=120.0) as client:
                response = await client.post(
                    f"{self.base_url}/chat/completions",
                    headers={
                        "Authorization": f"Bearer {self.api_key}",
                        "HTTP-Referer": settings.API_URL,
                        "X-Title": "AI Agent Evaluator",
                        "Content-Type": "application/json"
                    },
                    json={
                        "model": model,
                        "messages": [
                            {
                                "role": "system",
                                "content": "You are an expert code reviewer evaluating AI agent solutions. Always respond with valid JSON."
                            },
                            {
                                "role": "user",
                                "content": prompt
                            }
                        ],
                        "temperature": 0.1,
                        "max_tokens": 2000
                    }
                )
            
            if response.status_code != 200:
                raise Exception(f"OpenRouter API error: {response.status_code} - {response.text}")
            
            result = response.json()
            content = result["choices"][0]["message"]["content"]
            
            # Parse JSON response
            try:
                evaluation = json.loads(content)
            except json.JSONDecodeError:
                # Try to extract JSON from markdown code blocks
                import re
                json_match = re.search(r'```json\s*(\{.*?\})\s*```', content, re.DOTALL)
                if json_match:
                    evaluation = json.loads(json_match.group(1))
                else:
                    # Fallback: create structured response from text
                    evaluation = {
                        "scores": {},
                        "total_score": 0,
                        "feedback": content,
                        "strengths": [],
                        "improvements": []
                    }
            
            # Ensure required fields exist
            evaluation.setdefault("scores", {})
            evaluation.setdefault("feedback", "No feedback provided")
            evaluation.setdefault("strengths", [])
            evaluation.setdefault("improvements", [])
            
            # Calculate total score if not provided
            if "total_score" not in evaluation:
                evaluation["total_score"] = sum(evaluation["scores"].values())
            
            return {
                "agent": agent_name,
                "scores": evaluation["scores"],
                "total_score": min(100, max(0, evaluation["total_score"])),  # Clamp to 0-100
                "feedback": evaluation["feedback"],
                "strengths": evaluation["strengths"],
                "improvements": evaluation["improvements"],
                "model_used": model,
                "evaluation_type": "ai_judge"
            }
            
        except Exception as e:
            # Return fallback result on error
            return {
                "agent": agent_name,
                "scores": {},
                "total_score": 0,
                "feedback": f"Evaluation failed: {str(e)}",
                "strengths": [],
                "improvements": [],
                "model_used": model,
                "evaluation_type": "ai_judge",
                "error": str(e)
            }
    
    def _build_prompt(
        self, 
        task_config: Dict[str, Any], 
        baseline_files: Dict[str, str], 
        solution_files: Dict[str, str], 
        agent: str
    ) -> str:
        """Build evaluation prompt"""
        
        task_info = task_config.get("task", {})
        scoring = task_config.get("evaluation", {}).get("scoring", {})
        
        prompt = f"""# Task Evaluation: {task_info.get('name', 'Unknown Task')}

## Task Description
{task_info.get('description', 'No description provided')}

## Agent Being Evaluated
{agent}

## Scoring Criteria
{self._format_criteria(scoring)}

## Baseline Files (Original)
{self._format_files(baseline_files, "BASELINE")}

## Solution Files (Agent Output)
{self._format_files(solution_files, "SOLUTION")}

## Instructions
Please evaluate this solution based on the scoring criteria above. Consider:

1. **Task Completion**: Does the solution accomplish the stated goals?
2. **Code Quality**: Is the code well-structured, readable, and maintainable?
3. **Best Practices**: Does the solution follow established coding conventions?
4. **Performance**: Are there any obvious performance issues or improvements?
5. **Edge Cases**: Does the solution handle edge cases appropriately?
6. **Innovation**: Are there any clever or innovative approaches used?

Provide your evaluation as JSON with this exact structure:
```json
{{
  "scores": {{
    "criterion_name": score_out_of_max_weight,
    ...
  }},
  "total_score": sum_of_all_scores,
  "feedback": "Overall evaluation summary (2-3 sentences)",
  "strengths": ["strength1", "strength2", "strength3"],
  "improvements": ["improvement1", "improvement2", "improvement3"]
}}
```

Be objective and constructive in your evaluation."""
        
        # Add custom judge prompt if provided
        custom_prompt = task_config.get("ai_judge", {}).get("prompt_template")
        if custom_prompt:
            prompt += f"\n\n## Additional Evaluation Guidelines\n{custom_prompt}"
        
        return prompt
    
    def _format_criteria(self, criteria: Dict[str, Any]) -> str:
        """Format scoring criteria for the prompt"""
        if not criteria:
            return "No specific criteria defined."
        
        formatted = []
        for name, details in criteria.items():
            weight = details.get("weight", 0)
            description = details.get("description", "No description")
            formatted.append(f"- **{name}** ({weight} points): {description}")
        
        return "\n".join(formatted)
    
    def _format_files(self, files: Dict[str, str], label: str) -> str:
        """Format file contents for the prompt"""
        if not files:
            return f"{label}: No files provided"
        
        formatted = [f"{label}:"]
        for filename, content in files.items():
            # Truncate very long files
            if len(content) > 3000:
                content = content[:3000] + "\n... (truncated)"
            
            formatted.append(f"\n### {filename}")
            formatted.append(f"```\n{content}\n```")
        
        return "\n".join(formatted)


# Utility function to get available models
async def get_available_models() -> List[Dict[str, Any]]:
    """Get list of available models from OpenRouter"""
    if not settings.OPENROUTER_API_KEY:
        return []
    
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(
                "https://openrouter.ai/api/v1/models",
                headers={
                    "Authorization": f"Bearer {settings.OPENROUTER_API_KEY}",
                }
            )
        
        if response.status_code == 200:
            models = response.json()["data"]
            # Filter to popular coding/analysis models
            coding_models = [
                model for model in models
                if any(keyword in model["id"].lower() for keyword in [
                    "claude", "gpt", "mixtral", "llama", "codellama"
                ])
            ]
            return coding_models
        
    except Exception:
        pass
    
    # Fallback to common models
    return [
        {"id": "anthropic/claude-3-opus", "name": "Claude 3 Opus"},
        {"id": "anthropic/claude-3-sonnet", "name": "Claude 3 Sonnet"},
        {"id": "openai/gpt-4", "name": "GPT-4"},
        {"id": "mistralai/mixtral-8x7b-instruct", "name": "Mixtral 8x7B"},
    ]
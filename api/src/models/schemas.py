from pydantic import BaseModel, Field
from typing import List, Dict, Any, Optional
from datetime import datetime
from enum import Enum


class TaskCategory(str, Enum):
    REFACTORING = "refactoring"
    BUG_FIXING = "bug_fixing"
    FEATURE = "feature"
    OPTIMIZATION = "optimization"


class EvaluationType(str, Enum):
    RULE_BASED = "rule_based"
    AI_JUDGE = "ai_judge"
    HYBRID = "hybrid"


class EvaluationStatus(str, Enum):
    PENDING = "pending"
    ACTIVE = "active"
    COMPLETED = "completed"
    FAILED = "failed"


class AgentStatus(str, Enum):
    PENDING = "pending"
    READY = "ready"
    EVALUATING = "evaluating"
    COMPLETED = "completed"
    FAILED = "failed"


class ScoringCriterion(BaseModel):
    name: str = Field(..., description="Name of the scoring criterion")
    description: str = Field(..., description="Description of what this criterion measures")
    weight: int = Field(..., ge=1, le=100, description="Weight/points for this criterion")


class AgentPrompt(BaseModel):
    agent: str = Field(..., description="Agent name")
    prompt: str = Field(..., description="Task prompt for this agent")


class TaskCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=200)
    description: str = Field(..., min_length=1)
    category: TaskCategory
    use_ai_judge: bool = False
    ai_judge_model: Optional[str] = "claude-3-sonnet"
    judge_prompt: Optional[str] = None
    scoring_criteria: List[ScoringCriterion]
    agent_prompts: Dict[str, str] = Field(default_factory=dict)


class TaskResponse(BaseModel):
    id: str
    name: str
    description: str
    category: str
    has_ai_judge: bool
    created_at: datetime
    is_active: bool


class EvaluationCreate(BaseModel):
    task_id: str
    agents: List[str] = Field(..., min_items=1)


class EvaluationResponse(BaseModel):
    id: str
    task_id: str
    agents: List[str]
    status: EvaluationStatus
    agent_status: Dict[str, AgentStatus]
    created_at: datetime
    updated_at: datetime


class AgentResultResponse(BaseModel):
    agent_name: str
    score: Optional[int]
    breakdown: Optional[Dict[str, Any]]
    feedback: Optional[str]
    status: AgentStatus
    completed_at: Optional[datetime]


class EvaluationDetailResponse(EvaluationResponse):
    results: Dict[str, AgentResultResponse]
    metadata: Dict[str, Any]


class HealthResponse(BaseModel):
    status: str
    version: str
    environment: str


class ErrorResponse(BaseModel):
    detail: str
    type: str
    code: Optional[str] = None
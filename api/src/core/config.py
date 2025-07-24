from pydantic_settings import BaseSettings
from typing import List, Union
from pydantic import field_validator
import os


class Settings(BaseSettings):
    # Application
    NODE_ENV: str = "development"
    SECRET_KEY: str = "development-secret-key"
    API_URL: str = "http://localhost:8000"
    
    # Database
    DATABASE_URL: str = "postgresql://postgres:password@localhost:5432/evaluator"
    
    # Cache
    REDIS_URL: str = "redis://localhost:6379"
    
    # OpenRouter (Optional - can be set via API)
    OPENROUTER_API_KEY: str = ""
    DEFAULT_AI_JUDGE_MODEL: str = "claude-3-sonnet"
    
    # GitHub (Optional - for advanced workspace management)
    GITHUB_TOKEN: str = ""
    GITHUB_REPO: str = ""
    GITHUB_BRANCH_PREFIX: str = "eval"
    
    # Security
    JWT_SECRET: str = "jwt-secret-key"
    ALLOWED_ORIGINS: Union[List[str], str] = ["http://localhost:3000", "http://localhost:8000"]
    
    @field_validator('ALLOWED_ORIGINS', mode='before')
    @classmethod
    def parse_allowed_origins(cls, v):
        if isinstance(v, str):
            # Handle comma-separated string
            return [origin.strip() for origin in v.split(',') if origin.strip()]
        return v
    
    # Evaluation Settings
    MAX_EVALUATION_TIME: int = 3600  # 1 hour
    MAX_CONCURRENT_EVALUATIONS: int = 5
    
    # File Storage
    UPLOAD_MAX_SIZE_MB: int = 50
    RESULTS_RETENTION_DAYS: int = 90
    TASKS_DIR: str = "tasks"
    RESULTS_DIR: str = "results"
    
    class Config:
        env_file = ".env"
        case_sensitive = True


settings = Settings()
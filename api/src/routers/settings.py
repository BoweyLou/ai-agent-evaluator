from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional, Dict, Any
from ..services.openrouter import get_available_models

router = APIRouter(prefix="/settings", tags=["settings"])

# In-memory storage for API keys (in production, use secure storage)
_api_keys: Dict[str, str] = {}


class APIKeyRequest(BaseModel):
    openrouter_api_key: Optional[str] = None
    github_token: Optional[str] = None


class APIKeyResponse(BaseModel):
    openrouter_configured: bool
    github_configured: bool
    available_models: list = []


@router.post("/api-keys", response_model=dict)
async def update_api_keys(keys: APIKeyRequest):
    """Update API keys for the session"""
    
    if keys.openrouter_api_key:
        _api_keys["openrouter"] = keys.openrouter_api_key
    
    if keys.github_token:
        _api_keys["github"] = keys.github_token
    
    return {
        "message": "API keys updated",
        "openrouter_configured": "openrouter" in _api_keys,
        "github_configured": "github" in _api_keys
    }


@router.get("/api-keys", response_model=APIKeyResponse)
async def get_api_key_status():
    """Get API key configuration status"""
    
    # Get available models if OpenRouter is configured
    models = []
    if "openrouter" in _api_keys:
        try:
            # Temporarily set the key for model fetching
            import os
            original_key = os.environ.get("OPENROUTER_API_KEY")
            os.environ["OPENROUTER_API_KEY"] = _api_keys["openrouter"]
            
            models = await get_available_models()
            
            # Restore original key
            if original_key:
                os.environ["OPENROUTER_API_KEY"] = original_key
            else:
                os.environ.pop("OPENROUTER_API_KEY", None)
                
        except Exception:
            models = []
    
    return APIKeyResponse(
        openrouter_configured="openrouter" in _api_keys,
        github_configured="github" in _api_keys,
        available_models=models
    )


@router.delete("/api-keys")
async def clear_api_keys():
    """Clear all API keys"""
    global _api_keys
    _api_keys.clear()
    
    return {"message": "All API keys cleared"}


def get_openrouter_key() -> Optional[str]:
    """Get the current OpenRouter API key"""
    return _api_keys.get("openrouter")


def get_github_token() -> Optional[str]:
    """Get the current GitHub token"""
    return _api_keys.get("github")
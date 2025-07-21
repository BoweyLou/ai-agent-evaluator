from fastapi import APIRouter
from typing import List, Dict

router = APIRouter(prefix="/agents", tags=["agents"])

# Available agents configuration
AVAILABLE_AGENTS = {
    "claude": {
        "name": "Claude Code CLI",
        "description": "Anthropic's Claude with code editing capabilities",
        "type": "cli",
        "supported_tasks": ["refactoring", "bug_fixing", "feature", "optimization"]
    },
    "cursor": {
        "name": "Cursor AI",
        "description": "AI-powered code editor with intelligent suggestions",
        "type": "editor",
        "supported_tasks": ["refactoring", "feature", "optimization"]
    },
    "qdev": {
        "name": "Q Dev CLI",
        "description": "Amazon's Q Developer command line interface",
        "type": "cli",
        "supported_tasks": ["refactoring", "bug_fixing", "feature"]
    },
    "gemini": {
        "name": "Google Gemini",
        "description": "Google's Gemini AI model for code assistance",
        "type": "api",
        "supported_tasks": ["refactoring", "bug_fixing", "optimization"]
    },
    "copilot": {
        "name": "GitHub Copilot",
        "description": "GitHub's AI programming assistant",
        "type": "integration",
        "supported_tasks": ["refactoring", "feature", "optimization"]
    },
    "manual": {
        "name": "Manual/Human",
        "description": "Human developer reference implementation",
        "type": "manual",
        "supported_tasks": ["refactoring", "bug_fixing", "feature", "optimization"]
    }
}


@router.get("/", response_model=List[Dict])
async def list_agents(task_category: str = None):
    """List all available agents"""
    agents = []
    
    for agent_id, config in AVAILABLE_AGENTS.items():
        # Filter by task category if specified
        if task_category and task_category not in config["supported_tasks"]:
            continue
            
        agents.append({
            "id": agent_id,
            "name": config["name"],
            "description": config["description"],
            "type": config["type"],
            "supported_tasks": config["supported_tasks"]
        })
    
    return agents


@router.get("/{agent_id}", response_model=Dict)
async def get_agent(agent_id: str):
    """Get specific agent details"""
    if agent_id not in AVAILABLE_AGENTS:
        from fastapi import HTTPException
        raise HTTPException(status_code=404, detail="Agent not found")
    
    config = AVAILABLE_AGENTS[agent_id]
    return {
        "id": agent_id,
        "name": config["name"],
        "description": config["description"],
        "type": config["type"],
        "supported_tasks": config["supported_tasks"],
        "instructions": _get_agent_instructions(agent_id)
    }


def _get_agent_instructions(agent_id: str) -> Dict[str, str]:
    """Get usage instructions for each agent"""
    instructions = {
        "claude": {
            "setup": "Install Claude Code CLI from anthropic.com",
            "usage": "claude code --directory /path/to/workspace 'Your task prompt here'",
            "notes": "Works best with specific, detailed prompts"
        },
        "cursor": {
            "setup": "Download Cursor from cursor.sh",
            "usage": "Open workspace in Cursor, use Cmd+K to interact with AI",
            "notes": "Excellent for iterative development and code editing"
        },
        "qdev": {
            "setup": "Install AWS CLI and Q Developer extension",
            "usage": "qdev 'Your task description here'",
            "notes": "Integrates well with AWS services and infrastructure"
        },
        "gemini": {
            "setup": "Access through Google AI Studio or API",
            "usage": "Upload files and provide task description",
            "notes": "Good for analysis and code generation"
        },
        "copilot": {
            "setup": "Install GitHub Copilot in your IDE",
            "usage": "Use Copilot Chat or suggestions in your editor",
            "notes": "Works best within familiar development environment"
        },
        "manual": {
            "setup": "No setup required",
            "usage": "Implement the solution manually as a reference",
            "notes": "Provides human baseline for comparison"
        }
    }
    
    return instructions.get(agent_id, {
        "setup": "No specific instructions available",
        "usage": "Follow general guidelines for this agent",
        "notes": "Contact administrator for specific usage instructions"
    })
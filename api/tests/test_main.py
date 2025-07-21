"""
Basic tests for the API endpoints
"""

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from src.main import app
from src.models.database import get_db, Base

# Create test database
SQLALCHEMY_DATABASE_URL = "sqlite:///./test.db"
engine = create_engine(SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False})
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Create test tables
Base.metadata.create_all(bind=engine)


def override_get_db():
    try:
        db = TestingSessionLocal()
        yield db
    finally:
        db.close()


app.dependency_overrides[get_db] = override_get_db

client = TestClient(app)


def test_read_root():
    """Test the root endpoint"""
    response = client.get("/")
    assert response.status_code == 200
    data = response.json()
    assert "message" in data
    assert "AI Agent Evaluation Platform" in data["message"]


def test_health_check():
    """Test the health endpoint"""
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert "version" in data


def test_list_tasks_empty():
    """Test listing tasks when none exist"""
    response = client.get("/api/v1/tasks/")
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    assert len(data) == 0


def test_list_agents():
    """Test listing available agents"""
    response = client.get("/api/v1/agents/")
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    assert len(data) > 0
    
    # Check that standard agents are included
    agent_ids = [agent["id"] for agent in data]
    assert "claude" in agent_ids
    assert "cursor" in agent_ids


def test_get_agent_details():
    """Test getting details for a specific agent"""
    response = client.get("/api/v1/agents/claude")
    assert response.status_code == 200
    data = response.json()
    assert data["id"] == "claude"
    assert "name" in data
    assert "description" in data
    assert "instructions" in data


def test_get_nonexistent_agent():
    """Test getting details for a non-existent agent"""
    response = client.get("/api/v1/agents/nonexistent")
    assert response.status_code == 404


def test_list_evaluations_empty():
    """Test listing evaluations when none exist"""
    response = client.get("/api/v1/evaluations/")
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    assert len(data) == 0


def test_get_results_summary():
    """Test getting results summary"""
    response = client.get("/api/v1/results/summary")
    assert response.status_code == 200
    data = response.json()
    assert "total_evaluations" in data
    assert "completed_evaluations" in data
    assert "active_evaluations" in data


@pytest.mark.asyncio
async def test_css_evaluator():
    """Test the CSS evaluator directly"""
    from src.core.evaluators.css_evaluator import EnhancedCSSEvaluator
    
    evaluator = EnhancedCSSEvaluator()
    
    # Test HTML with repetitive inline styles
    baseline_files = {
        "test.html": '''
        <html>
        <body>
            <div style="font-family: Arial; font-size: 12px; color: red;">Content 1</div>
            <div style="font-family: Arial; font-size: 12px; color: red;">Content 2</div>
            <div style="font-family: Arial; font-size: 12px; color: red;">Content 3</div>
            <font face="Arial" size="2">Legacy font tag</font>
        </body>
        </html>
        '''
    }
    
    # Solution with consolidated styles
    solution_files = {
        "test.html": '''
        <html>
        <head>
            <style>
                .text-style { font-family: Arial; font-size: 12px; color: red; }
            </style>
        </head>
        <body>
            <div class="text-style">Content 1</div>
            <div class="text-style">Content 2</div>
            <div class="text-style">Content 3</div>
            <span class="text-style">Legacy font tag</span>
        </body>
        </html>
        '''
    }
    
    result = evaluator.evaluate(baseline_files, solution_files)
    
    assert "total_score" in result
    assert "scores" in result
    assert result["total_score"] > 0
    assert result["total_score"] <= 100
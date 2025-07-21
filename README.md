# AI Agent Evaluation Platform

A production-ready platform for evaluating AI coding agents on various tasks with automated scoring and AI-powered judging.

## Features

- 🌐 Web interface for managing evaluations
- 🤖 Support for multiple AI coding agents (Claude, Cursor, Q Dev, Gemini, Copilot)
- 📊 Automated scoring with rule-based and AI judge evaluation
- 🎯 Easy task creation through web UI
- 🔄 GitHub integration for code management
- 🧠 OpenRouter integration for AI judging
- 📈 Detailed comparison reports and visualizations

## Quick Start

```bash
# Clone the repository
git clone <repository-url>
cd ai-eval-platform

# Copy environment variables
cp .env.example .env
# Edit .env with your API keys

# Start the platform
docker-compose up

# Access the web interface
open http://localhost:3000
```

## Architecture

- **API**: FastAPI backend for evaluation logic
- **Web**: React dashboard for control and visualization
- **Worker**: Celery workers for background processing
- **Database**: PostgreSQL for storing evaluations
- **Cache**: Redis for task queuing

## Creating Tasks

1. Access the web interface at http://localhost:3000
2. Click "Create Task"
3. Upload baseline files
4. Configure scoring criteria
5. Set agent-specific prompts
6. Enable AI judge if desired

## Running Evaluations

1. Select a task from the dashboard
2. Choose agents to evaluate
3. Start the evaluation
4. Follow instructions to run each agent manually
5. Mark agents as complete
6. View automated scoring results

## Development

```bash
# API development
cd api
pip install -r requirements-dev.txt
uvicorn src.main:app --reload

# Web development
cd web
npm install
npm run dev

# Run tests
npm test
pytest
```
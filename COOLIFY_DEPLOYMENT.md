# 🚀 Coolify Deployment Guide

## Quick Deploy

1. **Create New Project** in Coolify
2. **Connect Repository**: `BoweyLou/ai-agent-evaluator`
3. **Docker Compose Configuration**:
   - Primary: `docker-compose.yml`
   - Override: `docker-compose.prod.yml` 
4. **Set Environment Variables** (see below)
5. **Deploy** 🎉

## Environment Variables

### Required for Production

```bash
# Application
NODE_ENV=production
SECRET_KEY=your-ultra-secure-secret-key-here

# Database (Coolify will provide these)
DATABASE_URL=postgresql://user:password@postgres:5432/evaluator

# Cache (Coolify will provide these)  
REDIS_URL=redis://redis:6379

# Your API Keys
OPENROUTER_API_KEY=sk-or-your-openrouter-key
GITHUB_TOKEN=ghp_your-github-token

# Repository
GITHUB_REPO=BoweyLou/ai-agent-evaluator
GITHUB_BRANCH_PREFIX=eval

# Security
JWT_SECRET=another-secure-jwt-secret
ALLOWED_ORIGINS=["https://your-domain.com","https://api.your-domain.com"]

# URLs (update with your domains)
API_URL=https://api.your-domain.com
```

### Optional Environment Variables

```bash
# Evaluation Settings
MAX_EVALUATION_TIME=3600
MAX_CONCURRENT_EVALUATIONS=5
DEFAULT_AI_JUDGE_MODEL=anthropic/claude-3-sonnet

# File Storage
UPLOAD_MAX_SIZE_MB=50
RESULTS_RETENTION_DAYS=90
```

## Domain Configuration

Set up two domains in Coolify:

1. **Web Interface**: `https://evaluator.yourcompany.com`
   - Points to `web` service (port 3000)
   
2. **API**: `https://api-evaluator.yourcompany.com` 
   - Points to `api` service (port 8000)

Then update environment:
```bash
API_URL=https://api-evaluator.yourcompany.com
ALLOWED_ORIGINS=["https://evaluator.yourcompany.com"]
```

## Services Overview

- **web** → React frontend (port 3000)
- **api** → FastAPI backend (port 8000)  
- **worker** → Background task processor
- **db** → PostgreSQL database
- **redis** → Cache and task queue

## Post-Deployment Verification

```bash
# Download and run verification script
curl -o verify.sh https://raw.githubusercontent.com/BoweyLou/ai-agent-evaluator/main/verify-deployment.sh
chmod +x verify.sh
./verify.sh https://your-domain.com
```

Or check manually:
- API Health: `https://api.your-domain.com/health`
- Web Interface: `https://evaluator.your-domain.com`

## Troubleshooting

### Build Failures

1. **npm ci failing**: The latest version fixes this with proper package.json setup
2. **Permission errors**: Fixed in updated Dockerfiles
3. **Missing dependencies**: Added gcc and build tools

### Runtime Issues

1. **Database connection**: Ensure DATABASE_URL is correctly set by Coolify
2. **CORS errors**: Check ALLOWED_ORIGINS includes your domain
3. **API not responding**: Verify all environment variables are set

### Checking Logs

In Coolify dashboard:
- Click on your application
- Go to "Logs" tab
- Select service (api, web, worker)
- Check for errors

## Getting API Keys

### OpenRouter (for AI Judge)
1. Go to https://openrouter.ai/
2. Sign up and get API key
3. Add to environment: `OPENROUTER_API_KEY=sk-or-...`

### GitHub (for Workspace Management)
1. Go to GitHub Settings → Developer settings → Personal access tokens
2. Create token with `repo` permissions
3. Add to environment: `GITHUB_TOKEN=ghp_...`

## First Usage

1. **Access web interface** at your domain
2. **Create first task**:
   - Go to "Create Task"
   - Upload HTML/CSS baseline files
   - Configure scoring criteria
   - Set agent prompts
3. **Run evaluation**:
   - Go to "Start Evaluation"  
   - Select task and agents
   - Follow instructions to run agents manually
   - Mark complete for automated scoring

## Scaling

- **Worker replicas**: Increase worker instances for more concurrent evaluations
- **Database**: Coolify handles PostgreSQL scaling
- **Redis**: Single instance sufficient for most workloads

## Updates

To update the deployment:
1. Push changes to GitHub
2. Coolify auto-deploys from main branch
3. Monitor logs during deployment

---

🎉 **Your AI Agent Evaluation Platform is ready for production!**
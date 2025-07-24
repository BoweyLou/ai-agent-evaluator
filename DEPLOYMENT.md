# Deployment Guide for AI Agent Evaluation Platform

## Coolify Deployment

### Important: Use Production Docker Compose

When deploying on Coolify, use `docker-compose.prod.yml` instead of the default `docker-compose.yml`.

The production compose file:
- Removes volume mounts that override container contents
- Sets production environment defaults
- Adds restart policies

### Configuration in Coolify

1. In your Coolify application settings, set the compose file path to:
   ```
   docker-compose.prod.yml
   ```

2. Set these environment variables:
   ```
   # Required
   DATABASE_URL=postgresql://postgres:password@db:5432/evaluator
   REDIS_URL=redis://redis:6379
   SECRET_KEY=your-ultra-secure-secret-key-here
   
   # Set to your actual Coolify domains
   REACT_APP_API_URL=https://your-api-domain.coolify.io
   ALLOWED_ORIGINS=https://your-web-domain.coolify.io,https://your-api-domain.coolify.io
   ```

3. After deployment, configure API keys via the web interface at `/settings`

### Troubleshooting

If you see "no available server" errors:
- Ensure REACT_APP_API_URL is set to your actual API domain
- Check that ALLOWED_ORIGINS includes both web and API domains
- Verify all containers are healthy in Coolify logs

### Port Configuration

Default ports (can be changed via environment variables):
- API: 8082
- Web: 3001
- Database: 5433
- Redis: 6381
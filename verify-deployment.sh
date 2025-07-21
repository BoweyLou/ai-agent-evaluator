#!/bin/bash

# Deployment Verification Script for AI Agent Evaluator
# Usage: ./verify-deployment.sh [BASE_URL]

BASE_URL=${1:-"http://localhost"}
API_URL="$BASE_URL:8000"
WEB_URL="$BASE_URL:3000"

echo "🚀 Verifying AI Agent Evaluator Deployment"
echo "=========================================="
echo "API URL: $API_URL"
echo "Web URL: $WEB_URL"
echo ""

# Function to check URL with timeout
check_url() {
    local url=$1
    local name=$2
    local expected_code=${3:-200}
    
    echo -n "Checking $name... "
    
    if response=$(curl -s -w "%{http_code}" -o /dev/null --max-time 10 "$url" 2>/dev/null); then
        if [[ "$response" == "$expected_code" ]]; then
            echo "✅ OK ($response)"
            return 0
        else
            echo "❌ FAIL (HTTP $response)"
            return 1
        fi
    else
        echo "❌ FAIL (No response)"
        return 1
    fi
}

# Function to check JSON endpoint
check_json() {
    local url=$1
    local name=$2
    local expected_field=$3
    
    echo -n "Checking $name... "
    
    if response=$(curl -s --max-time 10 "$url" 2>/dev/null); then
        if echo "$response" | jq -e ".$expected_field" >/dev/null 2>&1; then
            echo "✅ OK (JSON valid)"
            return 0
        else
            echo "❌ FAIL (Invalid JSON or missing field)"
            return 1
        fi
    else
        echo "❌ FAIL (No response)"
        return 1
    fi
}

# Check basic connectivity
echo "🔍 Basic Connectivity Tests"
echo "----------------------------"
api_ok=0
web_ok=0

if check_url "$API_URL/health" "API Health"; then
    api_ok=1
fi

if check_url "$WEB_URL" "Web Interface"; then
    web_ok=1
fi

echo ""

# Check API endpoints if API is running
if [[ $api_ok -eq 1 ]]; then
    echo "🔍 API Endpoint Tests"
    echo "---------------------"
    check_json "$API_URL/api/v1/agents/" "API Agents" "0"
    check_json "$API_URL/api/v1/tasks/" "API Tasks" "length"
    check_url "$API_URL/api/v1/results/summary" "API Results Summary"
    echo ""
fi

# Check Docker services if running locally
if [[ "$BASE_URL" == "http://localhost" ]]; then
    echo "🐳 Docker Services Check"
    echo "-------------------------"
    
    if command -v docker >/dev/null 2>&1; then
        services=("ai-eval-platform-api-1" "ai-eval-platform-web-1" "ai-eval-platform-db-1" "ai-eval-platform-redis-1")
        
        for service in "${services[@]}"; do
            echo -n "Checking $service... "
            if docker ps --format "table {{.Names}}" | grep -q "$service"; then
                echo "✅ Running"
            else
                echo "❌ Not running"
            fi
        done
    else
        echo "Docker not available - skipping service check"
    fi
    echo ""
fi

# Summary
echo "📋 Deployment Summary"
echo "====================="

if [[ $api_ok -eq 1 && $web_ok -eq 1 ]]; then
    echo "🎉 SUCCESS: Deployment is working!"
    echo ""
    echo "Next steps:"
    echo "1. Access web interface: $WEB_URL"
    echo "2. Create your first task via the web UI"
    echo "3. Set up API keys in environment variables:"
    echo "   - OPENROUTER_API_KEY for AI judge"
    echo "   - GITHUB_TOKEN for workspace management"
    echo ""
    exit 0
elif [[ $api_ok -eq 1 ]]; then
    echo "⚠️  PARTIAL: API is running but web interface failed"
    echo "Check web container logs and build process"
    exit 1
elif [[ $web_ok -eq 1 ]]; then
    echo "⚠️  PARTIAL: Web is running but API failed"
    echo "Check API container logs and dependencies"
    exit 1
else
    echo "❌ FAILED: Both API and web are not responding"
    echo "Check container logs and deployment configuration"
    exit 1
fi
FROM python:3.11-slim

# Install system dependencies
RUN apt-get update && apt-get install -y \
    git \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Create app directory
WORKDIR /app

# Install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Create non-root user
RUN addgroup --gid 1001 --system nodejs && \
    adduser --no-create-home --shell /bin/false --disabled-password --uid 1001 --system --group nodejs

# Create necessary directories
RUN mkdir -p /app/tasks /app/results && \
    chown -R nodejs:nodejs /app

USER nodejs

# Health check
HEALTHCHECK --interval=30s --timeout=3s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

# Expose port
EXPOSE 8000

# Start app
CMD ["uvicorn", "src.main:app", "--host", "0.0.0.0", "--port", "8000"]
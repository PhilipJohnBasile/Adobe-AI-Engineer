# Docker Deployment Guide

## Overview

This guide covers deploying the Creative Automation Pipeline using Docker for production environments.

## Quick Start

### Prerequisites
- Docker 20.10+
- Docker Compose 2.0+
- OpenAI API key

### Basic Deployment

1. **Clone and Setup**:
```bash
git clone <repository-url>
cd Adobe-AI-Engineer
cp .env.example .env
# Edit .env and add your OPENAI_API_KEY
```

2. **Build and Run**:
```bash
# Build the image
docker build -t creative-automation .

# Run single container
docker run -d \
  --name creative_automation \
  -e OPENAI_API_KEY="your-api-key" \
  -v $(pwd)/output:/app/output \
  -v $(pwd)/assets:/app/assets \
  -p 8000:8000 \
  creative-automation

# Or use Docker Compose (recommended)
docker-compose up -d
```

3. **Test the Deployment**:
```bash
# Check system status
docker exec creative_automation python main.py status

# Generate a campaign
docker exec creative_automation python main.py generate campaign_brief_skincare.yaml
```

## Production Deployment

### Environment Configuration

Create a production `.env` file:
```env
OPENAI_API_KEY=your-production-api-key
ENVIRONMENT=production
LOG_LEVEL=INFO
```

### Docker Compose Production

```yaml
version: '3.8'
services:
  creative-automation:
    image: creative-automation:latest
    environment:
      - OPENAI_API_KEY=${OPENAI_API_KEY}
      - ENVIRONMENT=production
    volumes:
      - /data/creative-automation/output:/app/output
      - /data/creative-automation/assets:/app/assets
      - /data/creative-automation/cache:/app/generated_cache
    restart: unless-stopped
    ports:
      - "8000:8000"
```

### Scaling with Multiple Instances

```yaml
version: '3.8'
services:
  creative-automation:
    image: creative-automation:latest
    deploy:
      replicas: 3
      resources:
        limits:
          memory: 2G
          cpus: 1.0
    environment:
      - OPENAI_API_KEY=${OPENAI_API_KEY}
    ports:
      - "8000-8002:8000"
```

## Container Management

### Common Commands

```bash
# View logs
docker logs creative_automation -f

# Execute commands in container
docker exec -it creative_automation bash
docker exec creative_automation python main.py analytics

# Process batch campaigns
docker exec creative_automation python main.py batch /app/campaigns/*.yaml

# Monitor system
docker exec creative_automation python main.py agent --duration 300
```

### Health Monitoring

```bash
# Check container health
docker ps
docker inspect creative_automation | grep Health

# View resource usage
docker stats creative_automation
```

## Volume Management

### Persistent Data

The container uses several mounted volumes:

- `/app/output` - Generated creative assets
- `/app/assets` - Input product images
- `/app/generated_cache` - AI-generated image cache
- `/app/batch_results` - Batch processing results

### Backup Strategy

```bash
# Backup generated assets
docker run --rm -v creative_automation_output:/data -v $(pwd):/backup alpine tar czf /backup/output_backup.tar.gz -C /data .

# Backup cache
docker run --rm -v creative_automation_cache:/data -v $(pwd):/backup alpine tar czf /backup/cache_backup.tar.gz -C /data .
```

## Network Configuration

### Reverse Proxy (Nginx)

```nginx
upstream creative_automation {
    server localhost:8000;
    server localhost:8001;
    server localhost:8002;
}

server {
    listen 80;
    server_name creative-automation.company.com;
    
    location / {
        proxy_pass http://creative_automation;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }
    
    location /health {
        proxy_pass http://creative_automation/health;
    }
}
```

## Security Considerations

### Environment Variables
- Never include API keys in the Docker image
- Use Docker secrets for sensitive data
- Rotate API keys regularly

### Container Security
```bash
# Run with non-root user
docker run --user 1000:1000 creative-automation

# Limit resources
docker run --memory=2g --cpus=1.0 creative-automation

# Read-only filesystem (except mounted volumes)
docker run --read-only --tmpfs /tmp creative-automation
```

## Monitoring and Logging

### Structured Logging
```bash
# Configure JSON logging
docker run -e LOG_FORMAT=json creative-automation

# Ship logs to centralized system
docker run --log-driver=fluentd creative-automation
```

### Metrics Collection
```bash
# Export container metrics
docker run -p 9090:9090 prom/prometheus

# Monitor with Grafana
docker run -p 3000:3000 grafana/grafana
```

## Troubleshooting

### Common Issues

1. **Permission Errors**:
```bash
# Fix volume permissions
docker exec creative_automation chown -R app:app /app/output
```

2. **Memory Issues**:
```bash
# Increase container memory
docker update --memory=4g creative_automation
```

3. **API Rate Limits**:
```bash
# Check API usage
docker exec creative_automation python main.py analytics
```

### Debug Mode
```bash
# Run with debug logging
docker run -e LOG_LEVEL=DEBUG creative-automation

# Interactive debugging
docker run -it --entrypoint=/bin/bash creative-automation
```

## Performance Optimization

### Multi-stage Builds
```dockerfile
# Optimized Dockerfile for production
FROM python:3.11-slim as builder
WORKDIR /build
COPY requirements.txt .
RUN pip install --user -r requirements.txt

FROM python:3.11-slim
COPY --from=builder /root/.local /root/.local
WORKDIR /app
COPY . .
```

### Resource Limits
```yaml
deploy:
  resources:
    limits:
      memory: 2G
      cpus: 1.0
    reservations:
      memory: 1G
      cpus: 0.5
```

## Integration Examples

### Kubernetes Deployment
```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: creative-automation
spec:
  replicas: 3
  template:
    spec:
      containers:
      - name: creative-automation
        image: creative-automation:latest
        env:
        - name: OPENAI_API_KEY
          valueFrom:
            secretKeyRef:
              name: api-keys
              key: openai
```

### CI/CD Pipeline
```yaml
# GitHub Actions example
- name: Build and Deploy
  run: |
    docker build -t creative-automation:${{ github.sha }} .
    docker tag creative-automation:${{ github.sha }} creative-automation:latest
    docker push creative-automation:latest
```

This deployment guide provides enterprise-ready containerization with production best practices for scalability, security, and monitoring.
# Creative Automation Platform - Technical Appendix

## API Endpoints Reference

### Flask API Server (Port 5004) - complete_app.py

| Method | Path | Purpose | Example Request/Response |
|--------|------|---------|-------------------------|
| GET | `/` | Main dashboard | Navigate to http://localhost:5004 |
| GET | `/create-campaign` | Campaign creation form | Returns HTML form page |
| POST | `/upload-campaign` | Upload campaign brief | `multipart/form-data` with YAML file |
| GET | `/view-campaign/<id>` | View campaign details | Returns campaign page with assets |
| GET | `/run-pipeline/<id>` | Execute pipeline for campaign | Triggers generation, returns status |
| GET | `/analytics` | Analytics dashboard | Returns metrics visualization page |
| GET | `/explorer` | Data explorer interface | Browse all system data |
| GET | `/outputs` | List all generated outputs | Returns directory listing |
| GET | `/download/<campaign>/<file>` | Download specific asset | Returns file download |
| GET | `/image/<campaign>/<file>` | Serve image for display | Returns image data |
| GET | `/api/status` | System status JSON | `{"status": "operational", "uptime": 3600}` |
| GET | `/api/ai-monitor-activity` | AI agent activity feed | Returns recent agent actions |
| POST | `/api/run-ai-tool` | Execute AI tool | `{"tool": "generate", "params": {...}}` |
| POST | `/api/campaigns/<id>/run` | Run campaign generation | `{"options": {"verbose": true}}` |
| POST | `/api/campaigns/<id>/validate` | Validate campaign | Returns validation results |
| POST | `/api/campaigns/<id>/update` | Update campaign data | `{"updates": {...}}` |
| GET | `/api/explorer/<section>` | Get explorer section data | Returns filtered data |
| GET | `/healthz` | Health check endpoint | `{"healthy": true}` |

### FastAPI Server (Port 8000) - src/api_server.py

| Method | Path | Purpose | Example Request/Response |
|--------|------|---------|-------------------------|
| POST | `/api/generate` | Generate creative assets | Request: `{"campaign_brief": "path/to/brief.yaml", "options": {"localize": ["US", "DE"]}}` |
| GET | `/api/campaigns` | List all campaigns | Response: `[{"id": "camp_123", "name": "Summer Sale"}]` |
| GET | `/api/campaigns/{id}` | Get campaign details | Response: `{"id": "camp_123", "status": "completed"}` |
| POST | `/api/compliance/check` | Run compliance check | Request: `{"campaign_id": "camp_123"}` |
| POST | `/api/localize` | Localize campaign | Request: `{"campaign_id": "camp_123", "markets": ["DE", "FR"]}` |
| GET | `/api/metrics` | Get system metrics | Response: `{"campaigns_processed": 100, "avg_time": 30.5}` |
| POST | `/api/predict/performance` | Predict campaign performance | Request: `{"campaign_id": "camp_123"}` |
| GET | `/api/models` | List ML models | Response: `{"models": ["ctr_predictor", "conversion_model"]}` |
| POST | `/api/agent/trigger` | Trigger AI agent action | Request: `{"action": "scan", "target": "campaign_briefs/"}` |
| GET | `/api/agent/status` | Get agent status | Response: `{"active": true, "last_scan": "2024-09-17T10:00:00Z"}` |
| GET | `/docs` | Interactive API documentation | Swagger UI interface |
| GET | `/redoc` | Alternative API docs | ReDoc interface |
| GET | `/health` | Health check | `{"status": "healthy", "timestamp": "2024-09-17T10:00:00Z"}` |

---

## Environment Variables

| Variable Name | Required | Purpose | Default/Example |
|---------------|----------|---------|-----------------|
| `OPENAI_API_KEY` | **Yes** | OpenAI API authentication | `sk-proj-xxxxx` |
| `FLASK_PORT` | No | Flask server port | `5004` |
| `API_PORT` | No | FastAPI server port | `8000` |
| `ENVIRONMENT` | No | Deployment environment | `development` / `production` |
| `LOG_LEVEL` | No | Logging verbosity | `INFO` / `DEBUG` |
| `CACHE_ENABLED` | No | Enable asset caching | `true` |
| `CACHE_DIR` | No | Cache directory path | `./generated_cache` |
| `OUTPUT_DIR` | No | Output directory | `./output` |
| `MAX_WORKERS` | No | Parallel processing threads | `4` |
| `RATE_LIMIT` | No | API rate limiting | `100` requests/minute |
| `BUDGET_LIMIT` | No | Daily API cost limit | `100.00` (USD) |
| `PROMETHEUS_ENABLED` | No | Enable metrics collection | `true` |
| `ALERT_WEBHOOK` | No | Webhook URL for alerts | `https://hooks.slack.com/xxx` |
| `S3_BUCKET` | No | S3 bucket for storage | `creative-assets-prod` |
| `AZURE_STORAGE_ACCOUNT` | No | Azure storage account | `creativestorage` |
| `MONGODB_URI` | No | MongoDB connection string | `mongodb://localhost:27017` |
| `POSTGRES_URL` | No | PostgreSQL connection | `postgresql://user:pass@localhost/db` |
| `REDIS_URL` | No | Redis cache connection | `redis://localhost:6379` |
| `SENTRY_DSN` | No | Error tracking | `https://xxx@sentry.io/xxx` |
| `DD_API_KEY` | No | Datadog monitoring | `dd_api_key_xxx` |

---

## Data Stores Overview

### SQLite Databases

| Database File | Purpose | Key Tables | Usage |
|--------------|---------|------------|--------|
| `analytics.db` | Performance analytics | `campaigns`, `metrics`, `predictions` | Stores campaign performance data and ML predictions |
| `audit_logs.db` | Audit trail | `events`, `users`, `actions` | Compliance and security audit logging |
| `collaboration.db` | Team collaboration | `projects`, `comments`, `approvals` | Workflow and approval tracking |
| `tenants.db` | Multi-tenancy | `tenants`, `subscriptions`, `usage` | Client isolation and billing |
| `cache.db` | Asset cache index | `assets`, `metadata`, `usage_stats` | Tracks cached assets for reuse |

### File Storage Structure

```
output/                      # Generated campaign assets
├── campaign_[timestamp]/    # Individual campaign outputs
│   ├── [product_name]/     # Product-specific assets
│   │   ├── 1x1.jpg        # Square aspect ratio
│   │   ├── 9x16.jpg       # Vertical aspect ratio
│   │   └── 16x9.jpg       # Horizontal aspect ratio
│   ├── compliance_report.txt
│   └── generation_report.json

batch_output/               # Batch processing results
├── batch_[timestamp]/     # Batch job outputs
│   └── summary.json       # Batch execution summary

generated_cache/           # Cached generated assets
├── [hash].jpg            # Cached images by content hash
└── cache_index.json      # Cache metadata

logs/                     # Application logs
├── app.log              # Main application log
├── generation.log       # Generation pipeline log
├── agent.log           # AI agent activity log
└── error.log           # Error tracking log

alerts/                  # Generated alerts
└── alert_[timestamp].json  # Individual alert records

models/                  # Trained ML models
├── ctr_predictor.joblib      # Click-through rate model
├── conversion_model.joblib   # Conversion prediction model
└── engagement_scorer.joblib  # Engagement scoring model
```

---

## Test Instructions

### Unit Tests
```bash
# Run all unit tests
pytest tests/unit/ -v

# Run with coverage
pytest tests/unit/ --cov=src --cov-report=html

# Run specific module tests
pytest tests/unit/test_image_generator.py -v
```

### Integration Tests
```bash
# Run integration tests
pytest tests/integration/ -v

# Test pipeline end-to-end
python3 test_task3_complete.py

# Test enhanced features
python3 test_enhanced_task3.py
```

### Performance Tests
```bash
# Load testing
python3 tests/performance/load_test.py --campaigns 100 --parallel 10

# Stress testing
python3 tests/performance/stress_test.py --duration 600
```

### Key Test Suites

| Test Suite | Command | Purpose | Expected Duration |
|------------|---------|---------|-------------------|
| Core Pipeline | `pytest tests/unit/test_pipeline.py` | Validate core generation flow | 30 seconds |
| Compliance | `pytest tests/unit/test_compliance.py` | Test brand validation | 15 seconds |
| AI Agent | `python3 test_ai_agent_comprehensive.py` | Test monitoring system | 2 minutes |
| API Endpoints | `pytest tests/integration/test_api.py` | Validate all endpoints | 1 minute |
| ML Models | `pytest tests/unit/test_models.py` | Test prediction accuracy | 45 seconds |
| Localization | `pytest tests/unit/test_localization.py` | Verify market adaptation | 30 seconds |

### Pre-Demo Test Checklist
```bash
# Quick smoke test before demo
./scripts/smoke_test.sh

# Or manually:
python3 main.py validate campaign_briefs/flash_sale_weekend.yaml
python3 main.py compliance campaign_briefs/flash_sale_weekend.yaml
python3 -c "import openai; print('API OK')"
curl -s http://localhost:5004/healthz
```

---

## Docker & Docker Compose

### Docker Build
```bash
# Build production image
docker build -t creative-automation:latest .

# Build with specific Python version
docker build --build-arg PYTHON_VERSION=3.10 -t creative-automation:py310 .

# Multi-stage build for smaller image
docker build -f Dockerfile.multistage -t creative-automation:slim .
```

### Docker Run Options
```bash
# Basic run
docker run -p 5004:5004 creative-automation

# With volume mounts
docker run -d \
  --name creative-platform \
  -p 5004:5004 \
  -p 8000:8000 \
  -v $(pwd)/output:/app/output \
  -v $(pwd)/campaign_briefs:/app/campaign_briefs \
  -v $(pwd)/logs:/app/logs \
  --env-file .env \
  creative-automation

# With resource limits
docker run -d \
  --memory="2g" \
  --cpus="2" \
  --restart=unless-stopped \
  creative-automation
```

### Docker Compose Services
```yaml
# docker-compose.yml structure
services:
  app:            # Main application (port 5004)
  api:            # FastAPI server (port 8000)
  prometheus:     # Metrics collection (port 9090)
  grafana:        # Dashboards (port 3000)
  redis:          # Cache backend (port 6379)
  postgres:       # Database (port 5432)
```

### Container Management
```bash
# View running containers
docker ps

# View logs
docker logs -f creative-platform

# Execute commands in container
docker exec creative-platform python3 main.py status

# Copy files from container
docker cp creative-platform:/app/output ./local_output

# Clean up
docker stop creative-platform
docker rm creative-platform
docker system prune -a  # Remove unused images
```

### Port Mappings

| Service | Internal Port | External Port | Purpose |
|---------|--------------|---------------|---------|
| Flask App | 5004 | 5004 | Web interface |
| FastAPI | 8000 | 8000 | REST API |
| Prometheus | 9090 | 9090 | Metrics |
| Grafana | 3000 | 3000 | Dashboards |
| Redis | 6379 | 6379 | Cache |
| PostgreSQL | 5432 | 5432 | Database |

---

## Known Issues & Fixes

### Issue 1: OpenAI Rate Limiting
**Symptom:** `Error: Rate limit exceeded`
**Fix:**
```bash
# Implement exponential backoff
export RATE_LIMIT=50  # Reduce requests per minute

# Or use alternative provider
python3 main.py generate brief.yaml --provider azure
```

### Issue 2: Memory Issues with Large Batches
**Symptom:** `MemoryError` during batch processing
**Fix:**
```bash
# Reduce batch size
python3 main.py batch process *.yaml --batch-size 10

# Increase Docker memory
docker run --memory="4g" creative-automation
```

### Issue 3: Cache Corruption
**Symptom:** Incorrect assets being retrieved
**Fix:**
```bash
# Clear cache
rm -rf generated_cache/*
rm -f cache.db

# Rebuild cache index
python3 scripts/rebuild_cache.py
```

### Issue 4: Port Conflicts
**Symptom:** `Address already in use`
**Fix:**
```bash
# Find conflicting process
lsof -i :5004
kill -9 <PID>

# Or use alternative port
FLASK_PORT=5005 python3 complete_app.py
```

### Issue 5: Database Lock
**Symptom:** `Database is locked`
**Fix:**
```bash
# Remove lock files
rm *.db-journal

# Or switch to PostgreSQL
export DATABASE_URL=postgresql://user:pass@localhost/creative
```

### Issue 6: SSL Certificate Errors
**Symptom:** `SSL: CERTIFICATE_VERIFY_FAILED`
**Fix:**
```bash
# Update certificates
pip install --upgrade certifi

# Or disable SSL (development only)
export PYTHONHTTPSVERIFY=0
```

### Issue 7: Slow Generation Times
**Symptom:** Generation takes >60 seconds
**Fix:**
```bash
# Enable caching
export CACHE_ENABLED=true

# Increase workers
export MAX_WORKERS=8

# Use GPU acceleration (if available)
export CUDA_VISIBLE_DEVICES=0
```

### Issue 8: Missing Aspect Ratios
**Symptom:** Not all aspect ratios generated
**Fix:**
```python
# Check brief structure
campaign_brief:
  output_requirements:
    aspect_ratios: ["1:1", "9:16", "16:9"]  # Ensure all listed
```

---

## Performance Tuning

### Optimization Settings
```bash
# Environment variables for performance
export MAX_WORKERS=8          # Parallel threads
export CACHE_ENABLED=true     # Asset caching
export CACHE_SIZE_MB=1000     # Cache size limit
export CONNECTION_POOL=20     # Database connections
export BATCH_SIZE=50          # Batch processing size
```

### Database Optimization
```sql
-- Create indexes for common queries
CREATE INDEX idx_campaigns_status ON campaigns(status);
CREATE INDEX idx_metrics_timestamp ON metrics(timestamp);
CREATE INDEX idx_cache_hash ON cache(content_hash);

-- Vacuum and analyze (SQLite)
VACUUM;
ANALYZE;
```

### Redis Cache Configuration
```bash
# redis.conf optimizations
maxmemory 1gb
maxmemory-policy allkeys-lru
save ""  # Disable persistence for cache
```

---

## Security Checklist

- [ ] API keys stored in `.env` file, not in code
- [ ] `.env` file excluded from version control
- [ ] HTTPS enabled for production deployment
- [ ] Rate limiting configured on all endpoints
- [ ] Input validation on all user inputs
- [ ] SQL injection prevention (parameterized queries)
- [ ] XSS protection (output encoding)
- [ ] CSRF tokens for state-changing operations
- [ ] Audit logging enabled
- [ ] Secrets rotated regularly
- [ ] Dependencies updated (no known vulnerabilities)
- [ ] Docker images scanned for vulnerabilities
- [ ] Network policies configured (if using Kubernetes)
- [ ] Backup strategy in place
- [ ] Disaster recovery plan documented

---

## Monitoring Queries

### Prometheus Queries
```promql
# Campaign processing rate
rate(campaigns_processed_total[5m])

# API response time (95th percentile)
histogram_quantile(0.95, rate(http_request_duration_seconds_bucket[5m]))

# Error rate
rate(errors_total[5m]) / rate(requests_total[5m])

# Cache hit ratio
rate(cache_hits_total[5m]) / rate(cache_requests_total[5m])

# Cost per hour
rate(api_cost_dollars[1h]) * 3600
```

### Log Analysis Commands
```bash
# Most common errors
grep ERROR logs/app.log | awk '{print $4}' | sort | uniq -c | sort -rn

# Campaign processing times
grep "Generation complete" logs/generation.log | awk '{print $NF}' | awk '{sum+=$1} END {print sum/NR}'

# API usage by endpoint
grep "POST\|GET" logs/access.log | awk '{print $6}' | sort | uniq -c | sort -rn

# Alert frequency
ls -la alerts/ | wc -l  # Total alerts
grep CRITICAL alerts/*.json | wc -l  # Critical alerts
```

---

## Deployment Checklist

### Pre-Deployment
- [ ] All tests passing
- [ ] Environment variables configured
- [ ] Database migrations completed
- [ ] SSL certificates installed
- [ ] Backup system tested
- [ ] Monitoring configured
- [ ] Alerts configured
- [ ] Documentation updated

### Deployment Steps
1. Tag release: `git tag -a v1.0.0 -m "Production release"`
2. Build Docker image: `docker build -t creative-automation:v1.0.0 .`
3. Push to registry: `docker push registry/creative-automation:v1.0.0`
4. Update deployment: `kubectl set image deployment/app app=registry/creative-automation:v1.0.0`
5. Verify health: `curl https://api.production.com/health`
6. Run smoke tests: `./scripts/production_smoke_test.sh`

### Post-Deployment
- [ ] Verify all endpoints responding
- [ ] Check metrics in monitoring
- [ ] Verify alerts working
- [ ] Test critical user flows
- [ ] Update status page
- [ ] Notify stakeholders
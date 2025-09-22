# Creative Automation Platform - Live Demo Runbook

## Pre-Demo Setup Checklist

### Environment Preparation
- [ ] Terminal windows arranged (3 windows recommended)
- [ ] Browser tabs ready (localhost:5004, localhost:3000 for Grafana)
- [ ] Clear previous outputs: `rm -rf output/* batch_output/* alerts/*.json`
- [ ] Verify .env file has valid OPENAI_API_KEY
- [ ] Docker Desktop running (if using Docker demo)
- [ ] Check disk space (need ~2GB free)

### Quick Health Check
```bash
# Verify Python version
python3 --version  # Should be 3.9+

# Check dependencies
pip list | grep -E "openai|flask|fastapi|pillow"

# Test API key
python3 -c "import os; print('API Key Set' if os.getenv('OPENAI_API_KEY') or open('.env').read().find('OPENAI_API_KEY') > 0 else 'Missing API Key')"
```

---

## Demo Path A: Local Python Execution

### Step 1: Start Web Interface
**Terminal 1:**
```bash
# Start the main web application
python app.py
```
**Expected Output:**
```
🚀 Creative Automation System - Web Interface
============================================================
📍 Dashboard: http://localhost:5004
🎯 Features:
   • Creative automation pipeline
   • AI monitoring agent
   • Data explorer interface
   • Analytics dashboard
 * Running on all addresses (0.0.0.0)
 * Running on http://127.0.0.1:5004
```

### Step 2: Validate Campaign Briefs
**Terminal 2:**
```bash
# List available campaign briefs
ls -la campaign_briefs/

# Validate a brief
python3 main.py validate campaign_briefs/flash_sale_weekend.yaml
```
**Expected Output:**
```
✅ Valid campaign brief structure
  - Campaign ID: flash_sale_weekend
  - Products: 1 defined
  - Target Regions: US
  - Aspect Ratios: 1:1, 9:16, 16:9
```

### Step 3: Run Compliance Check
```bash
# Check compliance before generation
python3 main.py compliance campaign_briefs/flash_sale_weekend.yaml
```
**Expected Output:**
```
📋 Compliance Check Results:
  Brand Guidelines: ✅ Defined
  Prohibited Terms: ✅ None found
  Color Compliance: ✅ Valid hex codes
  Score: 96.3%
```

### Step 4: Generate Creative Assets
```bash
# Generate with verbose output
python3 main.py generate campaign_briefs/flash_sale_weekend.yaml --verbose
```
**Expected Output:**
```
🚀 Generating Campaign Assets
Campaign: flash_sale_weekend
✅ Validation passed
🎨 Generating assets for: Everything On Sale
  - Creating 1:1 variant...
  - Creating 9:16 variant...
  - Creating 16:9 variant...
✅ Generation complete in 28.3 seconds
📁 Output saved to: output/campaign_20240917_143022/
```

### Step 5: Browse Generated Assets
**In Browser - http://localhost:5004:**
1. Click "All Outputs" in navigation
2. Click on the campaign folder
3. View generated images with different aspect ratios
4. Download compliance report

### Step 6: Start AI Monitoring Agent
**Terminal 3:**
```bash
# Run the AI agent
python3 main.py agent start
```
**Expected Output:**
```
🤖 AI Monitoring Agent Started
  Monitoring: campaign_briefs/
  Check Interval: 10 seconds
  Alert Threshold: 3 variants minimum
[2024-09-17 14:35:22] Scanning for new campaigns...
[2024-09-17 14:35:32] Campaign detected: tech_innovation_summit_2025
[2024-09-17 14:35:33] Triggering generation...
```

### Step 7: Process Multiple Campaigns (Batch)
```bash
# Process all campaigns in batch
python3 main.py batch process campaign_briefs/*.yaml --parallel
```
**Expected Output:**
```
📦 Batch Processing Started
  Files: 3 campaigns found
  Mode: Parallel execution
  
Processing: flash_sale_weekend.yaml [████████] 100%
Processing: sustainable_lifestyle.yaml [████████] 100%
Processing: tech_innovation.yaml [████████] 100%

✅ Batch Complete: 3/3 successful
Time: 45.2 seconds
Cost: $0.92
```

### Step 8: View Analytics
```bash
# Generate analytics report
python3 main.py analytics --export-html

# Open in browser
open analytics_report.html  # macOS
# or
xdg-open analytics_report.html  # Linux
```

---

## Demo Path B: Docker Execution

### Step 1: Build Docker Image
```bash
# Build the container
docker build -t creative-automation:latest .
```
**Expected Output:**
```
[+] Building 45.2s (15/15) FINISHED
=> [internal] load build definition
=> [internal] load .dockerignore
=> [base 1/8] FROM python:3.11-slim
=> [base 2/8] WORKDIR /app
=> [base 3/8] Installing system dependencies
=> CACHED [base 4/8] COPY requirements.txt
=> [base 5/8] RUN pip install -r requirements.txt
=> [base 6/8] COPY . .
=> [base 7/8] RUN mkdir -p output assets
=> [base 8/8] Setting environment variables
=> exporting to image
=> naming to docker.io/library/creative-automation:latest
```

### Step 2: Run Container
```bash
# Run with environment file
docker run -d \
  --name creative-platform \
  -p 5004:5004 \
  -p 8000:8000 \
  -v $(pwd)/output:/app/output \
  -v $(pwd)/campaign_briefs:/app/campaign_briefs \
  --env-file .env \
  creative-automation:latest \
  python app.py
```

### Step 3: Execute Commands in Container
```bash
# Validate campaign brief
docker exec creative-platform \
  python3 main.py validate campaign_briefs/flash_sale_weekend.yaml

# Generate assets
docker exec creative-platform \
  python3 main.py generate campaign_briefs/flash_sale_weekend.yaml
```

### Step 4: View Container Logs
```bash
# Follow logs
docker logs -f creative-platform

# Check specific component logs
docker exec creative-platform cat logs/generation.log
docker exec creative-platform cat logs/agent.log
```

### Step 5: Stop and Clean Up
```bash
# Stop container
docker stop creative-platform

# Remove container
docker rm creative-platform
```

---

## Demo Path C: Docker Compose with Full Stack

### Step 1: Start Full Stack
```bash
# Start all services
docker-compose up -d
```
**Services Started:**
- creative-automation (main app) - port 5004
- api-server (FastAPI) - port 8000
- prometheus (metrics) - port 9090
- grafana (dashboards) - port 3000

### Step 2: Access Services
**Browser Tabs:**
- Main App: http://localhost:5004
- API Docs: http://localhost:8000/docs
- Prometheus: http://localhost:9090
- Grafana: http://localhost:3000 (admin/admin)

### Step 3: Import Grafana Dashboard
1. Open Grafana (http://localhost:3000)
2. Login with admin/admin
3. Go to Dashboards → Import
4. Upload: `monitoring/grafana/dashboards/task3-dashboard.json`
5. Select Prometheus as data source
6. Click Import

### Step 4: Monitor Metrics
**In Grafana Dashboard:**
- Campaign processing rate
- API response times
- Cache hit rates
- Error rates
- Cost tracking

### Step 5: Generate Load for Metrics
```bash
# Generate multiple campaigns to populate metrics
for i in {1..5}; do
  docker-compose exec app \
    python3 main.py generate campaign_briefs/flash_sale_weekend.yaml
  sleep 2
done
```

---

## Monitoring & Alerts Demo

### Step 1: Trigger Alert Condition
```bash
# Create a campaign with insufficient variants
echo 'campaign_brief:
  campaign_id: test_alert
  campaign_name: "Alert Test"
  products:
    - name: "Test Product"
  target_regions: ["US"]
  output_requirements:
    aspect_ratios: ["1:1"]  # Only one ratio (below threshold)
' > campaign_briefs/test_alert.yaml

python3 main.py generate campaign_briefs/test_alert.yaml
```

### Step 2: Check Alert Generation
```bash
# View generated alerts
ls -la alerts/
cat alerts/alert_*.json | jq '.'
```
**Expected Alert:**
```json
{
  "timestamp": "2024-09-17T14:45:00Z",
  "severity": "HIGH",
  "type": "insufficient_variants",
  "campaign_id": "test_alert",
  "message": "Campaign has only 1 variant, minimum 3 required",
  "action_required": "Generate additional aspect ratios"
}
```

### Step 3: View Alert in Web UI
1. Go to http://localhost:5004
2. Click "AI Monitor" in navigation
3. View real-time alert feed
4. Click on alert for details

### Step 4: Check Logs
```bash
# Agent logs
tail -f logs/agent.log

# Generation logs
tail -f logs/generation.log

# Error logs
tail -f logs/error.log
```

---

## Quick Troubleshooting

### Issue: OpenAI API Error
```bash
# Error: "Invalid API key" or rate limit
# Fix: Update .env file
echo "OPENAI_API_KEY=your-valid-key" > .env

# Restart application
pkill -f app.py
python app.py
```

### Issue: Port Already in Use
```bash
# Error: "Address already in use"
# Find and kill process
lsof -i :5004
kill -9 <PID>

# Or use different port
python app.py --port 5005
```

### Issue: Missing Dependencies
```bash
# Error: "ModuleNotFoundError"
# Reinstall requirements
pip install -r requirements.txt

# For specific module
pip install openai pillow flask fastapi
```

### Issue: Docker Build Fails
```bash
# Clean Docker cache
docker system prune -a

# Rebuild with no cache
docker build --no-cache -t creative-automation .
```

### Issue: No Images Generated
```bash
# Check API connectivity
python3 -c "
import openai
from dotenv import load_dotenv
import os
load_dotenv()
openai.api_key = os.getenv('OPENAI_API_KEY')
print(openai.Model.list()['data'][0]['id'])
"

# Should print model ID if working
```

---

## Demo Highlights to Emphasize

### For Creative Lead
- Show the variety of aspect ratios generated
- Demonstrate brand compliance checking
- Highlight the speed (30 seconds vs hours)
- Show localization capabilities

### For Ad Operations
- Demonstrate batch processing capability
- Show the organized output structure  
- Highlight automation of repetitive tasks
- Display cost tracking and optimization

### For IT Department
- Show the API documentation (http://localhost:8000/docs)
- Demonstrate monitoring with Prometheus/Grafana
- Highlight containerization and scalability
- Show security features (audit logs)

### For Legal/Compliance
- Run compliance check command
- Show prohibited terms detection
- Display compliance scoring
- Demonstrate audit trail in logs

---

## Post-Demo Cleanup

```bash
# Stop all services
docker-compose down

# Clean generated files (optional)
rm -rf output/* batch_output/* alerts/*.json logs/*.log

# Reset database (optional)
rm -f *.db

# Clear cache (optional)  
rm -rf generated_cache/*
```

---

## Demo Success Checklist

- [ ] Generated assets for at least 2 different campaign briefs
- [ ] Showed all 3 aspect ratios (1:1, 9:16, 16:9)
- [ ] Demonstrated compliance checking
- [ ] Displayed web interface dashboard
- [ ] Showed AI agent monitoring
- [ ] Triggered and displayed an alert
- [ ] Reviewed analytics/metrics
- [ ] Answered stakeholder-specific questions
- [ ] Collected feedback and next steps

---

## Emergency Demo Fallback

If live generation fails, use pre-generated assets:

```bash
# Copy backup assets
cp -r demo_backup/output/* output/

# Show pre-recorded metrics
open demo_backup/analytics_report.html

# Display sample alerts
cat demo_backup/sample_alert.json | jq '.'
```

**Note:** Always have a backup plan. Pre-generate some assets before the demo and keep them ready in case of API issues or network problems.
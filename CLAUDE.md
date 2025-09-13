# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This is the Creative Automation for Social Campaigns FDE Take-Home Exercise, implementing an AI-driven creative automation pipeline for generating branded marketing assets at scale.

## Common Development Commands

### Setup and Installation
```bash
# Install Python dependencies
pip install -r task2/requirements.txt

# Set up environment variables
cp task2/config/.env.example task2/config/.env
# Edit .env file with your API keys
```

### Running the Pipeline
```bash
# Run the main creative pipeline
cd task2
python src/pipeline.py examples/campaign_brief_example.json

# Run with debug logging
python src/pipeline.py examples/campaign_brief_example.json --debug
```

### Testing
```bash
# Run basic tests (if implemented)
cd task2
python -m pytest tests/

# Test individual components
python -c "from src.generators.image_generator import ImageGenerator; print('Import successful')"
```

### Development Workflow
```bash
# Check code structure
find task2/src -name "*.py" | head -10

# View output assets
ls -la task2/output/

# Monitor logs
tail -f task2/pipeline.log
```

## Architecture Overview

The project consists of three main tasks:

### Task 1: Architecture & Roadmap (`task1/`)
- High-level system architecture documentation
- Implementation roadmap with timeline and investment details
- Stakeholder alignment strategy

### Task 2: Creative Automation Pipeline (`task2/`)
- **Main Pipeline**: `src/pipeline.py` - Central orchestrator
- **Generators**: AI-powered image and text generation
- **Processors**: Asset processing, format conversion, branding
- **Validators**: Brand compliance and legal validation
- **Configuration**: `config/config.yaml` for system settings

### Task 3: Agentic System (`task3/`)
- Intelligent monitoring and orchestration agents
- Stakeholder communication examples
- Automated quality assurance and alerting

## Key Components

### Pipeline Flow
1. **Campaign Brief Ingestion** - Parse JSON/YAML campaign requirements
2. **Asset Discovery** - Check for existing reusable assets  
3. **AI Generation** - Create missing assets using GenAI services
4. **Processing** - Add branding, text overlays, format conversion
5. **Validation** - Brand compliance and legal screening
6. **Output** - Organized multi-format campaign assets

### GenAI Integration (Cost-Optimized)
- **Primary Image**: OpenAI DALL-E 2 for cost-effective generation ($0.02/image)
- **Primary Text**: OpenAI GPT-4o-mini for budget-friendly text ($0.15/$0.60 per M tokens)
- **No Fallbacks**: Single provider for demo simplicity
- **Cost Control**: $2.00 daily budget with automatic enforcement

### Brand Compliance
- Logo detection and placement validation
- Color palette adherence checking  
- Text readability and contrast validation
- Legal disclaimer requirement verification

## Configuration

### Environment Variables Required (Cost-Optimized)
```bash
# OpenAI Services (Primary and Only)
OPENAI_API_KEY=your_openai_api_key_here

# Cost Control Settings
DAILY_BUDGET_LIMIT=2.00
CACHE_ENABLED=true
USE_DALL_E_2=true
```

### Key Configuration Files
- `task2/config/config.yaml` - Main system configuration
- `task2/config/.env` - Environment variables and secrets
- `task2/examples/` - Sample campaign briefs for testing

## Asset Organization

### Input Structure
```
task2/assets/
├── brand/           # Brand assets (logos, guidelines)
├── PROD_001/        # Product-specific existing assets
└── PROD_002/
```

### Output Structure
```
task2/output/
├── PROD_001/        # Generated assets by product
│   ├── PROD_001_square_North America_timestamp.png
│   ├── PROD_001_story_North America_timestamp.png
│   └── PROD_001_landscape_North America_timestamp.png
└── campaign_report_timestamp.json
```

## Development Notes

### Running the Demo
1. Add your OpenAI API key to `task2/config/.env`
2. Run `python demo_mode.py` from `task2/` directory
3. Generated assets saved to `task2/output/demo/`

### Cost Monitoring
1. Real-time budget tracking in `cost_tracker.py`
2. Automatic generation blocking at budget limit
3. Complete audit trail of all API costs

### Localization Support
- Text generation supports: English, Spanish, French, German, Italian
- Add new languages in `src/generators/text_generator.py`
- Update localization rules in the configuration

## Troubleshooting

### Common Issues
- **"Billing hard limit reached"**: Add funds to OpenAI account or use demo mode
- **"Prompt too long"**: Prompts auto-truncated to 1000 chars for DALL-E 2
- **Budget exceeded**: Automatic blocking when daily limit reached
- **Unicode errors**: Windows console encoding (doesn't affect functionality)

### Demo Commands
```bash
# Run full demonstration
python demo_mode.py

# Check cost tracking
python -c "from src.utils.cost_tracker import CostTracker; print('Cost tracking ready')"

# Verify configuration
python -c "import yaml; print('Config loaded')"
```

## Performance Optimization

- Configure `concurrent_generations` in config for parallel processing
- Enable caching for repeated similar requests
- Use appropriate image resolution settings
- Monitor API quota usage to avoid throttling

## Security Considerations

- Never commit API keys to repository
- Use environment variables for sensitive configuration
- Validate all input briefs before processing
- Implement appropriate access controls for production deployment

This pipeline demonstrates enterprise-grade creative automation with comprehensive validation, monitoring, and scalability features.
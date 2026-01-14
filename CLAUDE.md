# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This is an Adobe Forward Deployed AI Engineer take-home exercise focused on building a creative automation pipeline for scalable social ad campaigns. The project consists of three main tasks:

1. **Architecture Design**: High-level architecture diagram and roadmap for a content pipeline
2. **Creative Automation Pipeline**: Proof-of-concept implementation that automates creative asset generation using GenAI
3. **Agentic System Design**: AI-driven agent design for monitoring and managing campaign workflows

## Development Commands

### Running the Application

```bash
# Install dependencies
pip install -r requirements.txt

# Start the web dashboard (MAIN ENTRY POINT)
python3 complete_app.py
# Dashboard available at http://localhost:5004

# Run the unified pipeline (CLI)
python3 src/unified_task123_system.py <campaign_id>

# Run the main CLI with 30+ commands
python3 main.py --help
```

### Key Entry Points

| File | Purpose |
|------|---------|
| `complete_app.py` | **Main web dashboard** - Full-featured Flask UI with analytics, monitoring, campaign management |
| `src/unified_task123_system.py` | Unified CLI pipeline combining all three tasks |
| `main.py` | CLI interface with 30+ commands for generation, validation, monitoring |
| `app.py` | ~~Basic Flask server~~ (DEPRECATED - use complete_app.py instead) |

## Project Architecture

### Core Modules (src/)

- **production_ai_agent.py**: Enterprise-grade AI monitoring agent with ML integration
- **unified_task123_system.py**: Orchestrates all three tasks in a single pipeline
- **image_generator.py**: AI image generation with DALL-E integration
- **creative_composer.py**: Image composition and text overlay
- **compliance_checker.py**: Brand and legal compliance validation
- **asset_manager.py**: Asset discovery and management

### Web Templates (templates/)

- **complete_dashboard.html**: Full-featured dashboard UI (178KB)
- **create_campaign.html**: Campaign creation form
- **analytics.html**: Analytics and reporting
- **dashboard.html**: ~~Basic dashboard~~ (deprecated)

## Key Technical Requirements

1. **Campaign Brief Format**: Accept JSON/YAML with product, region, audience, and message fields
2. **Asset Generation**: OpenAI DALL-E 3 integration with multi-provider failover
3. **Aspect Ratios**: Generate 1:1, 9:16, 16:9, 4:5, 2:1 for all platforms
4. **Local Execution**: Runs locally as CLI tool or web app
5. **Output Organization**: Clear folder structure under output/

## Environment Setup

```bash
# Required environment variables (.env file)
OPENAI_API_KEY=sk-your-api-key-here
```

## Testing

```bash
# Run unit tests
pytest tests/ -v

# Test AI agent system
python3 main.py agent test

# Test unified pipeline
python3 src/unified_task123_system.py test_campaign
```

## Common Issues

### Missing Dependencies
If you see `ModuleNotFoundError`, install dependencies:
```bash
pip install -r requirements.txt
```

### Import Errors in src/
The src/ modules use relative imports. Run from the project root directory.

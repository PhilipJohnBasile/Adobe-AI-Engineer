# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This is an Adobe Forward Deployed AI Engineer take-home exercise focused on building a creative automation pipeline for scalable social ad campaigns. The project consists of three main tasks:

1. **Architecture Design**: High-level architecture diagram and roadmap for a content pipeline
2. **Creative Automation Pipeline**: Proof-of-concept implementation that automates creative asset generation using GenAI
3. **Agentic System Design**: AI-driven agent design for monitoring and managing campaign workflows

## Development Commands

Since the implementation hasn't been started yet, commands will depend on the technology stack chosen. Based on the .gitignore file, the project may use:

### For Python Implementation
```bash
# Create virtual environment
python -m venv venv
source venv/bin/activate  # On macOS/Linux

# Install dependencies (once requirements.txt exists)
pip install -r requirements.txt

# Run the pipeline (typical structure)
python task2/main.py --config config.yaml
```

### For Node.js/TypeScript Implementation
```bash
# Install dependencies (once package.json exists)
npm install

# Run development server
npm run dev

# Build production
npm run build

# Run tests
npm test
```

## Project Architecture

### Task 2 Implementation Structure
The creative automation pipeline should include:

- **Asset Ingestion Module**: Accept campaign briefs (JSON/YAML) and input assets
- **Storage Layer**: Local folder or mock storage for assets
- **GenAI Integration**: 
  - Image generation when assets are missing
  - Support for multiple aspect ratios (1:1, 9:16, 16:9)
  - Text overlay for campaign messages
- **Output Management**: Organized by product and aspect ratio in task2/output/

### Key Technical Requirements

1. **Campaign Brief Format**: Accept JSON/YAML with product, region, audience, and message fields
2. **Asset Generation**: Use GenAI APIs (Adobe Firefly, OpenAI DALL-E, or similar) for missing assets
3. **Aspect Ratios**: Generate at least three ratios (1:1 for Instagram, 9:16 for Stories, 16:9 for YouTube)
4. **Local Execution**: Must run locally as CLI tool or simple app
5. **Output Organization**: Clear folder structure under task2/output/

## Implementation Considerations

### GenAI API Integration
- Store API keys in .env file (already in .gitignore)
- Implement rate limiting and error handling for API calls
- Cache generated assets to minimize API costs (see cache.json in .gitignore)

### Asset Processing
- Use image processing libraries (Pillow for Python, Sharp for Node.js)
- Implement text overlay with brand-compliant fonts
- Ensure proper image resizing while maintaining quality

### Optional Features (Bonus Points)
- Brand compliance checks (logo presence, color validation)
- Legal content checks (prohibited words flagging)
- Logging and reporting mechanisms

## Testing Approach

Test the pipeline with:
1. Multiple campaign briefs with varying products
2. Missing asset scenarios to trigger GenAI generation
3. Different aspect ratio outputs
4. Edge cases (invalid briefs, API failures)

## Deliverable Requirements

1. **Working Code**: Complete Task 2 implementation
2. **Documentation**: Comprehensive README with setup, usage, examples
3. **Architecture Diagrams**: Task 1 deliverables
4. **AI Agent Design**: Task 3 specifications and stakeholder communication
5. **Demo Recording**: Screen recording showing the pipeline in action
6. **Presentation**: 30-minute presentation covering all three tasks
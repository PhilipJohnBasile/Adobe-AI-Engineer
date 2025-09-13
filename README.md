# Creative Automation for Social Campaigns - FDE Take-Home Exercise

A comprehensive creative automation pipeline that enables creative teams to generate variations for campaign assets using GenAI, designed for a global consumer goods company launching hundreds of localized social ad campaigns monthly.

## Project Overview

This project addresses the challenge of scaling creative content production while maintaining brand consistency and maximizing local relevance. It automates the generation of social media campaign assets across multiple aspect ratios and markets.

## Business Goals Addressed

- **Accelerate campaign velocity**: Rapidly produce campaign variations
- **Ensure brand consistency**: Maintain global brand guidelines
- **Maximize relevance & personalization**: Adapt to local cultures and preferences
- **Optimize marketing ROI**: Improve campaign efficiency
- **Gain actionable insights**: Track effectiveness at scale

## Project Structure

```
├── README.md                           # This file
├── task1/                             # High-level architecture and roadmap
│   ├── architecture_diagram.md        # Detailed architecture documentation
│   └── roadmap.md                     # Implementation roadmap
├── task2/                             # Creative automation pipeline (PoC)
│   ├── src/
│   │   ├── pipeline.py                # Main pipeline implementation
│   │   ├── generators/                # GenAI integration modules
│   │   ├── processors/                # Asset processing utilities
│   │   └── validators/                # Brand and compliance checks
│   ├── config/                        # Configuration files
│   ├── assets/                        # Input assets storage
│   ├── output/                        # Generated campaign assets
│   ├── examples/                      # Sample campaign briefs
│   └── requirements.txt               # Python dependencies
├── task3/                             # Agentic system design
│   ├── agent_design.md                # AI agent system architecture
│   └── stakeholder_communication.md   # Sample communications
└── presentation/                       # Presentation materials
    └── Creative_Automation_Presentation.md
```

## Quick Start

### Prerequisites

- Python 3.8+
- OpenAI API key (demo mode works without credits)
- Git

### Installation

1. Clone the repository:
```bash
git clone <repository-url>
cd adobe-creative-automation
```

2. Install dependencies:
```bash
pip install -r task2/requirements.txt
```

3. Set up environment variables:
```bash
cp task2/config/.env.example task2/config/.env
# Edit .env with your OpenAI API key (optional - demo mode works without)
```

4. Run the demo pipeline:
```bash
cd task2
python demo_mode.py
```

5. Or run with a custom campaign brief:
```bash
cd task2
python src/pipeline.py examples/campaign_brief_sample.json
```

## Features

### Task 1: Architecture & Roadmap
- Comprehensive system architecture for creative automation
- Stakeholder-aligned roadmap with clear milestones
- Integration points for storage, GenAI, and compliance systems

### Task 2: Creative Pipeline (PoC) - OpenAI Implementation
- **Campaign Brief Processing**: JSON/YAML campaign brief ingestion
- **OpenAI DALL-E 2**: Cost-optimized image generation ($0.016-0.020 per image)
- **OpenAI GPT-4o-mini**: Efficient text generation and localization
- **Multi-Format Output**: Standard social media aspect ratios (1:1, 9:16, 16:9)
- **Brand Compliance**: Automated validation with color/logo analysis
- **Cost Tracking**: Real-time budget monitoring with $2.00 daily demo limit
- **Demo Mode**: Graceful fallback when API limits are reached

### Task 3: Agentic System
- **Intelligent Monitoring**: Automated brief processing
- **Quality Assurance**: Asset sufficiency validation
- **Stakeholder Communication**: Automated alerts and reporting
- **Model Context Protocol**: Structured LLM interactions

## Technology Stack - Cost-Optimized Implementation

- **Backend**: Python 3.8+ with OpenAI API integration
- **Image Generation**: OpenAI DALL-E 2 (cost-optimized at $0.016-0.020/image)
- **Text Generation**: OpenAI GPT-4o-mini (efficient localization and copy)
- **Image Processing**: Pillow, OpenCV for format conversion and branding
- **Cost Management**: Real-time budget tracking and API quota monitoring
- **Storage**: Local filesystem with organized asset structure
- **Configuration**: YAML/JSON with environment variable management
- **Demo Features**: Mock asset generation when API limits reached

## Key Design Decisions

1. **Cost-Optimized GenAI**: Using OpenAI DALL-E 2 and GPT-4o-mini for maximum efficiency
2. **Real-Time Budget Control**: Daily spending limits with automatic generation blocking
3. **Graceful Degradation**: Demo mode fallback when API limits are reached
4. **Standard Social Formats**: Focus on core social media aspect ratios (1:1, 9:16, 16:9)
5. **Enterprise-Ready Architecture**: Scalable design suitable for production deployment

## Assumptions & Limitations

- OpenAI API key required for live generation (demo mode available without credits)
- Internet connectivity required for OpenAI API calls
- Multi-language support for localization (English, Spanish, French, German, Italian)
- Local filesystem storage for demo (enterprise storage integration possible)
- Basic brand compliance validation (can be enhanced with advanced AI models)
- Daily budget limit of $2.00 configured for cost-controlled demonstrations

## Demo Video

A demonstration video showing the complete pipeline in action is available in the presentation folder.

## Next Steps

1. Run the example campaign brief
2. Review generated assets in `task2/output/`
3. Explore the architecture documentation in `task1/`
4. Check the agentic system design in `task3/`

For detailed implementation information, see the individual task directories.
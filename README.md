# Adobe Creative Automation Platform

**Adobe AI Engineer Take-Home Exercise - Complete Implementation**

A production-ready creative automation pipeline that generates social ad campaign assets using GenAI, designed for global consumer goods companies launching hundreds of localized campaigns monthly.

## Overview

This enterprise platform automates the creation of creative assets for social ad campaigns by:
- Accepting campaign briefs in YAML/JSON format
- Managing existing assets or generating new ones using OpenAI DALL-E
- Composing final creatives with text overlays and brand elements
- Outputting assets in multiple aspect ratios (1:1, 9:16, 16:9)
- Providing intelligent monitoring with automated alerts and stakeholder communication

## Quick Start

### Prerequisites
- Python 3.8+
- OpenAI API key

### Installation

1. Clone the repository:
```bash
git clone <repository-url>
cd Adobe-AI-Engineer
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

3. Configure API key:
```bash
cp .env.example .env
# Edit .env and add your OpenAI API key
```

## Usage

### Adobe Creative Automation Platform Web Interface

Start the professional web application:

```bash
python3 complete_app.py
```

Then open: http://localhost:5004

**Enterprise Platform Features:**
- **Campaign Creation**: Intuitive form-based campaign brief creation with validation
- **Real-time Pipeline Execution**: Live progress tracking with detailed console output
- **Intelligent Monitoring**: Automated alerts, performance tracking, and stakeholder notifications
- **System Analytics**: Dashboard with performance metrics, system status, and cost tracking
- **Asset Management**: Browse, download, and manage generated creative assets
- **CLI Integration**: Access to all 26 professional CLI commands through web interface
- **Enterprise Tools**: Multi-tenant support, audit logging, and compliance tracking

### Command Line Interface

Generate creative assets from a campaign brief:

```bash
python3 main.py generate campaign_brief_example.yaml
```

### Available Commands

The system provides **26 professional CLI commands** organized into 4 categories:

#### 🎯 Core Pipeline Commands (6)
- **`generate`** - Generate creative assets for a social ad campaign
  ```bash
  python3 main.py generate campaign_brief.yaml --verbose --localize DE
  ```
- **`validate`** - Validate campaign brief file structure and content
- **`compliance`** - Run comprehensive compliance check on campaign brief
- **`localize`** - Localize campaign brief for specific market (US, UK, DE, JP, FR)
- **`markets`** - List supported markets and their localization details
- **`status`** - Get current system status from AI agent

#### 🏢 Enterprise Commands (11)
- **`tenant`** - Multi-tenant architecture management for enterprise isolation
- **`audit`** - Audit logging and compliance reporting for enterprise governance
- **`monitor`** - Advanced monitoring and observability system
- **`optimize`** - Performance optimization with caching and image optimization
- **`workflow`** - Workflow orchestration with visual pipeline designer
- **`serve`** - Start API server for system integration
- **`webhooks`** - Webhook notification system management
- **`ab-test`** - A/B testing framework for creative variants
- **`adobe`** - Adobe Creative Cloud SDK integration management
- **`analytics`** - Generate performance analytics dashboard
- **`moderate`** - Content moderation and brand safety validation

#### 🤖 Brand Intelligence Commands (4)
- **`brand`** - Advanced Computer Vision & Brand Intelligence System
- **`agent`** - AI agent system for monitoring campaigns and generating alerts
- **`batch`** - Process multiple campaigns in batch with optimization
- **`queue`** - Check batch processing queue status

#### 🔮 AI Enhancement Commands (5)
- **`predict-performance`** - Real-Time Creative Performance Prediction
- **`adobe-integration`** - Adobe Ecosystem Integration
- **`personalize`** - Intelligent Content Personalization
- **`collaborate`** - Enterprise Collaboration Platform
- **`analyze-performance`** - Advanced Analytics & Learning Loop

### Command Usage Examples

#### Basic Workflow
```bash
# 1. Validate campaign brief
python3 main.py validate campaign_brief_skincare.yaml

# 2. Check compliance
python3 main.py compliance campaign_brief_skincare.yaml

# 3. Generate assets
python3 main.py generate campaign_brief_skincare.yaml --verbose

# 4. Check status
python3 main.py status
```

#### Enterprise Workflow
```bash
# 1. Create tenant
python3 main.py tenant create enterprise_client

# 2. Start monitoring
python3 main.py monitor start

# 3. Generate with analytics
python3 main.py generate campaign_brief.yaml --verbose
python3 main.py analytics --export-html

# 4. Audit compliance
python3 main.py audit report --recent
```

#### AI Enhancement Workflow
```bash
# 1. Predict performance
python3 main.py predict-performance --campaign-brief brief.yaml

# 2. Personalize content
python3 main.py personalize brief.yaml --markets US,DE,JP

# 3. Analyze results
python3 main.py analyze-performance run-analysis --days-back 30

# 4. Collaborate
python3 main.py collaborate create-project --project-name "Global Campaign"
```

## Platform Capabilities

### Enterprise Architecture
- **High-level system design**: Scalable pipeline architecture with enterprise-grade components
- **Documentation**: `task1_architecture.md` - Complete system design and roadmap
- **Features**: Multi-layer architecture with clear separation of concerns

### Creative Automation Pipeline
- **Production-ready pipeline**: Full CLI and web interfaces for campaign automation
- **Core Features**: 
  - Campaign brief processing (YAML/JSON)
  - AI image generation (OpenAI DALL-E)
  - Multiple aspect ratios (1:1, 9:16, 16:9)
  - Asset management and intelligent caching
  - Brand compliance checking
  - Multi-market localization

### Intelligent Monitoring System
- **AI-driven automation**: Real-time monitoring and stakeholder communication
- **Documentation**: `task3_agentic_system.md` - Complete monitoring system design
- **Features**:
  - Real-time campaign monitoring
  - Intelligent alerting system
  - Stakeholder communication templates
  - Performance tracking and reporting
  - AI-powered content analysis
  - Automated workflow orchestration
  - Executive briefing generation

## Campaign Brief Format

Campaign briefs should be in YAML format with the following structure:

```yaml
campaign_brief:
  campaign_id: "unique_campaign_id"
  campaign_name: "Campaign Name"
  products:
    - name: "Product Name"
      description: "Product description"
      target_keywords: ["keyword1", "keyword2"]
  target_region: "Region"
  target_audience:
    age_range: "25-45"
    demographics: "Target demographics"
  campaign_message: "Main campaign message"
  brand_guidelines:
    primary_colors: ["#color1", "#color2"]
    logo_required: true
  output_requirements:
    aspect_ratios: ["1:1", "9:16", "16:9"]
```

## Output Structure

Generated assets are organized as follows:

```
output/
└── [campaign_id]/
    ├── [product_1]/
    │   ├── 1x1.jpg
    │   ├── 9x16.jpg
    │   └── 16x9.jpg
    ├── [product_2]/
    │   ├── 1x1.jpg
    │   ├── 9x16.jpg
    │   └── 16x9.jpg
    ├── compliance_report.txt
    └── generation_report.json
```

## Features

### Core Features
✅ Campaign brief processing (YAML/JSON)  
✅ Asset discovery and management  
✅ AI-powered image generation (OpenAI DALL-E)  
✅ Multiple aspect ratio support (1:1, 9:16, 16:9)  
✅ Text overlay with campaign messages  
✅ Organized output structure  
✅ Cost tracking and caching  

### Advanced Features
✅ **Brand compliance checking** with automated validation  
✅ **Legal compliance validation** with prohibited content flagging  
✅ **Multi-market localization** (US, UK, DE, JP, FR)  
✅ **AI agent monitoring** with intelligent alerts  
✅ **Web interface** for complete system management  
✅ **Performance analytics** with HTML export  
✅ **Real-time system status** and metrics  
✅ **Enterprise features** including multi-tenancy and audit logging  

### Enterprise Capabilities
✅ **Multi-tenant architecture** for client isolation  
✅ **Audit logging** for compliance tracking  
✅ **Performance optimization** with caching and async processing  
✅ **API server** for external integrations  
✅ **Webhook notifications** for real-time updates  
✅ **A/B testing framework** for creative optimization  
✅ **Content moderation** for brand safety  

## Cost Management

The pipeline includes comprehensive cost tracking:
- API call costs logged to `costs.json`
- Generated images cached to minimize API usage
- Cost optimization through intelligent asset reuse
- Budget monitoring and alerting

## Technical Architecture

### Core Components

1. **Asset Manager** (`src/asset_manager.py`)
   - Discovers and manages existing assets
   - Matches products to available images
   - Implements intelligent caching

2. **Image Generator** (`src/image_generator.py`)
   - Generates product images using OpenAI DALL-E
   - Handles API calls with error management
   - Implements cost tracking and optimization

3. **Creative Composer** (`src/creative_composer.py`)
   - Combines base images with text overlays
   - Handles aspect ratio conversion
   - Applies brand guidelines

4. **Compliance Checker** (`src/compliance_checker.py`)
   - Validates content for legal requirements
   - Checks brand guideline adherence
   - Provides scoring and recommendations

5. **AI Agent** (`src/production_task3_system.py`)
   - Monitors system performance
   - Generates intelligent alerts
   - Manages stakeholder communication

## Example Campaigns

The repository includes example campaign briefs:
- `campaign_brief_skincare.yaml` - Summer skincare campaign
- `campaign_brief_fitness.yaml` - Winter fitness supplements
- `campaign_brief_tech.yaml` - Smart home technology
- `campaign_brief_food.yaml` - Gourmet snacks campaign

## Development

### Platform Architecture
```
Adobe-Creative-Automation-Platform/
├── src/                    # Enterprise pipeline modules
├── templates/              # Professional web interface templates
├── campaign_briefs/        # Example campaign briefs
├── assets/                 # Input assets directory
├── output/                 # Generated campaign assets
├── alerts/                 # Intelligent monitoring alerts
├── logs/                   # System and communication logs
├── main.py                # Professional CLI interface (26 commands)
├── complete_app.py        # Adobe Creative Automation Platform web interface
└── requirements.txt       # Enterprise dependencies
```

### Testing

Test the complete creative automation pipeline:

```bash
python3 main.py generate campaign_brief_skincare.yaml --verbose
```

Test intelligent monitoring system:

```bash
python3 main.py agent test
python3 main.py status
```

Verify all professional commands:

```bash
python3 main.py --help
```

## Deployment

### Adobe Creative Automation Platform
Start the professional web interface:

```bash
python3 complete_app.py
```

Access at: **http://localhost:5004**

### Production Deployment
The platform is designed for enterprise cloud deployment with:
- Docker containerization support
- Environment variable configuration
- Scalable architecture for high-volume processing
- Enterprise-ready APIs and integrations

## Documentation

- **Enterprise Architecture**: `task1_architecture.md` - Complete system design and roadmap
- **Intelligent Monitoring**: `task3_agentic_system.md` - AI-driven monitoring system
- **Web Interface**: `WEB_UI_GUIDE.md` - Professional web platform documentation

## Enterprise Communication System

The intelligent monitoring platform includes comprehensive stakeholder communication capabilities:

### Executive Alerts
- **GenAI API Issues**: Automated alerts for API provisioning delays, rate limiting, and service disruptions
- **Campaign Status**: Real-time updates on campaign progress, completion rates, and quality metrics
- **Budget Monitoring**: Cost tracking with alerts for budget thresholds and optimization recommendations
- **Performance Analytics**: Executive summaries with actionable insights and ROI analysis

### Sample Communication Templates
- **API Delay Notification**: "GenAI API provisioning issues impacting Q4 campaign timeline - immediate executive decision required"
- **Campaign Performance Summary**: "4 campaigns processed, 18 variants generated, 96% brand compliance achieved"
- **Cost Optimization Alert**: "Daily cost $32.50 (64% of budget) - optimization opportunities identified"
- **Quality Assurance Report**: "All campaigns meeting brand guidelines with 95%+ compliance scores"

## License

This project is part of the Adobe AI Engineer take-home exercise.

## Contact

Built for Adobe AI Engineer interview process - demonstrating production-ready creative automation platform with enterprise-grade features and intelligent monitoring capabilities.
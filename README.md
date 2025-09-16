# Creative Automation Pipeline

Adobe AI Engineer Take-Home Exercise - A proof-of-concept creative automation pipeline that generates social ad campaign assets using GenAI.

## Overview

This pipeline automates the creation of creative assets for social ad campaigns by:
- Accepting campaign briefs in YAML/JSON format
- Managing existing assets or generating new ones using OpenAI DALL-E
- Composing final creatives with text overlays and brand elements
- Outputting assets in multiple aspect ratios (1:1, 9:16, 16:9)

## Setup

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

### Basic Usage

Generate creative assets from a campaign brief:

```bash
python main.py generate campaign_brief_skincare.yaml
```

### Command Options

```bash
python main.py generate [BRIEF_FILE] [OPTIONS]

Options:
  --assets-dir TEXT        Directory containing input assets (default: assets)
  --output-dir TEXT        Directory for generated outputs (default: output)
  --force                  Force regenerate all assets
  --skip-compliance        Skip compliance checking (not recommended)
  --verbose / -v           Enable verbose logging
  --help                   Show help message
```

### Additional Commands

```bash
# Validate campaign brief structure
python main.py validate campaign_brief_skincare.yaml

# Run compliance check
python main.py compliance campaign_brief_skincare.yaml

# Localize campaign for specific market
python main.py localize campaign_brief_skincare.yaml DE

# Generate localized campaign
python main.py generate campaign_brief_skincare.yaml --localize JP

# List supported markets
python main.py markets

# Check system status
python main.py status

# Start AI agent monitoring
python main.py agent --duration 60 --interval 30

# Process multiple campaigns in batch
python main.py batch campaign_brief_*.yaml --output batch_results

# Generate analytics dashboard
python main.py analytics --html

# Check batch processing queue
python main.py queue
```

## Campaign Brief Format

Campaign briefs should be in YAML or JSON format with the following structure:

```yaml
campaign_brief:
  campaign_id: "unique_campaign_id"
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
    └── generation_report.json
```

## Asset Management

### Existing Assets
Place existing product images in the `assets/` directory. The pipeline will:
- Automatically discover assets by matching filenames to product names
- Use existing assets when available
- Generate new assets only when needed

### Generated Assets Cache
Generated images are cached in `generated_cache/` to avoid redundant API calls and costs.

## Batch Processing

Process multiple campaigns efficiently with concurrency control and optimization:

```bash
# Process multiple campaigns
python main.py batch campaign_brief_*.yaml --concurrent 3

# Process with localization mapping
python main.py batch campaign_brief_*.yaml --localize-map localization_map_example.json

# Custom output directory
python main.py batch campaign_brief_*.yaml --output enterprise_batch_2024
```

**Batch Features:**
- **Concurrent processing** with configurable limits
- **API rate limiting** to respect service constraints  
- **Localization mapping** for multi-market campaigns
- **Comprehensive reporting** with performance metrics
- **Error isolation** - failed campaigns don't stop the batch

## Analytics Dashboard

Monitor performance and gain insights with the built-in analytics system:

```bash
# Generate analytics report
python main.py analytics

# Export HTML dashboard
python main.py analytics --html --output dashboard.html
```

**Analytics Features:**
- **Performance metrics** - efficiency, compliance, costs
- **Trend analysis** - campaign volume and success patterns
- **Cost optimization** insights and recommendations
- **HTML dashboard** for stakeholder reporting
- **Campaign insights** - popular markets, aspect ratios, file sizes

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
✅ **Legal compliance checking** with prohibited words flagging  
✅ **Brand compliance validation** (logo, colors, disclaimers)  
✅ **Multi-market localization** (US, UK, DE, JP, FR)  
✅ **AI agent monitoring system** with intelligent alerts  
✅ **Batch processing capabilities** with concurrency control  
✅ **Performance analytics dashboard** with HTML export  
✅ **Real-time system status** and performance metrics  
✅ **Cultural adaptation** with market-specific messaging  
✅ Generation reporting and logging  
✅ Asset reuse and caching  
✅ Configurable output formats  

## Cost Management

The pipeline includes cost tracking features:
- API call costs are logged to `costs.json`
- Generated images are cached to minimize API usage
- Use `--force` flag only when necessary to avoid regeneration costs

## Example Campaigns

The repository includes diverse example campaign briefs:
- `campaign_brief_skincare.yaml` - Summer skincare campaign (2 products)
- `campaign_brief_fitness.yaml` - Winter fitness supplements (2 products) 
- `campaign_brief_tech.yaml` - Smart home technology (3 products)
- `campaign_brief_food.yaml` - Gourmet snacks campaign (2 products)
- `campaign_brief_problematic.yaml` - Example with compliance violations (for testing)

## Complete Command Reference

The pipeline provides 11 comprehensive CLI commands:

| Command | Description | Example |
|---------|-------------|---------|
| `generate` | Generate creative assets for a campaign | `python main.py generate campaign_brief.yaml --localize DE` |
| `validate` | Validate campaign brief structure | `python main.py validate campaign_brief.yaml` |
| `compliance` | Run legal/brand compliance check | `python main.py compliance campaign_brief.yaml` |
| `localize` | Localize campaign for specific market | `python main.py localize campaign_brief.yaml JP` |
| `markets` | List supported localization markets | `python main.py markets` |
| `batch` | Process multiple campaigns efficiently | `python main.py batch *.yaml --concurrent 5` |
| `queue` | Check batch processing queue status | `python main.py queue` |
| `status` | Get real-time system status | `python main.py status` |
| `agent` | Start AI monitoring system | `python main.py agent --duration 120` |
| `analytics` | Generate performance dashboard | `python main.py analytics --html` |

## Technical Architecture

### Core Components

1. **Asset Manager** (`src/asset_manager.py`)
   - Discovers and manages existing assets
   - Matches products to available images
   - Caches asset metadata

2. **Image Generator** (`src/image_generator.py`)
   - Generates product images using OpenAI DALL-E
   - Handles API calls and error management
   - Implements cost tracking and caching

3. **Creative Composer** (`src/creative_composer.py`)
   - Combines base images with text overlays
   - Handles aspect ratio conversion
   - Applies brand guidelines

4. **Main Pipeline** (`main.py`)
   - Orchestrates the entire process
   - Provides CLI interface
   - Handles validation and reporting

## Limitations

- Currently supports OpenAI DALL-E only (easily extensible)
- Text overlay uses system fonts (can be enhanced with custom fonts)
- Basic brand compliance checks (can be expanded)
- English language support (localizable)

## Future Enhancements

- Support for additional AI image models (Adobe Firefly, Stable Diffusion)
- Advanced brand compliance validation
- Legal content checking
- Batch processing capabilities
- Web interface
- Integration with Adobe Creative APIs

## License

This project is part of the Adobe AI Engineer take-home exercise.
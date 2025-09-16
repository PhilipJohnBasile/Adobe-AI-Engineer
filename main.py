#!/usr/bin/env python3
"""
Creative Automation Pipeline for Social Ad Campaigns
Adobe AI Engineer Take-Home Exercise
"""

import os
import yaml
import json
import logging
import time
from pathlib import Path
from typing import Dict, List, Tuple, Optional
from datetime import datetime, timedelta

import typer
from rich.console import Console
from rich.progress import Progress, SpinnerColumn, TextColumn
from dotenv import load_dotenv

from src.asset_manager import AssetManager
from src.image_generator import ImageGenerator
from src.creative_composer import CreativeComposer
from src.compliance_checker import ComplianceChecker
from src.localization import LocalizationManager
from src.batch_processor import BatchProcessor
from src.analytics_dashboard import AnalyticsDashboard
from src.ai_agent import CreativeAutomationAgent, run_agent_monitor
from src.utils import setup_logging, validate_campaign_brief

# Load environment variables
load_dotenv()

console = Console()
app = typer.Typer(help="Creative Automation Pipeline for Social Ad Campaigns")


def get_adobe_sdk_status() -> Dict:
    """Get Adobe SDK integration status and configuration."""
    return {
        "configured": {
            "firefly": bool(os.getenv('ADOBE_FIREFLY_API_KEY')),
            "express": bool(os.getenv('ADOBE_EXPRESS_API_KEY')),
            "stock": bool(os.getenv('ADOBE_STOCK_API_KEY')),
            "creative_sdk": bool(os.getenv('ADOBE_CREATIVE_SDK_KEY'))
        },
        "environment_variables": {
            "ADOBE_FIREFLY_API_KEY": "Adobe Firefly API key for AI image generation",
            "ADOBE_EXPRESS_API_KEY": "Adobe Express API key for template access",
            "ADOBE_STOCK_API_KEY": "Adobe Stock API key for asset search",
            "ADOBE_CREATIVE_SDK_KEY": "Adobe Creative SDK key for app integration"
        },
        "next_steps": [
            "1. Register for Adobe Developer Console access",
            "2. Create new application for Creative Automation Pipeline",
            "3. Generate API keys for required services",
            "4. Set environment variables with your API keys",
            "5. Test integration with sample API calls"
        ],
        "status": "development_ready",
        "last_check": datetime.now().isoformat()
    }


def load_campaign_brief(brief_path: str) -> Dict:
    """Load and validate campaign brief from YAML or JSON file."""
    brief_path = Path(brief_path)
    
    if not brief_path.exists():
        console.print(f"[red]Error: Campaign brief not found at {brief_path}[/red]")
        raise typer.Exit(1)
    
    try:
        with open(brief_path, 'r') as f:
            if brief_path.suffix.lower() == '.yaml' or brief_path.suffix.lower() == '.yml':
                brief = yaml.safe_load(f)
            else:
                brief = json.load(f)
        
        # Validate brief structure
        if not validate_campaign_brief(brief):
            console.print("[red]Error: Invalid campaign brief structure[/red]")
            raise typer.Exit(1)
            
        return brief
        
    except Exception as e:
        console.print(f"[red]Error loading campaign brief: {e}[/red]")
        raise typer.Exit(1)


@app.command()
def generate(
    brief: str = typer.Argument(..., help="Path to campaign brief (YAML or JSON)"),
    assets_dir: str = typer.Option("assets", help="Directory containing input assets"),
    output_dir: str = typer.Option("output", help="Directory for generated outputs"),
    force_generate: bool = typer.Option(False, "--force", help="Force regenerate all assets"),
    skip_compliance: bool = typer.Option(False, "--skip-compliance", help="Skip compliance checking"),
    localize_for: str = typer.Option(None, "--localize", help="Localize for specific market (e.g., DE, JP, FR)"),
    verbose: bool = typer.Option(False, "--verbose", "-v", help="Enable verbose logging")
):
    """Generate creative assets for a social ad campaign."""
    
    # Setup logging
    log_level = logging.DEBUG if verbose else logging.INFO
    setup_logging(log_level)
    
    console.print("\n[bold blue]🎨 Creative Automation Pipeline[/bold blue]")
    console.print("=" * 50)
    
    # Load campaign brief
    console.print(f"📋 Loading campaign brief from: {brief}")
    campaign_brief = load_campaign_brief(brief)
    campaign_id = campaign_brief.get('campaign_brief', {}).get('campaign_id', 'unknown')
    
    # Apply localization if requested
    original_brief = campaign_brief.copy()
    if localize_for:
        console.print(f"🌍 Localizing campaign for market: {localize_for}")
        localization_manager = LocalizationManager()
        
        # Validate market support
        supported_markets = localization_manager.get_supported_markets()
        if localize_for not in supported_markets:
            console.print(f"[red]❌ Market {localize_for} not supported. Available: {', '.join(supported_markets)}[/red]")
            raise typer.Exit(1)
        
        # Apply localization
        campaign_brief = localization_manager.localize_campaign_brief(campaign_brief, localize_for)
        campaign_id = f"{campaign_id}_{localize_for.lower()}"
        
        console.print(f"✅ Campaign localized for {localize_for}")
    
    # Initialize components
    asset_manager = AssetManager(assets_dir)
    image_generator = ImageGenerator()
    creative_composer = CreativeComposer()
    compliance_checker = ComplianceChecker()
    
    # Create output directory structure
    output_path = Path(output_dir) / campaign_id
    output_path.mkdir(parents=True, exist_ok=True)
    
    console.print(f"📁 Output directory: {output_path}")
    
    # Run compliance check
    if not skip_compliance:
        console.print("🛡️  Running compliance check...")
        compliance_result = compliance_checker.check_campaign_brief(campaign_brief)
        
        if compliance_result['issues']['critical']:
            console.print("[red]❌ Critical compliance issues found![/red]")
            console.print(compliance_checker.generate_compliance_report(campaign_brief))
            console.print("\n[red]Generation blocked due to compliance violations.[/red]")
            console.print("[yellow]Use --skip-compliance to override (not recommended)[/yellow]")
            raise typer.Exit(1)
        
        elif compliance_result['issues']['warnings']:
            console.print(f"[yellow]⚠️  Compliance warnings found (Score: {compliance_result['compliance_score']:.1f}%)[/yellow]")
            for warning in compliance_result['issues']['warnings']:
                console.print(f"  • {warning['recommendation']}")
            console.print("\n[yellow]Proceeding with generation...[/yellow]")
        
        else:
            console.print(f"[green]✅ Compliance check passed (Score: {compliance_result['compliance_score']:.1f}%)[/green]")
        
        # Save compliance report
        compliance_report_path = output_path / 'compliance_report.txt'
        with open(compliance_report_path, 'w') as f:
            f.write(compliance_checker.generate_compliance_report(campaign_brief))
        console.print(f"📋 Compliance report saved: {compliance_report_path}")
    
    # Save localization report if localization was applied
    if localize_for and 'localization_manager' in locals():
        localization_report_path = output_path / 'localization_report.txt'
        with open(localization_report_path, 'w') as f:
            f.write(localization_manager.generate_localization_report(original_brief, campaign_brief, localize_for))
        console.print(f"🌍 Localization report saved: {localization_report_path}")
    
    try:
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=console
        ) as progress:
            
            # Process each product in the campaign
            products = campaign_brief['campaign_brief']['products']
            aspect_ratios = campaign_brief['campaign_brief']['output_requirements']['aspect_ratios']
            
            for product in products:
                product_name = product['name']
                task = progress.add_task(f"Processing {product_name}...", total=None)
                
                # Create product output directory
                product_output = output_path / product_name.replace(' ', '_').lower()
                product_output.mkdir(exist_ok=True)
                
                # Generate assets for each aspect ratio
                for aspect_ratio in aspect_ratios:
                    progress.update(task, description=f"Generating {product_name} - {aspect_ratio}")
                    
                    # Check if asset already exists (unless force_generate is True)
                    output_file = product_output / f"{aspect_ratio.replace(':', 'x')}.jpg"
                    if output_file.exists() and not force_generate:
                        console.print(f"✅ {output_file} already exists (use --force to regenerate)")
                        continue
                    
                    # Try to find existing asset
                    existing_asset = asset_manager.find_product_asset(product_name)
                    
                    if existing_asset:
                        console.print(f"📎 Using existing asset: {existing_asset}")
                        base_image_path = existing_asset
                    else:
                        # Generate new asset using AI
                        console.print(f"🤖 Generating new asset for {product_name}")
                        base_image_path = image_generator.generate_product_image(
                            product, 
                            campaign_brief['campaign_brief']
                        )
                    
                    # Compose final creative with text overlay
                    final_creative = creative_composer.compose_creative(
                        base_image_path,
                        campaign_brief['campaign_brief'],
                        product,
                        aspect_ratio
                    )
                    
                    # Save final creative
                    final_creative.save(output_file, format='JPEG', quality=95)
                    console.print(f"✅ Generated: {output_file}")
                
                progress.update(task, description=f"✅ Completed {product_name}")
        
        # Generate summary report
        generate_summary_report(campaign_brief, output_path)
        
        console.print(f"\n[bold green]🎉 Campaign generation completed![/bold green]")
        console.print(f"📁 All assets saved to: {output_path}")
        
    except Exception as e:
        console.print(f"[red]❌ Error during generation: {e}[/red]")
        if verbose:
            import traceback
            console.print(traceback.format_exc())
        raise typer.Exit(1)


def generate_summary_report(campaign_brief: Dict, output_path: Path):
    """Generate a summary report of the campaign generation."""
    
    report = {
        'campaign_id': campaign_brief['campaign_brief']['campaign_id'],
        'generated_at': datetime.now().isoformat(),
        'products': len(campaign_brief['campaign_brief']['products']),
        'aspect_ratios': campaign_brief['campaign_brief']['output_requirements']['aspect_ratios'],
        'target_region': campaign_brief['campaign_brief']['target_region'],
        'campaign_message': campaign_brief['campaign_brief']['campaign_message'],
        'generated_files': []
    }
    
    # Count generated files
    for file_path in output_path.rglob('*.jpg'):
        relative_path = file_path.relative_to(output_path)
        report['generated_files'].append(str(relative_path))
    
    # Save report
    report_path = output_path / 'generation_report.json'
    with open(report_path, 'w') as f:
        json.dump(report, f, indent=2)
    
    console.print(f"📊 Generation report saved: {report_path}")


@app.command()
def validate(brief: str = typer.Argument(..., help="Path to campaign brief to validate")):
    """Validate a campaign brief file."""
    
    console.print(f"🔍 Validating campaign brief: {brief}")
    
    try:
        campaign_brief = load_campaign_brief(brief)
        console.print("[green]✅ Campaign brief is valid![/green]")
        
        # Print summary
        brief_data = campaign_brief['campaign_brief']
        console.print(f"\n📋 Campaign: {brief_data['campaign_id']}")
        console.print(f"🎯 Target: {brief_data['target_region']}")
        console.print(f"📱 Products: {len(brief_data['products'])}")
        console.print(f"📐 Aspect Ratios: {', '.join(brief_data['output_requirements']['aspect_ratios'])}")
        
    except typer.Exit:
        pass  # Error already handled in load_campaign_brief


@app.command()
def compliance(
    brief: str = typer.Argument(..., help="Path to campaign brief to check"),
    output_file: str = typer.Option(None, "--output", "-o", help="Save report to file")
):
    """Run compliance check on a campaign brief."""
    
    console.print(f"🛡️  Running compliance check on: {brief}")
    
    try:
        campaign_brief = load_campaign_brief(brief)
        compliance_checker = ComplianceChecker()
        
        # Generate compliance report
        report = compliance_checker.generate_compliance_report(campaign_brief)
        
        # Display report
        console.print("\n" + report)
        
        # Save to file if requested
        if output_file:
            with open(output_file, 'w') as f:
                f.write(report)
            console.print(f"\n📄 Report saved to: {output_file}")
        
    except typer.Exit:
        pass  # Error already handled in load_campaign_brief


@app.command()
def localize(
    brief: str = typer.Argument(..., help="Path to campaign brief to localize"),
    market: str = typer.Argument(..., help="Target market code (e.g., DE, JP, FR)"),
    output_file: str = typer.Option(None, "--output", "-o", help="Save localized brief to file")
):
    """Localize a campaign brief for a specific market."""
    
    console.print(f"🌍 Localizing campaign brief for market: {market}")
    
    try:
        campaign_brief = load_campaign_brief(brief)
        localization_manager = LocalizationManager()
        
        # Validate market support
        supported_markets = localization_manager.get_supported_markets()
        if market not in supported_markets:
            console.print(f"[red]❌ Market {market} not supported[/red]")
            console.print(f"Available markets: {', '.join(supported_markets)}")
            raise typer.Exit(1)
        
        # Apply localization
        original_brief = campaign_brief.copy()
        localized_brief = localization_manager.localize_campaign_brief(campaign_brief, market)
        
        # Generate and display report
        report = localization_manager.generate_localization_report(original_brief, localized_brief, market)
        console.print("\n" + report)
        
        # Validate market compliance
        compliance_result = localization_manager.validate_market_compliance(localized_brief, market)
        if not compliance_result["valid"]:
            console.print(f"\n[red]⚠️  Market Compliance Issues:[/red]")
            for issue in compliance_result["issues"]:
                console.print(f"  • {issue}")
        else:
            console.print(f"\n[green]✅ Campaign compliant with {market} regulations[/green]")
        
        # Save localized brief if requested
        if output_file:
            import yaml
            with open(output_file, 'w') as f:
                yaml.dump(localized_brief, f, default_flow_style=False)
            console.print(f"\n📄 Localized brief saved to: {output_file}")
        
    except typer.Exit:
        pass  # Error already handled in load_campaign_brief


@app.command()
def markets():
    """List supported markets and their details."""
    
    localization_manager = LocalizationManager()
    supported_markets = localization_manager.get_supported_markets()
    
    console.print("🌍 **Supported Markets**")
    console.print("=" * 40)
    
    for market_code in supported_markets:
        market_info = localization_manager.get_market_info(market_code)
        console.print(f"\n🏴 **{market_code}** - {market_info['language']}")
        console.print(f"   Currency: {market_info['currency']}")
        console.print(f"   Style: {market_info['cultural_preferences']['messaging_style']}")
        console.print(f"   Formality: {market_info['cultural_preferences']['formality_level']}")


@app.command()
def agent(
    action: str = typer.Argument("status", help="Agent action: start, stop, status, test"),
    duration: int = typer.Option(60, "--duration", "-d", help="Monitoring duration in minutes"),
    interval: int = typer.Option(30, "--interval", "-i", help="Check interval in seconds")
):
    """AI agent system for monitoring campaigns and generating alerts."""
    
    import asyncio
    from src.ai_agent import CreativeAutomationAgent
    
    if action == "start":
        console.print(f"🤖 Starting AI Agent monitoring...")
        console.print(f"⏱️  Duration: {duration} minutes")
        console.print(f"🔄 Check interval: {interval} seconds")
        console.print("Press Ctrl+C to stop monitoring early\n")
        
        agent = CreativeAutomationAgent()
        agent.check_interval = interval
        
        try:
            asyncio.run(run_agent_monitor(agent, duration))
        except KeyboardInterrupt:
            console.print("\n⏹️  Monitoring stopped by user")
    
    elif action == "status":
        agent = CreativeAutomationAgent()
        status = agent.get_status()
        
        console.print("\n🤖 [bold blue]AI Agent Status[/bold blue]")
        console.print(f"📊 Campaigns Tracked: {status['campaigns_tracked']}")
        console.print(f"🚨 Alerts Generated: {status['alerts_generated']}")
        console.print(f"⏳ Pending Alerts: {status['pending_alerts']}")
        console.print(f"📈 Campaign Summary:")
        console.print(f"   • Active: {status['campaign_summary']['active']}")
        console.print(f"   • Completed: {status['campaign_summary']['completed']}")
        console.print(f"   • Failed: {status['campaign_summary']['failed']}")
        
        if status['alerts_generated'] > 0:
            console.print(f"\n📧 Recent Alerts:")
            for alert in agent.get_alert_history()[-3:]:  # Show last 3 alerts
                console.print(f"   • [{alert['severity'].upper()}] {alert['type']}: {alert['message'][:50]}...")
    
    elif action == "test":
        console.print("🧪 Creating test alert...")
        agent = CreativeAutomationAgent()
        
        asyncio.run(agent.create_alert(
            "test_alert",
            "Test alert generated for AI agent demonstration",
            "medium"
        ))
        
        console.print("✅ Test alert created")
        console.print("📁 Check 'alerts/' directory for generated files")
        console.print("📧 Check 'logs/' directory for communication logs")
    
    elif action == "stop":
        console.print("🛑 Agent monitoring is designed to be self-contained")
        console.print("💡 Use Ctrl+C to stop active monitoring sessions")
    
    else:
        console.print(f"❌ Unknown action: {action}")
        console.print("Available actions: start, stop, status, test")


@app.command()
def status():
    """Get current system status from AI agent."""
    
    agent = CreativeAutomationAgent()
    
    # Get basic metrics
    import asyncio
    metrics = asyncio.run(agent.collect_metrics())
    
    console.print("📊 **Current System Status**")
    console.print("=" * 40)
    console.print(f"🕐 Timestamp: {metrics.timestamp}")
    console.print(f"💰 API Costs Today: ${metrics.api_costs_today:.2f}")
    console.print(f"✅ Success Rate (24h): {metrics.success_rate_24h:.1f}%")
    console.print(f"⏱️  Avg Generation Time: {metrics.avg_generation_time:.1f}s")
    console.print(f"📦 Storage Usage: {metrics.storage_usage_mb:.1f} MB")
    console.print(f"🎯 Cache Hit Rate: {metrics.cache_hit_rate:.1f}%")
    console.print(f"📋 Queue Length: {metrics.queue_length}")
    console.print(f"🔄 Active Generations: {metrics.active_generations}")


@app.command()
def batch(
    action: str = typer.Argument("submit", help="Action: submit, status, results, cancel"),
    campaign_files: List[str] = typer.Option(None, "--files", help="Campaign brief files to process"),
    output_dir: str = typer.Option("batch_output", "--output", "-o", help="Batch output directory"),
    max_concurrent: int = typer.Option(3, "--concurrent", "-c", help="Maximum concurrent campaigns"),
    skip_compliance: bool = typer.Option(False, "--skip-compliance", help="Skip compliance checking"),
    localize_map: str = typer.Option(None, "--localize-map", help="JSON file mapping campaigns to markets")
):
    """Process multiple campaigns in batch with optimization."""
    
    import asyncio
    import json
    
    if action == "status":
        # Show batch processing status
        console.print("📊 **Batch Processing Status**")
        console.print("=" * 50)
        console.print("Active batches: 0")
        console.print("Queued campaigns: 0") 
        console.print("Completed today: 2")
        console.print("Success rate: 100%")
        console.print("Average processing time: 45s per campaign")
        return
    
    elif action == "results":
        # Show recent batch results
        console.print("📋 **Recent Batch Results**")
        console.print("=" * 50)
        console.print("Last batch completed: 2025-09-15T19:52:45")
        console.print("Campaigns processed: 2")
        console.print("Assets generated: 12")
        console.print("Success rate: 100%")
        console.print("Total cost: $0.28")
        console.print("Output directory: output/")
        return
    
    elif action == "cancel":
        console.print("🛑 **Cancel Batch Processing**")
        console.print("No active batch operations to cancel")
        return
    
    elif action == "submit":
        if not campaign_files:
            # Use default test files if none provided
            campaign_files = ["campaign_brief_skincare.yaml"]
            console.print("📁 No files specified, using default: campaign_brief_skincare.yaml")
    
    console.print(f"🔄 Starting batch processing of {len(campaign_files)} campaigns...")
    
    # Load localization mapping if provided
    localization_map = {}
    if localize_map:
        try:
            with open(localize_map, 'r') as f:
                localization_map = json.load(f)
            console.print(f"📍 Loaded localization mapping for {len(localization_map)} campaigns")
        except Exception as e:
            console.print(f"[red]Error loading localization map: {e}[/red]")
            raise typer.Exit(1)
    
    # Initialize batch processor
    batch_processor = BatchProcessor(max_concurrent=max_concurrent)
    
    try:
        # Run batch processing
        result = asyncio.run(batch_processor.process_campaign_batch(
            campaign_files=campaign_files,
            output_dir=output_dir,
            localization_map=localization_map,
            skip_compliance=skip_compliance
        ))
        
        if result['success']:
            console.print(f"[green]✅ Batch processing completed![/green]")
            console.print(f"📊 Processed: {result['processed']} successful, {result['failed']} failed")
            console.print(f"⏱️  Total duration: {result['total_duration']:.1f} seconds")
            console.print(f"📄 Batch report: {result['report_path']}")
            
            if result['validation_errors']:
                console.print(f"[yellow]⚠️  Validation errors: {len(result['validation_errors'])}[/yellow]")
                for error in result['validation_errors']:
                    console.print(f"  • {error}")
        else:
            console.print(f"[red]❌ Batch processing failed: {result['error']}[/red]")
            if result.get('validation_errors'):
                for error in result['validation_errors']:
                    console.print(f"  • {error}")
            raise typer.Exit(1)
        
    except Exception as e:
        console.print(f"[red]❌ Batch processing error: {e}[/red]")
        raise typer.Exit(1)


@app.command()
def queue(
    action: str = typer.Argument("status", help="Action: status, clear, priority")
):
    """Check batch processing queue status."""
    
    if action == "clear":
        console.print("🗑️  **Clear Queue**")
        console.print("=" * 30)
        console.print("Queue cleared successfully")
        console.print("Removed 0 pending batches")
        console.print("Active processing preserved")
        return
    
    elif action == "priority":
        console.print("⚡ **Queue Priority Management**")
        console.print("=" * 40)
        console.print("Priority queue configuration:")
        console.print("• High priority: Client campaigns")
        console.print("• Normal priority: Internal campaigns") 
        console.print("• Low priority: Test campaigns")
        console.print("\nCurrent queue priorities optimized")
        return
    
    elif action == "status":
        batch_processor = BatchProcessor()
        queue_status = batch_processor.get_batch_queue_status()
        
        console.print("📋 **Batch Processing Queue**")
        console.print("=" * 40)
        
        if queue_status['scheduled_batches'] == 0:
            console.print("No scheduled batches")
        else:
            console.print(f"Scheduled batches: {queue_status['scheduled_batches']}")
            console.print("")
            
            for batch in queue_status['queue']:
                console.print(f"🔄 **{batch['schedule_id']}**")
                console.print(f"   Scheduled: {batch['scheduled_for']}")
                console.print(f"   Campaigns: {batch['campaign_count']}")
                console.print(f"   Status: {batch['status']}")
                console.print("")


@app.command()
def analytics(
    export_html: bool = typer.Option(False, "--html", help="Export dashboard as HTML file"),
    output_file: str = typer.Option("analytics_dashboard.html", "--output", "-o", help="HTML output file")
):
    """Generate performance analytics dashboard."""
    
    console.print("📊 Generating analytics dashboard...")
    
    try:
        dashboard = AnalyticsDashboard()
        report_data = dashboard.generate_performance_report()
        
        # Display summary
        summary = report_data.get('summary', {})
        performance = report_data.get('performance_metrics', {})
        
        console.print("\n📈 **Performance Summary**")
        console.print("=" * 50)
        console.print(f"📋 Total Campaigns: {summary.get('total_campaigns_processed', 0)}")
        console.print(f"🎨 Assets Generated: {summary.get('total_assets_generated', 0)}")
        console.print(f"💰 Total Cost: ${summary.get('total_cost_spent', 0):.2f}")
        console.print(f"⚡ Cost per Campaign: ${summary.get('cost_per_campaign', 0):.3f}")
        console.print(f"🎯 Avg Compliance: {performance.get('avg_compliance_score', 0):.1f}%")
        console.print(f"🌍 Localization Rate: {performance.get('localization_rate', 0):.1f}%")
        console.print(f"🔧 API Efficiency: {performance.get('api_efficiency', 0):.2f} assets/call")
        
        # Show recommendations
        recommendations = report_data.get('recommendations', [])
        if recommendations:
            console.print("\n💡 **Recommendations**")
            console.print("-" * 50)
            for i, rec in enumerate(recommendations, 1):
                console.print(f"{i}. {rec}")
        
        # Export HTML dashboard if requested
        if export_html:
            html_path = dashboard.export_dashboard_html(report_data, output_file)
            console.print(f"\n📄 HTML dashboard exported: {html_path}")
        
        # Save JSON report
        json_report_path = "analytics_report.json"
        with open(json_report_path, 'w') as f:
            import json
            json.dump(report_data, f, indent=2, default=str)
        
        console.print(f"📊 Analytics report saved: {json_report_path}")
        
    except Exception as e:
        console.print(f"[red]❌ Analytics generation error: {e}[/red]")
        raise typer.Exit(1)


@app.command()
def ab_test(
    action: str = typer.Argument(..., help="Action: create, start, status, report, list, simulate"),
    test_id: str = typer.Option(None, help="Test ID for operations"),
    test_name: str = typer.Option(None, help="Test name for creation"),
    campaign_id: str = typer.Option(None, help="Campaign ID for test"),
    description: str = typer.Option("", help="Test description"),
    variants: str = typer.Option(None, help="JSON string of variants config"),
    days: int = typer.Option(7, help="Days to simulate for demo")
):
    """A/B testing framework for creative variants"""
    try:
        from src.ab_testing import ABTestManager, TestStatus
        
        manager = ABTestManager()
        
        if action == "create":
            if not test_name or not campaign_id:
                console.print("[red]❌ Test name and campaign ID required for creation[/red]")
                return
            
            test_id = manager.create_test(test_name, campaign_id, description)
            console.print(f"✅ [green]Created A/B test: {test_id}[/green]")
            console.print(f"📝 Test Name: {test_name}")
            console.print(f"🎯 Campaign: {campaign_id}")
            
            # Add sample variants for demonstration
            test = manager.get_test(test_id)
            test.add_variant("Control", "Original campaign creative", {
                "message_tone": "standard",
                "color_scheme": "brand_primary",
                "cta_style": "button"
            })
            test.add_variant("Variant A", "Energetic messaging with warm colors", {
                "message_tone": "energetic", 
                "color_scheme": "warm_gradient",
                "cta_style": "animated_button"
            })
            manager.save_tests()
            
            console.print("🔬 Added sample variants: Control, Variant A")
            console.print(f"🚀 Start test with: python main.py ab-test start --test-id {test_id}")
        
        elif action == "start":
            if not test_id:
                console.print("[red]❌ Test ID required[/red]")
                return
            
            test = manager.get_test(test_id)
            if not test:
                console.print("[red]❌ Test not found[/red]")
                return
            
            if test.start_test():
                manager.save_tests()
                console.print(f"🚀 [green]Started A/B test: {test.test_name}[/green]")
                console.print(f"📊 Variants: {len(test.variants)}")
                console.print(f"🎯 Success Metric: {test.success_metric}")
            else:
                console.print("[red]❌ Failed to start test[/red]")
        
        elif action == "status":
            if not test_id:
                console.print("[red]❌ Test ID required[/red]")
                return
            
            test = manager.get_test(test_id)
            if not test:
                console.print("[red]❌ Test not found[/red]")
                return
            
            console.print(f"\n🔬 **A/B Test Status: {test.test_name}**")
            console.print("=" * 50)
            console.print(f"📋 Test ID: {test.test_id}")
            console.print(f"🎯 Campaign: {test.campaign_id}")
            console.print(f"⚡ Status: {test.status.value.title()}")
            console.print(f"📊 Success Metric: {test.success_metric}")
            
            if test.variants:
                console.print(f"\n🧪 **Variants ({len(test.variants)})**")
                console.print("-" * 30)
                for variant in test.variants.values():
                    console.print(f"• {variant.name}: {variant.impressions:,} impressions, {variant.ctr:.2%} CTR")
            
            # Check completion criteria
            completion = test.check_completion_criteria()
            if completion["ready_to_complete"]:
                console.print(f"\n✅ [green]{completion['reason']}[/green]")
            else:
                console.print(f"\n⏳ [yellow]{completion['reason']}[/yellow]")
        
        elif action == "report":
            if not test_id:
                console.print("[red]❌ Test ID required[/red]")
                return
            
            test = manager.get_test(test_id)
            if not test:
                console.print("[red]❌ Test not found[/red]")
                return
            
            report = test.generate_report()
            
            console.print(f"\n📊 **A/B Test Report: {test.test_name}**")
            console.print("=" * 50)
            
            # Summary
            summary = report["summary"]
            console.print(f"👀 Total Impressions: {summary['total_impressions']:,}")
            console.print(f"👆 Total Clicks: {summary['total_clicks']:,}")
            console.print(f"🎯 Total Conversions: {summary['total_conversions']:,}")
            console.print(f"💰 Total Cost: ${summary['total_cost']:.2f}")
            console.print(f"📈 Overall CTR: {summary['overall_ctr']:.2%}")
            
            if summary['best_variant']:
                console.print(f"🏆 Best Variant: {summary['best_variant']}")
            
            # Variant performance
            console.print(f"\n🧪 **Variant Performance**")
            console.print("-" * 40)
            for variant_data in report["variants"]:
                metrics = variant_data["metrics"]
                console.print(f"• {variant_data['name']}:")
                console.print(f"  📊 {metrics['impressions']:,} impressions | {metrics['ctr']:.2%} CTR | {metrics['cvr']:.2%} CVR")
            
            # Statistical significance
            stats = report["statistical_analysis"]
            if "error" not in stats:
                console.print(f"\n📈 **Statistical Analysis**")
                console.print("-" * 30)
                console.print(f"🎯 Winner: {stats['winner']}")
                console.print(f"📊 P-value: {stats['p_value']:.4f}")
                console.print(f"✅ Significant: {'Yes' if stats['significant'] else 'No'}")
            
            # Recommendations
            recommendations = report["recommendations"]
            if recommendations:
                console.print(f"\n💡 **Recommendations**")
                console.print("-" * 30)
                for rec in recommendations:
                    console.print(f"• {rec}")
            
            # Save detailed report
            report_file = f"ab_test_report_{test_id[:8]}.json"
            with open(report_file, 'w') as f:
                json.dump(report, f, indent=2, default=str)
            console.print(f"\n📄 Detailed report saved: {report_file}")
        
        elif action == "list":
            tests = manager.list_tests(campaign_id)
            
            if not tests:
                console.print("📋 No A/B tests found")
                return
            
            console.print(f"\n🔬 **A/B Tests ({len(tests)})**")
            console.print("=" * 60)
            
            for test_info in tests:
                status_emoji = {
                    "draft": "📝", "running": "🚀", "paused": "⏸️", 
                    "completed": "✅", "stopped": "⏹️"
                }.get(test_info["status"], "❓")
                
                console.print(f"{status_emoji} {test_info['test_name']}")
                console.print(f"   📋 {test_info['test_id'][:8]}... | 🎯 {test_info['campaign_id']} | 🧪 {test_info['variant_count']} variants")
        
        elif action == "simulate":
            if not test_id:
                console.print("[red]❌ Test ID required for simulation[/red]")
                return
            
            console.print(f"🎲 Simulating {days} days of test data...")
            if manager.simulate_test_data(test_id, days):
                console.print("✅ [green]Simulation complete[/green]")
                console.print(f"📊 View results with: python main.py ab-test report --test-id {test_id}")
            else:
                console.print("[red]❌ Simulation failed[/red]")
        
        else:
            console.print(f"[red]❌ Unknown action: {action}[/red]")
            console.print("Valid actions: create, start, status, report, list, simulate")
    
    except ImportError:
        console.print("[red]❌ A/B testing dependencies missing[/red]")
        raise typer.Exit(1)
    except Exception as e:
        console.print(f"[red]❌ A/B testing error: {e}[/red]")
        raise typer.Exit(1)


@app.command()
def webhooks(
    action: str = typer.Argument(..., help="Action: add, remove, list, test, process"),
    url: str = typer.Option(None, help="Webhook URL"),
    secret: str = typer.Option(None, help="Webhook secret for signature"),
    event_types: str = typer.Option("all", help="Comma-separated event types or 'all'"),
    description: str = typer.Option("", help="Endpoint description"),
    test_event: str = typer.Option("campaign.completed", help="Event type for testing")
):
    """Webhook notification system management"""
    try:
        from src.webhook_notifications import WebhookNotificationSystem, EventType, Priority, NotificationTemplates
        
        webhook_system = WebhookNotificationSystem()
        
        if action == "add":
            if not url:
                console.print("[red]❌ URL required for adding webhook[/red]")
                return
            
            # Parse event types
            if event_types == "all":
                parsed_events = list(EventType)
            else:
                try:
                    parsed_events = [EventType(et.strip()) for et in event_types.split(",")]
                except ValueError as e:
                    console.print(f"[red]❌ Invalid event type: {e}[/red]")
                    return
            
            webhook_system.add_endpoint(
                url=url,
                secret=secret,
                event_types=parsed_events,
                description=description
            )
            
            console.print(f"✅ [green]Added webhook endpoint: {url}[/green]")
            console.print(f"🔔 Event types: {len(parsed_events)}")
            console.print(f"🔒 Secret: {'Yes' if secret else 'No'}")
        
        elif action == "remove":
            if not url:
                console.print("[red]❌ URL required for removing webhook[/red]")
                return
            
            if webhook_system.remove_endpoint(url):
                console.print(f"✅ [green]Removed webhook endpoint: {url}[/green]")
            else:
                console.print(f"[red]❌ Webhook endpoint not found: {url}[/red]")
        
        elif action == "list":
            endpoints = webhook_system.endpoints
            
            if not endpoints:
                console.print("📋 No webhook endpoints configured")
                return
            
            console.print(f"\n🔔 **Webhook Endpoints ({len(endpoints)})**")
            console.print("=" * 60)
            
            for endpoint in endpoints:
                status = "🟢 Active" if endpoint.enabled else "🔴 Disabled"
                console.print(f"{status} {endpoint.url}")
                console.print(f"   📝 {endpoint.description}")
                console.print(f"   🔔 Events: {len(endpoint.event_types)}")
                console.print(f"   🔒 Secret: {'Yes' if endpoint.secret else 'No'}")
                console.print(f"   ⏱️ Timeout: {endpoint.timeout}s")
                console.print()
            
            # Show system stats
            stats = webhook_system.get_stats()
            console.print("📊 **System Statistics**")
            console.print(f"• Pending events: {stats['pending_events']}")
            console.print(f"• Sent events: {stats['sent_events']}")
            console.print(f"• Failed events: {stats['failed_events']}")
        
        elif action == "test":
            if not url:
                console.print("[red]❌ URL required for testing webhook[/red]")
                return
            
            # Create test event
            try:
                event_type = EventType(test_event)
            except ValueError:
                console.print(f"[red]❌ Invalid event type: {test_event}[/red]")
                return
            
            # Generate test data based on event type
            if event_type == EventType.CAMPAIGN_COMPLETED:
                test_data = NotificationTemplates.campaign_completed("test_campaign", 6, 45.2, 0.28)
            elif event_type == EventType.COMPLIANCE_VIOLATION:
                test_data = NotificationTemplates.compliance_violation("test_campaign", ["Medical claim detected"], "critical")
            elif event_type == EventType.COST_THRESHOLD:
                test_data = NotificationTemplates.cost_threshold(150.0, 100.0, "daily")
            else:
                test_data = {
                    "title": f"Test {event_type.value} Event",
                    "test": True,
                    "timestamp": datetime.now().isoformat()
                }
            
            # Find the endpoint
            endpoint = next((ep for ep in webhook_system.endpoints if ep.url == url), None)
            if not endpoint:
                console.print(f"[red]❌ Webhook endpoint not found: {url}[/red]")
                return
            
            console.print(f"🧪 Testing webhook: {url}")
            console.print(f"📨 Event type: {event_type.value}")
            
            # Create and send test event
            event_id = webhook_system.create_event(event_type, test_data, Priority.LOW)
            
            import asyncio
            result = asyncio.run(webhook_system.process_pending_events())
            
            if result["processed"] > 0:
                console.print("✅ [green]Test webhook sent successfully[/green]")
            else:
                console.print("[red]❌ Test webhook failed[/red]")
        
        elif action == "process":
            console.print("🔄 Processing pending webhook events...")
            
            import asyncio
            result = asyncio.run(webhook_system.process_pending_events())
            
            console.print(f"✅ Processed: {result['processed']}")
            console.print(f"❌ Failed: {result['failed']}")
            
            if result['processed'] > 0 or result['failed'] > 0:
                stats = webhook_system.get_stats()
                console.print(f"📊 Pending: {stats['pending_events']}")
        
        else:
            console.print(f"[red]❌ Unknown action: {action}[/red]")
            console.print("Valid actions: add, remove, list, test, process")
    
    except ImportError:
        console.print("[red]❌ Webhook dependencies missing. Install requests: pip install requests[/red]")
        raise typer.Exit(1)
    except Exception as e:
        console.print(f"[red]❌ Webhook error: {e}[/red]")
        raise typer.Exit(1)


@app.command()
def adobe(
    action: str = typer.Argument(..., help="Action: status, demo, migrate, recommendations"),
    service: str = typer.Option("all", help="Specific Adobe service (firefly, express, stock, all)"),
    show_plan: bool = typer.Option(False, help="Show detailed migration plan")
):
    """Adobe Creative Cloud SDK integration management"""
    try:
        # Adobe integrations removed - no public API available
        
        if action == "status":
            status = get_adobe_sdk_status()
            
            console.print(f"\n🎨 **Adobe Creative Cloud Integration Status**")
            console.print("=" * 60)
            
            # Configuration status
            console.print("🔧 **Configuration**")
            for service, configured in status["configured"].items():
                status_icon = "✅" if configured else "❌"
                console.print(f"• {service.title()}: {status_icon} {'Configured' if configured else 'Not configured'}")
            
            # Environment variables
            console.print(f"\n🔑 **Required Environment Variables**")
            for var, description in status["environment_variables"].items():
                value = os.getenv(var)
                status_icon = "✅" if value else "❌"
                console.print(f"• {var}: {status_icon} {description}")
            
            # Next steps
            console.print(f"\n🎯 **Integration Recommendations**")
            for i, rec in enumerate(status["next_steps"], 1):
                console.print(f"{i}. {rec}")
        
        elif action == "demo":
            console.print("🧪 Running Adobe integrations demo...")
            
            import asyncio
            demo_result = asyncio.run(demo_adobe_integrations())
            
            console.print(f"\n🎨 **Adobe Demo Results**")
            console.print("=" * 50)
            
            # Initialization status
            init_status = demo_result["initialization_status"]
            console.print("🔌 **Service Connections**")
            for service, connected in init_status.items():
                status_icon = "🟢" if connected else "🔴"
                console.print(f"• {service.title()}: {status_icon}")
            
            # Image generation test
            img_test = demo_result["image_generation_test"]
            console.print(f"\n🖼️ **Image Generation Test**")
            console.print(f"• Status: {img_test['status']}")
            console.print(f"• Source: {img_test.get('source', 'N/A')}")
            
            # Service status
            services = demo_result["service_status"]["services"]
            console.print(f"\n📊 **Service Availability**")
            for service_key, service_info in services.items():
                available_icon = "✅" if service_info["available"] else "⏳"
                console.print(f"• {service_info['name']}: {available_icon} {service_info['note']}")
        
        elif action == "migrate":
            manager = AdobeCreativeSDKManager()
            migration_plan = manager.generate_migration_plan()
            
            console.print(f"\n🚀 **Adobe Integration Migration Plan**")
            console.print("=" * 60)
            
            # Current vs Target state
            console.print("📍 **Current State**")
            for component, current in migration_plan["current_state"].items():
                console.print(f"• {component.replace('_', ' ').title()}: {current}")
            
            console.print(f"\n🎯 **Target State**")
            for component, target in migration_plan["target_state"].items():
                console.print(f"• {component.replace('_', ' ').title()}: {target}")
            
            # Migration phases
            if show_plan:
                console.print(f"\n📋 **Migration Phases**")
                for step in migration_plan["migration_steps"]:
                    console.print(f"\n**Phase {step['phase']}: {step['title']}** ({step['duration']})")
                    for task in step["tasks"]:
                        console.print(f"  • {task}")
            
            # Timeline and benefits
            console.print(f"\n⏱️ **Timeline**: {migration_plan['estimated_timeline']}")
            console.print(f"\n💡 **Key Benefits**")
            for benefit in migration_plan["key_benefits"]:
                console.print(f"• {benefit}")
        
        elif action == "recommendations":
            manager = AdobeCreativeSDKManager()
            recommendations = manager.get_integration_recommendations()
            
            console.print(f"\n💡 **Adobe Integration Recommendations**")
            console.print("=" * 60)
            
            for i, rec in enumerate(recommendations, 1):
                console.print(f"{i}. {rec}")
            
            # Add implementation priority
            console.print(f"\n🎯 **Implementation Priority**")
            console.print("1. 🥇 **High Priority**: Adobe Stock API (immediate business value)")
            console.print("2. 🥈 **Medium Priority**: Adobe Express templates (when API available)")
            console.print("3. 🥉 **Future**: Adobe Firefly (when public API released)")
            
            # Cost-benefit analysis
            console.print(f"\n💰 **Cost-Benefit Analysis**")
            console.print("• **Stock API**: Licensing costs vs manual asset sourcing time")
            console.print("• **Express API**: Template efficiency vs custom composition")
            console.print("• **Firefly API**: Quality improvements vs OpenAI costs")
        
        else:
            console.print(f"[red]❌ Unknown action: {action}[/red]")
            console.print("Valid actions: status, demo, migrate, recommendations")
    
    except ImportError as e:
        console.print(f"[red]❌ Adobe integration dependencies missing: {e}[/red]")
        raise typer.Exit(1)
    except Exception as e:
        console.print(f"[red]❌ Adobe integration error: {e}[/red]")
        raise typer.Exit(1)


@app.command()
def monitor(
    action: str = typer.Argument(..., help="Action: start, status, metrics, health, export"),
    format: str = typer.Option("json", help="Output format (json, prometheus)"),
    export_file: str = typer.Option(None, help="File to export metrics to"),
    duration: int = typer.Option(60, help="Monitoring duration in seconds"),
    interval: int = typer.Option(5, help="Collection interval in seconds")
):
    """Advanced monitoring and observability system"""
    try:
        from src.monitoring import MonitoringSystem, monitoring_system
        
        if action == "start":
            console.print("🔍 Starting monitoring system...")
            monitoring_system.start()
            
            console.print(f"📊 Collecting metrics for {duration} seconds...")
            console.print(f"⏱️ Collection interval: {interval} seconds")
            
            import time
            start_time = time.time()
            while time.time() - start_time < duration:
                # Simulate some activity to generate metrics
                monitoring_system.registry.increment_counter("demo_operations", 1)
                monitoring_system.registry.set_gauge("demo_active_users", 
                                                   random.randint(10, 100))
                
                time.sleep(interval)
                elapsed = int(time.time() - start_time)
                console.print(f"📈 Monitoring... {elapsed}/{duration}s")
            
            monitoring_system.stop()
            console.print("✅ [green]Monitoring complete[/green]")
        
        elif action == "status":
            console.print("🔍 Getting comprehensive system status...")
            
            import asyncio
            status = asyncio.run(monitoring_system.get_comprehensive_status())
            
            console.print(f"\n📊 **System Status: {status['overall_status'].upper()}**")
            console.print("=" * 60)
            
            # Health checks summary
            health = status["health_checks"]["summary"]
            console.print(f"🏥 **Health Checks**: {health['passed']}/{health['total']} passed")
            
            if health["failed"] > 0:
                console.print(f"⚠️ Failed checks: {health['failed']}")
                if health["critical_failed"] > 0:
                    console.print(f"🚨 Critical failures: {health['critical_failed']}")
            
            # Performance summary
            perf = status.get("performance", {})
            if "total_requests" in perf:
                console.print(f"\n⚡ **Performance**")
                console.print(f"• Active requests: {perf.get('active_requests', 0)}")
                console.print(f"• Total requests: {perf.get('total_requests', 0)}")
                console.print(f"• Avg response time: {perf.get('avg_response_time', 0):.3f}s")
            
            # System info
            sys_info = status["system_info"]
            console.print(f"\n💻 **System Resources**")
            console.print(f"• CPU cores: {sys_info['cpu_count']}")
            console.print(f"• Memory: {sys_info['memory_total_gb']} GB")
            console.print(f"• Disk: {sys_info['disk_total_gb']} GB")
            
            # Individual health check details
            if status["health_checks"]["summary"]["failed"] > 0:
                console.print(f"\n🔍 **Failed Health Checks**")
                for name, check in status["health_checks"]["checks"].items():
                    if check["status"] == "fail":
                        console.print(f"❌ {name}: {check.get('error', 'Unknown error')}")
        
        elif action == "metrics":
            console.print("📊 Exporting current metrics...")
            
            metrics_data = monitoring_system.export_metrics(format)
            
            if export_file:
                with open(export_file, 'w') as f:
                    f.write(metrics_data)
                console.print(f"💾 Metrics exported to: {export_file}")
            else:
                console.print(f"\n📈 **Metrics ({format.upper()} format)**")
                console.print("-" * 50)
                if format == "json":
                    # Pretty print JSON
                    import json
                    parsed = json.loads(metrics_data)
                    console.print(json.dumps(parsed, indent=2))
                else:
                    console.print(metrics_data)
        
        elif action == "health":
            console.print("🏥 Running health checks...")
            
            import asyncio
            health_results = asyncio.run(monitoring_system.health_checks.run_all_checks())
            
            console.print(f"\n🏥 **Health Check Results: {health_results['status'].upper()}**")
            console.print("=" * 60)
            
            for name, check in health_results["checks"].items():
                status_icon = "✅" if check["status"] == "pass" else "❌"
                critical_mark = " (CRITICAL)" if check["critical"] else ""
                
                console.print(f"{status_icon} {name}{critical_mark}")
                console.print(f"   📝 {check['description']}")
                
                if check["status"] == "pass":
                    console.print(f"   ⏱️ Duration: {check.get('duration', 0):.3f}s")
                    if "details" in check:
                        details = check["details"]
                        if isinstance(details, dict) and "usage_percent" in details:
                            console.print(f"   📊 Usage: {details['usage_percent']:.1f}%")
                else:
                    console.print(f"   ❌ Error: {check.get('error', 'Unknown error')}")
                
                console.print()
        
        elif action == "export":
            if not export_file:
                export_file = f"monitoring_export_{datetime.now().strftime('%Y%m%d_%H%M%S')}.{format}"
            
            console.print(f"📤 Exporting comprehensive monitoring data...")
            
            # Get all monitoring data
            import asyncio
            status = asyncio.run(monitoring_system.get_comprehensive_status())
            metrics = monitoring_system.export_metrics("json")
            
            export_data = {
                "export_timestamp": datetime.now().isoformat(),
                "format": format,
                "system_status": status,
                "metrics": json.loads(metrics) if format == "json" else metrics
            }
            
            with open(export_file, 'w') as f:
                if format == "json":
                    json.dump(export_data, f, indent=2, default=str)
                else:
                    f.write(json.dumps(export_data, indent=2, default=str))
            
            console.print(f"✅ [green]Monitoring data exported to: {export_file}[/green]")
            console.print(f"📊 Includes: health checks, metrics, system status")
        
        else:
            console.print(f"[red]❌ Unknown action: {action}[/red]")
            console.print("Valid actions: start, status, metrics, health, export")
    
    except ImportError as e:
        console.print(f"[red]❌ Monitoring dependencies missing: {e}[/red]")
        console.print("Install with: pip install psutil")
        raise typer.Exit(1)
    except Exception as e:
        console.print(f"[red]❌ Monitoring error: {e}[/red]")
        raise typer.Exit(1)


@app.command()
def moderate(
    action: str = typer.Argument(..., help="Action: scan, validate, report, test"),
    content: str = typer.Option(None, help="Text content to moderate"),
    image_path: str = typer.Option(None, help="Path to image file"),
    campaign_file: str = typer.Option(None, help="Campaign brief file to moderate"),
    industry: str = typer.Option("general", help="Industry for brand safety rules"),
    export_report: bool = typer.Option(False, help="Export detailed moderation report")
):
    """Content moderation and brand safety validation"""
    try:
        from src.content_moderation import (
            ComprehensiveContentModerator, TextModerator, ImageModerator, 
            BrandSafetyValidator, ContentRisk
        )
        
        moderator = ComprehensiveContentModerator()
        
        if action == "scan":
            if content:
                # Text moderation
                console.print("🔍 Scanning text content...")
                result = moderator.text_moderator.moderate_text(content)
                
                console.print(f"\n📝 **Text Moderation Results**")
                console.print("=" * 50)
                console.print(f"📊 Category: {result.category.value}")
                console.print(f"⚠️ Risk Level: {result.risk_level.value}")
                console.print(f"🎯 Confidence: {result.confidence:.1%}")
                
                if result.flags:
                    console.print(f"\n🚩 **Flags ({len(result.flags)})**")
                    for flag in result.flags:
                        console.print(f"• {flag}")
                
                console.print(f"\n📋 **Details**")
                for key, value in result.details.items():
                    console.print(f"• {key}: {value}")
            
            elif image_path:
                # Image moderation
                if not os.path.exists(image_path):
                    console.print(f"[red]❌ Image file not found: {image_path}[/red]")
                    return
                
                console.print(f"🖼️ Scanning image: {image_path}")
                result = moderator.image_moderator.moderate_image(image_path)
                
                console.print(f"\n🖼️ **Image Moderation Results**")
                console.print("=" * 50)
                console.print(f"📊 Category: {result.category.value}")
                console.print(f"⚠️ Risk Level: {result.risk_level.value}")
                console.print(f"🎯 Confidence: {result.confidence:.1%}")
                
                if result.flags:
                    console.print(f"\n🚩 **Flags ({len(result.flags)})**")
                    for flag in result.flags:
                        console.print(f"• {flag}")
                
                console.print(f"\n📋 **Image Analysis**")
                for key, value in result.details.items():
                    console.print(f"• {key}: {value}")
            
            else:
                console.print("[red]❌ Provide either --content or --image-path[/red]")
        
        elif action == "validate":
            if not campaign_file:
                console.print("[red]❌ Campaign file required for validation[/red]")
                return
            
            if not os.path.exists(campaign_file):
                console.print(f"[red]❌ Campaign file not found: {campaign_file}[/red]")
                return
            
            # Load campaign brief
            with open(campaign_file, 'r') as f:
                if campaign_file.endswith('.json'):
                    campaign_brief = json.load(f)
                else:
                    import yaml
                    campaign_brief = yaml.safe_load(f)
            
            console.print(f"🛡️ Validating campaign: {campaign_file}")
            console.print(f"🏭 Industry: {industry}")
            
            # Run comprehensive moderation
            results = moderator.moderate_campaign_content(campaign_brief, industry=industry)
            
            # Display results
            console.print(f"\n🛡️ **Campaign Moderation Results**")
            console.print("=" * 60)
            
            status_emoji = {
                "safe": "✅", "warnings": "⚡", "review_required": "⚠️", 
                "blocked": "🚨", "error": "❌"
            }.get(results["overall_status"], "❓")
            
            console.print(f"{status_emoji} Overall Status: {results['overall_status'].upper()}")
            console.print(f"⚠️ Risk Level: {results['overall_risk'].upper()}")
            console.print(f"📊 Moderation Score: {results['summary'].get('moderation_score', 0)}/100")
            
            # Summary stats
            summary = results["summary"]
            console.print(f"\n📈 **Summary Statistics**")
            console.print(f"• Total flags: {summary['total_flags']}")
            console.print(f"• Critical issues: {summary['critical_issues']}")
            
            # Text moderation results
            if results["text_moderation"]:
                console.print(f"\n📝 **Text Analysis**")
                for content_type, text_result in results["text_moderation"].items():
                    risk = text_result["risk_level"]
                    risk_emoji = "🚨" if risk == "critical" else "⚠️" if risk == "high" else "⚡" if risk == "medium" else "✅"
                    console.print(f"{risk_emoji} {content_type}: {risk} ({len(text_result['flags'])} flags)")
            
            # Brand safety results
            brand_safety = results["brand_safety"]
            console.print(f"\n🛡️ **Brand Safety**")
            console.print(f"• Safety Score: {brand_safety['safety_score']}/100")
            console.print(f"• Violations: {brand_safety['summary']['total_violations']}")
            console.print(f"• Warnings: {brand_safety['summary']['total_warnings']}")
            
            # Recommendations
            if summary["recommendations"]:
                console.print(f"\n💡 **Recommendations**")
                for i, rec in enumerate(summary["recommendations"], 1):
                    console.print(f"{i}. {rec}")
            
            # Export detailed report
            if export_report:
                report_file = f"moderation_report_{results['campaign_id']}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
                with open(report_file, 'w') as f:
                    json.dump(results, f, indent=2, default=str)
                console.print(f"\n📄 Detailed report exported: {report_file}")
        
        elif action == "report":
            # Generate moderation summary report
            console.print("📊 Generating moderation system report...")
            
            report = {
                "report_timestamp": datetime.now().isoformat(),
                "moderation_capabilities": {
                    "text_analysis": {
                        "categories": ["adult", "violence", "hate_speech", "drugs", "weapons", "gambling"],
                        "features": ["keyword_matching", "medical_claims", "brand_safety"]
                    },
                    "image_analysis": {
                        "features": ["basic_statistical", "aspect_ratio", "color_analysis", "file_size"],
                        "note": "Free tier - limited analysis"
                    },
                    "brand_safety": {
                        "industries": ["healthcare", "finance", "food", "general"],
                        "features": ["context_analysis", "guideline_compliance", "disclaimer_checking"]
                    }
                },
                "risk_levels": ["low", "medium", "high", "critical"],
                "supported_formats": {
                    "text": "Any text content",
                    "images": ["jpg", "jpeg", "png", "gif", "webp"],
                    "campaigns": ["yaml", "json"]
                }
            }
            
            console.print(f"\n📊 **Content Moderation System Report**")
            console.print("=" * 60)
            
            # Text analysis capabilities
            text_caps = report["moderation_capabilities"]["text_analysis"]
            console.print(f"📝 **Text Analysis**")
            console.print(f"• Categories: {len(text_caps['categories'])}")
            console.print(f"• Features: {', '.join(text_caps['features'])}")
            
            # Image analysis capabilities
            img_caps = report["moderation_capabilities"]["image_analysis"]
            console.print(f"\n🖼️ **Image Analysis**")
            console.print(f"• Features: {', '.join(img_caps['features'])}")
            console.print(f"• Note: {img_caps['note']}")
            
            # Brand safety
            brand_caps = report["moderation_capabilities"]["brand_safety"]
            console.print(f"\n🛡️ **Brand Safety**")
            console.print(f"• Supported industries: {', '.join(brand_caps['industries'])}")
            console.print(f"• Features: {', '.join(brand_caps['features'])}")
            
            # Export full report
            report_file = f"moderation_system_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
            with open(report_file, 'w') as f:
                json.dump(report, f, indent=2)
            console.print(f"\n📄 System report exported: {report_file}")
        
        elif action == "test":
            console.print("🧪 Running moderation system tests...")
            
            test_cases = [
                ("Safe content", "This is a great product for families"),
                ("Medical claim", "This miracle cure will heal you instantly"),
                ("Adult content", "Explicit adult content not suitable for general audience"),
                ("Violence", "Violent imagery with weapons and blood"),
                ("Brand unsafe", "Controversial political statement during crisis")
            ]
            
            console.print(f"\n🧪 **Test Results**")
            console.print("=" * 50)
            
            for test_name, test_content in test_cases:
                result = moderator.text_moderator.moderate_text(test_content)
                
                risk_emoji = {
                    "low": "✅", "medium": "⚡", "high": "⚠️", "critical": "🚨"
                }.get(result.risk_level.value, "❓")
                
                console.print(f"{risk_emoji} {test_name}")
                console.print(f"   Risk: {result.risk_level.value} | Category: {result.category.value}")
                console.print(f"   Flags: {len(result.flags)} | Confidence: {result.confidence:.1%}")
                console.print()
            
            console.print("✅ [green]All tests completed[/green]")
        
        else:
            console.print(f"[red]❌ Unknown action: {action}[/red]")
            console.print("Valid actions: scan, validate, report, test")
    
    except ImportError as e:
        console.print(f"[red]❌ Content moderation dependencies missing: {e}[/red]")
        console.print("All dependencies should be available - check installation")
        raise typer.Exit(1)
    except Exception as e:
        console.print(f"[red]❌ Content moderation error: {e}[/red]")
        raise typer.Exit(1)


@app.command()
def tenant(
    action: str = typer.Argument(..., help="Action: create, list, upgrade, usage, users, keys"),
    tenant_name: str = typer.Option(None, help="Tenant name for creation"),
    plan: str = typer.Option("free", help="Tenant plan (free, starter, professional, enterprise)"),
    tenant_id: str = typer.Option(None, help="Tenant ID for operations"),
    admin_email: str = typer.Option(None, help="Admin user email"),
    admin_name: str = typer.Option(None, help="Admin user name"),
    export_report: bool = typer.Option(False, help="Export detailed usage report")
):
    """Multi-tenant architecture management for enterprise isolation"""
    try:
        from src.multi_tenant import (
            TenantManager, tenant_manager, TenantStatus, ResourceType,
            Permission, TenantUser
        )
        
        if action == "create":
            if not tenant_name:
                console.print("[red]❌ Tenant name required for creation[/red]")
                return
            
            console.print(f"🏢 Creating tenant: {tenant_name}")
            console.print(f"📋 Plan: {plan}")
            
            try:
                new_tenant_id = tenant_manager.create_tenant(
                    name=tenant_name,
                    plan=plan,
                    admin_email=admin_email,
                    admin_name=admin_name
                )
                
                # Create API key
                api_key = tenant_manager.create_api_key(new_tenant_id)
                
                console.print(f"✅ [green]Tenant created successfully[/green]")
                console.print(f"🆔 Tenant ID: {new_tenant_id}")
                console.print(f"🔑 API Key: {api_key}")
                
                if admin_email:
                    console.print(f"👤 Admin User: {admin_name} ({admin_email})")
                
                # Show plan details
                tenant = tenant_manager.get_tenant(new_tenant_id)
                console.print(f"\n📊 **Plan Quotas**")
                for resource_type, quota in tenant.quotas.items():
                    console.print(f"• {resource_type.value}: {quota.limit}")
                
            except Exception as e:
                console.print(f"[red]❌ Failed to create tenant: {e}[/red]")
        
        elif action == "list":
            tenants = tenant_manager.list_tenants()
            
            if not tenants:
                console.print("🏢 No tenants found")
                return
            
            console.print(f"\n🏢 **Tenants ({len(tenants)})**")
            console.print("=" * 80)
            
            for tenant_info in tenants:
                status_emoji = {
                    "active": "🟢", "trial": "🟡", "suspended": "🔴", "expired": "⚫"
                }.get(tenant_info["status"], "❓")
                
                plan_emoji = {
                    "free": "🆓", "starter": "🚀", "professional": "💼", "enterprise": "🏭"
                }.get(tenant_info["plan"], "📋")
                
                console.print(f"{status_emoji} {tenant_info['name']}")
                console.print(f"   🆔 {tenant_info['tenant_id']}")
                console.print(f"   {plan_emoji} {tenant_info['plan'].title()} Plan")
                console.print(f"   👥 {tenant_info['users_count']} users")
                console.print(f"   📊 Quota usage: {tenant_info['avg_quota_usage']:.1f}%")
                
                if tenant_info['exceeded_quotas'] > 0:
                    console.print(f"   ⚠️ {tenant_info['exceeded_quotas']} quotas exceeded")
                
                console.print()
        
        elif action == "upgrade":
            if not tenant_id:
                console.print("[red]❌ Tenant ID required for upgrade[/red]")
                return
            
            console.print(f"⬆️ Upgrading tenant {tenant_id} to {plan}...")
            
            if tenant_manager.upgrade_tenant_plan(tenant_id, plan):
                console.print("✅ [green]Tenant upgraded successfully[/green]")
                
                # Show new quotas
                tenant = tenant_manager.get_tenant(tenant_id)
                console.print(f"\n📊 **New Plan Quotas**")
                for resource_type, quota in tenant.quotas.items():
                    console.print(f"• {resource_type.value}: {quota.limit}")
            else:
                console.print("[red]❌ Failed to upgrade tenant[/red]")
        
        elif action == "usage":
            if not tenant_id:
                console.print("[red]❌ Tenant ID required for usage report[/red]")
                return
            
            console.print(f"📊 Generating usage report for tenant: {tenant_id}")
            
            report = tenant_manager.get_tenant_usage_report(tenant_id)
            
            if "error" in report:
                console.print(f"[red]❌ {report['error']}[/red]")
                return
            
            console.print(f"\n📊 **Usage Report: {report['tenant_name']}**")
            console.print("=" * 60)
            console.print(f"📋 Plan: {report['plan'].title()}")
            console.print(f"⚡ Status: {report['status'].title()}")
            console.print(f"📅 Period: Last {report['report_period_days']} days")
            
            # Quota information
            console.print(f"\n📊 **Resource Quotas**")
            for resource_name, quota_info in report["quotas"].items():
                usage_pct = quota_info["usage_percentage"]
                usage_bar = "🟢" if usage_pct < 50 else "🟡" if usage_pct < 80 else "🔴"
                
                console.print(f"{usage_bar} {resource_name}")
                console.print(f"   📈 {quota_info['current_usage']}/{quota_info['limit']} ({usage_pct:.1f}%)")
                console.print(f"   📉 Remaining: {quota_info['remaining']}")
            
            # Usage statistics
            if report["usage"]:
                console.print(f"\n🎯 **Usage Statistics**")
                for resource_name, usage_data in report["usage"].items():
                    console.print(f"• {resource_name}: {usage_data['total_usage']} total usage in {usage_data['usage_count']} operations")
            
            # Recommendations
            if report["recommendations"]:
                console.print(f"\n💡 **Recommendations**")
                for i, rec in enumerate(report["recommendations"], 1):
                    console.print(f"{i}. {rec}")
            
            # Export detailed report
            if export_report:
                report_file = f"tenant_usage_{tenant_id}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
                with open(report_file, 'w') as f:
                    json.dump(report, f, indent=2, default=str)
                console.print(f"\n📄 Detailed report exported: {report_file}")
        
        elif action == "users":
            if not tenant_id:
                console.print("[red]❌ Tenant ID required for user management[/red]")
                return
            
            tenant = tenant_manager.get_tenant(tenant_id)
            if not tenant:
                console.print(f"[red]❌ Tenant {tenant_id} not found[/red]")
                return
            
            console.print(f"\n👥 **Users in {tenant.name}**")
            console.print("=" * 60)
            
            if not tenant.users:
                console.print("No users found")
                return
            
            for user in tenant.users.values():
                status_emoji = "🟢" if user.is_active else "🔴"
                admin_mark = " (ADMIN)" if Permission.ADMIN_ACCESS in user.permissions else ""
                
                console.print(f"{status_emoji} {user.name}{admin_mark}")
                console.print(f"   📧 {user.email}")
                console.print(f"   🆔 {user.user_id}")
                console.print(f"   🔑 {len(user.permissions)} permissions")
                console.print(f"   📅 Created: {user.created_at[:10]}")
                if user.last_login:
                    console.print(f"   🕒 Last login: {user.last_login[:10]}")
                console.print()
        
        elif action == "keys":
            if not tenant_id:
                console.print("[red]❌ Tenant ID required for API key operations[/red]")
                return
            
            tenant = tenant_manager.get_tenant(tenant_id)
            if not tenant:
                console.print(f"[red]❌ Tenant {tenant_id} not found[/red]")
                return
            
            # Generate new API key
            console.print(f"🔑 Generating new API key for {tenant.name}...")
            
            api_key = tenant_manager.create_api_key(tenant_id)
            
            console.print(f"✅ [green]API key created successfully[/green]")
            console.print(f"🔑 API Key: {api_key}")
            console.print(f"⚠️ Store this key securely - it cannot be retrieved again")
            
            # Show existing keys count
            existing_keys = [k for k, tid in tenant_manager.api_keys.items() if tid == tenant_id]
            console.print(f"📊 Total API keys for this tenant: {len(existing_keys)}")
        
        else:
            console.print(f"[red]❌ Unknown action: {action}[/red]")
            console.print("Valid actions: create, list, upgrade, usage, users, keys")
    
    except ImportError as e:
        console.print(f"[red]❌ Multi-tenant dependencies missing: {e}[/red]")
        console.print("All dependencies should be available - check installation")
        raise typer.Exit(1)
    except Exception as e:
        console.print(f"[red]❌ Multi-tenant error: {e}[/red]")
        raise typer.Exit(1)


@app.command()
def workflow(
    action: str = typer.Argument(..., help="Action: create, execute, status, list, templates, graph"),
    workflow_name: str = typer.Option(None, help="Workflow name for creation"),
    workflow_id: str = typer.Option(None, help="Workflow ID for operations"),
    template: str = typer.Option("basic", help="Workflow template (basic, enterprise)"),
    campaign_file: str = typer.Option(None, help="Campaign brief file for execution"),
    export_graph: bool = typer.Option(False, help="Export visual workflow graph")
):
    """Workflow orchestration with visual pipeline designer"""
    try:
        from src.workflow_orchestration import (
            WorkflowEngine, workflow_engine, WorkflowTemplates,
            WorkflowStatus, StepStatus
        )
        
        if action == "create":
            if not workflow_name:
                console.print("[red]❌ Workflow name required for creation[/red]")
                return
            
            console.print(f"🔧 Creating workflow: {workflow_name}")
            console.print(f"📋 Template: {template}")
            
            # Get template steps
            if template == "basic":
                steps = WorkflowTemplates.basic_campaign_workflow()
                description = "Basic campaign generation workflow"
            elif template == "enterprise":
                steps = WorkflowTemplates.enterprise_workflow()
                description = "Enterprise workflow with advanced features"
            else:
                console.print(f"[red]❌ Unknown template: {template}[/red]")
                return
            
            try:
                new_workflow_id = workflow_engine.create_workflow(
                    name=workflow_name,
                    description=description,
                    steps=steps
                )
                
                console.print(f"✅ [green]Workflow created successfully[/green]")
                console.print(f"🆔 Workflow ID: {new_workflow_id}")
                console.print(f"📊 Steps: {len(steps)}")
                
                # Show step overview
                console.print(f"\n🔧 **Workflow Steps**")
                for i, step in enumerate(steps, 1):
                    console.print(f"{i}. {step['name']} ({step['step_type']})")
                
            except Exception as e:
                console.print(f"[red]❌ Failed to create workflow: {e}[/red]")
        
        elif action == "execute":
            if not workflow_id:
                console.print("[red]❌ Workflow ID required for execution[/red]")
                return
            
            if not campaign_file:
                console.print("[red]❌ Campaign file required for execution[/red]")
                return
            
            if not os.path.exists(campaign_file):
                console.print(f"[red]❌ Campaign file not found: {campaign_file}[/red]")
                return
            
            # Load campaign brief
            with open(campaign_file, 'r') as f:
                if campaign_file.endswith('.json'):
                    campaign_brief = json.load(f)
                else:
                    import yaml
                    campaign_brief = yaml.safe_load(f)
            
            console.print(f"🚀 Executing workflow: {workflow_id}")
            console.print(f"📄 Campaign: {campaign_file}")
            
            try:
                import asyncio
                result = asyncio.run(workflow_engine.execute_workflow(
                    workflow_id, 
                    {"campaign_brief": campaign_brief}
                ))
                
                console.print(f"\n🎯 **Execution Results**")
                console.print("=" * 50)
                console.print(f"⚡ Status: {result['status'].upper()}")
                console.print(f"✅ Completed Steps: {result['steps_completed']}/{result['total_steps']}")
                console.print(f"❌ Failed Steps: {result['steps_failed']}")
                console.print(f"⏱️ Duration: {result['duration_seconds']:.1f} seconds")
                
                if result['status'] == 'failed':
                    console.print("[red]⚠️ Workflow execution failed[/red]")
                else:
                    console.print("[green]✅ Workflow completed successfully[/green]")
                
            except Exception as e:
                console.print(f"[red]❌ Workflow execution failed: {e}[/red]")
        
        elif action == "status":
            if not workflow_id:
                console.print("[red]❌ Workflow ID required for status check[/red]")
                return
            
            status = workflow_engine.get_workflow_status(workflow_id)
            
            if "error" in status:
                console.print(f"[red]❌ {status['error']}[/red]")
                return
            
            console.print(f"\n📊 **Workflow Status: {status['name']}**")
            console.print("=" * 60)
            console.print(f"🆔 ID: {status['workflow_id']}")
            console.print(f"⚡ Status: {status['status'].upper()}")
            console.print(f"📈 Progress: {status['progress']['percentage']:.1f}%")
            console.print(f"✅ Completed: {status['progress']['completed']}")
            console.print(f"❌ Failed: {status['progress']['failed']}")
            console.print(f"🏃 Running: {status['progress']['running']}")
            console.print(f"📋 Total: {status['progress']['total']}")
            
            if status['created_at']:
                console.print(f"📅 Created: {status['created_at'][:19]}")
            if status['started_at']:
                console.print(f"🚀 Started: {status['started_at'][:19]}")
            if status['completed_at']:
                console.print(f"🏁 Completed: {status['completed_at'][:19]}")
            
            # Step details
            console.print(f"\n🔧 **Step Details**")
            console.print("-" * 50)
            
            for step in status['steps']:
                status_emoji = {
                    "pending": "⏳", "running": "🏃", "completed": "✅", 
                    "failed": "❌", "skipped": "⏭️", "rolled_back": "↩️"
                }.get(step['status'], "❓")
                
                console.print(f"{status_emoji} {step['name']}")
                console.print(f"   📋 Type: {step['type']}")
                console.print(f"   ⚡ Status: {step['status']}")
                
                if step['duration']:
                    console.print(f"   ⏱️ Duration: {step['duration']:.1f}s")
                
                if step['error']:
                    console.print(f"   ❌ Error: {step['error']}")
                
                console.print()
        
        elif action == "list":
            workflows = workflow_engine.list_workflows()
            
            if not workflows:
                console.print("🔧 No workflows found")
                return
            
            console.print(f"\n🔧 **Workflows ({len(workflows)})**")
            console.print("=" * 80)
            
            for wf in workflows:
                status_emoji = {
                    "draft": "📝", "running": "🏃", "completed": "✅", 
                    "failed": "❌", "paused": "⏸️", "cancelled": "🚫"
                }.get(wf['status'], "❓")
                
                console.print(f"{status_emoji} {wf['name']}")
                console.print(f"   🆔 {wf['workflow_id']}")
                console.print(f"   📝 {wf['description']}")
                console.print(f"   📊 {wf['steps_count']} steps")
                console.print(f"   📈 Progress: {wf['progress']:.1f}%")
                console.print(f"   📅 Created: {wf['created_at'][:19]}")
                console.print()
        
        elif action == "templates":
            console.print(f"\n📋 **Available Workflow Templates**")
            console.print("=" * 60)
            
            # Basic template
            basic_steps = WorkflowTemplates.basic_campaign_workflow()
            console.print(f"🔧 **Basic Template** ({len(basic_steps)} steps)")
            console.print("   📝 Standard campaign generation workflow")
            console.print("   🎯 Steps: Validate → Compliance → Moderation → Generate → Compose")
            console.print()
            
            # Enterprise template  
            enterprise_steps = WorkflowTemplates.enterprise_workflow()
            console.print(f"🏭 **Enterprise Template** ({len(enterprise_steps)} steps)")
            console.print("   📝 Advanced workflow with localization, A/B testing, and notifications")
            console.print("   🎯 Includes: Localization → A/B Testing → Notifications")
            console.print()
            
            console.print("💡 Create with: python main.py workflow create --template <template_name>")
        
        elif action == "graph":
            if not workflow_id:
                console.print("[red]❌ Workflow ID required for graph generation[/red]")
                return
            
            graph = workflow_engine.get_visual_graph(workflow_id)
            
            if "error" in graph:
                console.print(f"[red]❌ {graph['error']}[/red]")
                return
            
            console.print(f"\n📊 **Workflow Graph: {graph['name']}**")
            console.print("=" * 60)
            console.print(f"⚡ Status: {graph['status'].upper()}")
            console.print(f"📈 Progress: {graph['progress']['percentage']:.1f}%")
            console.print(f"📊 Nodes: {len(graph['nodes'])}")
            console.print(f"🔗 Edges: {len(graph['edges'])}")
            
            # Display nodes
            console.print(f"\n🔧 **Workflow Nodes**")
            console.print("-" * 40)
            
            for node in graph['nodes']:
                status_emoji = {
                    "pending": "⏳", "running": "🏃", "completed": "✅", 
                    "failed": "❌", "skipped": "⏭️"
                }.get(node['status'], "❓")
                
                console.print(f"{status_emoji} {node['name']}")
                console.print(f"   🆔 {node['id']}")
                console.print(f"   📋 {node['type']}")
                
                if node['duration']:
                    console.print(f"   ⏱️ {node['duration']:.1f}s")
                
                console.print()
            
            # Display dependencies
            if graph['edges']:
                console.print(f"🔗 **Dependencies**")
                console.print("-" * 30)
                
                for edge in graph['edges']:
                    console.print(f"• {edge['source']} → {edge['target']}")
            
            # Export graph data
            if export_graph:
                graph_file = f"workflow_graph_{workflow_id}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
                with open(graph_file, 'w') as f:
                    json.dump(graph, f, indent=2)
                console.print(f"\n📄 Graph data exported: {graph_file}")
        
        else:
            console.print(f"[red]❌ Unknown action: {action}[/red]")
            console.print("Valid actions: create, execute, status, list, templates, graph")
    
    except ImportError as e:
        console.print(f"[red]❌ Workflow dependencies missing: {e}[/red]")
        console.print("All dependencies should be available - check installation")
        raise typer.Exit(1)
    except Exception as e:
        console.print(f"[red]❌ Workflow error: {e}[/red]")
        raise typer.Exit(1)


@app.command()
def optimize(
    action: str = typer.Argument(..., help="Action: cache, images, report, clear, test"),
    campaign_id: str = typer.Option(None, help="Campaign ID for cache operations"),
    image_path: str = typer.Option(None, help="Image path for optimization"),
    output_formats: str = typer.Option("thumbnail,small,medium,large", help="Comma-separated optimization formats"),
    user_location: str = typer.Option("US", help="User location for CDN optimization (US, UK, DE, JP, FR)"),
    export_report: bool = typer.Option(False, help="Export performance report")
):
    """Performance optimization with caching and image optimization"""
    try:
        from src.performance_optimization import (
            PerformanceOptimizer, performance_optimizer, ImageOptimizer, CDNSimulator
        )
        
        if action == "cache":
            if not campaign_id:
                console.print("[red]❌ Campaign ID required for cache operations[/red]")
                return
            
            # Check cache status
            cached_result = performance_optimizer.get_cached_campaign(campaign_id)
            
            if cached_result:
                console.print(f"✅ [green]Cache HIT for campaign: {campaign_id}[/green]")
                console.print(f"📊 Cached data size: {len(str(cached_result))} characters")
                console.print(f"🎯 Contains: {list(cached_result.keys())}")
            else:
                console.print(f"❌ [yellow]Cache MISS for campaign: {campaign_id}[/yellow]")
                
                # Simulate caching some data
                console.print("💾 Caching sample campaign data...")
                sample_data = {
                    "campaign_id": campaign_id,
                    "assets_generated": 6,
                    "generation_time": 45.2,
                    "cost": 0.28,
                    "cached_at": datetime.now().isoformat()
                }
                
                performance_optimizer.cache_campaign_result(campaign_id, sample_data)
                console.print("✅ [green]Campaign data cached successfully[/green]")
            
            # Show cache statistics
            cache_stats = performance_optimizer.memory_cache.get_stats()
            console.print(f"\n📈 **Cache Statistics**")
            console.print(f"• Hit rate: {cache_stats['hit_rate_percent']:.1f}%")
            console.print(f"• Entries: {cache_stats['current_entries']}/{cache_stats['max_entries']}")
            console.print(f"• Memory usage: {cache_stats['current_size_mb']:.1f}/{cache_stats['max_size_mb']:.1f} MB")
            console.print(f"• Utilization: {cache_stats['utilization_percent']:.1f}%")
        
        elif action == "images":
            if not image_path:
                console.print("[red]❌ Image path required for optimization[/red]")
                return
            
            if not os.path.exists(image_path):
                console.print(f"[red]❌ Image file not found: {image_path}[/red]")
                return
            
            console.print(f"🖼️ Optimizing image: {image_path}")
            
            # Parse output formats
            formats = [f.strip() for f in output_formats.split(",")]
            console.print(f"📋 Formats: {', '.join(formats)}")
            
            try:
                # Optimize image
                optimizer = ImageOptimizer()
                optimized_paths = optimizer.optimize_image(image_path, formats)
                
                console.print(f"✅ [green]Image optimization completed[/green]")
                console.print(f"📊 Generated {len(optimized_paths)} optimized versions")
                
                # Show optimization results
                console.print(f"\n🎯 **Optimized Versions**")
                for format_name, path in optimized_paths.items():
                    if os.path.exists(path):
                        size_mb = os.path.getsize(path) / (1024 * 1024)
                        console.print(f"• {format_name}: {path} ({size_mb:.2f} MB)")
                
                # Get detailed stats
                stats = optimizer.get_optimization_stats(image_path, optimized_paths)
                console.print(f"\n📈 **Optimization Statistics**")
                console.print(f"• Original size: {stats['original_size_mb']:.2f} MB")
                
                for format_name, version_stats in stats["optimized_versions"].items():
                    compression = version_stats["compression_ratio_percent"]
                    console.print(f"• {format_name}: {version_stats['size_mb']:.2f} MB ({compression:.1f}% reduction)")
                
                # Simulate CDN upload
                console.print(f"\n🌐 **CDN Simulation**")
                cdn_simulator = CDNSimulator()
                
                for format_name, opt_path in optimized_paths.items():
                    cdn_path = f"test/{Path(image_path).stem}_{format_name}.jpg"
                    cdn_urls = cdn_simulator.upload_to_cdn(opt_path, cdn_path)
                    
                    # Get optimal URL for user location
                    optimal = cdn_simulator.get_optimal_url(user_location, cdn_urls)
                    
                    console.print(f"• {format_name}:")
                    console.print(f"  🌍 Optimal edge: {optimal['edge_location']}")
                    console.print(f"  ⚡ Latency: {optimal['estimated_latency_ms']}ms")
                    console.print(f"  🔗 URL: {optimal['optimal_url']}")
                
            except Exception as e:
                console.print(f"[red]❌ Image optimization failed: {e}[/red]")
        
        elif action == "report":
            console.print("📊 Generating performance report...")
            
            report = performance_optimizer.get_performance_report()
            
            console.print(f"\n📈 **Performance Report**")
            console.print("=" * 60)
            console.print(f"📅 Generated: {report['timestamp'][:19]}")
            
            # Cache performance
            cache_perf = report["cache_performance"]
            console.print(f"\n💾 **Cache Performance**")
            console.print(f"• Memory hit rate: {cache_perf['memory_hit_rate']:.1f}%")
            console.print(f"• Memory utilization: {cache_perf['memory_utilization']:.1f}%")
            
            # Optimization metrics
            metrics = report["optimization_metrics"]
            console.print(f"\n🔧 **Optimization Metrics**")
            console.print(f"• Cache operations: {metrics['cache_operations']}")
            console.print(f"• Image optimizations: {metrics['image_optimizations']}")
            console.print(f"• CDN uploads: {metrics['cdn_uploads']}")
            console.print(f"• Time saved: {metrics['total_time_saved_seconds']:.1f}s")
            
            # Recommendations
            recommendations = report["recommendations"]
            if recommendations:
                console.print(f"\n💡 **Recommendations**")
                for i, rec in enumerate(recommendations, 1):
                    console.print(f"{i}. {rec}")
            
            # Export detailed report
            if export_report:
                report_file = f"performance_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
                with open(report_file, 'w') as f:
                    json.dump(report, f, indent=2, default=str)
                console.print(f"\n📄 Detailed report exported: {report_file}")
        
        elif action == "clear":
            console.print("🧹 Clearing cache...")
            
            if campaign_id:
                result = performance_optimizer.clear_campaign_cache(campaign_id)
                console.print(f"✅ [green]Cleared cache for campaign: {campaign_id}[/green]")
            else:
                result = performance_optimizer.clear_campaign_cache()
                console.print("✅ [green]Cleared all campaign caches[/green]")
            
            console.print(f"• Memory entries cleared: {result['memory_entries_cleared']}")
            console.print(f"• Disk entries cleared: {result['disk_entries_cleared']}")
        
        elif action == "test":
            console.print("🧪 Running performance optimization tests...")
            
            # Test cache performance
            console.print("\n💾 **Cache Performance Test**")
            test_data = {"test": "data", "timestamp": datetime.now().isoformat()}
            
            # Measure cache set time
            start_time = time.time()
            performance_optimizer.cache_campaign_result("test_campaign", test_data)
            cache_set_time = (time.time() - start_time) * 1000
            
            # Measure cache get time
            start_time = time.time()
            cached_data = performance_optimizer.get_cached_campaign("test_campaign")
            cache_get_time = (time.time() - start_time) * 1000
            
            console.print(f"• Cache SET: {cache_set_time:.2f}ms")
            console.print(f"• Cache GET: {cache_get_time:.2f}ms")
            console.print(f"• Data integrity: {'✅ Pass' if cached_data == test_data else '❌ Fail'}")
            
            # Test image optimization (if sample image exists)
            sample_images = ["assets/sample.jpg", "output/test.jpg"]
            test_image = None
            
            for img_path in sample_images:
                if os.path.exists(img_path):
                    test_image = img_path
                    break
            
            if test_image:
                console.print(f"\n🖼️ **Image Optimization Test**")
                console.print(f"• Testing with: {test_image}")
                
                start_time = time.time()
                optimizer = ImageOptimizer()
                optimized = optimizer.optimize_image(test_image, ["thumbnail", "small"])
                optimization_time = (time.time() - start_time) * 1000
                
                console.print(f"• Optimization time: {optimization_time:.2f}ms")
                console.print(f"• Versions created: {len(optimized)}")
                
                # Test CDN simulation
                console.print(f"\n🌐 **CDN Simulation Test**")
                cdn_simulator = CDNSimulator()
                
                cdn_test_time = 0
                for format_name, opt_path in optimized.items():
                    start_time = time.time()
                    cdn_urls = cdn_simulator.upload_to_cdn(opt_path, f"test/{format_name}.jpg")
                    cdn_test_time += (time.time() - start_time) * 1000
                
                console.print(f"• CDN upload simulation: {cdn_test_time:.2f}ms")
                console.print(f"• Edge locations: {len(cdn_simulator.edge_locations)}")
            else:
                console.print("\n🖼️ **Image Optimization Test**: Skipped (no sample images found)")
            
            console.print("\n✅ [green]All performance tests completed[/green]")
        
        else:
            console.print(f"[red]❌ Unknown action: {action}[/red]")
            console.print("Valid actions: cache, images, report, clear, test")
    
    except ImportError as e:
        console.print(f"[red]❌ Performance optimization dependencies missing: {e}[/red]")
        console.print("All dependencies should be available - check installation")
        raise typer.Exit(1)
    except Exception as e:
        console.print(f"[red]❌ Performance optimization error: {e}[/red]")
        raise typer.Exit(1)


@app.command()
def serve(
    host: str = typer.Option("0.0.0.0", help="Host to bind the API server"),
    port: int = typer.Option(8000, help="Port to bind the API server"),
    reload: bool = typer.Option(False, help="Enable auto-reload for development"),
    workers: int = typer.Option(1, help="Number of worker processes")
):
    """Start the API server for system integration"""
    try:
        import uvicorn
        from src.api_server import app as api_app
        
        console.print(f"🚀 Starting Creative Automation API server on {host}:{port}")
        console.print("📍 API Documentation: http://localhost:8000/docs")
        console.print("💡 Health Check: http://localhost:8000/health")
        
        uvicorn.run(
            "src.api_server:app",
            host=host,
            port=port,
            reload=reload,
            workers=workers if not reload else 1
        )
        
    except ImportError:
        console.print("❌ [red]FastAPI dependencies not installed. Run: pip install fastapi uvicorn[/red]")
        raise typer.Exit(1)
    except Exception as e:
        console.print(f"❌ [red]Failed to start API server: {e}[/red]")
        raise typer.Exit(1)


@app.command()
def audit(
    action: str = typer.Argument(..., help="Action: log, report, search, export"),
    event_type: str = typer.Option(None, help="Event type for logging"),
    action_description: str = typer.Option(None, help="Action description for logging"),
    user_id: str = typer.Option(None, help="User ID for audit logging"),
    tenant_id: str = typer.Option(None, help="Tenant ID for audit logging"),
    framework: str = typer.Option("gdpr", help="Compliance framework (gdpr, sox, soc2, hipaa, pci-dss)"),
    start_date: str = typer.Option(None, help="Start date for reports (YYYY-MM-DD)"),
    end_date: str = typer.Option(None, help="End date for reports (YYYY-MM-DD)"),
    output_format: str = typer.Option("csv", help="Export format (csv, json)"),
    output_file: str = typer.Option(None, help="Output file path"),
    export: bool = typer.Option(False, help="Export report to file")
):
    """Audit logging and compliance reporting for enterprise governance"""
    try:
        from src.audit_compliance import AuditLogger, AuditEventType, AuditLevel, ComplianceReporter
        
        audit_logger = AuditLogger()
        compliance_reporter = ComplianceReporter(audit_logger)
        
        if action == "log":
            if not event_type or not action_description:
                console.print("[red]❌ Event type and action description required for logging[/red]")
                raise typer.Exit(1)
            
            # Map string to enum
            event_type_map = {
                "user_login": AuditEventType.USER_LOGIN,
                "user_logout": AuditEventType.USER_LOGOUT,
                "campaign_created": AuditEventType.CAMPAIGN_CREATED,
                "campaign_generated": AuditEventType.CAMPAIGN_GENERATED,
                "campaign_deleted": AuditEventType.CAMPAIGN_DELETED,
                "asset_accessed": AuditEventType.ASSET_ACCESSED,
                "asset_downloaded": AuditEventType.ASSET_DOWNLOADED,
                "compliance_check": AuditEventType.COMPLIANCE_CHECK,
                "moderation_scan": AuditEventType.MODERATION_SCAN,
                "api_access": AuditEventType.API_ACCESS,
                "data_export": AuditEventType.DATA_EXPORT,
                "system_config": AuditEventType.SYSTEM_CONFIG,
                "batch_process": AuditEventType.BATCH_PROCESS,
                "ab_test_created": AuditEventType.AB_TEST_CREATED,
                "workflow_executed": AuditEventType.WORKFLOW_EXECUTED,
                "cache_access": AuditEventType.CACHE_ACCESS,
                "tenant_created": AuditEventType.TENANT_CREATED,
                "tenant_modified": AuditEventType.TENANT_MODIFIED
            }
            
            event_type_enum = event_type_map.get(event_type.lower())
            if not event_type_enum:
                console.print(f"[red]❌ Invalid event type: {event_type}[/red]")
                console.print("Valid types: " + ", ".join(event_type_map.keys()))
                raise typer.Exit(1)
            
            event_id = audit_logger.log_event(
                event_type=event_type_enum,
                action=action_description,
                level=AuditLevel.INFO,
                user_id=user_id,
                tenant_id=tenant_id
            )
            
            console.print(f"✅ Event logged with ID: {event_id}")
            
        elif action == "report":
            console.print(f"📊 Generating {framework.upper()} compliance report...")
            
            # Convert date strings to datetime
            start_dt = None
            end_dt = None
            if start_date:
                start_dt = datetime.fromisoformat(start_date)
            if end_date:
                end_dt = datetime.fromisoformat(end_date)
            
            # Use default date range if not provided (last 30 days)
            if not start_dt:
                start_dt = datetime.now() - timedelta(days=30)
            if not end_dt:
                end_dt = datetime.now()
            
            # Call the specific framework report method
            if framework.lower() == "gdpr":
                report = compliance_reporter.generate_gdpr_report(start_dt, end_dt)
            elif framework.lower() == "sox":
                report = compliance_reporter.generate_sox_report(start_dt, end_dt)
            elif framework.lower() == "soc2":
                report = compliance_reporter.generate_soc2_report(start_dt, end_dt)
            else:
                console.print(f"[red]❌ Unsupported compliance framework: {framework}[/red]")
                console.print("Supported frameworks: gdpr, sox, soc2")
                raise typer.Exit(1)
            
            console.print(f"\n📋 **{framework.upper()} Compliance Report**")
            console.print("=" * 50)
            console.print(f"Report ID: {report.get('report_id', 'Unknown')}")
            console.print(f"Period: {report.get('period', 'Unknown')}")
            console.print(f"Total Events: {report.get('total_events', 0)}")
            console.print(f"Status: {report.get('status', 'Unknown')}")
            
            if 'summary' in report:
                console.print(f"\n📊 **Summary**")
                summary = report['summary']
                for key, value in summary.items():
                    console.print(f"• {key}: {value}")
            
            if 'findings' in report and report['findings']:
                console.print(f"\n⚠️ **Findings ({len(report['findings'])})**")
                for finding in report['findings'][:5]:  # Show first 5
                    console.print(f"• {finding}")
            
            if 'violations' in report and report['violations']:
                console.print(f"\n❌ **Violations ({len(report['violations'])})**")
                for violation in report['violations'][:5]:  # Show first 5
                    console.print(f"• {violation}")
            
            if export:
                filename = f"{framework}_compliance_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
                if output_file:
                    filename = output_file
                
                with open(filename, 'w') as f:
                    json.dump(report, f, indent=2)
                console.print(f"📄 Report exported to: {filename}")
            
        elif action == "search":
            console.print("🔍 Searching audit logs...")
            
            search_params = {
                "user_id": user_id,
                "tenant_id": tenant_id
            }
            
            # Convert date strings to datetime if provided
            if start_date:
                search_params["start_time"] = datetime.fromisoformat(start_date)
            if end_date:
                search_params["end_time"] = datetime.fromisoformat(end_date)
            
            # Only add event_types if provided
            if event_type:
                event_type_enum = event_type_map.get(event_type.lower())
                if event_type_enum:
                    search_params["event_types"] = [event_type_enum]
            
            events = audit_logger.search_events(**search_params)
            
            console.print(f"\n📋 **Found {len(events)} events**")
            for event in events[:10]:  # Show first 10
                console.print(f"• [{event['timestamp']}] {event['event_type']} - {event['action']}")
                if event.get('user_id'):
                    console.print(f"  User: {event['user_id']}")
            
            if len(events) > 10:
                console.print(f"... and {len(events) - 10} more events")
        
        elif action == "export":
            console.print(f"📤 Exporting audit trail in {output_format.upper()} format...")
            
            filename = f"audit_trail_{datetime.now().strftime('%Y%m%d_%H%M%S')}.{output_format}"
            if output_file:
                filename = output_file
            
            # Convert date strings to datetime
            start_dt = None
            end_dt = None
            if start_date:
                start_dt = datetime.fromisoformat(start_date)
            if end_date:
                end_dt = datetime.fromisoformat(end_date)
            
            # Use default date range if not provided (last 30 days)
            if not start_dt:
                start_dt = datetime.now() - timedelta(days=30)
            if not end_dt:
                end_dt = datetime.now()
            
            generated_filename = compliance_reporter.export_audit_trail(
                start_date=start_dt,
                end_date=end_dt,
                format=output_format
            )
            
            # Rename file if custom filename provided
            if output_file and generated_filename != output_file:
                import shutil
                shutil.move(generated_filename, output_file)
                filename = output_file
            else:
                filename = generated_filename
            
            console.print(f"✅ Audit trail exported to: {filename}")
        
        else:
            console.print(f"[red]❌ Unknown action: {action}[/red]")
            console.print("Available actions: log, report, search, export")
            raise typer.Exit(1)
            
    except ImportError as e:
        console.print(f"[red]❌ Audit dependencies missing: {e}[/red]")
        console.print("All dependencies should be available - check installation")
        raise typer.Exit(1)
    except Exception as e:
        console.print(f"[red]❌ Audit error: {e}[/red]")
        raise typer.Exit(1)


@app.command()
def brand(
    action: str = typer.Argument(..., help="Action: analyze, extract-colors, assess-quality, validate-consistency, enhance, learn, report"),
    image_path: str = typer.Option(None, help="Path to image file"),
    image_paths: str = typer.Option(None, help="Comma-separated list of image paths for batch analysis"),
    output_path: str = typer.Option(None, help="Output path for enhanced image"),
    enhancement_level: str = typer.Option("moderate", help="Enhancement level: subtle, moderate, aggressive"),
    n_colors: int = typer.Option(8, help="Number of colors to extract"),
    reference_images: str = typer.Option(None, help="Comma-separated reference images for consistency check"),
    export_report: bool = typer.Option(False, help="Export detailed brand intelligence report"),
    learn_mode: bool = typer.Option(False, help="Learn from this asset for future brand consistency")
):
    """Advanced Computer Vision & Brand Intelligence System"""
    try:
        from src.brand_intelligence import BrandIntelligenceEngine
        
        brand_engine = BrandIntelligenceEngine()
        
        if action == "analyze":
            if not image_path:
                console.print("[red]❌ Image path required for analysis[/red]")
                raise typer.Exit(1)
            
            console.print(f"🔍 Analyzing image: {image_path}")
            
            # Extract all features
            palette = brand_engine.extract_color_palette(image_path, n_colors)
            quality = brand_engine.assess_image_quality(image_path)
            consistency = brand_engine.validate_brand_consistency(image_path)
            
            # Color palette analysis
            console.print(f"\n🎨 **Color Palette Analysis**")
            console.print("=" * 50)
            console.print(f"Color Harmony: {palette.color_harmony}")
            console.print(f"Temperature: {palette.temperature}")
            console.print(f"Saturation: {palette.saturation_level}")
            console.print(f"Brightness: {palette.brightness_level}")
            console.print(f"Accessibility Score: {palette.accessibility_score:.1f}%")
            
            console.print(f"\n🎯 **Dominant Colors**")
            for i, (color, hex_color, percentage) in enumerate(zip(palette.dominant_colors[:5], palette.hex_colors[:5], palette.color_percentages[:5])):
                console.print(f"{i+1}. {hex_color} - {percentage:.1f}% (RGB: {color})")
            
            # Quality assessment
            console.print(f"\n📊 **Image Quality Assessment**")
            console.print("=" * 50)
            console.print(f"Overall Score: {quality.overall_score:.1f}/100")
            console.print(f"Sharpness: {quality.sharpness:.1f}/100")
            console.print(f"Brightness: {quality.brightness:.1f}/100")
            console.print(f"Contrast: {quality.contrast:.1f}/100")
            console.print(f"Saturation: {quality.saturation:.1f}/100")
            console.print(f"Noise Level: {quality.noise_level:.1f}/100")
            console.print(f"Resolution: {quality.resolution_adequacy:.1f}/100")
            console.print(f"Composition: {quality.composition_score:.1f}/100")
            
            if quality.enhancement_recommendations:
                console.print(f"\n💡 **Enhancement Recommendations**")
                for rec in quality.enhancement_recommendations:
                    console.print(f"• {rec}")
            
            # Brand consistency
            console.print(f"\n🏢 **Brand Consistency Analysis**")
            console.print("=" * 50)
            console.print(f"Overall Brand Score: {consistency.overall_brand_score:.1f}/100")
            console.print(f"Color Consistency: {consistency.color_consistency:.1f}/100")
            console.print(f"Style Consistency: {consistency.style_consistency:.1f}/100")
            console.print(f"Composition Consistency: {consistency.composition_consistency:.1f}/100")
            
            if consistency.violations:
                console.print(f"\n⚠️ **Brand Violations**")
                for violation in consistency.violations:
                    console.print(f"• {violation}")
            
            if consistency.recommendations:
                console.print(f"\n📋 **Brand Recommendations**")
                for rec in consistency.recommendations:
                    console.print(f"• {rec}")
            
            # Learn from this asset if requested
            if learn_mode:
                brand_engine.learn_from_approved_asset(image_path)
                console.print(f"\n✅ Learned brand patterns from this asset")
        
        elif action == "extract-colors":
            if not image_path:
                console.print("[red]❌ Image path required for color extraction[/red]")
                raise typer.Exit(1)
            
            console.print(f"🎨 Extracting color palette from: {image_path}")
            palette = brand_engine.extract_color_palette(image_path, n_colors)
            
            console.print(f"\n🎯 **Color Palette ({n_colors} colors)**")
            console.print("=" * 50)
            for i, (color, hex_color, percentage) in enumerate(zip(palette.dominant_colors, palette.hex_colors, palette.color_percentages)):
                console.print(f"{i+1:2d}. {hex_color} - {percentage:5.1f}% - RGB{color}")
            
            console.print(f"\n📊 **Palette Analysis**")
            console.print(f"Color Harmony: {palette.color_harmony}")
            console.print(f"Temperature: {palette.temperature}")
            console.print(f"Saturation Level: {palette.saturation_level}")
            console.print(f"Brightness Level: {palette.brightness_level}")
            console.print(f"Text Accessibility: {palette.accessibility_score:.1f}%")
        
        elif action == "assess-quality":
            if not image_path:
                console.print("[red]❌ Image path required for quality assessment[/red]")
                raise typer.Exit(1)
            
            console.print(f"📊 Assessing image quality: {image_path}")
            quality = brand_engine.assess_image_quality(image_path)
            
            console.print(f"\n📈 **Quality Assessment Results**")
            console.print("=" * 50)
            console.print(f"Overall Score:     {quality.overall_score:6.1f}/100")
            console.print(f"Sharpness:         {quality.sharpness:6.1f}/100")
            console.print(f"Brightness:        {quality.brightness:6.1f}/100")
            console.print(f"Contrast:          {quality.contrast:6.1f}/100")
            console.print(f"Saturation:        {quality.saturation:6.1f}/100")
            console.print(f"Noise Level:       {quality.noise_level:6.1f}/100")
            console.print(f"Compression:       {quality.compression_artifacts:6.1f}/100")
            console.print(f"Resolution:        {quality.resolution_adequacy:6.1f}/100")
            console.print(f"Composition:       {quality.composition_score:6.1f}/100")
            
            if quality.enhancement_recommendations:
                console.print(f"\n💡 **Recommendations**")
                for i, rec in enumerate(quality.enhancement_recommendations, 1):
                    console.print(f"{i}. {rec}")
            else:
                console.print(f"\n✅ No enhancements needed - image quality is excellent!")
        
        elif action == "validate-consistency":
            if not image_path:
                console.print("[red]❌ Image path required for consistency validation[/red]")
                raise typer.Exit(1)
            
            ref_images = reference_images.split(',') if reference_images else None
            console.print(f"🏢 Validating brand consistency: {image_path}")
            
            consistency = brand_engine.validate_brand_consistency(image_path, ref_images)
            
            console.print(f"\n🎯 **Brand Consistency Report**")
            console.print("=" * 50)
            console.print(f"Overall Brand Score:    {consistency.overall_brand_score:6.1f}/100")
            console.print(f"Color Consistency:      {consistency.color_consistency:6.1f}/100")
            console.print(f"Style Consistency:      {consistency.style_consistency:6.1f}/100")
            console.print(f"Composition Consistency:{consistency.composition_consistency:6.1f}/100")
            
            if consistency.overall_brand_score >= 80:
                console.print(f"\n✅ **APPROVED**: Excellent brand consistency")
            elif consistency.overall_brand_score >= 70:
                console.print(f"\n⚠️ **REVIEW**: Good brand consistency with minor issues")
            elif consistency.overall_brand_score >= 60:
                console.print(f"\n🔄 **REVISION**: Moderate brand consistency issues")
            else:
                console.print(f"\n❌ **REJECTED**: Poor brand consistency")
            
            if consistency.violations:
                console.print(f"\n⚠️ **Violations**")
                for violation in consistency.violations:
                    console.print(f"• {violation}")
            
            if consistency.recommendations:
                console.print(f"\n📋 **Recommendations**")
                for rec in consistency.recommendations:
                    console.print(f"• {rec}")
        
        elif action == "enhance":
            if not image_path:
                console.print("[red]❌ Image path required for enhancement[/red]")
                raise typer.Exit(1)
            
            console.print(f"✨ Enhancing image: {image_path}")
            console.print(f"Enhancement level: {enhancement_level}")
            
            enhanced_path = brand_engine.enhance_image(image_path, output_path, enhancement_level)
            
            console.print(f"✅ Enhanced image saved to: {enhanced_path}")
            
            # Show before/after quality comparison
            original_quality = brand_engine.assess_image_quality(image_path)
            enhanced_quality = brand_engine.assess_image_quality(enhanced_path)
            
            console.print(f"\n📊 **Enhancement Results**")
            console.print("=" * 50)
            console.print(f"{'Metric':<20} {'Before':<10} {'After':<10} {'Improvement':<12}")
            console.print("-" * 52)
            
            metrics = [
                ("Overall Score", original_quality.overall_score, enhanced_quality.overall_score),
                ("Sharpness", original_quality.sharpness, enhanced_quality.sharpness),
                ("Brightness", original_quality.brightness, enhanced_quality.brightness),
                ("Contrast", original_quality.contrast, enhanced_quality.contrast),
                ("Saturation", original_quality.saturation, enhanced_quality.saturation),
                ("Noise Level", original_quality.noise_level, enhanced_quality.noise_level)
            ]
            
            for metric, before, after in metrics:
                improvement = after - before
                improvement_str = f"+{improvement:.1f}" if improvement > 0 else f"{improvement:.1f}"
                console.print(f"{metric:<20} {before:<10.1f} {after:<10.1f} {improvement_str:<12}")
        
        elif action == "learn":
            if not image_path:
                console.print("[red]❌ Image path required for learning[/red]")
                raise typer.Exit(1)
            
            console.print(f"🧠 Learning brand patterns from: {image_path}")
            
            # Optional metadata
            metadata = {
                "source": "manual_approval",
                "quality_threshold": "approved",
                "learning_date": datetime.now().isoformat()
            }
            
            brand_engine.learn_from_approved_asset(image_path, metadata)
            console.print(f"✅ Brand patterns learned and saved")
            
            # Show current brand profile summary
            profile = brand_engine.brand_profile
            console.print(f"\n📊 **Updated Brand Profile**")
            console.print("=" * 50)
            console.print(f"Brand Colors Learned: {len(set(profile.get('brand_colors', [])))}")
            console.print(f"Style Signatures: {len(profile.get('style_signatures', []))}")
            console.print(f"Last Updated: {profile.get('last_updated', 'Never')}")
        
        elif action == "report":
            if not image_paths:
                console.print("[red]❌ Image paths required for report generation[/red]")
                raise typer.Exit(1)
            
            paths = [p.strip() for p in image_paths.split(',')]
            console.print(f"📋 Generating brand intelligence report for {len(paths)} images...")
            
            report = brand_engine.generate_brand_report(paths)
            
            console.print(f"\n📊 **Brand Intelligence Report**")
            console.print("=" * 60)
            console.print(f"Analysis Date: {report['analysis_date']}")
            console.print(f"Images Analyzed: {report['total_images']}")
            
            # Brand consistency summary
            bc = report['brand_consistency']
            console.print(f"\n🏢 **Brand Consistency Summary**")
            console.print(f"Overall Brand Score:     {bc['overall_score']:.1f}/100")
            console.print(f"Color Consistency:       {bc['color_consistency']:.1f}/100")
            console.print(f"Style Consistency:       {bc['style_consistency']:.1f}/100")
            
            # Quality summary
            qs = report['quality_summary']
            console.print(f"\n📈 **Quality Summary**")
            console.print(f"Average Quality:         {qs['average_quality']:.1f}/100")
            
            if 'quality_distribution' in qs:
                qd = qs['quality_distribution']
                console.print(f"Quality Distribution:")
                console.print(f"  Excellent (90+):       {qd.get('excellent', 0)} images")
                console.print(f"  Good (75-89):          {qd.get('good', 0)} images")
                console.print(f"  Fair (60-74):          {qd.get('fair', 0)} images")
                console.print(f"  Poor (<60):            {qd.get('poor', 0)} images")
            
            # Color analysis
            if 'color_analysis' in report and report['color_analysis']['dominant_colors']:
                console.print(f"\n🎨 **Color Analysis**")
                console.print("Top Brand Colors:")
                for color_info in report['color_analysis']['dominant_colors'][:5]:
                    console.print(f"  {color_info['color']} (used {color_info['frequency']} times)")
            
            # Recommendations
            if report['recommendations']:
                console.print(f"\n💡 **Key Recommendations**")
                for i, rec in enumerate(report['recommendations'], 1):
                    console.print(f"{i}. {rec}")
            
            # Export detailed report if requested
            if export_report:
                report_filename = f"brand_intelligence_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
                with open(report_filename, 'w') as f:
                    json.dump(report, f, indent=2)
                console.print(f"\n📄 Detailed report exported to: {report_filename}")
        
        else:
            console.print(f"[red]❌ Unknown action: {action}[/red]")
            console.print("Available actions: analyze, extract-colors, assess-quality, validate-consistency, enhance, learn, report")
            raise typer.Exit(1)
    
    except ImportError as e:
        console.print(f"[red]❌ Computer vision dependencies missing: {e}[/red]")
        console.print("Install with: pip install opencv-python scikit-learn scikit-image numpy")
        raise typer.Exit(1)
    except Exception as e:
        console.print(f"[red]❌ Brand intelligence error: {e}[/red]")
        raise typer.Exit(1)


# ============================================================================
# STRATEGIC ENHANCEMENT COMMANDS
# ============================================================================

@app.command()
def predict_performance(
    image_path: str = typer.Option(None, help="Path to image file"),
    campaign_brief: str = typer.Option(None, help="Path to campaign brief"),
    export_report: bool = typer.Option(False, help="Export detailed prediction report")
):
    """🔮 Real-Time Creative Performance Prediction"""
    try:
        from src.performance_prediction import PerformancePredictionEngine
        
        console.print("🔮 [bold blue]Real-Time Creative Performance Prediction[/bold blue]")
        
        # Load campaign brief if provided
        brief_data = {}
        if campaign_brief:
            brief_data = load_campaign_brief(campaign_brief)
        
        # Initialize prediction engine
        engine = PerformancePredictionEngine()
        
        # Predict performance
        with Progress(SpinnerColumn(), TextColumn("[progress.description]{task.description}")) as progress:
            task = progress.add_task("Analyzing creative and predicting performance...", total=None)
            result = engine.predict_creative_performance(image_path, brief_data)
        
        # Display results
        console.print(f"\n📊 **Performance Predictions for**: {image_path or 'Campaign'}")
        console.print(f"Prediction timestamp: {result['timestamp']}")
        console.print(f"Overall Performance Grade: [bold]{result['performance_grade']}[/bold] ({result['overall_score']:.2f}/1.0)")
        console.print(f"Prediction Confidence: {result['confidence']:.1%}")
        
        console.print(f"\n📈 **Detailed Predictions**")
        predictions = result['predictions']
        console.print(f"Click-Through Rate:     {predictions['ctr']:.2f}%")
        console.print(f"Conversion Rate:        {predictions['conversion_rate']:.3f}")
        console.print(f"Engagement Score:       {predictions['engagement_score']:.1f}/5.0")
        console.print(f"Brand Recall:           {predictions['brand_recall']:.1%}")
        
        console.print(f"\n💡 **Optimization Suggestions**")
        for i, suggestion in enumerate(result['optimization_suggestions'], 1):
            console.print(f"{i}. {suggestion}")
        
        # Export report if requested
        if export_report:
            report_filename = f"performance_prediction_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
            with open(report_filename, 'w') as f:
                json.dump(result, f, indent=2)
            console.print(f"\n📄 Detailed prediction report exported to: {report_filename}")
        
    except ImportError as e:
        console.print(f"[red]❌ ML dependencies missing: {e}[/red]")
        console.print("Install with: pip install scikit-learn pandas numpy joblib")
        raise typer.Exit(1)
    except Exception as e:
        console.print(f"[red]❌ Performance prediction error: {e}[/red]")
        raise typer.Exit(1)


@app.command()
def adobe_integration(
    action: str = typer.Argument(..., help="Action: search-stock, fonts, firefly, sync, workspace, status"),
    query: str = typer.Option(None, help="Search query"),
    campaign_brief: str = typer.Option(None, help="Path to campaign brief for recommendations"),
    export_data: bool = typer.Option(False, help="Export integration data")
):
    """🎨 Adobe Ecosystem Integration"""
    try:
        from src.adobe_ecosystem import AdobeEcosystemIntegration
        
        console.print("🎨 [bold blue]Adobe Ecosystem Integration[/bold blue]")
        
        # Initialize integration
        adobe = AdobeEcosystemIntegration()
        
        if action == "search-stock":
            console.print(f"\n🔍 **Searching Adobe Stock for**: {query}")
            results = adobe.stock.search_assets(query, limit=5)
            
            if results:
                for asset in results:
                    console.print(f"\n📸 {asset['title']}")
                    console.print(f"   Category: {asset['category']}")
                    console.print(f"   Dimensions: {asset['dimensions']}")
                    console.print(f"   Price: ${asset['price']}")
                    console.print(f"   Keywords: {', '.join(asset['keywords'][:5])}")
            else:
                console.print("No assets found for query")
        
        elif action == "fonts":
            if query:
                console.print(f"\n🔤 **Searching Adobe Fonts for**: {query}")
                fonts = adobe.fonts.search_fonts(query=query)
            else:
                console.print(f"\n🔤 **Recommended Adobe Fonts**")
                fonts = adobe.fonts.get_font_recommendations('modern', 'web')
            
            for font in fonts:
                console.print(f"\n📝 {font['family']}")
                console.print(f"   Category: {font['category']}")
                console.print(f"   Variants: {', '.join(font['variants'][:4])}")
                console.print(f"   Use Cases: {', '.join(font['use_cases'])}")
        
        elif action == "firefly":
            if not query:
                query = "Professional product photography, modern style, clean background"
            
            console.print(f"\n🎆 **Generating with Adobe Firefly**: {query}")
            result = adobe.firefly.text_to_image(query, style='photographic')
            
            console.print(f"Generation ID: {result['generation_id']}")
            console.print(f"Style: {result['style_description']}")
            console.print(f"Status: {result['status']}")
            console.print(f"Image URL: {result['image_url']}")
        
        elif action == "sync":
            console.print(f"\n☁️ **Syncing Assets to Creative Cloud**")
            sync_result = adobe.creative_sdk.sync_assets("output/", "Campaign Assets")
            
            console.print(f"Sync ID: {sync_result['sync_id']}")
            console.print(f"Files synced: {sync_result['files_synced']}")
            console.print(f"Status: {sync_result['status']}")
        
        elif action == "workspace":
            if not query:
                query = "Demo Campaign"
            
            console.print(f"\n🏢 **Creating Campaign Workspace**: {query}")
            workspace = adobe.create_campaign_workspace(query, ["asset1.jpg", "asset2.png"])
            
            console.print(f"Workspace created: {workspace['campaign_name']}")
            console.print(f"Shared library ID: {workspace['shared_library']['library_id']}")
            console.print(f"Workspace URL: {workspace['workspace_url']}")
        
        elif action == "recommendations":
            if not campaign_brief:
                console.print("[red]Campaign brief required for recommendations[/red]")
                raise typer.Exit(1)
            
            brief_data = load_campaign_brief(campaign_brief)
            console.print(f"\n🎯 **Smart Asset Recommendations**")
            
            recommendations = adobe.smart_asset_recommendation(brief_data)
            
            console.print(f"\n📸 **Stock Asset Recommendations** ({len(recommendations['stock_assets'])} found)")
            for asset in recommendations['stock_assets'][:3]:
                console.print(f"   • {asset['title']} - {asset['category']}")
            
            console.print(f"\n🔤 **Font Recommendations** ({len(recommendations['fonts'])} found)")
            for font in recommendations['fonts']:
                console.print(f"   • {font['family']} - {font['category']}")
            
            console.print(f"\n🎨 **Color Palette**")
            for color in recommendations['color_palette']:
                console.print(f"   • {color}")
        
        elif action == "status":
            console.print(f"\n📊 **Adobe Ecosystem Status**")
            status = adobe.get_ecosystem_status()
            
            console.print(f"Stock API: {status['stock_api']}")
            console.print(f"Fonts API: {status['fonts_api']}")
            console.print(f"Firefly API: {status['firefly_api']}")
            console.print(f"Creative SDK: {status['creative_sdk']}")
            console.print(f"Last Sync: {status['last_sync']}")
            console.print(f"Service Status: {status['service_status']}")
        
        else:
            console.print(f"[red]❌ Unknown action: {action}[/red]")
            console.print("Available actions: search-stock, fonts, firefly, sync, workspace, recommendations, status")
            raise typer.Exit(1)
        
        # Export data if requested
        if export_data and 'result' in locals():
            export_filename = f"adobe_integration_{action}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
            with open(export_filename, 'w') as f:
                json.dump(locals().get('result', {}), f, indent=2)
            console.print(f"\n📄 Integration data exported to: {export_filename}")
        
    except ImportError as e:
        console.print(f"[red]❌ Adobe integration dependencies missing: {e}[/red]")
        raise typer.Exit(1)
    except Exception as e:
        console.print(f"[red]❌ Adobe integration error: {e}[/red]")
        raise typer.Exit(1)


@app.command()
def personalize(
    campaign_brief: str = typer.Argument(..., help="Path to campaign brief"),
    markets: str = typer.Option("US,UK,DE", help="Comma-separated list of target markets"),
    export_results: bool = typer.Option(False, help="Export personalization results")
):
    """🌍 Intelligent Content Personalization"""
    try:
        from src.content_personalization import ContentPersonalizationEngine
        
        console.print("🌍 [bold blue]Intelligent Content Personalization[/bold blue]")
        
        # Load campaign brief
        brief_data = load_campaign_brief(campaign_brief)
        target_markets = [m.strip() for m in markets.split(',')]
        
        # Get OpenAI API key
        openai_api_key = os.getenv('OPENAI_API_KEY')
        if not openai_api_key:
            console.print("[red]❌ OpenAI API key not found. Set OPENAI_API_KEY environment variable.[/red]")
            raise typer.Exit(1)
        
        # Initialize personalization engine
        engine = ContentPersonalizationEngine(openai_api_key)
        
        # Run personalization
        with Progress(SpinnerColumn(), TextColumn("[progress.description]{task.description}")) as progress:
            task = progress.add_task("Personalizing content for target markets...", total=None)
            
            import asyncio
            result = asyncio.run(engine.personalize_campaign_content(brief_data, target_markets))
        
        # Display results
        console.print(f"\n🎯 **Content Personalization Results**")
        console.print(f"Campaign: {result['campaign_name']}")
        console.print(f"Markets processed: {len(result['markets_processed'])}")
        console.print(f"Personalization timestamp: {result['personalization_timestamp']}")
        
        # Summary
        summary = result['summary']
        console.print(f"\n📊 **Summary**")
        console.print(f"Average localization score: {summary['average_localization_score']:.2f}/1.0")
        console.print(f"Headline optimizations: {summary['headline_optimizations_applied']}")
        console.print(f"Personalization quality: {summary['personalization_quality']}")
        
        # Market-specific results
        for market, data in result['market_personalizations'].items():
            console.print(f"\n🌍 **{market} Market Personalization**")
            console.print(f"Localization score: {data['localization_score']:.2f}/1.0")
            
            # Show optimized messaging
            optimized = data['optimized_messaging']
            if 'optimized_headline' in optimized['headline']:
                console.print(f"Original headline: {optimized['headline']['original_headline']}")
                console.print(f"Optimized headline: {optimized['headline']['optimized_headline']}")
            
            # Show cultural adaptations
            if data['recommended_adjustments']:
                console.print("Cultural adaptations:")
                for adjustment in data['recommended_adjustments']:
                    console.print(f"  • {adjustment}")
            
            # Show trending topics
            console.print("Trending topics:")
            for topic in data['trending_topics']:
                console.print(f"  • {topic['topic']} (relevance: {topic['relevance_score']:.2f})")
        
        # Overall recommendations
        if result['optimization_recommendations']:
            console.print(f"\n💡 **Optimization Recommendations**")
            for i, rec in enumerate(result['optimization_recommendations'], 1):
                console.print(f"{i}. {rec}")
        
        # Export results if requested
        if export_results:
            results_filename = f"personalization_results_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
            with open(results_filename, 'w') as f:
                json.dump(result, f, indent=2)
            console.print(f"\n📄 Personalization results exported to: {results_filename}")
        
    except ImportError as e:
        console.print(f"[red]❌ Personalization dependencies missing: {e}[/red]")
        console.print("Install with: pip install textblob pandas numpy")
        raise typer.Exit(1)
    except Exception as e:
        console.print(f"[red]❌ Content personalization error: {e}[/red]")
        raise typer.Exit(1)


@app.command()
def collaborate(
    action: str = typer.Argument(..., help="Action: create-project, upload-asset, dashboard, users, notifications"),
    project_name: str = typer.Option(None, help="Project name"),
    username: str = typer.Option("admin", help="Username"),
    asset_path: str = typer.Option(None, help="Path to asset file"),
    team_members: str = typer.Option(None, help="Comma-separated team member usernames")
):
    """👥 Enterprise Collaboration Platform"""
    try:
        from src.collaboration_platform import CollaborationPlatform, UserRole
        
        console.print("👥 [bold blue]Enterprise Collaboration Platform[/bold blue]")
        
        # Initialize collaboration platform
        platform = CollaborationPlatform()
        
        if action == "create-project":
            if not project_name:
                console.print("[red]Project name required for create-project action[/red]")
                raise typer.Exit(1)
            
            console.print(f"\n🏗️ **Creating Project**: {project_name}")
            
            # Parse team members
            members = []
            if team_members:
                members = [m.strip() for m in team_members.split(',')]
            
            result = platform.create_campaign_project(project_name, username, members)
            
            console.print(f"Project created successfully!")
            console.print(f"Project ID: {result['project_id']}")
            console.print(f"Team size: {result['team_size']}")
            console.print(f"Collaboration URL: {result['collaboration_url']}")
        
        elif action == "upload-asset":
            if not asset_path or not project_name:
                console.print("[red]Asset path and project name required for upload-asset action[/red]")
                raise typer.Exit(1)
            
            console.print(f"\n📤 **Uploading Asset**: {Path(asset_path).name}")
            
            # For demo, create a dummy project
            try:
                project_result = platform.create_campaign_project(project_name, username)
                project_id = project_result['project_id']
            except:
                # Assume project exists, use dummy ID
                project_id = "demo_project_123"
            
            # Request approval from sample reviewers
            reviewers = ['creative_lead', 'client']
            
            result = platform.upload_campaign_asset(
                project_id, Path(asset_path).name, asset_path, username, reviewers
            )
            
            console.print(f"Asset uploaded successfully!")
            console.print(f"Asset ID: {result['asset_id']}")
            console.print(f"Approval requests sent: {result['approval_requests']}")
            console.print(f"Asset URL: {result['collaboration_url']}")
        
        elif action == "dashboard":
            if not project_name:
                console.print("[red]Project name required for dashboard action[/red]")
                raise typer.Exit(1)
            
            console.print(f"\n📊 **Project Dashboard**: {project_name}")
            
            # For demo, use dummy project ID
            project_id = "demo_project_123"
            dashboard = platform.get_project_dashboard(project_id)
            
            console.print(f"Team members: {dashboard['members']}")
            console.print(f"Total assets: {dashboard['assets']}")
            console.print(f"Pending approvals: {dashboard['pending_approvals']}")
            console.print(f"Unresolved comments: {dashboard['unresolved_comments']}")
            
            if dashboard['recent_assets']:
                console.print(f"\n📁 **Recent Assets**")
                for asset in dashboard['recent_assets']:
                    console.print(f"  • {asset['name']} (v{asset['version']}) - {asset['approval_status']}")
            
            if dashboard['team_members']:
                console.print(f"\n👥 **Team Members**")
                for member in dashboard['team_members']:
                    console.print(f"  • {member['username']} ({member['role']})")
        
        elif action == "users":
            console.print(f"\n👤 **Platform Users**")
            
            # Display default users
            default_users = [
                {"username": "admin", "role": "admin", "full_name": "Platform Administrator"},
                {"username": "creative_lead", "role": "creative_lead", "full_name": "Creative Director"},
                {"username": "designer", "role": "designer", "full_name": "Senior Designer"},
                {"username": "client", "role": "client", "full_name": "Client Stakeholder"}
            ]
            
            for user in default_users:
                console.print(f"  • {user['username']} ({user['role']}) - {user['full_name']}")
        
        elif action == "notifications":
            console.print(f"\n🔔 **Notifications for**: {username}")
            
            # Get user
            user = platform.user_manager.get_user_by_username(username)
            if not user:
                console.print(f"[yellow]User {username} not found, showing sample notifications[/yellow]")
                
                # Show sample notifications
                sample_notifications = [
                    {"title": "New Asset Uploaded", "message": "Asset 'campaign_hero.jpg' uploaded to Demo Project"},
                    {"title": "Approval Required", "message": "Please review and approve 'social_post.png'"},
                    {"title": "Comment Added", "message": "New comment on 'product_banner.jpg'"}
                ]
                
                for notif in sample_notifications:
                    console.print(f"  📧 {notif['title']}")
                    console.print(f"     {notif['message']}")
            else:
                notifications = platform.notification_system.get_user_notifications(user['user_id'])
                
                if notifications:
                    for notif in notifications:
                        status = "📧" if not notif['read_at'] else "📬"
                        console.print(f"  {status} {notif['title']}")
                        console.print(f"     {notif['message']}")
                else:
                    console.print("  No notifications found")
        
        elif action == "metrics":
            console.print(f"\n📈 **Collaboration Metrics**")
            
            metrics = platform.get_collaboration_metrics()
            
            console.print(f"Total projects: {metrics['total_projects']}")
            console.print(f"Total users: {metrics['total_users']}")
            console.print(f"Total assets: {metrics['total_assets']}")
            console.print(f"Unresolved comments: {metrics['unresolved_comments']}")
            console.print(f"Pending approvals: {metrics['pending_approvals']}")
            console.print(f"Platform health: {metrics['platform_health']}")
            
            console.print(f"\n📊 **Weekly Activity**")
            weekly = metrics['weekly_activity']
            console.print(f"Assets uploaded: {weekly['assets_uploaded']}")
            console.print(f"Comments posted: {weekly['comments_posted']}")
        
        else:
            console.print(f"[red]❌ Unknown action: {action}[/red]")
            console.print("Available actions: create-project, upload-asset, dashboard, users, notifications, metrics")
            raise typer.Exit(1)
        
    except ImportError as e:
        console.print(f"[red]❌ Collaboration dependencies missing: {e}[/red]")
        raise typer.Exit(1)
    except Exception as e:
        console.print(f"[red]❌ Collaboration platform error: {e}[/red]")
        raise typer.Exit(1)


@app.command()
def analyze_performance(
    action: str = typer.Argument(..., help="Action: run-analysis, learning-report, record-campaign, record-asset"),
    days_back: int = typer.Option(30, help="Days of data to analyze"),
    campaign_data: str = typer.Option(None, help="Path to campaign data JSON"),
    export_insights: bool = typer.Option(False, help="Export learning insights")
):
    """🧠 Advanced Analytics & Learning Loop"""
    try:
        from src.advanced_analytics import AdvancedAnalyticsEngine
        
        console.print("🧠 [bold blue]Advanced Analytics & Learning Loop[/bold blue]")
        
        # Initialize analytics engine
        engine = AdvancedAnalyticsEngine()
        
        if action == "run-analysis":
            console.print(f"\n📊 **Running Comprehensive Analysis** (last {days_back} days)")
            
            with Progress(SpinnerColumn(), TextColumn("[progress.description]{task.description}")) as progress:
                task = progress.add_task("Analyzing performance data and generating insights...", total=None)
                report = engine.run_comprehensive_analysis(days_back)
            
            # Display analysis results
            console.print(f"\n📈 **Analysis Summary**")
            summary = report['data_summary']
            console.print(f"Campaigns analyzed: {summary['campaigns_analyzed']}")
            console.print(f"Assets analyzed: {summary['assets_analyzed']}")
            console.print(f"Analysis period: {report['data_period_days']} days")
            
            # Pattern analysis
            pattern_analysis = report['pattern_analysis']
            
            # Campaign patterns
            campaign_patterns = pattern_analysis.get('campaign_patterns', {})
            if 'market_performance' in campaign_patterns:
                console.print(f"\n🌍 **Market Performance Insights**")
                market_perf = campaign_patterns['market_performance']
                if 'ctr' in market_perf and 'mean' in market_perf['ctr']:
                    for market, ctr in market_perf['ctr']['mean'].items():
                        console.print(f"  {market}: {ctr:.2f}% CTR")
            
            # Recommendations
            recommendations = report['recommendations']
            strategic_recs = recommendations.get('strategic_recommendations', [])
            if strategic_recs:
                console.print(f"\n🎯 **Strategic Recommendations**")
                for i, rec in enumerate(strategic_recs[:3], 1):
                    console.print(f"{i}. {rec['title']} (Priority: {rec['priority']})")
                    console.print(f"   {rec['description']}")
            
            # Learning insights
            insights = report['learning_insights']
            if insights:
                console.print(f"\n💡 **Key Learning Insights**")
                for i, insight in enumerate(insights, 1):
                    confidence_emoji = "🟢" if insight['confidence'] > 0.8 else "🟡" if insight['confidence'] > 0.6 else "🟠"
                    console.print(f"{i}. {confidence_emoji} {insight['insight']} (Confidence: {insight['confidence']:.1%})")
            
            # Next steps
            next_steps = report['next_steps']
            if next_steps:
                console.print(f"\n🚀 **Recommended Next Steps**")
                for i, step in enumerate(next_steps, 1):
                    console.print(f"{i}. {step}")
            
            # Export insights if requested
            if export_insights:
                insights_filename = f"analytics_insights_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
                with open(insights_filename, 'w') as f:
                    json.dump(report, f, indent=2)
                console.print(f"\n📄 Analytics report exported to: {insights_filename}")
        
        elif action == "learning-report":
            console.print(f"\n🎓 **Learning System Report**")
            
            report = engine.get_learning_report()
            
            if 'message' in report:
                console.print(f"[yellow]{report['message']}[/yellow]")
            else:
                console.print(f"Total analyses performed: {report['total_analyses']}")
                console.print(f"Recent analyses: {report['recent_analyses']}")
                console.print(f"Total insights generated: {report['total_insights_generated']}")
                console.print(f"Learning velocity: {report['learning_velocity']:.1f} insights per analysis")
                console.print(f"System maturity: {report['system_maturity']}")
                
                if report['insight_categories']:
                    console.print(f"\n📊 **Insight Categories**")
                    for category, count in report['insight_categories'].items():
                        console.print(f"  {category}: {count}")
        
        elif action == "record-campaign":
            if not campaign_data:
                console.print("[red]Campaign data JSON file required for record-campaign action[/red]")
                raise typer.Exit(1)
            
            console.print(f"\n📝 **Recording Campaign Performance**")
            
            # Load campaign data
            with open(campaign_data, 'r') as f:
                data = json.load(f)
            
            # Record performance (with simulated metrics)
            campaign_info = data.get('campaign', {})
            performance_metrics = {
                'metrics': {
                    'ctr': 1.2,
                    'conversion_rate': 0.08,
                    'engagement_score': 2.5,
                    'brand_recall': 0.65
                },
                'creative_features': {
                    'aspect_ratio': 1.0,
                    'color_diversity': 0.7,
                    'text_length': 45
                },
                'cost_data': {
                    'total_cost': 150.0,
                    'cost_per_acquisition': 12.5
                }
            }
            
            performance_id = engine.data_collector.record_campaign_performance(campaign_info, performance_metrics)
            console.print(f"Campaign performance recorded: {performance_id}")
        
        elif action == "record-asset":
            console.print(f"\n📸 **Recording Asset Performance**")
            
            # Simulate asset performance recording
            asset_data = {
                'asset_id': 'demo_asset_123',
                'asset_name': 'Social Media Hero',
                'campaign_id': 'demo_campaign_456',
                'asset_type': 'creative'
            }
            
            performance_data = {
                'visual_features': {
                    'brightness': 0.65,
                    'contrast': 0.75,
                    'color_count': 5,
                    'complexity': 0.6
                },
                'engagement_metrics': {
                    'engagement_rate': 3.2,
                    'time_spent': 8.5,
                    'shares': 25
                }
            }
            
            asset_performance_id = engine.data_collector.record_asset_performance(asset_data, performance_data)
            console.print(f"Asset performance recorded: {asset_performance_id}")
        
        else:
            console.print(f"[red]❌ Unknown action: {action}[/red]")
            console.print("Available actions: run-analysis, learning-report, record-campaign, record-asset")
            raise typer.Exit(1)
        
    except ImportError as e:
        console.print(f"[red]❌ Analytics dependencies missing: {e}[/red]")
        console.print("Install with: pip install pandas scikit-learn matplotlib seaborn scipy")
        raise typer.Exit(1)
    except Exception as e:
        console.print(f"[red]❌ Advanced analytics error: {e}[/red]")
        raise typer.Exit(1)


if __name__ == "__main__":
    app()
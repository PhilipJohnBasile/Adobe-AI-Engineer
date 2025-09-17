"""
Creative Automation Platform - Professional Web Interface
Production-ready creative automation pipeline with enterprise monitoring and AI-driven insights
Streamlined interface for campaign creation, asset generation, and performance analytics
"""
import os
import json
import yaml
import shutil
import subprocess
import asyncio
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Any, Optional
import logging
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Web framework
from flask import Flask, render_template, request, redirect, url_for, flash, jsonify, send_file
from werkzeug.utils import secure_filename
import uuid

# Import our systems
import sys
sys.path.append('src')

app = Flask(__name__)
app.secret_key = 'complete_system_key'
app.config['MAX_CONTENT_LENGTH'] = 50 * 1024 * 1024  # 50MB max

# Configuration
UPLOAD_FOLDER = 'uploads'
CAMPAIGN_BRIEFS_FOLDER = 'campaign_briefs'
ASSETS_FOLDER = 'assets'
OUTPUT_FOLDER = 'output'
ALLOWED_EXTENSIONS = {'yaml', 'yml', 'json', 'png', 'jpg', 'jpeg', 'gif', 'pdf'}

# Create folders
for folder in [UPLOAD_FOLDER, CAMPAIGN_BRIEFS_FOLDER, ASSETS_FOLDER, OUTPUT_FOLDER]:
    Path(folder).mkdir(exist_ok=True)

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def get_system_status():
    """Get complete system status"""
    try:
        # Check main.py availability
        main_py_available = Path('main.py').exists()
        
        # Check AI Monitor systems
        ai_monitor_systems = {
            'production': Path('src/production_ai_monitor.py').exists(),
            'enterprise': Path('src/enterprise_ai_monitor.py').exists()
        }
        
        # Get campaigns with details - match brief files with output folders
        brief_files = []
        for pattern in ['*.yaml', '*.yml', '*.json']:
            brief_files.extend(Path(CAMPAIGN_BRIEFS_FOLDER).glob(pattern))
        
        output_dirs = {d.name: d for d in Path(OUTPUT_FOLDER).iterdir() if d.is_dir()}
        
        recent_campaigns = []
        for brief_file in brief_files:
            try:
                with open(brief_file, 'r') as f:
                    if brief_file.suffix.lower() in ['.yaml', '.yml']:
                        data = yaml.safe_load(f)
                    else:
                        data = json.load(f)
                
                # Handle both old and new campaign brief formats
                if 'campaign_brief' in data:
                    # New format with campaign_brief wrapper
                    brief_data = data['campaign_brief']
                    campaign_name = brief_data.get('campaign_name', brief_file.stem)
                    campaign_message = brief_data.get('campaign_message', '')
                    products = [p.get('name', str(p)) if isinstance(p, dict) else str(p) for p in brief_data.get('products', [])]
                    target_regions = brief_data.get('target_regions', [brief_data.get('target_region', 'Global')])
                else:
                    # Old format without wrapper
                    campaign_name = data.get('campaign_name', brief_file.stem)
                    campaign_message = data.get('campaign_message', '')
                    products = [p.get('name', str(p)) if isinstance(p, dict) else str(p) for p in data.get('products', [])]
                    target_regions = data.get('target_regions', [data.get('target_region', 'Global')])
                
                # Check for matching output folders (including localized versions)
                has_outputs = False
                possible_output_names = [brief_file.stem]
                
                # Add localized versions if multi-region
                if len(target_regions) > 1:
                    for region in target_regions:
                        possible_output_names.append(f"{brief_file.stem}_{region.lower()}")
                
                for output_name in possible_output_names:
                    if output_name in output_dirs:
                        has_outputs = True
                        break
                
                recent_campaigns.append({
                    'id': brief_file.stem,
                    'name': campaign_name,
                    'products': products,
                    'target_regions': target_regions,
                    'campaign_message': campaign_message,
                    'has_outputs': has_outputs,
                    'created': datetime.fromtimestamp(brief_file.stat().st_mtime).strftime('%Y-%m-%d %H:%M'),
                    'file': brief_file.name
                })
            except Exception as e:
                logger.warning(f"Error reading {brief_file}: {e}")
        
        # Sort by creation time
        recent_campaigns.sort(key=lambda x: x['created'], reverse=True)
        
        # Get outputs
        output_dirs = [d for d in Path(OUTPUT_FOLDER).iterdir() if d.is_dir()]
        
        return {
            'system_ready': main_py_available,
            'ai_monitor_systems': ai_monitor_systems,
            'total_campaigns': len(recent_campaigns),
            'recent_campaigns': recent_campaigns[:10],  # Include recent campaigns
            'total_outputs': len(output_dirs),
            'cli_commands_available': 28,  # From main.py
            'last_updated': datetime.now().isoformat()
        }
    except Exception as e:
        logger.error(f"Error getting system status: {e}")
        return {'error': str(e)}

def get_latest_campaign():
    """Get the most recent campaign brief file"""
    briefs_dir = Path(CAMPAIGN_BRIEFS_FOLDER)
    if not briefs_dir.exists():
        return None
    
    # Get all YAML files sorted by modification time
    yaml_files = sorted(briefs_dir.glob('*.yaml'), key=lambda x: x.stat().st_mtime, reverse=True)
    if yaml_files:
        return str(yaml_files[0])
    return None

def get_latest_image():
    """Get the most recent generated image"""
    output_dir = Path(OUTPUT_FOLDER)
    if not output_dir.exists():
        return None
    
    # Find all image files
    image_files = []
    for ext in ['*.jpg', '*.png', '*.jpeg']:
        image_files.extend(output_dir.rglob(ext))
    
    if image_files:
        # Sort by modification time and return most recent
        image_files.sort(key=lambda x: x.stat().st_mtime, reverse=True)
        return str(image_files[0])
    return None

def run_cli_command(command: List[str], timeout: int = 300) -> Dict[str, Any]:
    """Run a CLI command safely"""
    try:
        # Ensure environment variables are passed to subprocess
        env = os.environ.copy()
        
        result = subprocess.run(
            command,
            capture_output=True,
            text=True,
            timeout=timeout,
            cwd=Path.cwd(),
            env=env
        )
        
        return {
            'success': result.returncode == 0,
            'stdout': result.stdout,
            'stderr': result.stderr,
            'return_code': result.returncode
        }
    except subprocess.TimeoutExpired:
        return {
            'success': False,
            'error': f'Command timed out after {timeout} seconds',
            'stdout': '',
            'stderr': ''
        }
    except Exception as e:
        return {
            'success': False,
            'error': str(e),
            'stdout': '',
            'stderr': ''
        }

@app.route('/')
def dashboard():
    """Main dashboard showing everything"""
    status = get_system_status()
    
    # Use campaigns from system status to avoid duplication
    campaigns = status.get('recent_campaigns', [])
    
    return render_template('complete_dashboard.html', 
                         status=status, 
                         campaigns=campaigns)

@app.route('/create-campaign')
def create_campaign():
    """Campaign creation page"""
    return render_template('complete_create.html')

@app.route('/upload-campaign', methods=['POST'])
def upload_campaign():
    """Handle campaign creation/upload"""
    try:
        # Handle file upload
        if 'file' in request.files and request.files['file'].filename:
            file = request.files['file']
            if file and allowed_file(file.filename):
                filename = secure_filename(file.filename)
                filepath = Path(CAMPAIGN_BRIEFS_FOLDER) / filename
                file.save(filepath)
                flash(f'Campaign brief uploaded: {filename}', 'success')
                return redirect(url_for('dashboard'))
        
        # Handle form data - create in CLI-compatible format
        campaign_id = request.form.get('campaign_id') or f'campaign_{uuid.uuid4().hex[:8]}'
        
        # Convert products to proper format
        products_list = []
        for product_name in [p.strip() for p in request.form.get('products', '').split(',') if p.strip()]:
            products_list.append({
                'name': product_name,
                'description': f'{product_name} product',
                'target_keywords': [product_name.lower()]
            })
        
        campaign_data = {
            'campaign_brief': {
                'campaign_id': campaign_id,
                'campaign_name': request.form.get('campaign_name', 'Untitled Campaign'),
                'products': products_list,
                'target_regions': request.form.getlist('target_regions') or [request.form.get('target_region', 'Global')],
                'target_audience': {
                    'age_range': '25-45',
                    'demographics': request.form.get('target_audience', 'General')
                },
                'campaign_message': request.form.get('campaign_message', ''),
                'brand_guidelines': {
                    'primary_colors': [c.strip() for c in request.form.get('colors', '').split(',') if c.strip()],
                    'logo_required': True
                },
                'output_requirements': {
                    'aspect_ratios': request.form.getlist('aspect_ratios') or ['1:1', '9:16', '16:9'],
                    'style': request.form.get('style', 'modern'),
                    'quality': request.form.get('quality', 'high'),
                    'formats': ['jpg', 'png']
                }
            },
            'created_at': datetime.now().isoformat()
        }
        
        # Save campaign brief
        filename = f"{campaign_id}.yaml"
        filepath = Path(CAMPAIGN_BRIEFS_FOLDER) / filename
        
        with open(filepath, 'w') as f:
            yaml.dump(campaign_data, f, default_flow_style=False)
        
        flash(f'Campaign created: {campaign_data["campaign_brief"]["campaign_name"]}', 'success')
        return redirect(url_for('dashboard'))
        
    except Exception as e:
        flash(f'Error creating campaign: {str(e)}', 'error')
        return redirect(url_for('create_campaign'))

@app.route('/run-pipeline/<campaign_id>')
def run_pipeline(campaign_id):
    """Run the complete pipeline using main.py"""
    try:
        # Find the campaign brief file
        brief_file = None
        for ext in ['yaml', 'yml', 'json']:
            candidate = Path(CAMPAIGN_BRIEFS_FOLDER) / f"{campaign_id}.{ext}"
            if candidate.exists():
                brief_file = candidate
                break
        
        if not brief_file:
            flash(f'Campaign brief not found: {campaign_id}', 'error')
            return redirect(url_for('dashboard'))
        
        flash(f'🚀 Starting complete pipeline for {campaign_id}...', 'info')
        
        # Run the main pipeline
        command = ['python3', 'main.py', 'generate', str(brief_file)]
        result = run_cli_command(command, timeout=600)  # 10 minutes
        
        if result['success']:
            flash(f'✅ Pipeline completed successfully for {campaign_id}!', 'success')
            if result['stdout']:
                # Show last part of output which has the summary
                output_lines = result["stdout"].split('\n')
                summary = '\n'.join(output_lines[-10:])
                flash(f'Output: {summary}', 'info')
        else:
            error_msg = result.get("error") or result.get("stderr", "Unknown error")
            # If stderr is empty but stdout has content, it might have the error
            if not error_msg and result.get('stdout'):
                output_lines = result["stdout"].split('\n')
                error_msg = '\n'.join(output_lines[-5:])
            flash(f'❌ Pipeline failed: {error_msg}', 'error')
        
    except Exception as e:
        flash(f'Error running pipeline: {str(e)}', 'error')
    
    return redirect(url_for('dashboard'))

@app.route('/run-ai-monitor/<campaign_id>')
def run_ai_monitor(campaign_id):
    """Run AI Monitor agent system"""
    try:
        flash(f'🤖 Starting AI Monitor for {campaign_id}...', 'info')
        
        # Run AI monitoring system
        command = ['python3', 'src/production_ai_monitor.py']
        result = run_cli_command(command, timeout=120)
        
        if result['success']:
            flash(f'✅ AI Monitor completed for {campaign_id}!', 'success')
        else:
            flash(f'❌ AI Monitor failed: {result.get("error", result.get("stderr", "Unknown error"))}', 'error')
        
    except Exception as e:
        flash(f'Error running AI Monitor: {str(e)}', 'error')
    
    return redirect(url_for('dashboard'))

@app.route('/run-enterprise/<campaign_id>')
def run_enterprise(campaign_id):
    """Run enterprise system"""
    try:
        flash(f'🏢 Starting enterprise system for {campaign_id}...', 'info')
        
        command = ['python3', 'src/enterprise_ai_monitor.py']
        result = run_cli_command(command, timeout=180)
        
        if result['success']:
            flash(f'✅ Enterprise system completed!', 'success')
        else:
            flash(f'❌ Enterprise system failed: {result.get("error", result.get("stderr", "Unknown error"))}', 'error')
            
    except Exception as e:
        flash(f'Error running enterprise system: {str(e)}', 'error')
    
    return redirect(url_for('dashboard'))

@app.route('/analytics')
def analytics():
    """Analytics dashboard"""
    try:
        # Run analytics generation
        command = ['python3', 'main.py', 'analytics']
        result = run_cli_command(command, timeout=60)
        
        analytics_data = {
            'command_output': result.get('stdout', ''),
            'success': result['success'],
            'timestamp': datetime.now().isoformat()
        }
        
        return render_template('analytics.html', analytics=analytics_data)
        
    except Exception as e:
        flash(f'Error generating analytics: {str(e)}', 'error')
        return redirect(url_for('dashboard'))

@app.route('/cli-commands')
def cli_commands():
    """Show all available CLI commands"""
    
    # Get help from main.py
    command = ['python3', 'main.py', '--help']
    result = run_cli_command(command, timeout=30)
    
    cli_help = result.get('stdout', 'Help not available')
    
    # Define available commands (actual commands from main.py)
    commands = [
        {'name': 'generate', 'description': 'Generate creative assets from campaign brief'},
        {'name': 'validate', 'description': 'Validate campaign brief structure'},
        {'name': 'compliance', 'description': 'Check brand compliance'},
        {'name': 'localize', 'description': 'Localize campaign for specific markets'},
        {'name': 'markets', 'description': 'List supported markets and their details'},
        {'name': 'agent', 'description': 'AI agent actions: start, stop, status, test'},
        {'name': 'status', 'description': 'Get current system status from AI agent'},
        {'name': 'batch', 'description': 'Batch processing: submit, status, results, cancel'},
        {'name': 'queue', 'description': 'Queue management: status, clear, priority'},
        {'name': 'analytics', 'description': 'Generate analytics dashboard'},
        {'name': 'ab-test', 'description': 'A/B testing: create, start, status, report'},
        {'name': 'webhooks', 'description': 'Webhook management: add, remove, list, test'},
        {'name': 'integrate', 'description': 'Third-party integrations: status, demo, migrate'},
        {'name': 'monitor', 'description': 'System monitoring: start, status, metrics'},
        {'name': 'moderate', 'description': 'Content moderation: scan, validate, report'},
        {'name': 'workflow', 'description': 'Workflow management: create, execute, status'},
        {'name': 'optimize', 'description': 'Optimization: cache, images, report, clear'},
        {'name': 'serve', 'description': 'Start API server'},
        {'name': 'audit', 'description': 'Audit logging: log, report, search, export'},
        {'name': 'brand', 'description': 'Brand analysis: analyze, extract-colors, assess-quality'},
        {'name': 'predict-performance', 'description': 'Predict asset performance using AI'},
        {'name': 'api-connect', 'description': 'External API connections and webhooks'},
        {'name': 'personalize', 'description': 'Personalize campaigns for audiences'},
        {'name': 'collaborate', 'description': 'Team collaboration features'},
        {'name': 'analyze-performance', 'description': 'Performance analysis and learning'},
    ]
    
    return render_template('cli_commands.html', commands=commands, cli_help=cli_help)

@app.route('/run-command', methods=['POST'])
def run_command():
    """Run a custom CLI command"""
    try:
        command_name = request.form.get('command')
        campaign_id = request.form.get('campaign_id', '')
        
        if not command_name:
            flash('No command specified', 'error')
            return redirect(url_for('cli_commands'))
        
        # Build command
        if campaign_id:
            brief_file = None
            for ext in ['yaml', 'yml', 'json']:
                candidate = Path(CAMPAIGN_BRIEFS_FOLDER) / f"{campaign_id}.{ext}"
                if candidate.exists():
                    brief_file = candidate
                    break
            
            if brief_file:
                command = ['python3', 'main.py', command_name, str(brief_file)]
            else:
                command = ['python3', 'main.py', command_name]
        else:
            command = ['python3', 'main.py', command_name]
        
        flash(f'🔄 Running command: {" ".join(command)}', 'info')
        
        result = run_cli_command(command, timeout=300)
        
        if result['success']:
            flash(f'✅ Command completed successfully!', 'success')
            if result['stdout']:
                flash(f'Output: {result["stdout"][:500]}...', 'info')
        else:
            flash(f'❌ Command failed: {result.get("error", result.get("stderr", "Unknown error"))}', 'error')
    
    except Exception as e:
        flash(f'Error running command: {str(e)}', 'error')
    
    return redirect(url_for('cli_commands'))

@app.route('/view-campaign/<campaign_id>')
def view_campaign(campaign_id):
    """View campaign details and outputs"""
    # Load campaign data
    campaign_data = None
    for ext in ['yaml', 'yml', 'json']:
        filepath = Path(CAMPAIGN_BRIEFS_FOLDER) / f"{campaign_id}.{ext}"
        if filepath.exists():
            try:
                with open(filepath, 'r') as f:
                    if ext in ['yaml', 'yml']:
                        campaign_data = yaml.safe_load(f)
                    else:
                        campaign_data = json.load(f)
                break
            except Exception as e:
                logger.error(f"Error loading campaign: {e}")
    
    if not campaign_data:
        flash(f'Campaign {campaign_id} not found', 'error')
        return redirect(url_for('dashboard'))
    
    # Check for outputs
    output_dir = Path(OUTPUT_FOLDER) / campaign_id
    outputs = []
    if output_dir.exists():
        for file_path in output_dir.rglob('*'):
            if file_path.is_file():
                outputs.append({
                    'name': file_path.name,
                    'path': str(file_path.relative_to(Path('.'))),
                    'size': file_path.stat().st_size,
                    'created': datetime.fromtimestamp(file_path.stat().st_mtime).strftime('%Y-%m-%d %H:%M'),
                    'type': file_path.suffix.lower()
                })
    
    return render_template('view_campaign.html', 
                         campaign=campaign_data, 
                         campaign_id=campaign_id,
                         outputs=outputs)

@app.route('/download/<campaign_id>/<path:filename>')
def download_file(campaign_id, filename):
    """Download output file"""
    try:
        output_dir = Path(OUTPUT_FOLDER) / campaign_id
        file_path = output_dir / filename
        
        if file_path.exists() and file_path.is_file():
            return send_file(file_path, as_attachment=True)
        else:
            flash(f'File {filename} not found in {output_dir}', 'error')
            return redirect(url_for('list_all_outputs'))
    except Exception as e:
        flash(f'Error downloading file: {str(e)}', 'error')
        return redirect(url_for('list_all_outputs'))

@app.route('/image/<campaign_id>/<path:filename>')
def serve_image(campaign_id, filename):
    """Serve image file for preview"""
    try:
        output_dir = Path(OUTPUT_FOLDER) / campaign_id
        file_path = output_dir / filename
        
        if file_path.exists() and file_path.is_file():
            return send_file(file_path)
        else:
            return "Image not found", 404
    except Exception as e:
        return f"Error serving image: {str(e)}", 500

@app.route('/outputs')
def list_all_outputs():
    """List all generated outputs across campaigns"""
    all_outputs = []
    output_base = Path(OUTPUT_FOLDER)
    
    if output_base.exists():
        for campaign_dir in output_base.iterdir():
            if campaign_dir.is_dir():
                for file_path in campaign_dir.rglob('*'):
                    if file_path.is_file() and file_path.suffix.lower() in ['.jpg', '.png', '.jpeg', '.gif', '.webp']:
                        # Get relative path from campaign directory
                        relative_to_campaign = file_path.relative_to(campaign_dir)
                        all_outputs.append({
                            'campaign': campaign_dir.name,
                            'name': str(relative_to_campaign),  # Include subdirectory path
                            'path': str(file_path.relative_to(Path('.'))),
                            'size': file_path.stat().st_size,
                            'type': file_path.suffix,
                            'created': datetime.fromtimestamp(file_path.stat().st_mtime).strftime('%Y-%m-%d %H:%M')
                        })
    
    return render_template('outputs_gallery.html', outputs=all_outputs)

@app.route('/api/status')
def api_status():
    """API endpoint for system status"""
    return jsonify(get_system_status())

@app.route('/api/ai-monitor-activity')
def api_ai_monitor_activity():
    """API endpoint for AI Monitor activity data"""
    try:
        alerts_dir = Path('alerts')
        logs_dir = Path('logs')
        
        # Get recent alerts (last 10, filter duplicates and test alerts)
        recent_alerts = []
        seen_messages = set()
        if alerts_dir.exists():
            alert_files = sorted(alerts_dir.glob('*.json'), key=lambda x: x.stat().st_mtime, reverse=True)[:20]
            for alert_file in alert_files:
                try:
                    with open(alert_file, 'r') as f:
                        alert_data = json.load(f)
                        message = alert_data.get('message', 'Unknown alert')
                        alert_type = alert_data.get('alert_type', '')
                        
                        # Skip test alerts and duplicates
                        if ('test' in message.lower() or 
                            'test' in alert_type.lower() or 
                            message in seen_messages):
                            continue
                            
                        seen_messages.add(message)
                        recent_alerts.append({
                            'message': message,
                            'severity': alert_data.get('severity', 'UNKNOWN').replace('AlertSeverity.', ''),
                            'timestamp': alert_data.get('timestamp', ''),
                            'campaign_id': alert_data.get('campaign_id', ''),
                            'alert_type': alert_type
                        })
                        
                        if len(recent_alerts) >= 5:
                            break
                except Exception as e:
                    logger.warning(f"Error reading alert {alert_file}: {e}")
        
        # Get campaign tracking data
        campaign_tracking = []
        if logs_dir.exists():
            tracking_files = sorted(logs_dir.glob('*_variant_tracking.json'), key=lambda x: x.stat().st_mtime, reverse=True)[:3]
            for tracking_file in tracking_files:
                try:
                    with open(tracking_file, 'r') as f:
                        tracking_data = json.load(f)
                        campaign_tracking.append({
                            'campaign_id': tracking_data.get('campaign_id', ''),
                            'variants_count': tracking_data.get('variants_count', 0),
                            'target_count': tracking_data.get('target_count', 0),
                            'completion_rate': tracking_data.get('completion_rate', 0),
                            'tracked_at': tracking_data.get('tracked_at', '')
                        })
                except Exception as e:
                    logger.warning(f"Error reading tracking {tracking_file}: {e}")
        
        # Get recent communications
        recent_communications = []
        if logs_dir.exists():
            comm_files = sorted(logs_dir.glob('*_communication.txt'), key=lambda x: x.stat().st_mtime, reverse=True)[:3]
            for comm_file in comm_files:
                try:
                    with open(comm_file, 'r') as f:
                        content = f.read()
                        subject_line = content.split('\n')[0].replace('Subject: ', '') if content else 'Email Communication'
                        recent_communications.append({
                            'subject': subject_line[:80] + '...' if len(subject_line) > 80 else subject_line,
                            'timestamp': datetime.fromtimestamp(comm_file.stat().st_mtime).isoformat(),
                            'file': comm_file.name
                        })
                except Exception as e:
                    logger.warning(f"Error reading communication {comm_file}: {e}")
        
        return jsonify({
            'recent_alerts': recent_alerts,
            'campaign_tracking': campaign_tracking,
            'recent_communications': recent_communications,
            'last_updated': datetime.now().isoformat()
        })
        
    except Exception as e:
        logger.error(f"Error getting AI monitor activity: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/run-ai-tool', methods=['POST'])
def api_run_ai_tool():
    """API endpoint to run AI tools"""
    try:
        data = request.get_json()
        tool_name = data.get('tool')
        
        if not tool_name:
            return jsonify({'success': False, 'error': 'No tool specified'}), 400
        
        # Get latest campaign and image dynamically
        latest_campaign = get_latest_campaign() or 'campaign_briefs/holiday_collection_2024.yaml'
        latest_image = get_latest_image() or 'output/sample.jpg'
        
        # Map tool names to CLI commands
        tool_commands = {
            # Pipeline Management
            'generate-pipeline': ['python3', 'main.py', 'generate', latest_campaign],
            'validate-campaigns': ['python3', 'main.py', 'validate', latest_campaign],
            'compliance-check': ['python3', 'main.py', 'compliance', latest_campaign],
            'localize-campaigns': ['python3', 'main.py', 'localize', latest_campaign, 'US'],
            'batch-processing': ['python3', 'main.py', 'batch', 'status'],
            'api-server': ['python3', 'main.py', 'serve', '--host', '0.0.0.0', '--port', '8001'],
            
            # Analytics & Reporting Hub
            'analytics-dashboard': ['python3', 'main.py', 'analytics', '--html'],
            'system-health': ['python3', 'main.py', 'monitor', 'health'],
            'performance-metrics': ['python3', 'main.py', 'monitor', 'metrics'],
            'export-reports': ['python3', 'main.py', 'monitor', 'export'],
            'cost-analysis': ['python3', 'main.py', 'analytics'],
            
            # A/B Testing Center
            'create-ab-test': ['python3', 'main.py', 'ab_test', 'create', '--test-name', 'Dashboard_Test'],
            'start-ab-test': ['python3', 'main.py', 'ab_test', 'start', '--test-id', 'test_001'],
            'ab-test-results': ['python3', 'main.py', 'ab_test', 'status'],
            'ab-test-reports': ['python3', 'main.py', 'ab_test', 'report'],
            
            # External Integration Suite
            'stock-search': ['python3', 'main.py', 'integration', 'search-stock', '--query', 'creative'],
            'ai-generate': ['python3', 'main.py', 'integration', 'generate'],
            'font-library': ['python3', 'main.py', 'integration', 'fonts'],
            'workspace': ['python3', 'main.py', 'integration', 'workspace'],
            'api-status': ['python3', 'main.py', 'api', 'status'],
            
            # System-wide tools
            'analytics': ['python3', 'main.py', 'analytics'],
            'monitor': ['python3', 'main.py', 'monitor', 'status'],
            'audit': ['python3', 'main.py', 'audit', 'report'],
            'integration-status': ['python3', 'main.py', 'integrate', 'status'],
            'collaborate': ['python3', 'main.py', 'collaborate', 'status'],
            'workflow': ['python3', 'main.py', 'workflow', 'status'],
            'optimize': ['python3', 'main.py', 'optimize', 'report'],
            
            # Advanced AI features
            'tenant-management': ['python3', 'main.py', 'tenant', 'list'],
            'webhooks': ['python3', 'main.py', 'webhooks', 'list'],
            'queue': ['python3', 'main.py', 'queue', 'status'],
            'moderate-content': ['python3', 'main.py', 'moderate', 'report'],
            'ab-testing': ['python3', 'main.py', 'ab_test', 'list'],
            'brand-intelligence': ['python3', 'main.py', 'brand', 'report'],
            'advanced-integration': ['python3', 'main.py', 'integration', 'advanced'],
            'performance-analysis': ['python3', 'main.py', 'analyze_performance', 'run-analysis'],
            
            # Enterprise Administration
            'audit-logs': ['python3', 'main.py', 'audit', 'log'],
            'tenant-admin': ['python3', 'main.py', 'tenant', 'list'],
            'workflow-designer': ['python3', 'main.py', 'workflow', 'templates'],
            'usage-reports': ['python3', 'main.py', 'tenant', 'usage'],
            'security-audit': ['python3', 'main.py', 'audit', 'report'],
            
            # Content Intelligence Panel
            'content-scan': ['python3', 'main.py', 'moderate', 'scan', '--campaign-file', latest_campaign],
            'brand-analysis': ['python3', 'main.py', 'brand', 'analyze', '--image-path', latest_image] if latest_image else ['python3', 'main.py', 'brand', 'report'],
            'quality-assessment': ['python3', 'main.py', 'brand', 'assess-quality', '--image-path', latest_image] if latest_image else ['python3', 'main.py', 'brand', 'report'],
            'consistency-check': ['python3', 'main.py', 'brand', 'validate-consistency'],
            'color-extraction': ['python3', 'main.py', 'brand', 'extract-colors', '--image-path', latest_image] if latest_image else ['python3', 'main.py', 'brand', 'report'],
            
            # Collaboration Platform
            'create-project': ['python3', 'main.py', 'collaborate', 'create-project', '--project-name', 'New_Project'],
            'team-dashboard': ['python3', 'main.py', 'collaborate', 'dashboard'],
            'upload-assets': ['python3', 'main.py', 'collaborate', 'upload-asset'],
            'notifications': ['python3', 'main.py', 'collaborate', 'notifications'],
            'user-management': ['python3', 'main.py', 'collaborate', 'users'],
            
            # Performance Intelligence
            'predict-performance': ['python3', 'main.py', 'predict-performance', '--image-path', latest_image] if latest_image else ['python3', 'main.py', 'predict-performance'],
            'ml-analytics': ['python3', 'main.py', 'analyze-performance', 'run-analysis'],
            'personalization': ['python3', 'main.py', 'personalize', latest_campaign, '--markets', 'US,DE,JP'],
            'optimization-engine': ['python3', 'main.py', 'optimize', 'report'],
            'learning-insights': ['python3', 'main.py', 'analyze_performance', 'learning-report'],
            
            # Real-time Monitoring
            'live-dashboard': ['python3', 'main.py', 'monitor', 'status'],
            'diversity-tracker': ['python3', 'main.py', 'analytics'],
            'predictive-flagging': ['python3', 'main.py', 'predict-performance'],
            'variant-intelligence': ['python3', 'main.py', 'analytics'],
            'real-time-alerts': ['python3', 'main.py', 'agent', 'status'],
            
            # Advanced Orchestration
            'pipeline-orchestrator': ['python3', 'main.py', 'workflow', 'status'],
            'unified-system': ['python3', 'main.py', 'status'],
            'intelligent-automation': ['python3', 'main.py', 'agent', 'status'],
            'workflow-engine': ['python3', 'main.py', 'workflow', 'list'],
            'ci-cd-integration': ['python3', 'main.py', 'serve', '--help']
        }
        
        command = tool_commands.get(tool_name)
        if not command:
            return jsonify({'success': False, 'error': f'Unknown tool: {tool_name}'}), 400
        
        # Run the command
        result = run_cli_command(command, timeout=60)
        
        return jsonify({
            'success': result['success'],
            'output': result['stdout'] if result['success'] else None,
            'error': result.get('stderr') or result.get('error') if not result['success'] else None
        })
        
    except Exception as e:
        logger.error(f"Error running AI tool: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/run-campaign-ai-tool', methods=['POST'])
def api_run_campaign_ai_tool():
    """API endpoint to run campaign-specific AI tools"""
    try:
        data = request.get_json()
        tool_name = data.get('tool')
        campaign_id = data.get('campaign_id')
        
        if not tool_name:
            return jsonify({'success': False, 'error': 'No tool specified'}), 400
        if not campaign_id:
            return jsonify({'success': False, 'error': 'No campaign ID specified'}), 400
        
        # Get campaign brief path
        campaign_brief = f'campaign_briefs/{campaign_id}.yaml'
        if not Path(campaign_brief).exists():
            return jsonify({'success': False, 'error': f'Campaign brief not found: {campaign_brief}'}), 404
        
        # Map campaign-specific tool names to CLI commands
        tool_commands = {
            # Campaign-specific tools
            'predict-performance': ['python3', 'main.py', 'predict-performance', '--campaign', campaign_brief],
            'brand-analyze': ['python3', 'main.py', 'brand', 'analyze', '--campaign', campaign_brief],
            'personalize': ['python3', 'main.py', 'personalize', campaign_brief, '--markets', 'US,DE,JP'],
            'ab-test': ['python3', 'main.py', 'ab_test', 'simulate', '--campaign', campaign_brief, '--days', '7'],
            'moderate': ['python3', 'main.py', 'moderate', 'scan', '--campaign', campaign_brief],
            'analyze-performance': ['python3', 'main.py', 'analyze_performance', 'run-analysis', '--campaign', campaign_brief],
            
            # Universal tools (work in both contexts)
            'validate': ['python3', 'main.py', 'validate', campaign_brief],
            'compliance-check': ['python3', 'main.py', 'compliance', campaign_brief],
            'status-check': ['python3', 'main.py', 'status'],
            'optimize-assets': ['python3', 'main.py', 'optimize', 'report', '--campaign', campaign_brief]
        }
        
        command = tool_commands.get(tool_name)
        if not command:
            return jsonify({'success': False, 'error': f'Unknown campaign tool: {tool_name}'}), 400
        
        # Run the command
        result = run_cli_command(command, timeout=60)
        
        return jsonify({
            'success': result['success'],
            'output': result['stdout'] if result['success'] else None,
            'error': result.get('stderr') or result.get('error') if not result['success'] else None
        })
        
    except Exception as e:
        logger.error(f"Error running campaign AI tool: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/explorer')
def data_explorer():
    """Comprehensive data explorer view"""
    return render_template('data_explorer.html')

@app.route('/api/explorer/<section>')
def api_explorer_data(section):
    """API endpoint for data explorer sections"""
    try:
        if section == 'overview':
            # Count all files
            total_files = 0
            campaigns_count = 0
            images_count = 0
            alerts_count = 0
            
            # Count output files
            output_path = Path(OUTPUT_FOLDER)
            if output_path.exists():
                campaigns_count = len(list(output_path.iterdir()))
                for campaign_dir in output_path.iterdir():
                    if campaign_dir.is_dir():
                        for file in campaign_dir.rglob('*'):
                            if file.is_file():
                                total_files += 1
                                if file.suffix.lower() in ['.jpg', '.png', '.jpeg']:
                                    images_count += 1
            
            # Count alerts
            alerts_path = Path('alerts')
            if alerts_path.exists():
                alerts_count = len(list(alerts_path.glob('*.json')))
            
            # Count logs
            logs_path = Path('logs')
            if logs_path.exists():
                total_files += len(list(logs_path.glob('*.json')))
            
            # Get recent activity timeline
            timeline = []
            # Add recent campaign activities
            if output_path.exists():
                for campaign_dir in sorted(output_path.iterdir(), key=lambda x: x.stat().st_mtime, reverse=True)[:5]:
                    if campaign_dir.is_dir():
                        timeline.append({
                            'timestamp': datetime.fromtimestamp(campaign_dir.stat().st_mtime).strftime('%H:%M:%S'),
                            'message': f'Campaign {campaign_dir.name} generated'
                        })
            
            return jsonify({
                'total_files': total_files,
                'campaigns_count': campaigns_count,
                'images_count': images_count,
                'alerts_count': alerts_count,
                'timeline': timeline
            })
            
        elif section == 'campaigns':
            campaigns = []
            output_path = Path(OUTPUT_FOLDER)
            if output_path.exists():
                for campaign_dir in output_path.iterdir():
                    if campaign_dir.is_dir():
                        campaign_data = {
                            'id': campaign_dir.name,
                            'name': campaign_dir.name,
                            'products': 0,
                            'images': 0,
                            'date': datetime.fromtimestamp(campaign_dir.stat().st_mtime).strftime('%Y-%m-%d %H:%M')
                        }
                        
                        # Count products and images
                        for item in campaign_dir.iterdir():
                            if item.is_dir():
                                campaign_data['products'] += 1
                                campaign_data['images'] += len(list(item.glob('*.jpg'))) + len(list(item.glob('*.png')))
                        
                        campaigns.append(campaign_data)
            
            return jsonify({'campaigns': campaigns})
            
        elif section == 'images':
            images = []
            output_path = Path(OUTPUT_FOLDER)
            if output_path.exists():
                for campaign_dir in output_path.iterdir():
                    if campaign_dir.is_dir():
                        for product_dir in campaign_dir.iterdir():
                            if product_dir.is_dir():
                                for file in product_dir.glob('*'):
                                    if file.is_file() and file.suffix.lower() in ['.jpg', '.png', '.jpeg']:
                                        # Create proper path for image URL
                                        relative_path = f"{product_dir.name}/{file.name}"
                                        images.append({
                                            'name': file.name,
                                            'url': url_for('serve_image', 
                                                         campaign_id=campaign_dir.name, 
                                                         filename=relative_path),
                                            'campaign': campaign_dir.name,
                                            'product': product_dir.name,
                                            'size': f'{file.stat().st_size // 1024}KB',
                                            'dimensions': file.stem.split('_')[-1] if '_' in file.stem else 'unknown'
                                        })
            
            return jsonify({'images': images})
            
        elif section == 'logs':
            logs = []
            
            # Check for actual log files first
            logs_path = Path('logs')
            if logs_path.exists():
                for log_file in sorted(logs_path.glob('*.json'), key=lambda x: x.stat().st_mtime, reverse=True)[:50]:
                    try:
                        with open(log_file) as f:
                            log_data = json.load(f)
                            logs.append({
                                'level': log_data.get('level', 'INFO'),
                                'timestamp': log_data.get('timestamp', ''),
                                'message': log_data.get('message', str(log_data))[:200]
                            })
                    except:
                        pass
            
            # Add recent pipeline activity as logs
            output_path = Path(OUTPUT_FOLDER)
            if output_path.exists():
                for campaign_dir in sorted(output_path.iterdir(), key=lambda x: x.stat().st_mtime, reverse=True)[:20]:
                    if campaign_dir.is_dir():
                        # Check for generation report
                        report_file = campaign_dir / 'generation_report.json'
                        if report_file.exists():
                            try:
                                with open(report_file) as f:
                                    report_data = json.load(f)
                                    logs.append({
                                        'level': 'INFO',
                                        'timestamp': report_data.get('generated_at', ''),
                                        'message': f"Campaign '{report_data.get('campaign_id', campaign_dir.name)}' generated {len(report_data.get('generated_files', []))} assets"
                                    })
                            except:
                                pass
                        else:
                            # Fallback to directory modification time
                            logs.append({
                                'level': 'INFO',
                                'timestamp': datetime.fromtimestamp(campaign_dir.stat().st_mtime).isoformat(),
                                'message': f"Campaign '{campaign_dir.name}' created"
                            })
            
            return jsonify({'logs': logs})
            
        elif section == 'alerts':
            alerts = []
            
            # Check for actual alert files first
            alerts_path = Path('alerts')
            if alerts_path.exists():
                for alert_file in sorted(alerts_path.glob('*.json'), key=lambda x: x.stat().st_mtime, reverse=True)[:20]:
                    try:
                        with open(alert_file) as f:
                            alert_data = json.load(f)
                            alerts.append({
                                'title': alert_data.get('type', 'Alert'),
                                'message': alert_data.get('description', ''),
                                'severity': alert_data.get('severity', 'info'),
                                'timestamp': alert_data.get('timestamp', '')
                            })
                    except:
                        pass
            
            # Generate system status alerts
            output_path = Path(OUTPUT_FOLDER)
            if output_path.exists():
                # Check for compliance issues
                for campaign_dir in output_path.iterdir():
                    if campaign_dir.is_dir():
                        compliance_file = campaign_dir / 'compliance_report.txt'
                        if compliance_file.exists():
                            try:
                                with open(compliance_file, 'r') as f:
                                    content = f.read()
                                    if 'REVIEW REQUIRED' in content:
                                        alerts.append({
                                            'title': 'Compliance Issue',
                                            'message': f"Campaign {campaign_dir.name} requires review before launch",
                                            'severity': 'warning',
                                            'timestamp': datetime.fromtimestamp(compliance_file.stat().st_mtime).isoformat()
                                        })
                                    elif 'FAILED' in content:
                                        alerts.append({
                                            'title': 'Compliance Failure',
                                            'message': f"Campaign {campaign_dir.name} failed compliance checks",
                                            'severity': 'error',
                                            'timestamp': datetime.fromtimestamp(compliance_file.stat().st_mtime).isoformat()
                                        })
                            except:
                                pass
            
            # Add system health alerts
            current_time = datetime.now()
            alerts.append({
                'title': 'System Status',
                'message': 'Creative Automation Platform is running normally',
                'severity': 'success',
                'timestamp': current_time.isoformat()
            })
            
            return jsonify({'alerts': alerts})
            
        else:
            return jsonify({'error': 'Invalid section'}), 404
            
    except Exception as e:
        logger.error(f"Error in data explorer API: {e}")
        return jsonify({'error': str(e)}), 500

def load_campaign_brief(file_path):
    """Load and validate campaign brief from file"""
    try:
        with open(file_path, 'r') as f:
            if file_path.endswith('.json'):
                return json.load(f)
            else:  # yaml
                return yaml.safe_load(f)
    except Exception as e:
        logger.error(f"Error loading brief {file_path}: {e}")
        return None

def save_campaign_brief(brief_data, brief_id=None):
    """Save campaign brief to file"""
    try:
        if not brief_id:
            brief_id = f"campaign_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        
        # Ensure campaign_briefs folder exists
        Path(CAMPAIGN_BRIEFS_FOLDER).mkdir(exist_ok=True)
        
        # Wrap in campaign_brief structure to match existing pattern
        wrapped_data = {
            'campaign_brief': {
                'campaign_id': brief_id,
                'campaign_name': brief_data.get('campaign_name', ''),
                'products': [
                    {'name': p.strip(), 'description': f"Product: {p.strip()}"} 
                    if isinstance(p, str) else p 
                    for p in brief_data.get('products', [])
                ],
                'target_regions': brief_data.get('target_regions') or [brief_data.get('target_region', 'Global')],
                'target_audience': brief_data.get('target_audience', ''),
                'campaign_message': brief_data.get('campaign_message', ''),
                'created_at': brief_data.get('created_at', datetime.now().isoformat()),
                'output_requirements': {
                    'aspect_ratios': ['1:1', '9:16', '16:9'],
                    'formats': ['JPG']
                }
            }
        }
        
        # Save as YAML
        yaml_path = Path(CAMPAIGN_BRIEFS_FOLDER) / f"{brief_id}.yaml"
        with open(yaml_path, 'w') as f:
            yaml.dump(wrapped_data, f, default_flow_style=False, allow_unicode=True)
        
        return str(yaml_path)
    except Exception as e:
        logger.error(f"Error saving brief: {e}")
        return None

def validate_campaign_brief(brief_data):
    """Validate campaign brief structure"""
    required_fields = ['campaign_name', 'products', 'campaign_message']
    
    for field in required_fields:
        if field not in brief_data or not brief_data[field]:
            return False, f"Missing required field: {field}"
    
    # Check that either target_region or target_regions is provided
    has_target_region = brief_data.get('target_region')
    has_target_regions = brief_data.get('target_regions')
    
    if not has_target_region and not has_target_regions:
        return False, "Missing required field: target_regions (select at least one region)"
    
    products = brief_data.get('products', [])
    if isinstance(products, str):
        products = [p.strip() for p in products.split(',') if p.strip()]
    
    if len(products) < 2:
        return False, "At least 2 products are required"
    
    return True, "Valid"

@app.route('/healthz')
def healthz():
    """Health check endpoint"""
    return jsonify({
        'status': 'healthy',
        'timestamp': datetime.now().isoformat(),
        'version': '1.0.0'
    })

@app.route('/api/campaigns/brief', methods=['GET', 'POST'])
def campaign_brief():
    """Campaign brief API endpoint"""
    if request.method == 'GET':
        # Check if specific campaign ID requested
        campaign_id = request.args.get('campaign_id')
        
        if campaign_id:
            # Load specific campaign brief
            brief_file = None
            for ext in ['yaml', 'yml', 'json']:
                candidate = Path(CAMPAIGN_BRIEFS_FOLDER) / f"{campaign_id}.{ext}"
                if candidate.exists():
                    brief_file = candidate
                    break
            
            if brief_file:
                try:
                    with open(brief_file, 'r') as f:
                        if brief_file.suffix.lower() in ['.yaml', '.yml']:
                            data = yaml.safe_load(f)
                        else:
                            data = json.load(f)
                    
                    return jsonify({
                        'status': 'success',
                        'brief': data,
                        'file_path': str(brief_file)
                    })
                except Exception as e:
                    return jsonify({
                        'status': 'error',
                        'message': f'Error loading campaign brief: {e}'
                    }), 500
            else:
                return jsonify({
                    'status': 'error',
                    'message': f'Campaign brief not found: {campaign_id}'
                }), 404
        else:
            # Return current/latest brief
            latest_brief_path = get_latest_campaign()
            if latest_brief_path:
                brief_data = load_campaign_brief(latest_brief_path)
                if brief_data:
                    return jsonify({
                        'status': 'success',
                        'brief': brief_data,
                        'file_path': latest_brief_path
                    })
            
            return jsonify({
                'status': 'success',
                'brief': None,
                'message': 'No campaign briefs found'
            })
    
    elif request.method == 'POST':
        try:
            # Handle both JSON and form data
            if request.is_json:
                brief_data = request.get_json()
            else:
                # Handle form data
                brief_data = {
                    'campaign_name': request.form.get('name', ''),
                    'products': [p.strip() for p in request.form.get('products', '').split(',') if p.strip()],
                    'target_regions': request.form.getlist('target_regions') or [request.form.get('region', 'Global')],
                    'campaign_message': request.form.get('message', ''),
                    'created_at': datetime.now().isoformat()
                }
            
            # Validate brief
            is_valid, message = validate_campaign_brief(brief_data)
            if not is_valid:
                return jsonify({
                    'status': 'error',
                    'message': message
                }), 400
            
            # Save brief
            brief_path = save_campaign_brief(brief_data)
            if brief_path:
                return jsonify({
                    'status': 'success',
                    'message': 'Campaign brief saved successfully',
                    'file_path': brief_path,
                    'brief': brief_data
                })
            else:
                return jsonify({
                    'status': 'error',
                    'message': 'Failed to save campaign brief'
                }), 500
                
        except Exception as e:
            logger.error(f"Error in campaign brief endpoint: {e}")
            return jsonify({
                'status': 'error',
                'message': f'Server error: {str(e)}'
            }), 500

@app.route('/api/campaigns/upload', methods=['POST'])
def upload_campaign_brief():
    """Upload campaign brief file"""
    try:
        if 'file' not in request.files:
            return jsonify({'status': 'error', 'message': 'No file provided'}), 400
        
        file = request.files['file']
        if file.filename == '':
            return jsonify({'status': 'error', 'message': 'No file selected'}), 400
        
        if not allowed_file(file.filename):
            return jsonify({'status': 'error', 'message': 'Invalid file type. Only JSON and YAML files are allowed.'}), 400
        
        # Read and parse file
        file_content = file.read().decode('utf-8')
        try:
            if file.filename.endswith('.json'):
                brief_data = json.loads(file_content)
            else:  # yaml/yml
                brief_data = yaml.safe_load(file_content)
        except Exception as parse_error:
            return jsonify({
                'status': 'error', 
                'message': f'Failed to parse file: {str(parse_error)}'
            }), 400
        
        # Extract from campaign_brief wrapper if present
        if 'campaign_brief' in brief_data:
            brief_data = brief_data['campaign_brief']
        
        # Normalize field names
        normalized_brief = {
            'campaign_name': brief_data.get('campaign_name', ''),
            'products': brief_data.get('products', []),
            'target_regions': brief_data.get('target_regions') or [brief_data.get('target_region', 'Global')],
            'target_audience': brief_data.get('target_audience', ''),
            'campaign_message': brief_data.get('campaign_message', '')
        }
        
        # Validate brief
        is_valid, message = validate_campaign_brief(normalized_brief)
        if not is_valid:
            return jsonify({'status': 'error', 'message': message}), 400
        
        return jsonify({
            'status': 'success',
            'message': 'File uploaded and parsed successfully',
            'brief': normalized_brief
        })
        
    except Exception as e:
        logger.error(f"Error uploading brief: {e}")
        return jsonify({'status': 'error', 'message': f'Upload error: {str(e)}'}), 500

@app.route('/api/campaigns/<campaign_id>/run', methods=['POST'])
def api_run_campaign(campaign_id):
    """API endpoint to run campaign pipeline with detailed feedback"""
    try:
        # Find the campaign brief file
        brief_file = None
        for ext in ['yaml', 'yml', 'json']:
            candidate = Path(CAMPAIGN_BRIEFS_FOLDER) / f"{campaign_id}.{ext}"
            if candidate.exists():
                brief_file = candidate
                break
        
        if not brief_file:
            return jsonify({
                'status': 'error',
                'message': f'Campaign brief not found: {campaign_id}'
            }), 404
        
        # Get selected regions from request if provided
        data = request.get_json() or {}
        selected_regions = data.get('regions', [])
        
        # Validate campaign brief first
        validate_command = ['python3', 'main.py', 'validate', str(brief_file)]
        validate_result = run_cli_command(validate_command, timeout=30)
        
        if not validate_result['success']:
            return jsonify({
                'status': 'error',
                'message': 'Campaign brief validation failed',
                'details': validate_result.get('stderr', 'Unknown validation error')
            }), 400
        
        # Run the main pipeline
        generate_command = ['python3', 'main.py', 'generate', str(brief_file)]
        
        # Add region-specific flags if provided
        if selected_regions and len(selected_regions) == 1:
            generate_command.extend(['--localize', selected_regions[0]])
        
        # Run with extended timeout for generation
        result = run_cli_command(generate_command, timeout=900)  # 15 minutes
        
        if result['success']:
            # Parse output for key information
            output_lines = result['stdout'].split('\n')
            
            # Extract generation summary
            summary_info = {
                'campaign_id': campaign_id,
                'completed': True,
                'output': result['stdout'],
                'regions_processed': [],
                'files_generated': []
            }
            
            # Parse output for regions and files
            for line in output_lines:
                if 'Processing region:' in line:
                    region = line.split('Processing region:')[1].strip()
                    summary_info['regions_processed'].append(region)
                elif 'Generated:' in line and '.jpg' in line:
                    file_path = line.split('Generated:')[1].strip()
                    summary_info['files_generated'].append(file_path)
            
            return jsonify({
                'status': 'success',
                'message': f'Pipeline completed successfully for {campaign_id}',
                'summary': summary_info,
                'output': result['stdout']
            })
        else:
            return jsonify({
                'status': 'error',
                'message': 'Pipeline execution failed',
                'details': result.get('stderr', 'Unknown error'),
                'output': result.get('stdout', '')
            }), 500
            
    except Exception as e:
        logger.error(f"Error running campaign {campaign_id}: {e}")
        return jsonify({
            'status': 'error',
            'message': f'Internal error: {str(e)}'
        }), 500

@app.route('/api/campaigns/<campaign_id>/validate', methods=['POST'])
def api_validate_campaign(campaign_id):
    """API endpoint to validate campaign brief"""
    try:
        # Find the campaign brief file
        brief_file = None
        for ext in ['yaml', 'yml', 'json']:
            candidate = Path(CAMPAIGN_BRIEFS_FOLDER) / f"{campaign_id}.{ext}"
            if candidate.exists():
                brief_file = candidate
                break
        
        if not brief_file:
            return jsonify({
                'status': 'error',
                'message': f'Campaign brief not found: {campaign_id}'
            }), 404
        
        # Run validation
        command = ['python3', 'main.py', 'validate', str(brief_file)]
        result = run_cli_command(command, timeout=30)
        
        if result['success']:
            return jsonify({
                'status': 'success',
                'message': 'Campaign brief is valid',
                'output': result['stdout']
            })
        else:
            return jsonify({
                'status': 'error',
                'message': 'Campaign brief validation failed',
                'details': result.get('stderr', 'Unknown validation error'),
                'output': result.get('stdout', '')
            }), 400
            
    except Exception as e:
        return jsonify({
            'status': 'error',
            'message': f'Internal error: {str(e)}'
        }), 500

@app.route('/api/campaigns/<campaign_id>/update', methods=['POST'])
def api_update_campaign(campaign_id):
    """API endpoint to update an existing campaign brief"""
    try:
        # Get the updated data
        brief_data = request.get_json()
        if not brief_data:
            return jsonify({
                'status': 'error',
                'message': 'No data provided'
            }), 400
        
        # Find the existing campaign brief file
        brief_file = None
        for ext in ['yaml', 'yml', 'json']:
            candidate = Path(CAMPAIGN_BRIEFS_FOLDER) / f"{campaign_id}.{ext}"
            if candidate.exists():
                brief_file = candidate
                break
        
        if not brief_file:
            return jsonify({
                'status': 'error',
                'message': f'Campaign brief not found: {campaign_id}'
            }), 404
        
        # Validate the updated brief
        is_valid, message = validate_campaign_brief(brief_data)
        if not is_valid:
            return jsonify({
                'status': 'error',
                'message': message
            }), 400
        
        # Update the campaign brief file
        try:
            # Wrap in campaign_brief structure if needed
            if 'campaign_brief' not in brief_data:
                wrapped_data = {
                    'campaign_brief': {
                        'campaign_id': campaign_id,
                        'campaign_name': brief_data.get('campaign_name', ''),
                        'products': [
                            {'name': p.strip(), 'description': f"Product: {p.strip()}"} 
                            if isinstance(p, str) else p
                            for p in brief_data.get('products', [])
                        ],
                        'target_regions': brief_data.get('target_regions', []),
                        'target_audience': brief_data.get('target_audience', ''),
                        'campaign_message': brief_data.get('campaign_message', ''),
                        'created_at': brief_data.get('created_at', datetime.now().isoformat()),
                        'updated_at': datetime.now().isoformat()
                    }
                }
                
                # Add comprehensive fields if they exist
                if brief_data.get('brand_guidelines'):
                    wrapped_data['campaign_brief']['brand_guidelines'] = brief_data['brand_guidelines']
                if brief_data.get('budget_constraints'):
                    wrapped_data['campaign_brief']['budget_constraints'] = brief_data['budget_constraints']
                if brief_data.get('timeline'):
                    wrapped_data['campaign_brief']['timeline'] = brief_data['timeline']
                if brief_data.get('output_requirements'):
                    wrapped_data['campaign_brief']['output_requirements'] = brief_data['output_requirements']
            else:
                wrapped_data = brief_data
                wrapped_data['campaign_brief']['updated_at'] = datetime.now().isoformat()
            
            # Save the updated file
            with open(brief_file, 'w', encoding='utf-8') as f:
                if brief_file.suffix.lower() in ['.yaml', '.yml']:
                    yaml.dump(wrapped_data, f, default_flow_style=False, allow_unicode=True, sort_keys=False)
                else:
                    json.dump(wrapped_data, f, indent=2, ensure_ascii=False)
            
            return jsonify({
                'status': 'success',
                'message': 'Campaign updated successfully',
                'file_path': str(brief_file),
                'brief': wrapped_data
            })
            
        except Exception as e:
            return jsonify({
                'status': 'error',
                'message': f'Error saving campaign: {e}'
            }), 500
        
    except Exception as e:
        logger.error(f"Error updating campaign {campaign_id}: {e}")
        return jsonify({
            'status': 'error',
            'message': f'Internal error: {str(e)}'
        }), 500

if __name__ == '__main__':
    print("🚀 Creative Automation System - Web Interface")
    print("=" * 60)
    print("📍 Dashboard: http://localhost:5004")
    print("🎯 Features:")
    print("   • Creative automation pipeline")
    print("   • AI Monitor agent system")
    print("   • Campaign creation and management")
    print("   • Real-time analytics and reporting")
    print("   • File management and downloads")
    print("=" * 60)
    app.run(debug=True, host='0.0.0.0', port=5004)
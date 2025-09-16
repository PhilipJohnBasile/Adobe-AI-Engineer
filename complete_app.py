"""
Adobe Creative Automation Platform - Professional Web Interface
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
        
        # Get campaigns
        campaigns = []
        for pattern in ['*.yaml', '*.yml', '*.json']:
            campaigns.extend(Path(CAMPAIGN_BRIEFS_FOLDER).glob(pattern))
        
        # Get outputs
        output_dirs = [d for d in Path(OUTPUT_FOLDER).iterdir() if d.is_dir()]
        
        return {
            'system_ready': main_py_available,
            'ai_monitor_systems': ai_monitor_systems,
            'total_campaigns': len(campaigns),
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
        result = subprocess.run(
            command,
            capture_output=True,
            text=True,
            timeout=timeout,
            cwd=Path.cwd()
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
    
    # Get recent campaigns
    campaigns = []
    brief_files = []
    for pattern in ['*.yaml', '*.yml', '*.json']:
        brief_files.extend(Path(CAMPAIGN_BRIEFS_FOLDER).glob(pattern))
    
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
                products = [p.get('name', str(p)) if isinstance(p, dict) else str(p) for p in brief_data.get('products', [])]
            else:
                # Old format without wrapper
                campaign_name = data.get('campaign_name', brief_file.stem)
                products = [p.get('name', str(p)) if isinstance(p, dict) else str(p) for p in data.get('products', [])]
            
            campaigns.append({
                'id': brief_file.stem,
                'name': campaign_name,
                'products': products,
                'created': datetime.fromtimestamp(brief_file.stat().st_mtime).strftime('%Y-%m-%d %H:%M'),
                'file': brief_file.name
            })
        except Exception as e:
            logger.warning(f"Error reading {brief_file}: {e}")
    
    # Sort by creation time
    campaigns.sort(key=lambda x: x['created'], reverse=True)
    
    return render_template('complete_dashboard.html', 
                         status=status, 
                         campaigns=campaigns[:10])  # Show recent 10

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
                'target_region': request.form.get('target_region', 'Global'),
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
        {'name': 'adobe', 'description': 'Adobe integration: status, demo, migrate'},
        {'name': 'monitor', 'description': 'System monitoring: start, status, metrics'},
        {'name': 'moderate', 'description': 'Content moderation: scan, validate, report'},
        {'name': 'workflow', 'description': 'Workflow management: create, execute, status'},
        {'name': 'optimize', 'description': 'Optimization: cache, images, report, clear'},
        {'name': 'serve', 'description': 'Start API server'},
        {'name': 'audit', 'description': 'Audit logging: log, report, search, export'},
        {'name': 'brand', 'description': 'Brand analysis: analyze, extract-colors, assess-quality'},
        {'name': 'predict-performance', 'description': 'Predict asset performance using AI'},
        {'name': 'adobe-integration', 'description': 'Adobe Stock, Fonts, Firefly integration'},
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
            
            # Adobe Integration Suite
            'adobe-stock-search': ['python3', 'main.py', 'adobe-integration', 'search-stock', '--query', 'creative'],
            'adobe-firefly': ['python3', 'main.py', 'adobe-integration', 'firefly'],
            'adobe-fonts': ['python3', 'main.py', 'adobe-integration', 'fonts'],
            'adobe-workspace': ['python3', 'main.py', 'adobe-integration', 'workspace'],
            'adobe-express': ['python3', 'main.py', 'adobe', 'status'],
            
            # System-wide tools
            'analytics': ['python3', 'main.py', 'analytics'],
            'monitor': ['python3', 'main.py', 'monitor', 'status'],
            'audit': ['python3', 'main.py', 'audit', 'report'],
            'adobe-integration': ['python3', 'main.py', 'adobe', 'status'],
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
            'adobe-advanced': ['python3', 'main.py', 'adobe_integration', 'status'],
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
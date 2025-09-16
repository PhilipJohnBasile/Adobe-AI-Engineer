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
        
        # Check Task 3 systems
        task3_systems = {
            'production': Path('src/production_task3_system.py').exists(),
            'enterprise': Path('src/enterprise_task3_system.py').exists()
        }
        
        # Get campaigns
        campaigns = []
        for pattern in ['*.yaml', '*.yml', '*.json']:
            campaigns.extend(Path(CAMPAIGN_BRIEFS_FOLDER).glob(pattern))
        
        # Get outputs
        output_dirs = [d for d in Path(OUTPUT_FOLDER).iterdir() if d.is_dir()]
        
        return {
            'system_ready': main_py_available,
            'task3_systems': task3_systems,
            'total_campaigns': len(campaigns),
            'total_outputs': len(output_dirs),
            'cli_commands_available': 28,  # From main.py
            'last_updated': datetime.now().isoformat()
        }
    except Exception as e:
        logger.error(f"Error getting system status: {e}")
        return {'error': str(e)}

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
                flash(f'Output: {result["stdout"][:200]}...', 'info')
        else:
            flash(f'❌ Pipeline failed: {result.get("error", result.get("stderr", "Unknown error"))}', 'error')
        
    except Exception as e:
        flash(f'Error running pipeline: {str(e)}', 'error')
    
    return redirect(url_for('dashboard'))

@app.route('/run-task3/<campaign_id>')
def run_task3(campaign_id):
    """Run Task 3 AI agent monitoring"""
    try:
        flash(f'🤖 Starting Task 3 AI agent for {campaign_id}...', 'info')
        
        # Run Task 3 monitoring
        command = ['python3', 'src/production_task3_system.py']
        result = run_cli_command(command, timeout=120)
        
        if result['success']:
            flash(f'✅ Task 3 monitoring completed for {campaign_id}!', 'success')
        else:
            flash(f'❌ Task 3 failed: {result.get("error", result.get("stderr", "Unknown error"))}', 'error')
        
    except Exception as e:
        flash(f'Error running Task 3: {str(e)}', 'error')
    
    return redirect(url_for('dashboard'))

@app.route('/run-enterprise/<campaign_id>')
def run_enterprise(campaign_id):
    """Run enterprise system"""
    try:
        flash(f'🏢 Starting enterprise system for {campaign_id}...', 'info')
        
        command = ['python3', 'src/enterprise_task3_system.py']
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

@app.route('/download/<campaign_id>/<filename>')
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

@app.route('/image/<campaign_id>/<filename>')
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
                        all_outputs.append({
                            'campaign': campaign_dir.name,
                            'name': file_path.name,
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

if __name__ == '__main__':
    print("🚀 Creative Automation System - Web Interface")
    print("=" * 60)
    print("📍 Dashboard: http://localhost:5004")
    print("🎯 Features:")
    print("   • Task 2: Creative automation pipeline")
    print("   • Task 3: AI agent monitoring system")
    print("   • Campaign creation and management")
    print("   • Real-time analytics and reporting")
    print("   • File management and downloads")
    print("=" * 60)
    app.run(debug=True, host='0.0.0.0', port=5004)
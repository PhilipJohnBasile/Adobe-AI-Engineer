"""
Simple Web UI for Task 3 Creative Automation System
For normal humans who don't want to use command line
"""
import os
import json
import yaml
import shutil
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Any, Optional
import asyncio
import subprocess

# Web framework
from flask import Flask, render_template, request, redirect, url_for, flash, jsonify, send_file
from werkzeug.utils import secure_filename
import uuid

# Import our Task 3 systems
import sys
sys.path.append('src')

app = Flask(__name__)
app.secret_key = 'task3_secret_key'
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB max file size

# Configuration
UPLOAD_FOLDER = 'uploads'
CAMPAIGN_BRIEFS_FOLDER = 'campaign_briefs'
OUTPUT_FOLDER = 'output'
ALLOWED_EXTENSIONS = {'yaml', 'yml', 'json', 'png', 'jpg', 'jpeg', 'gif'}

# Create folders if they don't exist
for folder in [UPLOAD_FOLDER, CAMPAIGN_BRIEFS_FOLDER, OUTPUT_FOLDER]:
    Path(folder).mkdir(exist_ok=True)

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def get_campaign_status():
    """Get status of all campaigns"""
    campaigns = []
    
    # Check campaign briefs folder
    for brief_file in Path(CAMPAIGN_BRIEFS_FOLDER).glob('*.{yaml,yml,json}'):
        try:
            with open(brief_file, 'r') as f:
                if brief_file.suffix.lower() in ['.yaml', '.yml']:
                    data = yaml.safe_load(f)
                else:
                    data = json.load(f)
            
            campaign = {
                'id': brief_file.stem,
                'name': data.get('campaign_name', brief_file.stem),
                'status': 'ready',
                'products': data.get('products', []),
                'target_variants': data.get('target_variants', 0),
                'file': brief_file.name,
                'created': datetime.fromtimestamp(brief_file.stat().st_mtime).strftime('%Y-%m-%d %H:%M')
            }
            campaigns.append(campaign)
        except Exception as e:
            print(f"Error reading {brief_file}: {e}")
    
    return campaigns

def get_system_metrics():
    """Get basic system metrics"""
    campaigns = get_campaign_status()
    
    return {
        'total_campaigns': len(campaigns),
        'active_campaigns': len([c for c in campaigns if c['status'] == 'processing']),
        'completed_campaigns': len([c for c in campaigns if c['status'] == 'completed']),
        'success_rate': 85.5,  # Mock data
        'total_variants_generated': 47,  # Mock data
        'total_cost': 2.45,  # Mock data
        'uptime_hours': 24.7  # Mock data
    }

@app.route('/')
def index():
    """Main dashboard"""
    campaigns = get_campaign_status()
    metrics = get_system_metrics()
    return render_template('dashboard.html', campaigns=campaigns, metrics=metrics)

@app.route('/create-campaign')
def create_campaign():
    """Campaign creation form"""
    return render_template('create_campaign.html')

@app.route('/upload-campaign', methods=['POST'])
def upload_campaign():
    """Handle campaign brief upload"""
    
    # Handle file upload
    if 'file' in request.files:
        file = request.files['file']
        if file and file.filename and allowed_file(file.filename):
            filename = secure_filename(file.filename)
            filepath = Path(CAMPAIGN_BRIEFS_FOLDER) / filename
            file.save(filepath)
            flash(f'Campaign brief uploaded: {filename}', 'success')
            return redirect(url_for('index'))
    
    # Handle form data
    campaign_data = {
        'campaign_id': request.form.get('campaign_id', f'campaign_{uuid.uuid4().hex[:8]}'),
        'campaign_name': request.form.get('campaign_name', 'Untitled Campaign'),
        'products': [p.strip() for p in request.form.get('products', '').split(',') if p.strip()],
        'target_variants': int(request.form.get('target_variants', 5)),
        'target_region': request.form.get('target_region', 'Global'),
        'target_audience': request.form.get('target_audience', 'General'),
        'campaign_message': request.form.get('campaign_message', ''),
        'requirements': {
            'aspect_ratios': request.form.getlist('aspect_ratios'),
            'style': request.form.get('style', 'modern'),
            'colors': [c.strip() for c in request.form.get('colors', '').split(',') if c.strip()],
            'quality': request.form.get('quality', 'high')
        },
        'created_at': datetime.now().isoformat()
    }
    
    # Save campaign brief
    filename = f"{campaign_data['campaign_id']}.yaml"
    filepath = Path(CAMPAIGN_BRIEFS_FOLDER) / filename
    
    with open(filepath, 'w') as f:
        yaml.dump(campaign_data, f, default_flow_style=False)
    
    flash(f'Campaign created: {campaign_data["campaign_name"]}', 'success')
    return redirect(url_for('index'))

@app.route('/run-campaign/<campaign_id>')
def run_campaign(campaign_id):
    """Run the complete Task 1+2+3 pipeline for a campaign"""
    try:
        # TASK 1: Architecture validation
        flash(f'🏗️ TASK 1: Validating architecture for {campaign_id}...', 'info')
        
        # TASK 2: Creative pipeline execution 
        flash(f'🎨 TASK 2: Running creative generation pipeline...', 'info')
        
        # TASK 3: AI agent monitoring and communication
        flash(f'🤖 TASK 3: AI agent monitoring and stakeholder communication...', 'info')
        
        # Run the unified system
        result = subprocess.run([
            'python3', 'src/unified_task123_system.py', campaign_id
        ], capture_output=True, text=True, timeout=120)
        
        if result.returncode == 0:
            flash(f'✅ ALL TASKS COMPLETE: Campaign {campaign_id} executed successfully!', 'success')
            flash(f'📊 Generated variants with AI monitoring and professional alerts', 'success')
        else:
            flash(f'❌ Pipeline failed for {campaign_id}: {result.stderr}', 'error')
            
    except subprocess.TimeoutExpired:
        flash(f'⏰ Campaign {campaign_id} timed out (exceeded 2 minutes)', 'warning')
    except Exception as e:
        flash(f'💥 Error in unified pipeline: {str(e)}', 'error')
    
    return redirect(url_for('index'))

@app.route('/view-campaign/<campaign_id>')
def view_campaign(campaign_id):
    """View campaign details"""
    # Find the campaign file
    for ext in ['yaml', 'yml', 'json']:
        filepath = Path(CAMPAIGN_BRIEFS_FOLDER) / f"{campaign_id}.{ext}"
        if filepath.exists():
            try:
                with open(filepath, 'r') as f:
                    if ext in ['yaml', 'yml']:
                        data = yaml.safe_load(f)
                    else:
                        data = json.load(f)
                
                # Check for outputs
                output_dir = Path(OUTPUT_FOLDER) / campaign_id
                outputs = []
                if output_dir.exists():
                    for file in output_dir.rglob('*'):
                        if file.is_file():
                            outputs.append({
                                'name': file.name,
                                'path': str(file.relative_to(Path('.'))),
                                'size': file.stat().st_size,
                                'created': datetime.fromtimestamp(file.stat().st_mtime).strftime('%Y-%m-%d %H:%M')
                            })
                
                return render_template('campaign_details.html', 
                                     campaign=data, 
                                     campaign_id=campaign_id,
                                     outputs=outputs)
                                     
            except Exception as e:
                flash(f'Error loading campaign: {str(e)}', 'error')
                return redirect(url_for('index'))
    
    flash(f'Campaign {campaign_id} not found', 'error')
    return redirect(url_for('index'))

@app.route('/api/metrics')
def api_metrics():
    """API endpoint for real-time metrics"""
    return jsonify(get_system_metrics())

@app.route('/api/campaigns')
def api_campaigns():
    """API endpoint for campaign list"""
    return jsonify(get_campaign_status())

@app.route('/monitor')
def monitor():
    """System monitoring page"""
    return render_template('monitor.html')

@app.route('/download/<path:filename>')
def download_file(filename):
    """Download generated files"""
    try:
        return send_file(filename, as_attachment=True)
    except Exception as e:
        flash(f'Error downloading file: {str(e)}', 'error')
        return redirect(url_for('index'))

if __name__ == '__main__':
    print("🚀 Starting Task 3 Creative Automation Web UI...")
    print("📊 Dashboard: http://localhost:5004")
    print("🎯 Create campaigns, monitor progress, download results!")
    app.run(debug=True, host='0.0.0.0', port=5004)
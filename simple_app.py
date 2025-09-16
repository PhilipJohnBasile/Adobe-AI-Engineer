"""
SIMPLE Creative Automation System
For normal people who just want to:
1. Upload a campaign brief
2. Click a button
3. Get creative assets

No complexity, no quantum consciousness, just working automation.
"""
import os
import json
import yaml
from pathlib import Path
from datetime import datetime
from flask import Flask, render_template, request, redirect, url_for, flash, send_file
from werkzeug.utils import secure_filename
import uuid

app = Flask(__name__)
app.secret_key = 'simple_key'

# Simple config
UPLOAD_FOLDER = 'campaigns'
OUTPUT_FOLDER = 'generated'
Path(UPLOAD_FOLDER).mkdir(exist_ok=True)
Path(OUTPUT_FOLDER).mkdir(exist_ok=True)

def generate_creative_assets(campaign_data):
    """Simple creative generation (simulated)"""
    
    campaign_id = campaign_data.get('campaign_id', 'demo')
    products = campaign_data.get('products', ['Product'])
    
    # Create output folder
    output_dir = Path(OUTPUT_FOLDER) / campaign_id
    output_dir.mkdir(exist_ok=True)
    
    # Simulate generating assets
    generated_files = []
    
    for product in products:
        for ratio in ['1x1', '9x16', '16x9']:
            for i in range(1, 4):  # 3 variants per product per ratio
                filename = f"{product}_{ratio}_{i}.jpg"
                filepath = output_dir / filename
                
                # Create a simple text file as placeholder
                with open(filepath, 'w') as f:
                    f.write(f"Generated creative asset:\n")
                    f.write(f"Campaign: {campaign_data.get('campaign_name', 'Demo')}\n")
                    f.write(f"Product: {product}\n")
                    f.write(f"Aspect Ratio: {ratio}\n")
                    f.write(f"Variant: {i}\n")
                    f.write(f"Message: {campaign_data.get('campaign_message', 'Default message')}\n")
                
                generated_files.append(filename)
    
    return {
        'success': True,
        'files_generated': len(generated_files),
        'output_directory': str(output_dir),
        'files': generated_files
    }

@app.route('/')
def home():
    """Simple home page"""
    
    # Get existing campaigns
    campaigns = []
    for campaign_file in Path(UPLOAD_FOLDER).glob('*.json'):
        try:
            with open(campaign_file, 'r') as f:
                data = json.load(f)
                data['id'] = campaign_file.stem
                campaigns.append(data)
        except:
            pass
    
    return render_template('simple_home.html', campaigns=campaigns)

@app.route('/create', methods=['GET', 'POST'])
def create_campaign():
    """Create a new campaign"""
    
    if request.method == 'POST':
        # Get form data
        campaign_data = {
            'campaign_id': request.form.get('campaign_id') or f"campaign_{uuid.uuid4().hex[:8]}",
            'campaign_name': request.form.get('campaign_name', 'Untitled Campaign'),
            'products': [p.strip() for p in request.form.get('products', '').split(',') if p.strip()],
            'campaign_message': request.form.get('campaign_message', ''),
            'target_region': request.form.get('target_region', 'Global'),
            'created_at': datetime.now().isoformat()
        }
        
        # Save campaign
        campaign_file = Path(UPLOAD_FOLDER) / f"{campaign_data['campaign_id']}.json"
        with open(campaign_file, 'w') as f:
            json.dump(campaign_data, f, indent=2)
        
        flash(f"Campaign '{campaign_data['campaign_name']}' created successfully!", 'success')
        return redirect(url_for('home'))
    
    return render_template('simple_create.html')

@app.route('/generate/<campaign_id>')
def generate_campaign(campaign_id):
    """Generate assets for a campaign"""
    
    # Load campaign
    campaign_file = Path(UPLOAD_FOLDER) / f"{campaign_id}.json"
    if not campaign_file.exists():
        flash(f"Campaign {campaign_id} not found", 'error')
        return redirect(url_for('home'))
    
    try:
        with open(campaign_file, 'r') as f:
            campaign_data = json.load(f)
        
        # Generate assets
        result = generate_creative_assets(campaign_data)
        
        if result['success']:
            flash(f"✅ Generated {result['files_generated']} creative assets!", 'success')
            flash(f"📁 Files saved to: {result['output_directory']}", 'info')
        else:
            flash("❌ Generation failed", 'error')
            
    except Exception as e:
        flash(f"Error: {str(e)}", 'error')
    
    return redirect(url_for('home'))

@app.route('/view/<campaign_id>')
def view_campaign(campaign_id):
    """View campaign details and generated assets"""
    
    # Load campaign
    campaign_file = Path(UPLOAD_FOLDER) / f"{campaign_id}.json"
    if not campaign_file.exists():
        flash(f"Campaign {campaign_id} not found", 'error')
        return redirect(url_for('home'))
    
    with open(campaign_file, 'r') as f:
        campaign_data = json.load(f)
    
    # Check for generated files
    output_dir = Path(OUTPUT_FOLDER) / campaign_id
    generated_files = []
    if output_dir.exists():
        generated_files = [f.name for f in output_dir.iterdir() if f.is_file()]
    
    return render_template('simple_view.html', 
                         campaign=campaign_data, 
                         campaign_id=campaign_id,
                         generated_files=generated_files)

@app.route('/download/<campaign_id>/<filename>')
def download_file(campaign_id, filename):
    """Download a generated file"""
    
    file_path = Path(OUTPUT_FOLDER) / campaign_id / filename
    if file_path.exists():
        return send_file(file_path, as_attachment=True)
    else:
        flash("File not found", 'error')
        return redirect(url_for('view_campaign', campaign_id=campaign_id))

if __name__ == '__main__':
    print("🚀 Simple Creative Automation System")
    print("📍 Open: http://localhost:5000")
    print("💡 Just upload campaigns and generate assets!")
    app.run(debug=True, port=5000)
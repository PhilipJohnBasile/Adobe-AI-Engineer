#!/usr/bin/env python3
"""
Script to upgrade all campaign briefs to the comprehensive format
with brand guidelines, budget constraints, timeline, and detailed product info.
"""

import yaml
import json
from pathlib import Path
import sys
import random
from datetime import datetime, timedelta

def generate_brand_guidelines():
    """Generate realistic brand guidelines"""
    colors = [
        ['#007BFF', '#28A745', '#FFC107'],  # Blue, Green, Yellow
        ['#DC3545', '#6C757D', '#17A2B8'],  # Red, Gray, Cyan
        ['#E83E8C', '#20C997', '#FD7E14'],  # Pink, Teal, Orange
        ['#6F42C1', '#28A745', '#FFD700'],  # Purple, Green, Gold
        ['#495057', '#007BFF', '#F8F9FA']   # Dark Gray, Blue, Light Gray
    ]
    
    fonts = [
        ['Arial', 'Helvetica', 'Roboto'],
        ['Georgia', 'Times New Roman', 'Serif'],
        ['Montserrat', 'Open Sans', 'Lato'],
        ['Poppins', 'Inter', 'Source Sans Pro'],
        ['Playfair Display', 'Merriweather', 'Lora']
    ]
    
    tones = [
        'professional and authoritative',
        'friendly and approachable', 
        'luxury and sophisticated',
        'energetic and youthful',
        'trustworthy and reliable',
        'innovative and forward-thinking',
        'warm and inclusive',
        'bold and confident'
    ]
    
    return {
        'primary_colors': random.choice(colors),
        'fonts': random.choice(fonts),
        'tone': f"{random.choice(['high', 'medium', 'critical'])} campaign with {random.choice(tones)}"
    }

def generate_budget_constraints():
    """Generate realistic budget constraints"""
    priorities = {
        'high': {'limit': random.randint(15, 25), 'cost': random.randint(30, 50)},
        'medium': {'limit': random.randint(8, 15), 'cost': random.randint(15, 30)},
        'critical': {'limit': random.randint(25, 40), 'cost': random.randint(50, 100)}
    }
    
    priority = random.choice(['high', 'medium', 'critical'])
    constraints = priorities[priority]
    
    return {
        'generation_limit': constraints['limit'],
        'max_api_cost': float(constraints['cost'])
    }

def generate_timeline():
    """Generate realistic timeline"""
    priorities = ['critical', 'high', 'medium', 'low']
    priority = random.choice(priorities)
    
    # Generate future launch date
    days_ahead = random.randint(30, 180)
    launch_date = (datetime.now() + timedelta(days=days_ahead)).strftime('%Y-%m-%d')
    
    return {
        'launch_date': launch_date,
        'priority': priority,
        'rush_order': priority in ['critical', 'high']
    }

def generate_output_requirements():
    """Generate comprehensive output requirements"""
    qualities = ['premium', 'high', 'standard']
    formats = [
        ['JPG', 'PNG'],
        ['JPG', 'PNG', 'WEBP'],
        ['PNG'],
        ['JPG']
    ]
    
    aspect_ratios = [
        ['1:1', '9:16', '16:9'],
        ['1:1', '9:16'],
        ['16:9', '1:1'],
        ['1:1', '9:16', '16:9', '4:5']
    ]
    
    return {
        'aspect_ratios': random.choice(aspect_ratios),
        'formats': random.choice(formats),
        'quality': random.choice(qualities)
    }

def enhance_products(products):
    """Enhance basic products with detailed descriptions and keywords"""
    
    # Product enhancement database
    product_enhancements = {
        'premium_wireless_headphones': {
            'description': 'High-fidelity wireless headphones with active noise cancellation',
            'keywords': ['premium', 'wireless', 'noise-canceling', 'audio']
        },
        'eco-friendly_water_bottle': {
            'description': 'Sustainable stainless steel water bottle with temperature retention',
            'keywords': ['eco-friendly', 'sustainable', 'steel', 'insulated']
        },
        'smart_fitness_tracker': {
            'description': 'Advanced fitness tracking with heart rate and sleep monitoring',
            'keywords': ['fitness', 'smart', 'tracking', 'health']
        },
        'artisan_coffee_blend': {
            'description': 'Single-origin artisan coffee blend with rich flavor profile',
            'keywords': ['artisan', 'coffee', 'organic', 'premium']
        },
        'luxury_skincare_serum': {
            'description': 'Anti-aging luxury skincare serum with natural ingredients',
            'keywords': ['luxury', 'skincare', 'anti-aging', 'natural']
        },
        'biodegradable_phone_case': {
            'description': 'Eco-friendly biodegradable phone case with protective design',
            'keywords': ['biodegradable', 'eco-friendly', 'protective', 'sustainable']
        },
        'smart_watch_pro': {
            'description': 'Professional smartwatch with health monitoring and GPS',
            'keywords': ['smartwatch', 'professional', 'health', 'GPS']
        },
        'wireless_earbuds_elite': {
            'description': 'Elite wireless earbuds with premium sound quality',
            'keywords': ['wireless', 'earbuds', 'elite', 'premium']
        },
        'portable_charger_max': {
            'description': 'High-capacity portable charger for multiple devices',
            'keywords': ['portable', 'charger', 'high-capacity', 'devices']
        },
        'smart_watch_premium': {
            'description': 'Premium smartwatch with health monitoring and fitness tracking',
            'keywords': ['smartwatch', 'premium', 'health', 'fitness']
        }
    }
    
    enhanced_products = []
    for product in products:
        if isinstance(product, dict):
            # Already enhanced
            enhanced_products.append(product)
        else:
            # Simple string product name
            product_name = str(product).strip()
            product_key = product_name.lower().replace(' ', '_').replace('-', '_')
            
            if product_key in product_enhancements:
                enhancement = product_enhancements[product_key]
            else:
                # Generate generic enhancement
                enhancement = {
                    'description': f'Premium {product_name.lower()} with advanced features',
                    'keywords': [w.lower() for w in product_name.split()[:3]] + ['premium']
                }
            
            enhanced_products.append({
                'name': product_name,
                'description': enhancement['description'],
                'target_keywords': enhancement['keywords']
            })
    
    return enhanced_products

def upgrade_campaign_brief(file_path):
    """Upgrade a single campaign brief to comprehensive format"""
    try:
        # Read the file
        with open(file_path, 'r', encoding='utf-8') as f:
            if file_path.suffix.lower() == '.json':
                data = json.load(f)
            else:
                data = yaml.safe_load(f)
        
        # Skip malformed files
        if not data or 'campaign_brief' not in data:
            print(f"⚠️  Skipping {file_path.name} - no campaign_brief found")
            return False
            
        campaign_brief = data['campaign_brief']
        
        # Check if already comprehensive (has brand_guidelines)
        if 'brand_guidelines' in campaign_brief:
            print(f"✅ {file_path.name} - already comprehensive")
            return False
        
        # Enhance the campaign brief
        print(f"🔄 Upgrading {file_path.name} to comprehensive format...")
        
        # Add brand guidelines
        campaign_brief['brand_guidelines'] = generate_brand_guidelines()
        
        # Add budget constraints
        campaign_brief['budget_constraints'] = generate_budget_constraints()
        
        # Add timeline
        campaign_brief['timeline'] = generate_timeline()
        
        # Enhance output requirements
        if 'output_requirements' not in campaign_brief:
            campaign_brief['output_requirements'] = generate_output_requirements()
        else:
            # Enhance existing requirements
            existing = campaign_brief['output_requirements']
            enhanced = generate_output_requirements()
            campaign_brief['output_requirements'] = {
                'aspect_ratios': existing.get('aspect_ratios', enhanced['aspect_ratios']),
                'formats': existing.get('formats', enhanced['formats']),
                'quality': enhanced['quality']
            }
        
        # Enhance products
        if 'products' in campaign_brief:
            campaign_brief['products'] = enhance_products(campaign_brief['products'])
        
        # Enhance target audience if simple
        if 'target_audience' in campaign_brief:
            audience = campaign_brief['target_audience']
            if isinstance(audience, str) and len(audience.split()) < 4:
                # Enhance simple audience
                priorities = ['high priority', 'medium priority', 'critical priority']
                ages = ['18-35', '25-45', '35-55', '18-65']
                campaign_brief['target_audience'] = f"{random.choice(priorities)} customers aged {random.choice(ages)}"
        
        # Write back to file
        with open(file_path, 'w', encoding='utf-8') as f:
            if file_path.suffix.lower() == '.json':
                json.dump(data, f, indent=2, ensure_ascii=False)
            else:
                yaml.dump(data, f, default_flow_style=False, allow_unicode=True, sort_keys=False)
                
        print(f"✅ {file_path.name} - upgraded successfully")
        return True
        
    except Exception as e:
        print(f"❌ Error processing {file_path.name}: {e}")
        return False

def main():
    """Main function to upgrade all campaign briefs"""
    campaign_briefs_dir = Path('campaign_briefs')
    
    if not campaign_briefs_dir.exists():
        print("❌ campaign_briefs directory not found")
        sys.exit(1)
        
    print("🚀 Upgrading campaign briefs to comprehensive format...")
    print("=" * 70)
    
    files_processed = 0
    files_upgraded = 0
    
    # Process all YAML and JSON files
    for pattern in ['*.yaml', '*.yml', '*.json']:
        for file_path in campaign_briefs_dir.glob(pattern):
            files_processed += 1
            if upgrade_campaign_brief(file_path):
                files_upgraded += 1
                
    print("=" * 70)
    print(f"📊 Summary:")
    print(f"   Files processed: {files_processed}")
    print(f"   Files upgraded: {files_upgraded}")
    print(f"   Files skipped: {files_processed - files_upgraded}")
    
    if files_upgraded > 0:
        print("✅ Campaign briefs have been upgraded to comprehensive format!")
        print("🎯 Enhanced features:")
        print("   • Brand guidelines (colors, fonts, tone)")
        print("   • Budget constraints (generation limits, API costs)")
        print("   • Timeline (launch dates, priority, rush orders)")
        print("   • Enhanced product descriptions with keywords")
        print("   • Comprehensive output requirements")
    else:
        print("ℹ️  No files needed upgrading.")

if __name__ == '__main__':
    main()
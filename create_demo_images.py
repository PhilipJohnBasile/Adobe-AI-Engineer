#!/usr/bin/env python3
"""
Create demo images for testing the brand intelligence system.
"""

import os
from PIL import Image, ImageDraw, ImageFont
import numpy as np

def create_demo_image(filename, width=512, height=512, colors=None, text="DEMO"):
    """Create a simple demo image with specified colors."""
    if colors is None:
        colors = [(255, 100, 100), (100, 255, 100), (100, 100, 255)]
    
    # Create base image
    img = Image.new('RGB', (width, height), color=colors[0])
    draw = ImageDraw.Draw(img)
    
    # Add some geometric shapes with different colors
    draw.rectangle([50, 50, width-50, height-50], fill=colors[1])
    draw.ellipse([100, 100, width-100, height-100], fill=colors[2])
    
    # Add text
    try:
        font = ImageFont.truetype("Arial.ttf", 48)
    except (OSError, IOError):
        font = ImageFont.load_default()
    
    bbox = draw.textbbox((0, 0), text, font=font)
    text_width = bbox[2] - bbox[0]
    text_height = bbox[3] - bbox[1]
    text_x = (width - text_width) // 2
    text_y = (height - text_height) // 2
    
    draw.text((text_x, text_y), text, fill=(255, 255, 255), font=font)
    
    # Save image
    img.save(filename)
    print(f"Created demo image: {filename}")

def main():
    """Create various demo images for testing."""
    os.makedirs("demo_images", exist_ok=True)
    
    # High quality image
    create_demo_image("demo_images/high_quality.png", 1024, 1024, 
                     [(70, 130, 180), (255, 215, 0), (220, 20, 60)], "HIGH QUALITY")
    
    # Low quality image (smaller, with noise)
    img = Image.new('RGB', (256, 256), color=(100, 100, 100))
    # Add noise
    noise = np.random.randint(0, 50, (256, 256, 3))
    img_array = np.array(img)
    noisy_img = Image.fromarray(np.clip(img_array + noise, 0, 255).astype(np.uint8))
    draw = ImageDraw.Draw(noisy_img)
    draw.text((50, 128), "LOW QUALITY", fill=(255, 255, 255))
    noisy_img.save("demo_images/low_quality.png")
    print("Created demo image: demo_images/low_quality.png")
    
    # Brand consistent image
    create_demo_image("demo_images/brand_consistent.png", 512, 512,
                     [(0, 123, 191), (255, 184, 28), (108, 117, 125)], "BRAND A")
    
    # Different brand image
    create_demo_image("demo_images/different_brand.png", 512, 512,
                     [(255, 69, 0), (0, 191, 255), (50, 205, 50)], "BRAND B")

if __name__ == "__main__":
    main()
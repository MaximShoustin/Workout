#!/usr/bin/env python3
"""
Helper script to resize images before converting to base64.
Usage: python3 resize_image.py <input_image> <output_image> <max_size>
"""

import sys
from pathlib import Path

try:
    from PIL import Image
    PIL_AVAILABLE = True
except ImportError:
    PIL_AVAILABLE = False

def resize_image(input_path, output_path, max_size=32):
    """Resize image to max_size x max_size pixels while maintaining aspect ratio."""
    if not PIL_AVAILABLE:
        print("PIL (Pillow) is required for image resizing.")
        print("Install it with: pip install Pillow")
        return False
    
    try:
        with Image.open(input_path) as img:
            # Convert to RGBA to ensure transparency support
            if img.mode != 'RGBA':
                img = img.convert('RGBA')
            
            # Calculate new size maintaining aspect ratio
            img.thumbnail((max_size, max_size), Image.Resampling.LANCZOS)
            
            # Save the resized image
            img.save(output_path, 'PNG', optimize=True)
            print(f"✅ Resized image saved as: {output_path}")
            print(f"   Original size: {Path(input_path).stat().st_size} bytes")
            print(f"   New size: {Path(output_path).stat().st_size} bytes")
            return True
            
    except Exception as e:
        print(f"Error resizing image: {e}")
        return False

if __name__ == "__main__":
    if len(sys.argv) < 3:
        print("Usage: python3 resize_image.py <input_image> <output_image> [max_size]")
        print("Example: python3 resize_image.py dumbbell.png dumbbell_small.png 24")
        sys.exit(1)
    
    input_path = sys.argv[1]
    output_path = sys.argv[2]
    max_size = int(sys.argv[3]) if len(sys.argv) > 3 else 32
    
    if not PIL_AVAILABLE:
        print("PIL (Pillow) is not installed. Please install it with:")
        print("pip install Pillow")
        sys.exit(1)
    
    resize_image(input_path, output_path, max_size) 
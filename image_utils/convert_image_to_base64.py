#!/usr/bin/env python3
"""
Helper script to convert images to base64 for embedding in HTML.
Usage: python3 convert_image_to_base64.py <image_path>
"""

import base64
import sys
from pathlib import Path

def convert_image_to_base64(image_path):
    """Convert an image file to base64 string."""
    try:
        with open(image_path, 'rb') as image_file:
            # Read and encode the image
            base64_string = base64.b64encode(image_file.read()).decode('utf-8')
            
            # Get file extension to determine image type
            file_extension = Path(image_path).suffix.lower()
            if file_extension in ['.jpg', '.jpeg']:
                mime_type = 'image/jpeg'
            elif file_extension == '.png':
                mime_type = 'image/png'
            elif file_extension == '.gif':
                mime_type = 'image/gif'
            elif file_extension == '.webp':
                mime_type = 'image/webp'
            else:
                mime_type = 'image/png'  # Default
            
            print(f"Image: {image_path}")
            print(f"Size: {len(base64_string)} characters")
            print(f"MIME Type: {mime_type}")
            print("\n" + "="*50)
            print("BASE64 STRING (copy this):")
            print("="*50)
            print(base64_string)
            print("="*50)
            
            # Also show how to use it
            print(f"\nTo use this in your HTML generator, replace:")
            print(f'    "dumbbell": None,')
            print(f"with:")
            print(f'    "dumbbell": "{base64_string}",')
            
            return base64_string
            
    except FileNotFoundError:
        print(f"Error: Image file '{image_path}' not found.")
        return None
    except Exception as e:
        print(f"Error converting image: {e}")
        return None

if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: python3 convert_image_to_base64.py <image_path>")
        print("Example: python3 convert_image_to_base64.py dumbbell.png")
        sys.exit(1)
    
    image_path = sys.argv[1]
    convert_image_to_base64(image_path) 
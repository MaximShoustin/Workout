#!/usr/bin/env python3
"""
Create a simple SVG dumbbell icon for demonstration.
"""

import base64

# Simple SVG dumbbell icon
svg_content = '''<svg width="24" height="24" viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg">
  <defs>
    <linearGradient id="metalGrad" x1="0%" y1="0%" x2="100%" y2="100%">
      <stop offset="0%" style="stop-color:#e8e8e8;stop-opacity:1" />
      <stop offset="50%" style="stop-color:#c0c0c0;stop-opacity:1" />
      <stop offset="100%" style="stop-color:#a0a0a0;stop-opacity:1" />
    </linearGradient>
  </defs>
  
  <!-- Left weight -->
  <ellipse cx="4" cy="12" rx="3" ry="6" fill="url(#metalGrad)" stroke="#808080" stroke-width="0.5"/>
  
  <!-- Handle -->
  <rect x="7" y="10.5" width="10" height="3" rx="1.5" fill="url(#metalGrad)" stroke="#808080" stroke-width="0.5"/>
  
  <!-- Right weight -->
  <ellipse cx="20" cy="12" rx="3" ry="6" fill="url(#metalGrad)" stroke="#808080" stroke-width="0.5"/>
  
  <!-- Handle grip lines -->
  <line x1="9" y1="11" x2="9" y2="13" stroke="#909090" stroke-width="0.3"/>
  <line x1="11" y1="11" x2="11" y2="13" stroke="#909090" stroke-width="0.3"/>
  <line x1="13" y1="11" x2="13" y2="13" stroke="#909090" stroke-width="0.3"/>
  <line x1="15" y1="11" x2="15" y2="13" stroke="#909090" stroke-width="0.3"/>
</svg>'''

# Convert SVG to base64
svg_base64 = base64.b64encode(svg_content.encode('utf-8')).decode('utf-8')

print("Simple SVG Dumbbell Icon Created!")
print("="*50)
print("Base64 string for testing:")
print("="*50)
print(svg_base64)
print("="*50)

# Save the SVG file too
with open('simple_dumbbell.svg', 'w') as f:
    f.write(svg_content)

print("\nSimple dumbbell SVG saved as 'simple_dumbbell.svg'")
print("You can open it in a browser to see how it looks!")
print("\nTo use this in your HTML generator temporarily, replace:")
print('    "dumbbell": None,')
print("with:")
print(f'    "dumbbell": "{svg_base64}",')
print("\nNote: For SVG, you'd need to change the image format to 'image/svg+xml'") 
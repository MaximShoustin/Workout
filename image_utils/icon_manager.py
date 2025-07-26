#!/usr/bin/env python3
"""
Icon management system for workout equipment SVG icons.
Automatically loads and converts SVG files to base64 for HTML embedding.
"""

import base64
from pathlib import Path
from typing import Dict, Optional

ICONS_DIR = Path(__file__).parent / "icons"

# Cache for loaded icons to avoid repeated file I/O
_icon_cache = None

def load_svg_icons() -> Dict[str, str]:
    """Load all SVG icons from the icons directory and convert to base64."""
    global _icon_cache
    
    # Return cached icons if available
    if _icon_cache is not None:
        return _icon_cache
    
    icons = {}
    
    if not ICONS_DIR.exists():
        print(f"⚠️  Icons directory {ICONS_DIR} not found")
        _icon_cache = icons
        return icons
    
    svg_files = list(ICONS_DIR.glob("*.svg"))
    if not svg_files:
        print(f"⚠️  No SVG files found in {ICONS_DIR}")
        _icon_cache = icons
        return icons
    
    print(f"📁 Loading {len(svg_files)} SVG icons from {ICONS_DIR}")
    
    for svg_file in svg_files:
        try:
            # Use filename without extension as the equipment type
            equipment_type = svg_file.stem.lower()
            
            # Read and encode the SVG
            with open(svg_file, 'r', encoding='utf-8') as f:
                svg_content = f.read()
            
            # Convert to base64
            base64_string = base64.b64encode(svg_content.encode('utf-8')).decode('utf-8')
            icons[equipment_type] = base64_string
            
            print(f"   ✅ {equipment_type}: {svg_file.name}")
            
        except Exception as e:
            print(f"   ❌ Failed to load {svg_file.name}: {e}")
    
    print(f"📋 Loaded {len(icons)} icons: {', '.join(icons.keys())}")
    
    # Cache the loaded icons
    _icon_cache = icons
    return icons

def get_equipment_icon_html(equipment_name: str, size: str = "20px") -> Optional[str]:
    """Get HTML img tag for equipment icon if available."""
    icons = load_svg_icons()
    equipment_lower = equipment_name.lower()
    
    # Try direct match first
    if equipment_lower in icons:
        base64_data = icons[equipment_lower]
        return f'<img src="data:image/svg+xml;base64,{base64_data}" alt="{equipment_lower}" style="width:{size};height:{size};vertical-align:middle;margin-right:4px;">'
    
    # Try partial matches for compound names
    for icon_name, base64_data in icons.items():
        if icon_name in equipment_lower:
            return f'<img src="data:image/svg+xml;base64,{base64_data}" alt="{icon_name}" style="width:{size};height:{size};vertical-align:middle;margin-right:4px;">'
    
    return None

def list_available_icons():
    """List all available icons."""
    icons = load_svg_icons()
    if icons:
        print("Available equipment icons:")
        for equipment_type in sorted(icons.keys()):
            svg_file = ICONS_DIR / f"{equipment_type}.svg"
            file_size = svg_file.stat().st_size if svg_file.exists() else 0
            print(f"  • {equipment_type:<15} ({file_size:,} bytes)")
    else:
        print("No icons available")

def create_icon_template(equipment_name: str, color: str = "#808080"):
    """Create a basic SVG template for new equipment."""
    template = f'''<svg width="24" height="24" viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg">
  <defs>
    <linearGradient id="grad_{equipment_name}" x1="0%" y1="0%" x2="100%" y2="100%">
      <stop offset="0%" style="stop-color:#e8e8e8;stop-opacity:1" />
      <stop offset="50%" style="stop-color:{color};stop-opacity:1" />
      <stop offset="100%" style="stop-color:#606060;stop-opacity:1" />
    </linearGradient>
  </defs>
  
  <!-- Add your {equipment_name} shape here -->
  <rect x="6" y="6" width="12" height="12" rx="2" fill="url(#grad_{equipment_name})" stroke="#404040" stroke-width="0.5"/>
  <text x="12" y="15" text-anchor="middle" font-family="Arial" font-size="8" fill="white">{equipment_name[:2].upper()}</text>
</svg>'''
    
    output_path = ICONS_DIR / f"{equipment_name.lower()}.svg"
    with open(output_path, 'w') as f:
        f.write(template)
    
    print(f"📝 Created template icon: {output_path}")
    print(f"   Edit the SVG to customize the {equipment_name} appearance")

if __name__ == "__main__":
    import sys
    
    if len(sys.argv) > 1:
        command = sys.argv[1]
        if command == "list":
            list_available_icons()
        elif command == "create" and len(sys.argv) > 2:
            equipment_name = sys.argv[2]
            color = sys.argv[3] if len(sys.argv) > 3 else "#808080"
            create_icon_template(equipment_name, color)
        else:
            print("Usage:")
            print("  python3 icon_manager.py list                    # List available icons")
            print("  python3 icon_manager.py create <name> [color]   # Create template icon")
    else:
        list_available_icons() 
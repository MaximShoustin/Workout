#!/usr/bin/env python3
"""
Create SVG icon templates for missing equipment types.
"""

from icon_manager import create_icon_template, list_available_icons
from pathlib import Path

# Common equipment types and their colors
EQUIPMENT_TEMPLATES = {
    "dip_parallel_bars": "#2C5AA0",  # Blue
    "medicine_ball": "#8B0000",     # Dark red
    "resistance_band": "#FFD700",   # Gold
    "pull_up_bar": "#4A4A4A",       # Dark gray
    "foam_roller": "#00CED1",       # Dark turquoise
    "yoga_mat": "#9370DB",          # Medium purple
    "battle_rope": "#8B4513",       # Saddle brown
    "suspension_trainer": "#FF4500", # Orange red
    "step_platform": "#32CD32",     # Lime green
    "agility_ladder": "#FF69B4",    # Hot pink
}

def create_all_templates():
    """Create templates for all equipment types."""
    icons_dir = Path("icons")
    existing_icons = set()
    
    if icons_dir.exists():
        existing_icons = {f.stem.lower() for f in icons_dir.glob("*.svg")}
    
    print("🎨 Creating SVG templates for missing equipment icons...")
    print(f"📁 Existing icons: {', '.join(sorted(existing_icons))}")
    print()
    
    created_count = 0
    for equipment, color in EQUIPMENT_TEMPLATES.items():
        if equipment.lower() not in existing_icons:
            print(f"📝 Creating template for: {equipment}")
            create_icon_template(equipment, color)
            created_count += 1
        else:
            print(f"✅ Already exists: {equipment}")
    
    print()
    if created_count > 0:
        print(f"🎉 Created {created_count} new icon templates!")
        print("💡 Edit the SVG files in the icons/ directory to customize their appearance")
        print("🔄 Templates use placeholder shapes - replace with actual equipment designs")
    else:
        print("✨ All equipment types already have icons!")

def show_usage():
    """Show usage examples."""
    print("Usage examples:")
    print("  python3 create_missing_icons.py                    # Create all missing templates")
    print("  python3 icon_manager.py create barbell '#9B59B6'   # Create specific template")
    print("  python3 icon_manager.py list                       # List existing icons")

if __name__ == "__main__":
    import sys
    
    if len(sys.argv) > 1 and sys.argv[1] in ["help", "--help", "-h"]:
        show_usage()
    else:
        create_all_templates()
        print()
        print("📋 Current icon status:")
        list_available_icons() 
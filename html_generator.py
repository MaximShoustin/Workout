#!/usr/bin/env python3
"""HTML generation and formatting for workout reports."""

from datetime import datetime
from typing import Dict, List, Optional


def format_exercise_link(exercise_name: str, exercise_link: str, exercise_id: int = None, pictures_path: str = "config/pictures") -> str:
    """Format exercise with embedded video popup if valid URL provided, otherwise return plain name. Show ID if provided."""
    from pathlib import Path
    
    display_name = exercise_name
    
    # Check if picture exists (using exercise ID)
    has_picture = False
    picture_path = ""
    if exercise_id is not None and exercise_id != -1:
        # Use absolute path for file existence check
        absolute_picture_path = Path("config/pictures") / f"{exercise_id}.png"
        has_picture = absolute_picture_path.exists()
        # Use relative path for HTML src attribute
        picture_path = f"{pictures_path}/{exercise_id}.png"
    
    # Original video functionality - keep exactly the same
    if exercise_link and exercise_link != "some url" and exercise_link.strip():
        # Convert YouTube URLs to embed format with autoplay (muted to bypass browser restrictions)
        embed_url = exercise_link
        autoplay_params = "autoplay=1&mute=1&enablejsapi=1&modestbranding=1&rel=0"
        if "youtube.com/watch?v=" in exercise_link:
            video_id = exercise_link.split("watch?v=")[1].split("&")[0]
            embed_url = f"https://www.youtube.com/embed/{video_id}?{autoplay_params}"
        elif "youtube.com/shorts/" in exercise_link:
            video_id = exercise_link.split("/shorts/")[1].split("?")[0]
            embed_url = f"https://www.youtube.com/embed/{video_id}?{autoplay_params}"
        elif "youtu.be/" in exercise_link:
            video_id = exercise_link.split("youtu.be/")[1].split("?")[0]
            embed_url = f"https://www.youtube.com/embed/{video_id}?{autoplay_params}"
        
        # Create unique ID for this exercise
        html_id = exercise_name.lower().replace(" ", "_").replace("-", "_").replace("+", "plus").replace("→", "to")
        
        # Original video HTML + new picture button if available
        video_html = f'''<span class="exercise-with-video">
            <span class="exercise-name" onclick="toggleVideo('{html_id}')">{display_name}</span>
            <div id="video_{html_id}" class="video-popup">
                <iframe src="{embed_url}" frameborder="0" allowfullscreen></iframe>
                <button class="close-video" onclick="toggleVideo('{html_id}')">&times;</button>
            </div>'''
        
        # Add picture button if picture exists
        if has_picture:
            video_html += f'''
            <button class="picture-button" onclick="togglePicture('{html_id}')" title="View exercise image">
                👁
            </button>
            <div id="picture_{html_id}" class="picture-popup">
                <img src="{picture_path}" alt="{exercise_name}" onerror="handleImageError(this)" />
                <button class="close-picture" onclick="togglePicture('{html_id}')">&times;</button>
            </div>'''
        
        video_html += '</span>'
        return video_html
    else:
        # No video, but check if there's a picture
        if has_picture:
            html_id = exercise_name.lower().replace(" ", "_").replace("-", "_").replace("+", "plus").replace("→", "to")
            return f'''<span class="exercise-with-picture">
                {display_name}
                <button class="picture-button" onclick="togglePicture('{html_id}')" title="View exercise image">
                    👁
                </button>
                <div id="picture_{html_id}" class="picture-popup">
                    <img src="{picture_path}" alt="{exercise_name}" onerror="handleImageError(this)" />
                    <button class="close-picture" onclick="togglePicture('{html_id}')">&times;</button>
                </div>
            </span>'''
        else:
            return display_name


def format_exercise_id_badge(exercise_id: int) -> str:
    if exercise_id is not None and exercise_id != -1:
        return f'<span class="exercise-id-badge">{exercise_id}</span>'
    return ''


def get_equipment_icon(equipment_name: str) -> str:
    """Get appropriate icon for equipment type - SVG icon or emoji fallback."""
    from image_utils.icon_manager import get_equipment_icon_html
    
    equipment_lower = equipment_name.lower()
    
    # Try to get SVG icon first
    svg_icon = get_equipment_icon_html(equipment_lower)
    if svg_icon:
        return svg_icon
    
    # Fallback to emoji icons
    if "barbell" in equipment_lower:
        return "🏋️"
    elif "dumbbell" in equipment_lower:
        return "💪"
    elif "kettlebell" in equipment_lower:
        return "⚡"
    elif "bench" in equipment_lower:
        return "┬─┬"
    elif "plyo" in equipment_lower or "box" in equipment_lower:
        return "📦"
    elif "slam" in equipment_lower and "ball" in equipment_lower:
        return "⚫"
    elif "dip" in equipment_lower and "parallel" in equipment_lower:
        return "🤸"
    else:
        return "🏋️‍♂️"  # Default gym equipment icon


def format_equipment_tags(equipment_data: Dict) -> str:
    """Format equipment requirements as colored tags."""
    if not equipment_data:
        return ""
    
    tags_html = '<div class="equipment-tags">'
    
    for equipment_type, equipment_info in equipment_data.items():
        count = equipment_info.get("count", 1)
        
        # Determine tag color class based on equipment type
        if "kettlebell" in equipment_type.lower():
            tag_class = "tag-kettlebells"
        elif "dumbbell" in equipment_type.lower():
            tag_class = "tag-dumbbells"
        elif "barbell" in equipment_type.lower():
            tag_class = "tag-barbells"
        elif "bench" in equipment_type.lower():
            tag_class = "tag-bench"
        elif "plyo" in equipment_type.lower() or "box" in equipment_type.lower():
            tag_class = "tag-plyo"
        elif "slam" in equipment_type.lower():
            tag_class = "tag-slam"
        elif "dip" in equipment_type.lower():
            tag_class = "tag-dip"
        else:
            tag_class = "tag-default"
        
        # Format equipment name (e.g., "kettlebells_16kg" -> "kettlebell 16 kg")
        display_name = equipment_type.replace("_", " ").replace("kg", " kg")
        display_name = display_name.replace("dumbbells", "dumbbell").replace("kettlebells", "kettlebell")
        display_name = display_name.replace("slam balls", "slam ball")
        
        # Get equipment icon
        equipment_icon = get_equipment_icon(equipment_type)
        
        # Create tag with count and icon
        if count > 1:
            tag_text = f"{equipment_icon} {display_name} x{count}"
        else:
            tag_text = f"{equipment_icon} {display_name}"
            
        tags_html += f'<span class="equipment-tag {tag_class}">{tag_text}</span>'
    
    tags_html += '</div>'
    return tags_html


def format_muscle_tags(muscles_str: str) -> str:
    """Format muscle groups as colored tags."""
    if not muscles_str or not muscles_str.strip():
        return ""
    
    tags_html = '<div class="muscle-tags">'
    
    # Split muscles by comma and clean up
    muscles = [muscle.strip().lower() for muscle in muscles_str.split(",") if muscle.strip()]
    
    for muscle in muscles:
        # Determine tag color class based on muscle group
        if muscle in ["chest", "pecs", "pectorals"]:
            tag_class = "muscle-chest"
        elif muscle in ["back", "lats", "rhomboids", "traps"]:
            tag_class = "muscle-back"
        elif muscle in ["shoulders", "delts", "deltoids"]:
            tag_class = "muscle-shoulders"
        elif muscle in ["biceps", "bicep"]:
            tag_class = "muscle-biceps"
        elif muscle in ["triceps", "tricep"]:
            tag_class = "muscle-triceps"
        elif muscle in ["legs", "quads", "quadriceps", "hamstrings", "calves", "glutes"]:
            tag_class = "muscle-legs"
        elif muscle in ["core", "abs", "abdominals", "obliques"]:
            tag_class = "muscle-core"
        else:
            tag_class = "muscle-other"
        
        tags_html += f'<span class="muscle-tag {tag_class}">{muscle.title()}</span>'
    
    tags_html += '</div>'
    return tags_html


def analyze_workout_distribution(stations: List[Dict]) -> Dict[str, any]:
    """Analyze the movement type and muscle distribution in the current workout using precise area and muscle data."""
    from collections import defaultdict
    
    # Initialize counters
    area_counts = defaultdict(int)
    muscle_counts = defaultdict(int)
    station_areas = defaultdict(int)
    
    total_exercises = 0
    
    # Analyze each exercise in the workout using precise data
    for station in stations:
        station_area = station.get('area', 'unknown')
        station_areas[station_area] += 1
        
        # Check all step exercises (dynamically determine number of steps)
        step_num = 1
        while f'step{step_num}' in station:
            step_key = f'step{step_num}'
            step_muscles_key = f'step{step_num}_muscles'
            
            if step_key in station:
                # Get area from station (since all exercises in a station target the same area)
                area = station_area
                area_counts[area] += 1
                total_exercises += 1
                
                # Get muscle data
                muscles_str = station.get(step_muscles_key, '')
                if muscles_str:
                    # Parse individual muscles
                    muscles = [muscle.strip().lower() for muscle in muscles_str.split(",") if muscle.strip()]
                    for muscle in muscles:
                        muscle_counts[muscle] += 1
            
            step_num += 1
    
    # Categorize muscles into groups for better visualization
    muscle_groups = {
        "Chest": ["chest", "pecs", "pectorals"],
        "Back": ["back", "lats", "rhomboids", "traps"],
        "Shoulders": ["shoulders", "delts", "deltoids"],
        "Arms": ["biceps", "triceps", "forearms"],
        "Legs": ["legs", "quads", "quadriceps", "hamstrings", "calves", "glutes"],
        "Core": ["core", "abs", "abdominals", "obliques"]
    }
    
    # Group muscle counts
    grouped_muscles = defaultdict(int)
    for muscle, count in muscle_counts.items():
        grouped = False
        for group_name, group_muscles in muscle_groups.items():
            if muscle in group_muscles:
                grouped_muscles[group_name] += count
                grouped = True
                break
        if not grouped:
            grouped_muscles["Other"] += count
    
    return {
        "area_distribution": dict(area_counts),
        "muscle_distribution": dict(muscle_counts),
        "grouped_muscles": dict(grouped_muscles),
        "station_areas": dict(station_areas),
        "total_exercises": total_exercises
    }


def generate_html_workout(plan: Dict, stations: List[Dict], equipment_requirements: Optional[Dict] = None, validation_summary: Optional[Dict] = None, global_active_rest_schedule: Optional[List[Dict]] = None, selected_active_rest_exercises: Optional[List[Dict]] = None, selected_warm_up_exercises: Optional[List[Dict]] = None, is_workout_store: bool = False) -> str:
    """Generate a styled HTML workout plan."""
    title = plan.get("title", "Station Map")
    notes = plan.get("notes", "")
    work = plan["timing"]["work"]
    rest = plan["timing"]["rest"]
    steps_per_station = plan.get('steps_per_station', 2)
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    css = """
    <style>
        body { 
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; 
            line-height: 1.6; 
            color: #333; 
            max-width: 1200px; 
            margin: 0 auto; 
            padding: 20px;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            min-height: 100vh;
        }
        .container {
            background: white;
            border-radius: 15px;
            padding: 30px;
            box-shadow: 0 10px 30px rgba(0,0,0,0.3);
        }
        h1 { 
            color: #2c3e50; 
            text-align: center; 
            margin-bottom: 10px;
            font-size: 2.5em;
            font-weight: 300;
        }
        .subtitle { 
            text-align: center; 
            color: #7f8c8d; 
            font-style: italic; 
            margin-bottom: 30px;
        }
        .notes {
            background: #ecf0f1;
            padding: 15px;
            border-left: 4px solid #3498db;
            margin-bottom: 25px;
            border-radius: 5px;
        }
        table { 
            width: 100%; 
            border-collapse: collapse; 
            margin: 20px 0;
            background: white;
            border-radius: 10px;
            overflow: hidden;
            box-shadow: 0 5px 15px rgba(0,0,0,0.1);
        }
        th { 
            background: linear-gradient(135deg, #3498db, #2980b9);
            color: white; 
            padding: 15px; 
            text-align: left;
            font-weight: 600;
            font-size: 0.9em;
            text-transform: uppercase;
            letter-spacing: 1px;
            white-space: nowrap;
        }
        td { 
            padding: 15px; 
            border-bottom: 1px solid #ecf0f1;
            vertical-align: top;
        }
        tr:nth-child(even) { 
            background: #f8f9fa; 
        }
        tr:hover {
            background: #e3f2fd;
            transition: all 0.3s ease;
        }
        .station-letter { 
            font-weight: bold; 
            font-size: 1.2em;
            color: #2980b9;
            display: block;
            text-align: center;
        }
        .area-badge {
            display: block;
            padding: 5px 12px;
            border-radius: 20px;
            font-size: 0.85em;
            font-weight: 600;
            text-transform: uppercase;
            color: white;
            text-align: center;
            margin: 0 auto;
            width: fit-content;
        }
        .upper { background: #e74c3c; }
        .lower { background: #27ae60; }
        .core { background: #f39c12; }
        .active-rest { background: #28a745; }
        .exercise {
            font-weight: 500;
            margin-bottom: 3px;
            position: relative;
        }
        .exercise-with-video {
            position: relative;
            display: inline-block;
        }
        .exercise-name {
            color: #2980b9;
            cursor: pointer;
            text-decoration: none;
            border-bottom: 1px dotted #2980b9;
            transition: all 0.3s ease;
        }
        .exercise-name:hover {
            color: #e74c3c;
            border-bottom: 1px solid #e74c3c;
            background: rgba(231, 76, 60, 0.1);
            padding: 2px 4px;
            border-radius: 3px;
        }
        .video-popup {
            display: none;
            position: absolute;
            top: 0;
            left: 100%;
            margin-left: 20px;
            width: 240px;
            height: 360px;
            background: white;
            border: 2px solid #2980b9;
            border-radius: 8px;
            box-shadow: 0 8px 25px rgba(0,0,0,0.3);
            z-index: 1000;
            overflow: hidden;
        }
        
        /* Fix video positioning in Global Active Rest section */
        .active-rest-section .video-popup {
            position: fixed !important;
            top: 50% !important;
            left: 50% !important;
            transform: translate(-50%, -50%) !important;
            margin: 0 !important;
            z-index: 10000 !important;
        }
        .video-popup iframe {
            width: 100%;
            height: calc(100% - 35px);
            border: none;
        }
        .close-video {
            position: absolute;
            bottom: 5px;
            right: 10px;
            background: #e74c3c;
            color: white;
            border: none;
            width: 25px;
            height: 25px;
            border-radius: 50%;
            cursor: pointer;
            font-size: 16px;
            line-height: 1;
            z-index: 1001;
        }
        .close-video:hover {
            background: #c0392b;
        }
        
        /* Picture button and popup styles */
        .picture-button {
            margin-left: 8px;
            background: #2ecc71;
            color: white;
            border: none;
            border-radius: 4px;
            width: 24px;
            height: 24px;
            font-size: 14px;
            cursor: pointer;
            display: inline-flex;
            align-items: center;
            justify-content: center;
            vertical-align: middle;
            position: relative;
            z-index: 10;
            flex-shrink: 0;
        }
        .picture-button:hover {
            background: #27ae60;
        }

        
        /* Exercise cell wrapper for better layout */
        .exercise-cell-wrapper {
            display: flex;
            align-items: center;
            gap: 4px;
            flex-wrap: wrap;
            min-height: 28px;
        }
        .picture-popup {
            display: none;
            position: absolute;
            top: 0;
            left: 100%;
            margin-left: 20px;
            width: 400px;
            height: 300px;
            max-width: 400px;
            max-height: 500px;
            min-width: 200px;
            min-height: 150px;
            background: white;
            border: 2px solid #2ecc71;
            border-radius: 8px;
            box-shadow: 0 4px 15px rgba(0,0,0,0.3);
            z-index: 1000;
            overflow: hidden;
        }
        .picture-popup img {
            width: 100%;
            height: 100%;
            object-fit: contain;
            display: block;
        }
        .close-picture {
            position: absolute;
            top: 5px;
            right: 10px;
            background: #e74c3c;
            color: white;
            border: none;
            border-radius: 50%;
            width: 25px;
            height: 25px;
            font-size: 16px;
            cursor: pointer;
            display: flex;
            align-items: center;
            justify-content: center;
            font-weight: bold;
        }
        .close-picture:hover {
            background: #c0392b;
        }
        
        /* Fix picture positioning in Global Active Rest section */
        .active-rest-section .picture-popup {
            position: fixed !important;
            top: 50% !important;
            left: 50% !important;
            transform: translate(-50%, -50%) !important;
            margin: 0 !important;
            z-index: 10000 !important;
        }
        .rest-activity {
            font-style: italic;
            color: #7f8c8d;
            position: relative;
        }
        .rest-activity .exercise-name {
            color: #8e44ad;
            border-bottom: 1px dotted #8e44ad;
        }
        .rest-activity .exercise-name:hover {
            color: #27ae60;
            border-bottom: 1px solid #27ae60;
            background: rgba(39, 174, 96, 0.1);
        }
        .timestamp {
            text-align: center;
            color: #95a5a6;
            margin-top: 30px;
            font-size: 0.9em;
        }
        .equipment-section {
            margin-top: 40px;
            background: #f8f9fa;
            border-radius: 10px;
            padding: 25px;
        }
        .equipment-title {
            font-size: 1.4em;
            font-weight: 600;
            color: #2c3e50;
            margin-bottom: 20px;
            text-align: center;
            border-bottom: 2px solid #3498db;
            padding-bottom: 10px;
        }
        .equipment-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
            gap: 15px;
        }
        .equipment-item {
            background: white;
            padding: 15px;
            border-radius: 8px;
            border-left: 4px solid #3498db;
            box-shadow: 0 2px 5px rgba(0,0,0,0.1);
            display: flex;
            justify-content: space-between;
            align-items: center;
        }
        .equipment-name {
            font-weight: 500;
            color: #2c3e50;
            text-transform: capitalize;
        }
        .equipment-count {
            background: #3498db;
            color: white;
            padding: 5px 12px;
            border-radius: 20px;
            font-size: 0.9em;
            font-weight: 600;
        }
        .workout-analysis {
            margin-top: 40px;
            background: #f1f8ff;
            border-radius: 10px;
            padding: 25px;
        }
        .analysis-title {
            font-size: 1.4em;
            font-weight: 600;
            color: #2c3e50;
            margin-bottom: 20px;
            text-align: center;
            border-bottom: 2px solid #e74c3c;
            padding-bottom: 10px;
        }
        .distribution-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 15px;
            margin-bottom: 20px;
        }
        .distribution-item {
            background: white;
            padding: 15px;
            border-radius: 8px;
            border-left: 4px solid #e74c3c;
            box-shadow: 0 2px 5px rgba(0,0,0,0.1);
            text-align: center;
        }
        .distribution-type {
            font-weight: 600;
            color: #2c3e50;
            font-size: 1.1em;
            margin-bottom: 8px;
        }
        .distribution-count {
            font-size: 1.5em;
            font-weight: bold;
            color: #e74c3c;
            margin-bottom: 5px;
        }
        .distribution-percentage {
            font-size: 0.9em;
            color: #7f8c8d;
            font-style: italic;
        }
        .workout-balance {
            background: white;
            padding: 15px;
            border-radius: 8px;
            border: 1px solid #e1e8ed;
            text-align: center;
        }
        .balance-indicator {
            font-weight: 600;
            margin-top: 10px;
        }
        .balanced { color: #27ae60; }
        .upper-heavy { color: #f39c12; }
        .lower-heavy { color: #3498db; }
        .core-heavy { color: #9b59b6; }
        .power-heavy { color: #e74c3c; }
        .balance-icon {
            margin-right: 8px;
            font-size: 1.2em;
        }
        .balance-text {
            font-weight: 600;
        }
        
        /* Advanced Analysis Styles */
        .analysis-section {
            background: white;
            border-radius: 10px;
            padding: 20px;
            margin-bottom: 20px;
            box-shadow: 0 2px 8px rgba(0,0,0,0.1);
        }
        .section-title {
            font-size: 1.2em;
            font-weight: 600;
            color: #2c3e50;
            margin-bottom: 15px;
            padding-bottom: 8px;
            border-bottom: 2px solid #ecf0f1;
        }
        .distribution-stats {
            display: flex;
            flex-direction: column;
            gap: 4px;
        }
        .stat-item {
            font-size: 0.9em;
            color: #7f8c8d;
            font-weight: 500;
        }
        
        /* Muscle Distribution Styles */
        .muscle-distribution-grid {
            display: flex;
            flex-direction: column;
            gap: 12px;
            margin-bottom: 20px;
        }
        .muscle-item {
            border-radius: 8px;
            padding: 12px;
            border: 1px solid #ecf0f1;
            position: relative;
            overflow: hidden;
        }
        .muscle-info {
            display: flex;
            justify-content: space-between;
            align-items: center;
            position: relative;
            z-index: 2;
        }
        .muscle-name {
            font-weight: 600;
            color: #2c3e50;
        }
        .muscle-stats {
            font-size: 0.9em;
            color: #7f8c8d;
            font-weight: 500;
        }
        .muscle-bar {
            height: 4px;
            background: #ecf0f1;
            border-radius: 2px;
            margin-top: 8px;
            overflow: hidden;
        }
        .muscle-fill {
            height: 100%;
            border-radius: 2px;
            transition: width 0.3s ease;
        }
        .validation-section {
            margin-top: 40px;
            background: #f8f9fa;
            border-radius: 10px;
            padding: 25px;
        }
        .validation-title {
            font-size: 1.4em;
            font-weight: 600;
            color: #2c3e50;
            margin-bottom: 20px;
            text-align: center;
            padding-bottom: 10px;
        }
        .validation-valid {
            border-bottom: 2px solid #27ae60;
        }
        .validation-warning {
            border-bottom: 2px solid #f39c12;
        }
        .validation-error {
            border-bottom: 2px solid #e74c3c;
        }
        .validation-status {
            display: flex;
            align-items: center;
            justify-content: center;
            margin-bottom: 20px;
            font-size: 1.1em;
            font-weight: 500;
        }
        .status-icon {
            font-size: 1.5em;
            margin-right: 10px;
        }
        .validation-issues {
            background: #fff;
            border-left: 4px solid #e74c3c;
            padding: 15px;
            margin-bottom: 20px;
            border-radius: 5px;
        }
        .validation-issues h4 {
            color: #e74c3c;
            margin-top: 0;
            margin-bottom: 10px;
        }
        .validation-issues ul {
            margin: 0;
            padding-left: 20px;
        }
        .validation-issues li {
            margin-bottom: 5px;
            color: #666;
        }
        .utilization-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
            gap: 15px;
            margin-top: 20px;
        }
        .utilization-item {
            background: white;
            padding: 15px;
            border-radius: 8px;
            box-shadow: 0 2px 5px rgba(0,0,0,0.1);
        }
        .utilization-header {
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin-bottom: 10px;
        }
        .utilization-name {
            font-weight: 600;
            color: #2c3e50;
            text-transform: capitalize;
        }
        .utilization-sufficient {
            color: #27ae60;
            font-size: 0.9em;
            font-weight: 500;
        }
        .utilization-insufficient {
            color: #e74c3c;
            font-size: 0.9em;
            font-weight: 500;
        }
        .utilization-unused {
            color: #95a5a6;
            font-size: 0.9em;
            font-weight: 500;
        }
        .utilization-bar {
            height: 8px;
            background: #ecf0f1;
            border-radius: 4px;
            overflow: hidden;
            margin-bottom: 8px;
        }
        .utilization-fill {
            height: 100%;
            border-radius: 4px;
            transition: width 0.3s ease;
        }
        .utilization-full {
            background: #27ae60;
        }
        .utilization-partial {
            background: #3498db;
        }
        .utilization-zero {
            background: #bdc3c7;
        }
        .utilization-details {
            font-size: 0.9em;
            color: #666;
            display: flex;
            justify-content: space-between;
        }
        .equipment-tags {
            margin-top: 5px;
            display: flex;
            flex-wrap: wrap;
            gap: 4px;
            justify-content: center;
        }
        .equipment-tag {
            display: inline-block;
            padding: 2px 6px;
            border-radius: 12px;
            font-size: 0.75em;
            font-weight: 500;
            color: white;
            text-transform: lowercase;
        }
        .tag-kettlebells { background: #e74c3c; }
        .tag-dumbbells { background: #3498db; }
        .tag-barbells { background: #9b59b6; }
        .tag-bench { background: #27ae60; }
        .tag-plyo { background: #f39c12; }
        .tag-slam { background: #34495e; }
        .tag-dip { background: #16a085; }
        .tag-default { background: #95a5a6; }
        
        /* Muscle Tags Styles */
        .muscle-tags {
            margin-top: 3px;
            display: flex;
            flex-wrap: wrap;
            gap: 3px;
            justify-content: center;
        }
        .muscle-tag {
            display: inline-block;
            padding: 1px 4px;
            border-radius: 8px;
            font-size: 0.65em;
            font-weight: 400;
            color: white;
            text-transform: capitalize;
        }
        .muscle-chest { background: #e91e63; }
        .muscle-back { background: #2196f3; } 
        .muscle-shoulders { background: #ff9800; }
        .muscle-biceps { background: #4caf50; }
        .muscle-triceps { background: #9c27b0; }
        .muscle-legs { background: #795548; }
        .muscle-core { background: #f44336; }
        .muscle-other { background: #607d8b; }
        
        /* Active Rest Section Styles */
        .active-rest-section {
            margin-top: 40px;
            background: linear-gradient(135deg, #f8f9fa, #e9ecef);
            border-radius: 15px;
            padding: 30px;
            box-shadow: 0 5px 15px rgba(0,0,0,0.1);
            border: 2px solid #28a745;
        }
        .active-rest-title {
            font-size: 1.8em;
            font-weight: 600;
            color: #2c3e50;
            margin-bottom: 10px;
            text-align: center;
            border-bottom: 3px solid #28a745;
            padding-bottom: 15px;
            background: linear-gradient(135deg, #28a745, #20c997);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            background-clip: text;
        }
        .active-rest-description {
            text-align: center;
            color: #6c757d;
            font-style: italic;
            margin-bottom: 25px;
            font-size: 1.1em;
        }
        .active-rest-section table {
            width: 100%;
            border-collapse: collapse;
            margin: 20px 0;
            background: white;
            border-radius: 10px;
            overflow: hidden;
            box-shadow: 0 5px 15px rgba(0,0,0,0.1);
        }
        .active-rest-section table th {
            background: linear-gradient(135deg, #28a745, #20c997);
            color: white;
            padding: 15px;
            text-align: left;
            font-weight: 600;
            font-size: 0.9em;
            text-transform: uppercase;
            letter-spacing: 1px;
            white-space: nowrap;
        }
        .active-rest-section table td {
            padding: 15px;
            border-bottom: 1px solid #ecf0f1;
            vertical-align: top;
        }
        .active-rest-section table tr:nth-child(even) {
            background: #f8f9fa;
        }
        .active-rest-section table tr:hover {
            background: #e8f5e8;
            transition: all 0.3s ease;
        }
        
        /* Warm Up Section Styles */
        .warm-up-section {
            margin-top: 40px;
            background: linear-gradient(135deg, #fff8e1, #ffe0b2);
            border-radius: 15px;
            padding: 30px;
            box-shadow: 0 5px 15px rgba(0,0,0,0.1);
            border: 2px solid #ff9800;
        }
        .warm-up-title {
            font-size: 1.8em;
            font-weight: 600;
            color: #2c3e50;
            margin-bottom: 10px;
            text-align: center;
            border-bottom: 3px solid #ff9800;
            padding-bottom: 15px;
            background: linear-gradient(135deg, #ff9800, #f57c00);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            background-clip: text;
        }
        .warm-up-description {
            text-align: center;
            color: #6c757d;
            font-style: italic;
            margin-bottom: 25px;
            font-size: 1.1em;
        }
        .warm-up-section table {
            width: 100%;
            border-collapse: collapse;
            margin: 20px 0;
            background: white;
            border-radius: 10px;
            overflow: hidden;
            box-shadow: 0 5px 15px rgba(0,0,0,0.1);
        }
        .warm-up-section table th {
            background: linear-gradient(135deg, #ff9800, #f57c00);
            color: white;
            padding: 15px;
            text-align: left;
            font-weight: 600;
            font-size: 0.9em;
            text-transform: uppercase;
            letter-spacing: 1px;
        }
        .warm-up-section table td {
            padding: 15px;
            border-bottom: 1px solid #ecf0f1;
            vertical-align: top;
        }
        .warm-up-section table tr:nth-child(even) {
            background: #fff8e1;
        }
        .warm-up-section table tr:hover {
            background: #ffecb3;
            transition: all 0.3s ease;
        }
        .warm-up-exercise {
            display: flex;
            align-items: center;
            gap: 10px;
        }
        .warm-up-number {
            background: #ff9800;
            color: white;
            font-weight: bold;
            width: 25px;
            height: 25px;
            border-radius: 50%;
            display: flex;
            align-items: center;
            justify-content: center;
            font-size: 0.8em;
            flex-shrink: 0;
        }
        .warm-up-instructions {
            color: #666;
            font-style: italic;
        }
        
        /* Mobile step labels - hidden on desktop */
        .mobile-step-label,
        .mobile-rest-label {
            display: none;
        }
        @media (max-width: 768px) {
            body { padding: 10px; }
            .container { padding: 20px; }
            h1 { font-size: 2em; }
            table { 
                width: 100% !important; 
                margin: 10px 0;
                box-sizing: border-box;
            }
            table, tr, td { display: block; }
            th, thead { display: none !important; }
            thead tr { display: none !important; }
            tr {
                width: 100%;
                margin-bottom: 25px;
                border: 2px solid #3498db;
                border-radius: 12px;
                background: linear-gradient(145deg, #ffffff, #f8f9fa);
                padding: 20px;
                box-sizing: border-box;
                box-shadow: 0 8px 20px rgba(52, 152, 219, 0.15);
                position: relative;
            }
            tr:before {
                content: "";
                position: absolute;
                top: 0;
                left: 0;
                right: 0;
                height: 4px;
                background: linear-gradient(90deg, #3498db, #2980b9);
                border-radius: 12px 12px 0 0;
            }
            td { 
                border: none;
                position: relative;
                padding: 15px;
                width: 100%;
                box-sizing: border-box;
                margin-bottom: 8px;
                border-radius: 6px;
                min-height: 60px;
                display: block;
                overflow: visible;
                text-align: center;
            }
            td.exercise {
                background: rgba(52, 152, 219, 0.05);
                border-left: 4px solid #3498db;
            }
            td.rest-activity {
                background: rgba(46, 204, 113, 0.05);
                border-left: 4px solid #2ecc71;
                margin-bottom: 15px;
            }

            td .exercise-with-video,
            td .exercise-name {
                display: block !important;
                margin: 8px auto !important;
                line-height: 1.4;
                text-align: center !important;
            }
            td .equipment-tags {
                display: block !important;
                margin: 8px auto !important;
                line-height: 1.2;
                text-align: center !important;
                justify-content: center !important;
            }
            
            /* Show mobile step labels */
            .mobile-step-label {
                display: block !important;
                background: rgba(52, 152, 219, 0.15) !important;
                color: #2980b9 !important;
                font-weight: 700 !important;
                font-size: 0.8em !important;
                padding: 6px 12px !important;
                border-radius: 15px !important;
                margin: 0 auto 10px auto !important;
                border: 1px solid #3498db !important;
                width: fit-content !important;
                text-align: center !important;
                white-space: nowrap !important;
            }
            
            .mobile-rest-label {
                display: block !important;
                background: rgba(46, 204, 113, 0.15) !important;
                color: #27ae60 !important;
                font-weight: 700 !important;
                font-size: 0.8em !important;
                padding: 6px 12px !important;
                border-radius: 15px !important;
                margin: 0 auto 10px auto !important;
                border: 1px solid #2ecc71 !important;
                width: fit-content !important;
                text-align: center !important;
                white-space: nowrap !important;
            }
            .video-popup {
                position: fixed !important;
                top: 50% !important;
                left: 50% !important;
                transform: translate(-50%, -50%) !important;
                margin: 0 !important;
                width: 90vw !important;
                max-width: 280px !important;
                height: 60vh !important;
                max-height: 400px !important;
                z-index: 9999 !important;
            }
            .picture-popup {
                position: fixed !important;
                top: 50% !important;
                left: 50% !important;
                transform: translate(-50%, -50%) !important;
                margin: 0 !important;
                width: 90vw !important;
                height: 60vh !important;
                max-width: 350px !important;
                max-height: 70vh !important;
                min-width: 200px !important;
                min-height: 200px !important;
                z-index: 9999 !important;
            }
            .exercise-with-video {
                position: static !important;
            }
            .exercise {
                position: static !important;
            }
        }
        .exercise-cell-wrapper {
            position: relative;
            display: flex;
            flex-direction: column;
            align-items: center;
            gap: 8px;
            min-height: 28px;
            padding-top: 5px;
        }
        
        /* Mobile-specific layout for exercise content */
        @media (max-width: 768px) {
            .exercise-cell-wrapper {
                display: flex;
                flex-direction: column;
                align-items: center;
                gap: 8px;
                padding: 10px 5px;
                position: relative;
            }
            
            .exercise-id-badge {
                position: static !important;
                display: inline-block !important;
                background: #9b59b6 !important;
                color: white !important;
                font-size: 0.75em !important;
                padding: 3px 8px !important;
                border-radius: 12px !important;
                font-weight: 600 !important;
                margin-top: 5px !important;
                box-shadow: 0 2px 4px rgba(0,0,0,0.1) !important;
                z-index: 1 !important;
            }
            
            .picture-button {
                position: static !important;
                margin: 5px 0 !important;
                display: inline-block !important;
            }
            
            .exercise-with-video,
            .exercise-with-picture {
                display: flex !important;
                flex-direction: column !important;
                align-items: center !important;
                gap: 5px !important;
                text-align: center !important;
            }
        }
        
        /* Default desktop positioning for exercise ID badge */
        .exercise-id-badge {
            background: #9b59b6;
            color: white;
            font-size: 11px;
            font-weight: 600;
            padding: 2px 6px;
            border-radius: 10px;
            margin-left: 6px;
            display: inline-block;
            vertical-align: middle;
            line-height: 1.2;
        }
    </style>
    """
    
    html = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{title}</title>
    {css}
</head>
<body>
    <div class="container">
        <h1>{title}</h1>
        <div class="subtitle">Generated on {timestamp}</div>
        
        {f'<div class="notes">{notes}</div>' if notes else ''}
        """
    
    # Add Warm Up section if provided
    if selected_warm_up_exercises:
        html += f"""
        <div class="warm-up-section">
            <h2 class="warm-up-title">🔥 Warm Up Exercises</h2>
            <p class="warm-up-description">Complete these exercises before starting the workout</p>
            
            <table>
                <thead>
                    <tr>
                        <th>Exercise</th>
                        <th>Instructions</th>
                    </tr>
                </thead>
                <tbody>"""
        
        for idx, exercise in enumerate(selected_warm_up_exercises, 1):
            html += f"""
                    <tr>
                        <td class="warm-up-exercise">
                            <span class="warm-up-number">{idx}</span>
                            {format_exercise_link(exercise["name"], exercise.get("link", ""), exercise.get("id", -1))}
                        </td>
                        <td class="warm-up-instructions">
                            Perform for 30-60 seconds
                        </td>
                    </tr>"""
        
        html += """
                </tbody>
            </table>
        </div>
        """
    
    html += """
        <table>
            <thead>
                <tr>
                    <th>Station</th>"""
    
    # Generate dynamic headers based on steps_per_station (without rest columns)
    for step_num in range(1, steps_per_station + 1):
        html += f"""
                    <th>{work}s Step {step_num}</th>"""
    
    html += """
                </tr>
            </thead>
            <tbody>"""
    
    letters = "ABCDEFGHIJKLMNOPQRSTUVWXYZ"
    for idx, st in enumerate(stations):
        letter = letters[idx]
        area_class = st['area'].lower()
        html += f"""
                <tr>
                    <td data-label="Station">
                        <span class="station-letter">{letter}</span><br>
                        <span class="area-badge {area_class}">{st['area']}</span>
                    </td>"""
        
        # Generate dynamic step columns (without rest columns)
        for step_num in range(1, steps_per_station + 1):
            step_key = f'step{step_num}'
            step_link_key = f'step{step_num}_link'
            step_equipment_key = f'step{step_num}_equipment'
            step_muscles_key = f'step{step_num}_muscles'
            step_id_key = f'step{step_num}_id'
            
            html += f"""
                     <td data-label="Step {step_num}" class="exercise">
                         <span class="mobile-step-label">Step {step_num}:</span>
                         <div class="exercise-cell-wrapper">
                             {format_exercise_link(st.get(step_key, ''), st.get(step_link_key, ''), st.get(step_id_key, None), "../config/pictures" if is_workout_store else "config/pictures")}
                             {format_exercise_id_badge(st.get(step_id_key, None))}
                         </div>
                         {format_muscle_tags(st.get(step_muscles_key, ''))}
                         {format_equipment_tags(st.get(step_equipment_key, {}))}
                     </td>"""
        
        html += """
                </tr>"""
    
    html += f"""
            </tbody>
        </table>"""
        
    # Add Global Active Rest Schedule section if provided
    if global_active_rest_schedule and selected_active_rest_exercises:
        work = plan["timing"]["work"]
        rest = plan["timing"]["rest"]
        active_rest_count = plan.get("active_rest_count", 4)
        
        html += f"""
        
        <div class="active-rest-section">
            <h2 class="active-rest-title">🏃‍♂️ Global Active Rest Program</h2>
            <p class="active-rest-description">Everyone does these exercises together during rest periods</p>
            
            <table>
                <thead>
                    <tr>
                        <th>Station</th>"""
        
        # Add step headers for active rest exercises
        for idx, exercise in enumerate(selected_active_rest_exercises, 1):
            if exercise["name"] != "Rest":
                html += f"""
                        <th>{rest}s Step {idx}</th>"""
        
        html += """
                    </tr>
                </thead>
                <tbody>
                    <tr>
                        <td data-label="Station">
                            <span class="station-letter">⚡</span><br>
                            <span class="area-badge active-rest">active rest</span>
                        </td>"""
        
        # Add exercise columns
        for idx, exercise in enumerate(selected_active_rest_exercises, 1):
            if exercise["name"] != "Rest":
                html += f"""
                        <td data-label="Step {idx}" class="exercise">
                            <span class="mobile-step-label">Step {idx}:</span>
                            {format_exercise_link(exercise["name"], exercise.get("link", ""), exercise.get("id", -1))}
                        </td>"""
        
        html += """
                    </tr>
                </tbody>
            </table>
        </div>"""
    
    # Add equipment requirements section if available
    if equipment_requirements:
        html += f"""
        <div class="equipment-section">
            <div class="equipment-title">📋 Equipment Required for This Workout</div>
            <div class="equipment-grid">"""
        
        # Sort equipment by utilization percentage (100% to 0%), then alphabetically for ties
        equipment_with_util = []
        for equipment_name in equipment_requirements.keys():
            if validation_summary and equipment_name in validation_summary.get("utilization_by_type", {}):
                util_pct = validation_summary["utilization_by_type"][equipment_name]["utilization_pct"]
            else:
                util_pct = 0.0
            equipment_with_util.append((equipment_name, util_pct))
        
        # Sort by utilization percentage (descending), then alphabetically
        equipment_with_util.sort(key=lambda x: (-x[1], x[0]))
        
        for equipment_name, _ in equipment_with_util:
            equipment_info = equipment_requirements[equipment_name]
            count = equipment_info.get("count", 1)
            # Clean up equipment name for display (remove prefixes, underscores)
            display_name = equipment_name.replace("_", " ").replace("kg", " kg").replace("dumbbells", "dumbbell").replace("kettlebells", "kettlebell").replace("slam balls", "slam ball").title()
            # Get appropriate icon for this equipment type
            icon = get_equipment_icon(equipment_name)
            
            html += f"""
                <div class="equipment-item">
                    <span class="equipment-name">{icon} {display_name}</span>
                    <span class="equipment-count">{count}x</span>
                </div>"""
        
        html += """
            </div>
        </div>"""
    
    # Add workout distribution analysis
    workout_analysis = analyze_workout_distribution(stations)
    if workout_analysis and workout_analysis.get("total_exercises", 0) > 0:
        area_distribution = workout_analysis["area_distribution"]
        grouped_muscles = workout_analysis["grouped_muscles"]
        station_areas = workout_analysis["station_areas"]
        total_exercises = workout_analysis["total_exercises"]
        
        html += f"""
        <div class="workout-analysis">
            <div class="analysis-title">💪 Advanced Workout Analysis</div>
            
            <!-- Station Area Distribution -->
            <div class="analysis-section">
                <h3 class="section-title">🎯 Station Area Targeting</h3>
                <div class="distribution-grid">"""
        
        # Area distribution with icons
        area_icons = {"upper": "💪", "lower": "🦵", "core": "🔥"}
        area_colors = {"upper": "#3498db", "lower": "#27ae60", "core": "#e74c3c"}
        
        for area, station_count in station_areas.items():
            exercise_count = area_distribution.get(area, 0)
            station_percentage = (station_count / len(stations) * 100) if len(stations) > 0 else 0
            exercise_percentage = (exercise_count / total_exercises * 100) if total_exercises > 0 else 0
            icon = area_icons.get(area, "🏋️")
            color = area_colors.get(area, "#95a5a6")
            
            html += f"""
                <div class="distribution-item" style="border-left: 4px solid {color}">
                    <div class="distribution-type">{icon} {area.title()}</div>
                    <div class="distribution-stats">
                        <span class="stat-item">{station_count} stations ({station_percentage:.0f}%)</span>
                        <span class="stat-item">{exercise_count} exercises ({exercise_percentage:.0f}%)</span>
                    </div>
                </div>"""
        
        html += f"""
                </div>
            </div>
            
            <!-- Muscle Group Analysis -->
            <div class="analysis-section">
                <h3 class="section-title">🎯 Muscle Group Distribution</h3>
                <div class="muscle-distribution-grid">"""
        
        # Muscle group distribution with colors
        muscle_icons = {
            "Chest": "🔥", "Back": "💪", "Shoulders": "🌟", 
            "Arms": "💥", "Legs": "🦵", "Core": "⚡", "Other": "🏋️"
        }
        muscle_colors = {
            "Chest": "#e91e63", "Back": "#2196f3", "Shoulders": "#ff9800",
            "Arms": "#4caf50", "Legs": "#795548", "Core": "#f44336", "Other": "#607d8b"
        }
        
        # Sort muscle groups by count (highest first)
        sorted_muscles = sorted(grouped_muscles.items(), key=lambda x: x[1], reverse=True)
        
        for muscle_group, count in sorted_muscles:
            if count > 0:
                percentage = (count / sum(grouped_muscles.values()) * 100) if sum(grouped_muscles.values()) > 0 else 0
                icon = muscle_icons.get(muscle_group, "🏋️")
                color = muscle_colors.get(muscle_group, "#95a5a6")
                
                html += f"""
                    <div class="muscle-item" style="background: linear-gradient(90deg, {color}22 0%, {color}44 {percentage}%, transparent {percentage}%)">
                        <div class="muscle-info">
                            <span class="muscle-name">{icon} {muscle_group}</span>
                            <span class="muscle-stats">{count} exercises • {percentage:.1f}%</span>
                        </div>
                        <div class="muscle-bar">
                            <div class="muscle-fill" style="width: {percentage}%; background: {color}"></div>
                        </div>
                    </div>"""
        
        # Add workout balance assessment
        balance_class = "balanced"
        balance_text = "Well-balanced workout"
        balance_icon = "⚖️"
        
        if area_distribution:
            max_area = max(area_distribution.items(), key=lambda x: x[1])
            max_percentage = (max_area[1] / total_exercises * 100)
            
            if max_percentage > 50:
                if max_area[0] == "upper":
                    balance_class = "upper-heavy"
                    balance_text = "Upper body focused workout"
                    balance_icon = "💪"
                elif max_area[0] == "lower":
                    balance_class = "lower-heavy"
                    balance_text = "Lower body focused workout"
                    balance_icon = "🦵"
                elif max_area[0] == "core":
                    balance_class = "core-heavy"
                    balance_text = "Core focused workout"
                    balance_icon = "🔥"
        
        html += f"""
                </div>
                
                <div class="workout-balance">
                    <div>Total Exercises: <strong>{total_exercises}</strong></div>
                    <div class="balance-indicator {balance_class}">
                        <span class="balance-icon">{balance_icon}</span>
                        <span class="balance-text">{balance_text}</span>
                    </div>
                </div>
            </div>
        </div>"""
    
    # Add equipment validation section if available
    if validation_summary:
        is_valid = validation_summary["is_valid"]
        issues = validation_summary["issues"]
        utilization_by_type = validation_summary.get("utilization_by_type", {})
        
        # Determine validation status
        if is_valid:
            status_class = "validation-valid"
            status_icon = "✅"
            status_text = "Equipment validation passed"
            status_color = "#27ae60"
        else:
            status_class = "validation-warning"
            status_icon = "⚠️"
            status_text = "Equipment validation warnings"
            status_color = "#f39c12"
        
        html += f"""
        <div class="validation-section">
            <div class="validation-title {status_class}">⚙️ Equipment Validation</div>
            <div class="validation-status" style="color: {status_color};">
                <span class="status-icon">{status_icon}</span>
                <span>{status_text}</span>
            </div>"""
        
        # Show issues if any
        if issues:
            html += f"""
            <div class="validation-issues">
                <h4>Issues Found:</h4>
                <ul>"""
            for issue in issues:
                html += f"<li>{issue}</li>"
            html += """
                </ul>
            </div>"""
        
        # Show equipment utilization for ALL equipment (including 0% usage)
        all_equipment = plan.get("equipment", {})
        if all_equipment:
            html += f"""
            <div class="utilization-grid">"""
            
            # Create list of equipment with utilization percentages for sorting
            equipment_with_util = []
            for equipment_type in all_equipment.keys():
                if equipment_type in utilization_by_type:
                    util_pct = utilization_by_type[equipment_type]["utilization_pct"]
                else:
                    util_pct = 0.0
                equipment_with_util.append((equipment_type, util_pct))
            
            # Sort by utilization percentage (100% to 0%), then alphabetically for ties
            equipment_with_util.sort(key=lambda x: (-x[1], x[0]))
            
            for equipment_type, _ in equipment_with_util:
                available = all_equipment[equipment_type].get("count", 0)
                
                # Check if this equipment is being used
                if equipment_type in utilization_by_type:
                    util_info = utilization_by_type[equipment_type]
                    required = util_info["required"]
                    utilization_pct = util_info["utilization_pct"]
                    sufficient = util_info["sufficient"]
                else:
                    # Equipment not being used - 0% utilization
                    required = 0
                    utilization_pct = 0.0
                    sufficient = True  # Not being used, so sufficient
                
                # Clean up equipment name for display
                display_name = equipment_type.replace("_", " ").replace("kg", " kg").replace("dumbbells", "dumbbell").replace("kettlebells", "kettlebell").replace("slam balls", "slam ball").title()
                # Get appropriate icon for this equipment type
                icon = get_equipment_icon(equipment_type)
                
                # Determine utilization bar color
                if utilization_pct == 100.0:
                    bar_class = "utilization-full"
                elif utilization_pct == 0.0:
                    bar_class = "utilization-zero"  # New class for 0% usage
                else:
                    bar_class = "utilization-partial"
                
                # Status text
                if required == 0:
                    status_class = "utilization-unused"
                    status_text = "○ Unused"
                elif sufficient:
                    status_class = "utilization-sufficient"
                    status_text = "✓ Available"
                else:
                    status_class = "utilization-insufficient"
                    status_text = "⚠ Insufficient"
                
                html += f"""
                <div class="utilization-item">
                    <div class="utilization-header">
                        <span class="utilization-name">{icon} {display_name}</span>
                        <span class="{status_class}">{status_text}</span>
                    </div>
                    <div class="utilization-bar">
                        <div class="utilization-fill {bar_class}" style="width: {min(utilization_pct, 100)}%;"></div>
                    </div>
                    <div class="utilization-details">
                        <span>Need: {required}x</span>
                        <span>Have: {available}x</span>
                        <span>{utilization_pct:.1f}% utilization</span>
                    </div>
                </div>"""
            
            html += """
            </div>"""
        
        html += """
        </div>"""
    
    html += f"""
        
        <div class="timestamp">
            Workout generated with Workout Station Generator based on Annya's plan
        </div>
    </div>
    
    <script>
        function toggleVideo(exerciseId) {{
            const video = document.getElementById('video_' + exerciseId);
            const iframe = video.querySelector('iframe');
            const allVideos = document.querySelectorAll('.video-popup');
            
            // Stop and hide all other videos first
            allVideos.forEach(v => {{
                if (v.id !== 'video_' + exerciseId) {{
                    stopVideo(v);
                }}
            }});
            
            // Toggle the selected video
            if (video.style.display === 'none' || video.style.display === '') {{
                video.style.display = 'block';
                
                // Smart positioning to avoid cutoff
                positionVideoSmart(video);
                
                // Reload the iframe to start fresh
                const originalSrc = iframe.getAttribute('data-src') || iframe.src;
                iframe.setAttribute('data-src', originalSrc);
                iframe.src = originalSrc;
            }} else {{
                stopVideo(video);
            }}
        }}
        
        function positionVideoSmart(videoElement) {{
            // Check if video is in active rest section
            const activeRestSection = videoElement.closest('.active-rest-section');
            if (activeRestSection) {{
                // Create backdrop for active rest videos
                let backdrop = document.getElementById('video-backdrop');
                if (!backdrop) {{
                    backdrop = document.createElement('div');
                    backdrop.id = 'video-backdrop';
                    backdrop.style.position = 'fixed';
                    backdrop.style.top = '0';
                    backdrop.style.left = '0';
                    backdrop.style.width = '100vw';
                    backdrop.style.height = '100vh';
                    backdrop.style.background = 'rgba(0, 0, 0, 0.7)';
                    backdrop.style.zIndex = '9999';
                    backdrop.style.display = 'none';
                    document.body.appendChild(backdrop);
                    
                    // Close video when clicking backdrop
                    backdrop.addEventListener('click', function() {{
                        document.querySelectorAll('.video-popup').forEach(video => {{
                            stopVideo(video);
                        }});
                    }});
                }}
                backdrop.style.display = 'block';
                
                // For active rest videos, use fixed centering to avoid overlap
                videoElement.style.position = 'fixed';
                videoElement.style.top = '50%';
                videoElement.style.left = '50%';
                videoElement.style.transform = 'translate(-50%, -50%)';
                videoElement.style.margin = '0';
                videoElement.style.zIndex = '10000';
                videoElement.style.right = 'auto';
                videoElement.style.bottom = 'auto';
                return; // Skip the normal positioning logic
            }}
            
            const viewportHeight = window.innerHeight;
            const viewportWidth = window.innerWidth;
            const videoHeight = 360;
            const videoWidth = 240;
            
            // Get the exercise element (parent of video popup)
            const exerciseElement = videoElement.parentElement;
            const exerciseRect = exerciseElement.getBoundingClientRect();
            
            // Calculate available space on all sides
            const spaceRight = viewportWidth - exerciseRect.right - 20;
            const spaceLeft = exerciseRect.left - 20;
            const spaceBelow = viewportHeight - exerciseRect.top - 20;
            
            // Reset all positioning styles first
            videoElement.style.position = 'absolute';
            videoElement.style.top = '0';
            videoElement.style.bottom = 'auto';
            videoElement.style.left = '100%';
            videoElement.style.right = 'auto';
            videoElement.style.marginLeft = '20px';
            videoElement.style.marginRight = '0';
            videoElement.style.marginTop = '0';
            videoElement.style.zIndex = '1000';
            
            // Check if we're in a right column (less than video width + margin space)
            if (spaceRight < videoWidth + 20) {{
                if (spaceLeft >= videoWidth + 20) {{
                    // Position to the left
                    videoElement.style.left = 'auto';
                    videoElement.style.right = '100%';
                    videoElement.style.marginLeft = '0';
                    videoElement.style.marginRight = '20px';
                }} else {{
                    // Not enough space on either side - use fixed centering
                    videoElement.style.position = 'fixed';
                    videoElement.style.left = '50%';
                    videoElement.style.right = 'auto';
                    videoElement.style.marginLeft = '-120px'; // Half of video width
                    videoElement.style.marginRight = '0';
                    videoElement.style.zIndex = '10000';
                    
                    // Center vertically too
                    videoElement.style.top = '50%';
                    videoElement.style.marginTop = '-180px'; // Half of video height
                    return; // Skip vertical positioning logic below
                }}
            }}
            
            // Handle vertical positioning for non-fixed elements
            if (spaceBelow < videoHeight) {{
                // Position above the exercise
                videoElement.style.top = 'auto';
                videoElement.style.bottom = '0';
            }}
        }}
        
        function stopVideo(videoElement) {{
            const iframe = videoElement.querySelector('iframe');
            // Stop video by clearing and restoring src
            const originalSrc = iframe.getAttribute('data-src') || iframe.src;
            iframe.setAttribute('data-src', originalSrc);
            iframe.src = '';
            videoElement.style.display = 'none';
            
            // Hide backdrop if it exists
            const backdrop = document.getElementById('video-backdrop');
            if (backdrop) {{
                backdrop.style.display = 'none';
            }}
        }}
        
        // Picture popup functions
        function togglePicture(exerciseId) {{
            console.log('togglePicture called with:', exerciseId);
            const picture = document.getElementById('picture_' + exerciseId);
            console.log('Picture element found:', picture);
            
            if (!picture) {{
                console.error('Picture element not found for ID:', 'picture_' + exerciseId);
                return;
            }}
            
            const allPictures = document.querySelectorAll('.picture-popup');
            
            // Hide all other pictures first
            allPictures.forEach(p => {{
                if (p.id !== 'picture_' + exerciseId) {{
                    p.style.display = 'none';
                }}
            }});
            
            // Toggle the selected picture
            if (picture.style.display === 'none' || picture.style.display === '') {{
                console.log('Showing picture');
                picture.style.display = 'block';
                positionPictureSmart(picture);
            }} else {{
                console.log('Hiding picture');
                picture.style.display = 'none';
            }}
        }}
        
        // Handle missing images
        function handleImageError(img) {{
            // Replace broken image with a message
            const errorDiv = document.createElement('div');
            errorDiv.className = 'image-error';
            errorDiv.innerHTML = '📷 Image not available<br><small>Exercise ID: ' + img.src.split('/').pop().split('.')[0] + '</small>';
            errorDiv.style.cssText = 'text-align: center; padding: 20px; color: #666; font-size: 14px; border: 2px dashed #ccc; border-radius: 8px; background: #f9f9f9;';
            
            // Replace the image with the error message
            img.parentNode.replaceChild(errorDiv, img);
        }}
        
        function positionPictureSmart(pictureElement) {{
            // Check if picture is in active rest section
            const activeRestSection = pictureElement.closest('.active-rest-section');
            if (activeRestSection) {{
                // For active rest pictures, use fixed centering
                pictureElement.style.position = 'fixed';
                pictureElement.style.top = '50%';
                pictureElement.style.left = '50%';
                pictureElement.style.transform = 'translate(-50%, -50%)';
                pictureElement.style.margin = '0';
                pictureElement.style.zIndex = '10000';
                return;
            }}
            
            // For regular workout pictures, apply smart positioning similar to videos
            const viewportHeight = window.innerHeight;
            const viewportWidth = window.innerWidth;
            const pictureWidth = 400; // Default picture width from CSS
            const pictureHeight = 300; // Estimated picture height
            
            // Get the exercise element (parent of picture popup)
            const exerciseElement = pictureElement.parentElement;
            const exerciseRect = exerciseElement.getBoundingClientRect();
            
            // Calculate available space on all sides
            const spaceRight = viewportWidth - exerciseRect.right - 20;
            const spaceLeft = exerciseRect.left - 20;
            const spaceBelow = viewportHeight - exerciseRect.top - 20;
            
            // Reset all positioning styles first
            pictureElement.style.position = 'absolute';
            pictureElement.style.top = '0';
            pictureElement.style.bottom = 'auto';
            pictureElement.style.left = '100%';
            pictureElement.style.right = 'auto';
            pictureElement.style.marginLeft = '20px';
            pictureElement.style.marginRight = '0';
            pictureElement.style.marginTop = '0';
            pictureElement.style.transform = 'none';
            pictureElement.style.zIndex = '1000';
            
            // Check if we're in a right column (less than picture width + margin space)
            if (spaceRight < pictureWidth + 20) {{
                if (spaceLeft >= pictureWidth + 20) {{
                    // Position to the left
                    pictureElement.style.left = 'auto';
                    pictureElement.style.right = '100%';
                    pictureElement.style.marginLeft = '0';
                    pictureElement.style.marginRight = '20px';
                }} else {{
                    // Not enough space on either side - use fixed centering
                    pictureElement.style.position = 'fixed';
                    pictureElement.style.left = '50%';
                    pictureElement.style.top = '50%';
                    pictureElement.style.transform = 'translate(-50%, -50%)';
                    pictureElement.style.margin = '0';
                    pictureElement.style.zIndex = '10000';
                    return;
                }}
            }}
            
            // Handle vertical positioning for non-fixed elements
            if (spaceBelow < pictureHeight) {{
                // Position above the exercise
                pictureElement.style.top = 'auto';
                pictureElement.style.bottom = '0';
            }}
        }}
        
        // Close video when clicking outside
        document.addEventListener('click', function(e) {{
            if (!e.target.closest('.exercise-with-video') && !e.target.closest('.video-popup')) {{
                document.querySelectorAll('.video-popup').forEach(video => {{
                    stopVideo(video);
                }});
            }}
            if (!e.target.closest('.exercise-with-picture') && !e.target.closest('.picture-popup') && !e.target.closest('.picture-button')) {{
                document.querySelectorAll('.picture-popup').forEach(picture => {{
                    picture.style.display = 'none';
                }});
            }}
        }});
    </script>
</body>
</html>"""
    
    return html 
#!/usr/bin/env python3
"""HTML generation and formatting for workout reports."""

from datetime import datetime
from typing import Dict, List, Optional


def format_exercise_link(exercise_name: str, exercise_link: str, exercise_id: int = None, pictures_path: str = "config/pictures", video_type: str = None) -> str:
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
    
    # Video functionality - support both YouTube and MP4
    if exercise_link and exercise_link != "some url" and exercise_link.strip():
        # Create unique ID for this exercise - sanitize all special characters
        import re
        html_id = exercise_name.lower()
        html_id = html_id.replace(" ", "_").replace("-", "_").replace("+", "plus").replace("→", "to")
        html_id = html_id.replace("'", "").replace("(", "").replace(")", "").replace("/", "_")
        html_id = html_id.replace(",", "").replace(".", "").replace(":", "").replace(";", "")
        html_id = html_id.replace("&", "and").replace("#", "").replace("%", "").replace("@", "")
        # Remove any remaining non-alphanumeric characters except underscores
        html_id = re.sub(r'[^a-z0-9_]', '', html_id)
        
        # Determine video type if not explicitly provided
        if video_type is None:
            if any(youtube_domain in exercise_link for youtube_domain in ["youtube.com", "youtu.be"]):
                video_type = 'youtube'
            elif exercise_link.endswith('.mp4') or 'config/videos/' in exercise_link:
                video_type = 'mp4'
            else:
                video_type = 'youtube'  # Default fallback
        
        if video_type == 'mp4':
            # MP4 video support - use dynamic path like pictures
            videos_path = pictures_path.replace("/pictures", "/videos")
            # Extract just the filename from the exercise_link (e.g., "122.mp4" from "config/videos/122.mp4")
            video_filename = exercise_link.split('/')[-1] if '/' in exercise_link else exercise_link
            video_src = f"{videos_path}/{video_filename}"
            
            video_html = f'''<span class="exercise-with-video">
            <span class="exercise-name" onclick="toggleVideo('{html_id}')">{display_name}</span>
            <div id="video_{html_id}" class="video-popup">
                <video controls muted preload="metadata">
                    <source src="{video_src}" type="video/mp4">
                    Your browser does not support the video tag.
                </video>
                <button class="close-video" onclick="toggleVideo('{html_id}')">&times;</button>
            </div>'''
        else:
            # YouTube video support (original functionality)
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
            
            video_html = f'''<span class="exercise-with-video">
            <span class="exercise-name" onclick="toggleVideo('{html_id}')">{display_name}</span>
            <div id="video_{html_id}" class="video-popup">
                <iframe src="{embed_url}" frameborder="0" allowfullscreen></iframe>
                <button class="close-video" onclick="toggleVideo('{html_id}')">&times;</button>
            </div>'''
        
        # Picture button functionality removed - images now integrated directly into cards
        
        video_html += '</span>'
        return video_html
    else:
        # No video - picture button functionality removed, images now integrated directly into cards
        return display_name


def format_exercise_id_badge(exercise_id: int) -> str:
    if exercise_id is not None and exercise_id != -1:
        return f'<span class="exercise-id-badge">{exercise_id}</span>'
    return ''


def get_exercise_background_images(exercise_id: int, exercise_name: str, pictures_path: str = "config/pictures") -> tuple:
    """Get background images for an exercise, returns (image_html, has_images)."""
    from pathlib import Path
    
    if exercise_id is None or exercise_id == -1:
        return "", False
    
    # Check if this is a right-side unilateral exercise
    is_right_unilateral = exercise_name and "(Right)" in exercise_name
    flip_class = " flipped" if is_right_unilateral else ""
    
    # First check for single image (original format)
    single_image_path = Path("config/pictures") / f"{exercise_id}.png"
    
    # Then check for multiple images (new format: id_1.png, id_2.png, etc.)
    multiple_images = []
    for i in range(1, 4):  # Check for up to 3 images (_1, _2, _3)
        multi_image_path = Path("config/pictures") / f"{exercise_id}_{i}.png"
        if multi_image_path.exists():
            multiple_images.append(f"{pictures_path}/{exercise_id}_{i}.png")
    
    if multiple_images:
        # Use multiple images - exactly like view-all mode
        images_html = ""
        for img_src in multiple_images:
            images_html += f'<img src="{img_src}" alt="{exercise_name}" />'
        return f'<div class="exercise-images{flip_class}">{images_html}</div>', True
    elif single_image_path.exists():
        # Use single image (backward compatibility) - exactly like view-all mode
        return f'<img src="{pictures_path}/{exercise_id}.png" alt="{exercise_name}" class="exercise-image{flip_class}" />', True
    else:
        return "", False

def get_exercise_background_style(exercise_id: int, exercise_name: str, pictures_path: str = "config/pictures") -> tuple:
    """Get CSS background style for mobile view, returns (style_attr, has_images, is_flipped)."""
    from pathlib import Path
    
    if exercise_id is None or exercise_id == -1:
        return "", False, False
    
    # Check if this is a right-side unilateral exercise
    is_right_unilateral = exercise_name and "(Right)" in exercise_name
    
    # First check for single image (original format)
    single_image_path = Path("config/pictures") / f"{exercise_id}.png"
    
    # Check for multiple images (use first one for mobile background)
    first_image = None
    for i in range(1, 4):  # Check for up to 3 images (_1, _2, _3)
        multi_image_path = Path("config/pictures") / f"{exercise_id}_{i}.png"
        if multi_image_path.exists():
            first_image = f"{pictures_path}/{exercise_id}_{i}.png"
            break
    
    if first_image:
        # Use first image from multiple images for mobile background
        return f'style="background-image: url(\'{first_image}\');"', True, is_right_unilateral
    elif single_image_path.exists():
        # Use single image as background
        return f'style="background-image: url(\'{pictures_path}/{exercise_id}.png\');"', True, is_right_unilateral
    else:
        return "", False, False


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


def format_muscle_tags(muscles_data) -> str:
    """Format muscle groups as colored tags.
    
    Args:
        muscles_data: Either a string (comma-separated) or list of muscle names
    """
    if not muscles_data:
        return ""
    
    tags_html = '<div class="muscle-tags">'
    
    # Handle both string and array formats
    if isinstance(muscles_data, str):
        if not muscles_data.strip():
            return ""
        # Split muscles by comma and clean up
        muscles = [muscle.strip().lower() for muscle in muscles_data.split(",") if muscle.strip()]
    elif isinstance(muscles_data, list):
        # Already a list, just clean up
        muscles = [muscle.strip().lower() for muscle in muscles_data if muscle and muscle.strip()]
    else:
        return ""
    
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
                muscles_data = station.get(step_muscles_key, '')
                if muscles_data:
                    # Handle both string and array formats
                    if isinstance(muscles_data, str):
                        muscles = [muscle.strip().lower() for muscle in muscles_data.split(",") if muscle.strip()]
                    elif isinstance(muscles_data, list):
                        muscles = [muscle.strip().lower() for muscle in muscles_data if muscle and muscle.strip()]
                    else:
                        muscles = []
                    
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


def generate_html_workout(plan: Dict, stations: List[Dict], equipment_requirements: Optional[Dict] = None, validation_summary: Optional[Dict] = None, global_active_rest_schedule: Optional[List[Dict]] = None, selected_active_rest_exercises: Optional[List[Dict]] = None, selected_crossfit_path_exercises: Optional[List[Dict]] = None, is_workout_store: bool = False) -> str:
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
            table-layout: fixed;
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
            width: auto;
        }
        /* Station column should be narrower */
        th:first-child {
            width: 120px;
        }
        /* All step columns should have equal width */
        th:not(:first-child) {
            width: calc((100% - 120px) / """ + str(steps_per_station) + """);
        }
        td { 
            padding: 15px; 
            border-bottom: 1px solid #ecf0f1;
            vertical-align: top;
            width: auto;
        }
        /* Station column should be narrower */
        td:first-child {
            width: 120px;
        }
        /* All step columns should have equal width */
        td:not(:first-child) {
            width: calc((100% - 120px) / """ + str(steps_per_station) + """);
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
            min-height: 120px;
            border-radius: 8px;
            overflow: hidden;
        }
        .exercise.has-background {
            background-color: rgba(0,0,0,0.1);
        }
        .exercise-image {
            position: absolute;
            top: 8px;
            left: 8px;
            right: 8px;
            bottom: 8px;
            width: calc(100% - 16px);
            height: calc(100% - 16px);
            object-fit: cover;
            z-index: 1;
            border-radius: 6px;
        }
        .exercise-images {
            position: absolute;
            top: 8px;
            left: 8px;
            right: 8px;
            bottom: 8px;
            width: calc(100% - 16px);
            height: calc(100% - 16px);
            z-index: 1;
            display: flex;
            flex-direction: row;
            gap: 2px;
            border-radius: 6px;
            overflow: hidden;
        }
        .exercise-images img {
            flex: 1;
            width: 0;
            height: 100%;
            object-fit: cover;
            display: block;
        }
        /* Flip images horizontally for right-side unilateral exercises */
        .exercise-images.flipped img,
        .exercise-image.flipped {
            transform: scaleX(-1);
        }
        .exercise.has-background .exercise-cell-wrapper {
            position: relative;
            z-index: 2;
            background: linear-gradient(transparent 0%, rgba(0,0,0,0.1) 40%, rgba(0,0,0,0.8) 100%);
            height: 100%;
            min-height: 120px;
            display: flex;
            flex-direction: column;
            justify-content: flex-end;
            padding: 12px;
            border-radius: 8px;
        }
        /* Add exercise-content class for consistency with view-all mode */
        .exercise.has-background .exercise-cell-wrapper {
            /* This mimics the exercise-content class from view-all mode */
        }
        .exercise.has-background .exercise-name {
            color: white;
            text-shadow: 1px 1px 2px rgba(0,0,0,0.8);
            border-bottom-color: rgba(255,255,255,0.7);
        }
        .exercise.has-background .exercise-name:hover {
            color: #ffd700;
            text-shadow: 0 0 8px rgba(255,215,0,0.6);
            border-bottom-color: #ffd700;
            background: rgba(255,215,0,0.2);
        }
        .exercise.has-background .muscle-tag {
            background: rgba(255,255,255,0.9);
            color: #333;
        }
        .exercise.has-background .equipment-tag {
            background: rgba(255,255,255,0.9);
            color: #333;
        }
        .exercise.has-background .exercise-id-badge {
            background: rgba(155, 89, 182, 0.9) !important;
            color: white !important;
            text-shadow: 1px 1px 2px rgba(0,0,0,0.8);
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
        .video-popup iframe,
        .video-popup video {
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
        
        /* Picture button styles removed - images now integrated directly into cards */

        
        /* Exercise cell wrapper for better layout */
        .exercise-cell-wrapper {
            display: flex;
            align-items: center;
            gap: 4px;
            flex-wrap: wrap;
            min-height: 120px;
            padding: 12px;
            position: relative;
        }
        /* Ensure consistent cell wrapper height for exercises without background */
        .exercise:not(.has-background) .exercise-cell-wrapper {
            align-items: flex-start;
            background: rgba(248, 249, 250, 0.8);
            border-radius: 8px;
            height: 120px;
            min-height: 120px;
            display: flex;
            flex-direction: column;
            justify-content: flex-start;
        }
        /* Force consistent height for all exercise cells */
        .exercise {
            height: 120px !important;
        }
        .exercise td {
            height: 120px !important;
        }
        /* Picture popup styles removed - images now integrated directly into cards */
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
        
        /* CrossFit Path Section Styles */
        .crossfit-path-section {
            margin-top: 40px;
            background: linear-gradient(135deg, #fff8e1, #ffe0b2);
            border-radius: 15px;
            padding: 30px;
            box-shadow: 0 5px 15px rgba(0,0,0,0.1);
            border: 2px solid #ff9800;
        }
        .crossfit-path-title {
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
        .crossfit-path-description {
            text-align: center;
            color: #6c757d;
            font-style: italic;
            margin-bottom: 25px;
            font-size: 1.1em;
        }
        .crossfit-path-inline-image {
            max-width: 200px;
            max-height: 150px;
            border-radius: 8px;
            box-shadow: 0 2px 8px rgba(0,0,0,0.1);
            margin-top: 10px;
            display: block;
            margin-left: auto;
            margin-right: auto;
        }
        .crossfit-path-multi-images {
            display: flex;
            flex-direction: row;
            gap: 8px;
            justify-content: center;
            margin-top: 10px;
        }
        .crossfit-path-multi-images img {
            max-width: 150px;
            max-height: 120px;
            border-radius: 8px;
            box-shadow: 0 2px 8px rgba(0,0,0,0.1);
            object-fit: cover;
        }
        .crossfit-path-section table {
            width: 100%;
            border-collapse: collapse;
            margin: 20px 0;
            background: white;
            border-radius: 10px;
            overflow: hidden;
            box-shadow: 0 5px 15px rgba(0,0,0,0.1);
        }
        .crossfit-path-section table th {
            background: linear-gradient(135deg, #ff9800, #f57c00);
            color: white;
            padding: 15px;
            text-align: left;
            font-weight: 600;
            font-size: 0.9em;
            text-transform: uppercase;
            letter-spacing: 1px;
        }
        .crossfit-path-section table td {
            padding: 15px;
            border-bottom: 1px solid #ecf0f1;
            vertical-align: top;
        }
        .crossfit-path-section table tr:nth-child(even) {
            background: #fff8e1;
        }
        .crossfit-path-section table tr:hover {
            background: #ffecb3;
            transition: all 0.3s ease;
        }
        .crossfit-path-exercise {
            display: flex;
            align-items: center;
            gap: 10px;
        }
        .crossfit-path-number {
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
        .crossfit-path-instructions {
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
            table, tbody, tr, td { display: block; }
            thead { display: none !important; }
            th { display: none !important; }
            
            /* Style single images for mobile - full card size */
            tbody td:not(:first-child) .exercise-image {
                position: absolute !important;
                top: 8px !important;
                left: 8px !important;
                right: 8px !important;
                bottom: 8px !important;
                width: calc(100% - 16px) !important;
                height: calc(100% - 16px) !important;
                object-fit: cover !important;
                border-radius: 6px !important;
                z-index: 1 !important;
                display: block !important;
            }
            
            /* Style multiple images for mobile - full card size */
            tbody td:not(:first-child) .exercise-images {
                position: absolute !important;
                top: 8px !important;
                left: 8px !important;
                right: 8px !important;
                bottom: 8px !important;
                width: calc(100% - 16px) !important;
                height: calc(100% - 16px) !important;
                display: flex !important;
                flex-direction: row !important;
                gap: 2px !important;
                z-index: 1 !important;
            }
            
            tbody td:not(:first-child) .exercise-images img {
                flex: 1 !important;
                width: 0 !important;
                height: 100% !important;
                object-fit: cover !important;
                border-radius: 6px !important;
                display: block !important;
            }
            
            
            /* Station rows */
            tbody tr {
                width: 100%;
                margin-bottom: 25px;
                border: 2px solid #3498db;
                border-radius: 12px;
                background: linear-gradient(145deg, #ffffff, #f8f9fa);
                padding: 0;
                box-shadow: 0 8px 20px rgba(52, 152, 219, 0.15);
                display: flex;
                flex-wrap: wrap;
            }
            
            /* Station header */
            tbody td:first-child {
                width: 100% !important;
                background: linear-gradient(135deg, #3498db, #2980b9);
                color: white;
                text-align: center;
                font-weight: 700;
                font-size: 1.1em;
                padding: 15px;
                margin: 0;
                border-radius: 10px 10px 0 0;
                text-transform: uppercase;
                letter-spacing: 1px;
            }
            
            /* Exercise cards - 2 per row with background images */
            tbody td:not(:first-child) {
                width: calc(50% - 8px) !important;
                margin: 4px !important;
                padding: 16px !important;
                min-height: 350px !important;
                border-radius: 8px !important;
                position: relative !important;
                overflow: hidden !important;
            }
            
            /* Ensure text content is visible over full-size images */
            tbody td:not(:first-child) .mobile-step-label {
                position: relative !important;
                z-index: 2 !important;
                background: rgba(255, 255, 255, 0.9) !important;
                padding: 4px 8px !important;
                border-radius: 4px !important;
                margin-bottom: 8px !important;
                backdrop-filter: blur(2px) !important;
            }
            
            /* Remove background and blur from muscle and equipment tags in mobile */
            tbody td:not(:first-child) .muscle-tags,
            tbody td:not(:first-child) .equipment-tags {
                position: relative !important;
                z-index: 2 !important;
                background: none !important;
                padding: 0 !important;
                border-radius: 0 !important;
                margin-bottom: 0 !important;
                backdrop-filter: none !important;
            }
            
            /* Exercise cell wrapper without background blur */
            tbody td:not(:first-child) .exercise-cell-wrapper {
                position: relative !important;
                z-index: 2 !important;
            }
            
            /* Remove background and blur from exercise-cell-wrapper in mobile */
            tbody td:not(:first-child).has-background .exercise-cell-wrapper {
                background: none !important;
                padding: 8px !important;
                border-radius: 0 !important;
                margin-bottom: 8px !important;
                backdrop-filter: none !important;
            }
            
            /* Content wrapper */
            tbody td:not(:first-child) .exercise-cell-wrapper {
                position: relative;
                z-index: 2;
                color: white;
                text-shadow: 1px 1px 2px rgba(0,0,0,0.8);
            }
            
            /* Mobile step labels */
            .mobile-step-label {
                display: block !important;
                background: rgba(41, 128, 185, 0.9);
                color: white;
                padding: 6px 12px;
                margin: -16px -16px 12px -16px;
                font-weight: 600;
                font-size: 0.8em;
                text-align: center;
                border-radius: 6px 6px 0 0;
            }
            
            tbody tr {
                width: 100%;
                margin-bottom: 25px;
                border: 2px solid #3498db;
                border-radius: 12px;
                background: linear-gradient(145deg, #ffffff, #f8f9fa);
                padding: 0;
                box-sizing: border-box;
                box-shadow: 0 8px 20px rgba(52, 152, 219, 0.15);
                position: relative;
                overflow: hidden;
                display: flex;
                flex-wrap: wrap;
            }
            tbody tr:before {
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
                box-sizing: border-box;
                margin-bottom: 8px;
                border-radius: 6px;
                min-height: 60px;
                display: block;
                overflow: visible;
                text-align: center;
            }
            /* Exercise cells - 2 per row */
            tbody td:not(:first-child) {
                display: flex !important;
                text-align: left !important;
                width: calc(50% - 8px) !important;
                margin: 4px;
                flex-direction: column;
            }
            /* Station header - full width */
            tbody td:first-child {
                width: 100% !important;
                margin: 0 0 8px 0;
            }
            /* Station column - make it a header */
            tbody td:first-child {
                background: #3498db !important;
                color: white !important;
                font-weight: 600 !important;
                font-size: 1.2em !important;
                text-align: center !important;
                padding: 15px !important;
                margin: 0 !important;
                border: none !important;
                border-radius: 12px 12px 0 0 !important;
                box-shadow: none !important;
                z-index: 10 !important;
                position: relative !important;
                width: 100% !important;
                display: block !important;
            }
            /* Exercise columns */
            tbody td:not(:first-child) {
                background: rgba(52, 152, 219, 0.05);
                border-left: 4px solid #3498db;
                margin: 0;
                padding: 15px;
                border-radius: 0;
                position: relative;
                overflow: hidden;
            }
            /* Last exercise gets bottom border radius */
            tbody td:last-child {
                border-radius: 0 0 12px 12px !important;
            }
            /* Mobile layout: step info on top, image on bottom for 2-column layout */
            tbody td:not(:first-child) {
                align-items: flex-start;
                justify-content: space-between;
                min-height: 300px;
                gap: 12px;
                padding: 16px;
                flex-direction: column;
            }
            /* Step content - organized layout */
            tbody td:not(:first-child) .exercise-cell-wrapper {
                width: 100%;
                position: relative;
                z-index: 2;
                background: none !important;
                min-height: auto !important;
                order: 1;
                text-align: center;
                display: flex !important;
                flex-direction: column !important;
                align-items: center !important;
                gap: 8px !important;
                flex: 1;
            }
            /* Single images - positioned at bottom */
            .exercise-image {
                position: relative !important;
                top: auto !important;
                left: auto !important;
                right: auto !important;
                bottom: auto !important;
                width: 100px !important;
                height: 100px !important;
                margin: 0 auto !important;
                display: block !important;
                opacity: 1 !important;
                visibility: visible !important;
                z-index: 10 !important;
                object-fit: cover !important;
                border-radius: 8px !important;
                box-shadow: 0 2px 8px rgba(0,0,0,0.2) !important;
                order: 3 !important;
                flex-shrink: 0 !important;
            }
            /* Mobile step labels for 2-column layout */
            tbody td:not(:first-child) .mobile-step-label {
                display: block !important;
                background: #2980b9;
                color: white;
                padding: 6px 12px;
                margin: -16px -16px 12px -16px;
                font-weight: 600;
                font-size: 0.8em;
                text-align: center;
                border-radius: 0;
                order: 0 !important;
            }
            /* Muscle and equipment tags - positioned at bottom in one line */
            tbody td:not(:first-child) .muscle-tags {
                position: absolute !important;
                bottom: 8px !important;
                left: 8px !important;
                right: 50% !important;
                display: flex !important;
                flex-wrap: wrap !important;
                gap: 2px !important;
                justify-content: flex-start !important;
                font-size: 0.65em !important;
                z-index: 2 !important;
                margin: 0 !important;
            }
            
            tbody td:not(:first-child) .equipment-tags {
                position: absolute !important;
                bottom: 8px !important;
                left: 50% !important;
                right: 8px !important;
                display: flex !important;
                flex-wrap: wrap !important;
                gap: 2px !important;
                justify-content: flex-end !important;
                font-size: 0.65em !important;
                z-index: 2 !important;
                margin: 0 !important;
            }
            tbody td:not(:first-child) .muscle-tag,
            tbody td:not(:first-child) .equipment-tag {
                font-size: 0.65em !important;
                padding: 2px 4px !important;
                margin: 1px !important;
            }
            /* Show mobile step labels */
            .mobile-step-label {
                display: block !important;
                background: #2980b9;
                color: white;
                padding: 8px 12px;
                margin: -15px -15px 15px -15px;
                font-weight: 600;
                font-size: 0.9em;
                text-align: center;
                border-radius: 6px 6px 0 0;
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
            /* Picture popup mobile styles removed - images now integrated directly into cards */
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
            min-height: 120px;
            padding: 12px;
        }
        
        /* Mobile-specific layout for exercise content */
        @media (max-width: 768px) {
            .exercise-cell-wrapper {
                display: flex;
                flex-direction: column;
                align-items: center;
                gap: 8px;
                padding: 12px;
                position: relative;
                min-height: 120px;
            }
            
            .exercise-id-badge {
                position: absolute !important;
                top: 8px !important;
                left: 8px !important;
                display: inline-block !important;
                background: #9b59b6 !important;
                color: white !important;
                font-size: 0.75em !important;
                padding: 3px 8px !important;
                border-radius: 12px !important;
                font-weight: 600 !important;
                margin: 0 !important;
                box-shadow: 0 2px 4px rgba(0,0,0,0.3) !important;
                z-index: 3 !important;
            }
            
            /* Picture button mobile styles removed - images now integrated directly into cards */
            
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
    
    # Check if we're in CrossFit path mode for minimal layout
    is_crossfit_path_mode = plan.get("crossfit_path", False)
    
    # Always show the same header (title + subtitle + notes)
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
    
    # (is_crossfit_path_mode already defined above)
    
    # Add CrossFit Path section if provided
    if selected_crossfit_path_exercises:
        if is_crossfit_path_mode:
            # CrossFit path mode: simplified layout without instructions column
            html += f"""
            <div class="crossfit-path-section">
                <h2 class="crossfit-path-title">🔥 CrossFit Path Exercises</h2>
                <p class="crossfit-path-description">Complete these exercises in order</p>
                
                <table>
                    <thead>
                        <tr>
                            <th>Exercise</th>
                        </tr>
                    </thead>
                    <tbody>"""
            
            for idx, exercise in enumerate(selected_crossfit_path_exercises, 1):
                # Create exercise link without picture functionality
                exercise_name = exercise["name"]
                exercise_link = exercise.get("link", "")
                exercise_id = exercise.get("id", -1)
                
                # Format exercise with video only (no pictures)
                if exercise_link and exercise_link != "some url" and exercise_link.strip():
                    # Convert YouTube URLs to embed format
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
                    import re
                    html_id = exercise_name.lower()
                    html_id = html_id.replace(" ", "_").replace("-", "_").replace("+", "plus").replace("→", "to")
                    html_id = html_id.replace("'", "").replace("(", "").replace(")", "").replace("/", "_")
                    html_id = html_id.replace(",", "").replace(".", "").replace(":", "").replace(";", "")
                    html_id = html_id.replace("&", "and").replace("#", "").replace("%", "").replace("@", "")
                    html_id = re.sub(r'[^a-z0-9_]', '', html_id)
                    
                    exercise_html = f'''<span class="exercise-with-video">
            <span class="exercise-name" onclick="toggleVideo('{html_id}')">{exercise_name}</span>
            <div id="video_{html_id}" class="video-popup">
                <iframe src="{embed_url}" frameborder="0" allowfullscreen></iframe>
                <button class="close-video" onclick="toggleVideo('{html_id}')">&times;</button>
            </div></span>'''
                else:
                    exercise_html = f'<span class="exercise-name">{exercise_name}</span>'
                
                # Check if picture exists and add inline image (support multi-images)
                picture_html = ""
                if exercise_id is not None and exercise_id != -1:
                    from pathlib import Path
                    pictures_path = "../config/pictures" if is_workout_store else "config/pictures"
                    
                    # Check for multiple images first (id_1.png, id_2.png, id_3.png)
                    multiple_images = []
                    for i in range(1, 4):  # Check for up to 3 images
                        multi_image_path = Path("config/pictures") / f"{exercise_id}_{i}.png"
                        if multi_image_path.exists():
                            multiple_images.append(f"{pictures_path}/{exercise_id}_{i}.png")
                    
                    if multiple_images:
                        # Display multiple images side by side
                        images_html = ""
                        for img_src in multiple_images:
                            images_html += f'<img src="{img_src}" alt="{exercise_name}" onerror="this.style.display=\'none\'" />'
                        picture_html = f'<br><div class="crossfit-path-multi-images">{images_html}</div>'
                    else:
                        # Fallback to single image
                        absolute_picture_path = Path("config/pictures") / f"{exercise_id}.png"
                        if absolute_picture_path.exists():
                            picture_path = f"{pictures_path}/{exercise_id}.png"
                            picture_html = f'<br><img src="{picture_path}" alt="{exercise_name}" class="crossfit-path-inline-image" onerror="this.style.display=\'none\'" />'
                
                html += f"""
                        <tr>
                            <td class="crossfit-path-exercise">
                                <span class="crossfit-path-number">{idx}</span>
                                <div class="exercise-cell-wrapper">
                                    {exercise_html}
                                    {format_exercise_id_badge(exercise.get("id", None))}
                                </div>
                                {picture_html}
                            </td>
                        </tr>"""
            
            html += """
                    </tbody>
                </table>
            </div>
            """
        else:
            # Regular mode: keep instructions column
            html += f"""
            <div class="crossfit-path-section">
                <h2 class="crossfit-path-title">🔥 CrossFit Path Exercises</h2>
                <p class="crossfit-path-description">Complete these exercises before starting the workout</p>
                
                <table>
                    <thead>
                        <tr>
                            <th>Exercise</th>
                            <th>Instructions</th>
                        </tr>
                    </thead>
                    <tbody>"""
            
            for idx, exercise in enumerate(selected_crossfit_path_exercises, 1):
                html += f"""
                        <tr>
                            <td class="crossfit-path-exercise">
                                <span class="crossfit-path-number">{idx}</span>
                                {format_exercise_link(exercise["name"], exercise.get("link", ""), exercise.get("id", -1), "config/pictures", exercise.get("video_type"))}
                            </td>
                            <td class="crossfit-path-instructions">
                                Perform for 30-60 seconds
                            </td>
                        </tr>"""
            
            html += """
                    </tbody>
                </table>
            </div>
            """
        
        # In CrossFit path mode, skip all other sections and go straight to closing
        if is_crossfit_path_mode:
            html += """
    </div>
    
    <script>
        // Fix image paths based on current location
        function fixImagePaths() {
            const currentPath = window.location.pathname;
            const isInWorkoutStore = currentPath.includes('/workout_store/') || currentPath.includes('\\\\workout_store\\\\');
            
            // Find all crossfit-path-inline-image and multi-image elements
            const images = document.querySelectorAll('.crossfit-path-inline-image, .crossfit-path-multi-images img');
            
            images.forEach(img => {
                let src = img.getAttribute('src');
                
                if (isInWorkoutStore) {
                    // If in workout_store/, ensure path starts with ../
                    if (!src.startsWith('../config/pictures/')) {
                        src = src.replace('config/pictures/', '../config/pictures/');
                        img.setAttribute('src', src);
                    }
                } else {
                    // If in root (index.html), ensure path doesn't start with ../
                    if (src.startsWith('../config/pictures/')) {
                        src = src.replace('../config/pictures/', 'config/pictures/');
                        img.setAttribute('src', src);
                    }
                }
            });
        }
        
        // Fix video paths based on current location
        function fixVideoPaths() {
            const currentPath = window.location.pathname;
            const isInWorkoutStore = currentPath.includes('/workout_store/') || currentPath.includes('\\\\workout_store\\\\');
            
            // Find all video source elements
            const videoSources = document.querySelectorAll('video source');
            
            videoSources.forEach(source => {
                let src = source.getAttribute('src');
                
                if (isInWorkoutStore) {
                    // If in workout_store/, ensure path starts with ../
                    if (!src.startsWith('../config/videos/')) {
                        src = src.replace('config/videos/', '../config/videos/');
                        source.setAttribute('src', src);
                    }
                } else {
                    // If in root (index.html), ensure path doesn't start with ../
                    if (src.startsWith('../config/videos/')) {
                        src = src.replace('../config/videos/', 'config/videos/');
                        source.setAttribute('src', src);
                    }
                }
            });
        }
        
        // Call fixImagePaths and fixVideoPaths when page loads
        document.addEventListener('DOMContentLoaded', function() {
            fixImagePaths();
            fixVideoPaths();
        });
        
        function toggleVideo(exerciseId) {
            const video = document.getElementById('video_' + exerciseId);
            const iframe = video.querySelector('iframe');
            const allVideos = document.querySelectorAll('.video-popup');
            
            // Stop and hide all other videos first
            allVideos.forEach(v => {
                if (v.id !== 'video_' + exerciseId) {
                    stopVideo(v);
                }
            });
            
            if (video.style.display === 'none' || video.style.display === '') {
                // Position video relative to the exercise
                const exerciseElement = video.parentElement;
                positionVideo(video, exerciseElement);
                video.style.display = 'block';
                
                // Start playing
                const src = iframe.src;
                iframe.src = src;
            } else {
                stopVideo(video);
            }
        }
        
        function stopVideo(video) {
            const iframe = video.querySelector('iframe');
            iframe.src = iframe.src; // This stops the video
            video.style.display = 'none';
        }
        
        // togglePicture function removed - images now integrated directly into cards
        
        function positionVideo(videoElement, exerciseElement) {
            const rect = exerciseElement.getBoundingClientRect();
            const spaceRight = window.innerWidth - rect.right;
            const spaceLeft = rect.left;
            const spaceBelow = window.innerHeight - rect.bottom;
            
            const videoWidth = 240;
            const videoHeight = 360;
            
            // Reset positioning
            videoElement.style.position = 'absolute';
            videoElement.style.left = '100%';
            videoElement.style.right = 'auto';
            videoElement.style.top = '0';
            videoElement.style.bottom = 'auto';
            videoElement.style.marginLeft = '20px';
            videoElement.style.marginRight = '0';
            videoElement.style.marginTop = '0';
            videoElement.style.zIndex = '1000';
            
            // Check if we're in a right column (less than video width + margin space)
            if (spaceRight < videoWidth + 20) {
                if (spaceLeft >= videoWidth + 20) {
                    // Position to the left
                    videoElement.style.left = 'auto';
                    videoElement.style.right = '100%';
                    videoElement.style.marginLeft = '0';
                    videoElement.style.marginRight = '20px';
                } else {
                    // Not enough space on either side - use fixed centering
                    videoElement.style.position = 'fixed';
                    videoElement.style.left = '50%';
                    videoElement.style.top = '50%';
                    videoElement.style.transform = 'translate(-50%, -50%)';
                    videoElement.style.margin = '0';
                    videoElement.style.zIndex = '10000';
                    return;
                }
            }
            
            // Handle vertical positioning for non-fixed elements
            if (spaceBelow < videoHeight) {
                // Position above the exercise
                videoElement.style.top = 'auto';
                videoElement.style.bottom = '0';
            }
        }
        
        function positionPicture(pictureElement, exerciseElement) {
            const rect = exerciseElement.getBoundingClientRect();
            const spaceRight = window.innerWidth - rect.right;
            const spaceLeft = rect.left;
            const spaceBelow = window.innerHeight - rect.bottom;
            
            const pictureWidth = 400;
            const pictureHeight = 300;
            
            // Reset positioning
            pictureElement.style.position = 'absolute';
            pictureElement.style.left = '100%';
            pictureElement.style.right = 'auto';
            pictureElement.style.top = '0';
            pictureElement.style.bottom = 'auto';
            pictureElement.style.marginLeft = '20px';
            pictureElement.style.marginRight = '0';
            pictureElement.style.marginTop = '0';
            pictureElement.style.zIndex = '1000';
            
            // Check if we're in a right column (less than picture width + margin space)
            if (spaceRight < pictureWidth + 20) {
                if (spaceLeft >= pictureWidth + 20) {
                    // Position to the left
                    pictureElement.style.left = 'auto';
                    pictureElement.style.right = '100%';
                    pictureElement.style.marginLeft = '0';
                    pictureElement.style.marginRight = '20px';
                } else {
                    // Not enough space on either side - use fixed centering
                    pictureElement.style.position = 'fixed';
                    pictureElement.style.left = '50%';
                    pictureElement.style.top = '50%';
                    pictureElement.style.transform = 'translate(-50%, -50%)';
                    pictureElement.style.margin = '0';
                    pictureElement.style.zIndex = '10000';
                    return;
                }
            }
            
            // Handle vertical positioning for non-fixed elements
            if (spaceBelow < pictureHeight) {
                // Position above the exercise
                pictureElement.style.top = 'auto';
                pictureElement.style.bottom = '0';
            }
        }
        
        // Close video when clicking outside
        document.addEventListener('click', function(e) {
            if (!e.target.closest('.exercise-with-video') && !e.target.closest('.video-popup')) {
                document.querySelectorAll('.video-popup').forEach(video => {
                    stopVideo(video);
                });
            }
            // Picture popup event handlers removed - images now integrated directly into cards
        });
    </script>
</body>
</html>"""
            return html
    
    # Only show stations table and analysis in regular mode, not in CrossFit path mode
    if not (is_crossfit_path_mode and selected_crossfit_path_exercises):
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
                step_video_type_key = f'step{step_num}_video_type'
                
                # Get background image for this exercise
                exercise_id = st.get(step_id_key, None)
                exercise_name = st.get(step_key, '')
                pictures_path = "../config/pictures" if is_workout_store else "config/pictures"
                bg_image_html, has_bg = get_exercise_background_images(exercise_id, exercise_name, pictures_path)
                exercise_class = "exercise has-background" if has_bg else "exercise"
                
                html += f"""
                     <td data-label="Step {step_num}" class="{exercise_class}">
                         <span class="mobile-step-label">Step {step_num}:</span>
                         <div class="exercise-cell-wrapper">
                             {format_exercise_link(st.get(step_key, ''), st.get(step_link_key, ''), st.get(step_id_key, None), pictures_path, st.get(step_video_type_key, None))}
                             {format_exercise_id_badge(st.get(step_id_key, None))}
                         </div>
                         {format_muscle_tags(st.get(step_muscles_key, ''))}
                         {format_equipment_tags(st.get(step_equipment_key, {}))}
                         {bg_image_html}
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
                            {format_exercise_link(exercise["name"], exercise.get("link", ""), exercise.get("id", -1), "config/pictures", exercise.get("video_type"))}
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
    
    # Close the conditional for regular mode sections
    # (This closes the if not is_crossfit_path_mode: block that started before the stations table)
    
    # Add closing elements based on mode
    if is_crossfit_path_mode and selected_crossfit_path_exercises:
        # CrossFit path mode: no timestamp, just close container
        html += """
    </div>"""
    else:
        # Regular mode: include timestamp
        html += f"""
        
        <div class="timestamp">
            Workout generated with Workout Station Generator based on Annya's plan
        </div>
    </div>"""
    
    html += """
    <script>
        // Fix image paths based on current location
        function fixImagePaths() {{
            const currentPath = window.location.pathname;
            const isInWorkoutStore = currentPath.includes('/workout_store/') || currentPath.includes('\\\\workout_store\\\\');
            
            // Find all crossfit-path-inline-image and multi-image elements
            const images = document.querySelectorAll('.crossfit-path-inline-image, .crossfit-path-multi-images img');
            
            images.forEach(img => {{
                let src = img.getAttribute('src');
                
                if (isInWorkoutStore) {{
                    // If in workout_store/, ensure path starts with ../
                    if (!src.startsWith('../config/pictures/')) {{
                        src = src.replace('config/pictures/', '../config/pictures/');
                        img.setAttribute('src', src);
                    }}
                }} else {{
                    // If in root (index.html), ensure path doesn't start with ../
                    if (src.startsWith('../config/pictures/')) {{
                        src = src.replace('../config/pictures/', 'config/pictures/');
                        img.setAttribute('src', src);
                    }}
                }}
            }});
        }}
        
        // Fix video paths based on current location
        function fixVideoPaths() {{
            const currentPath = window.location.pathname;
            const isInWorkoutStore = currentPath.includes('/workout_store/') || currentPath.includes('\\\\workout_store\\\\');
            
            // Find all video source elements
            const videoSources = document.querySelectorAll('video source');
            
            videoSources.forEach(source => {{
                let src = source.getAttribute('src');
                
                if (isInWorkoutStore) {{
                    // If in workout_store/, ensure path starts with ../
                    if (!src.startsWith('../config/videos/')) {{
                        src = src.replace('config/videos/', '../config/videos/');
                        source.setAttribute('src', src);
                    }}
                }} else {{
                    // If in root (index.html), ensure path doesn't start with ../
                    if (src.startsWith('../config/videos/')) {{
                        src = src.replace('../config/videos/', 'config/videos/');
                        source.setAttribute('src', src);
                    }}
                }}
            }});
        }}
        
        // Call fixImagePaths and fixVideoPaths when page loads
        document.addEventListener('DOMContentLoaded', function() {{
            fixImagePaths();
            fixVideoPaths();
        }});
        
        function toggleVideo(exerciseId) {{
            const video = document.getElementById('video_' + exerciseId);
            const iframe = video.querySelector('iframe');
            const videoElement = video.querySelector('video');
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
                
                if (iframe) {{
                    // YouTube video - reload the iframe to start fresh
                    const originalSrc = iframe.getAttribute('data-src') || iframe.src;
                    iframe.setAttribute('data-src', originalSrc);
                    iframe.src = originalSrc;
                }} else if (videoElement) {{
                    // MP4 video - start playing
                    videoElement.currentTime = 0;
                    videoElement.play().catch(e => console.log('Video autoplay prevented:', e));
                }}
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
            const video = videoElement.querySelector('video');
            
            if (iframe) {{
                // YouTube video - stop by clearing and restoring src
                const originalSrc = iframe.getAttribute('data-src') || iframe.src;
                iframe.setAttribute('data-src', originalSrc);
                iframe.src = '';
            }} else if (video) {{
                // MP4 video - pause and reset
                video.pause();
                video.currentTime = 0;
            }}
            
            videoElement.style.display = 'none';
            
            // Hide backdrop if it exists
            const backdrop = document.getElementById('video-backdrop');
            if (backdrop) {{
                backdrop.style.display = 'none';
            }}
        }}
        
        // Picture popup functions removed - images now integrated directly into cards
        
        // Image error handling removed - images now integrated directly into cards
        
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
            // Picture popup event handlers removed - images now integrated directly into cards
        }});
    </script>
</body>
</html>"""
    
    return html 
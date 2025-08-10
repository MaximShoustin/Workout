#!/usr/bin/env python3
"""File I/O utilities for workout generator."""

import csv
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional
import json

from config import WORKOUT_STORE_DIR
from html_generator import generate_html_workout


def save_workout_html(plan: Dict, stations: List[Dict], equipment_requirements: Optional[Dict] = None, validation_summary: Optional[Dict] = None, global_active_rest_schedule: Optional[List[Dict]] = None, selected_active_rest_exercises: Optional[List[Dict]] = None, update_index_html: bool = True, used_exercise_ids: Optional[List[int]] = None) -> Path:
    """Generate HTML workout and save to timestamped file in workout_store directory.
    Also updates index.html in project root for GitHub Pages if update_index_html is True."""
    # Create workout_store directory if it doesn't exist
    WORKOUT_STORE_DIR.mkdir(exist_ok=True)
    
    # Generate filename with current datetime
    timestamp = datetime.now().strftime("%d-%m-%Y-%H-%M-%S")
    filename = f"WORKOUT_{timestamp}.html"
    filepath = WORKOUT_STORE_DIR / filename
    
    # Generate HTML content once
    html_content = generate_html_workout(plan, stations, equipment_requirements, validation_summary, global_active_rest_schedule, selected_active_rest_exercises)
    
    # Save to timestamped file in workout_store directory
    with filepath.open('w', encoding='utf-8') as f:
        f.write(html_content)

    # Write LAST_WORKOUT_PLAN.json with per-station used exercise IDs if stations are provided
    if stations is not None:
        last_plan_path = WORKOUT_STORE_DIR / "LAST_WORKOUT_PLAN.json"
        station_letters = "ABCDEFGHIJKLMNOPQRSTUVWXYZ"
        stations_json = []
        for idx, st in enumerate(stations):
            letter = station_letters[idx]
            # Collect all step IDs for this station
            step_ids = []
            step_num = 1
            while True:
                step_id_key = f"step{step_num}_id"
                if step_id_key in st:
                    step_id = st[step_id_key]
                    if step_id != -1:
                        step_ids.append(step_id)
                    step_num += 1
                else:
                    break
            stations_json.append({"station": letter, "used_exercise_ids": step_ids})
        with last_plan_path.open('w', encoding='utf-8') as f:
            json.dump({"stations": stations_json}, f, indent=2)
    
    # Also save to index.html in project root for GitHub Pages if requested
    if update_index_html:
        index_path = Path("index.html")
        with index_path.open('w', encoding='utf-8') as f:
            f.write(html_content)
    
    return filepath


def write_csv(stations: List[Dict], path: Path, steps_per_station: int = 2) -> None:
    """Write stations data to CSV file with flexible number of steps."""
    with path.open('w', newline='', encoding='utf-8') as csvfile:
        writer = csv.writer(csvfile)
        
        # Generate dynamic headers
        headers = ['Station', 'Area', 'Equipment']
        for step_num in range(1, steps_per_station + 1):
            headers.append(f'Step {step_num}')
        writer.writerow(headers)
        
        letters = "ABCDEFGHIJKLMNOPQRSTUVWXYZ"
        for idx, st in enumerate(stations):
            letter = letters[idx]
            row = [letter, st['area'], st['equipment']]
            
            # Add step data dynamically
            for step_num in range(1, steps_per_station + 1):
                step_key = f'step{step_num}'
                row.append(st.get(step_key, ''))
            
            writer.writerow(row) 
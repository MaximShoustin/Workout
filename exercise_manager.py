#!/usr/bin/env python3
"""Exercise Management CLI
========================

Interactive command-line interface for adding new exercises to the workout database.
Provides guided prompts for exercise data collection, validation, and storage.

Usage:
    python main.py -add
"""

import json
import sys
import re
from pathlib import Path
from typing import Dict, List, Optional, Set
from config import EQUIP_DIR, load_json


class ExerciseManager:
    """Manages exercise data collection, validation, and storage."""
    
    def __init__(self):
        self.valid_areas = ['upper', 'lower', 'core']
        self.valid_categories = {
            'upper_body', 'hinge_power', 'squat_lunge', 'core_carry', 
            'shoulders', 'triceps', 'biceps', 'posterior_chain', 'power'
        }
        self.equipment_files = self._load_equipment_files()
        
    def _load_equipment_files(self) -> Dict[str, Dict]:
        """Load all equipment files and their data."""
        files = {}
        for file_path in EQUIP_DIR.glob("*.json"):
            if file_path.name not in ['active_rest.json', 'crossfit_path.json']:
                try:
                    data = load_json(file_path)
                    files[file_path.stem] = {
                        'path': file_path,
                        'data': data,
                        'categories': list(data.get('lifts', {}).keys())
                    }
                except Exception as e:
                    print(f"⚠️  Warning: Could not load {file_path.name}: {e}")
        return files
    
    def _get_next_exercise_id(self) -> int:
        """Generate the next available exercise ID across all equipment files."""
        max_id = -1
        
        for equipment_name, equipment_info in self.equipment_files.items():
            data = equipment_info['data']
            for category, exercises in data.get('lifts', {}).items():
                for exercise in exercises:
                    if isinstance(exercise, dict):
                        exercise_id = exercise.get('id', -1)
                        if exercise_id > max_id:
                            max_id = exercise_id
        
        return max_id + 1
    
    def _validate_url(self, url: str) -> bool:
        """Validate if the URL is properly formatted."""
        if not url.strip():
            return True  # Empty URL is allowed
        
        url_pattern = re.compile(
            r'^https?://'  # http:// or https://
            r'(?:(?:[A-Z0-9](?:[A-Z0-9-]{0,61}[A-Z0-9])?\.)+[A-Z]{2,6}\.?|'  # domain...
            r'localhost|'  # localhost...
            r'\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})'  # ...or ip
            r'(?::\d+)?'  # optional port
            r'(?:/?|[/?]\S+)$', re.IGNORECASE)
        
        return url_pattern.match(url) is not None
    
    def _validate_muscles(self, muscles: str) -> bool:
        """Validate muscle groups against known muscle groups."""
        if not muscles.strip():
            return False
        
        # Load muscle groups from classification file
        muscle_file = Path('muscle_groups_classification.json')
        if muscle_file.exists():
            try:
                muscle_data = load_json(muscle_file)
                valid_muscles = set()
                
                # Extract all muscle names from the classification
                for category, groups in muscle_data.get('muscle_groups', {}).items():
                    for group, info in groups.items():
                        valid_muscles.update(info.get('muscles', []))
                
                # Check if all provided muscles are valid
                provided_muscles = [m.strip().lower() for m in muscles.split(',')]
                for muscle in provided_muscles:
                    if muscle and muscle not in valid_muscles:
                        print(f"   ⚠️  Unknown muscle: '{muscle}'. Consider adding it to muscle_groups_classification.json")
                        return False
                return True
            except Exception:
                pass
        
        # Fallback validation - just check format
        return bool(re.match(r'^[a-zA-Z\s,]+$', muscles))
    
    def _collect_exercise_data(self) -> Dict:
        """Collect exercise data through interactive prompts."""
        print("🏋️  Adding New Exercise")
        print("=" * 50)
        print()
        
        exercise_data = {}
        
        # Exercise Name
        while True:
            name = input("📝 Exercise name: ").strip()
            if name:
                exercise_data['name'] = name
                break
            print("   ❌ Exercise name is required.")
        
        # Exercise Link (optional)
        while True:
            link = input("🔗 Video link (optional): ").strip()
            if not link or self._validate_url(link):
                exercise_data['link'] = link
                break
            print("   ❌ Please enter a valid URL (starting with http:// or https://)")
        
        # Exercise Area
        print(f"📍 Available areas: {', '.join(self.valid_areas)}")
        while True:
            area = input("📍 Exercise area: ").strip().lower()
            if area in self.valid_areas:
                exercise_data['area'] = area
                break
            print(f"   ❌ Please choose from: {', '.join(self.valid_areas)}")
        
        # Muscles
        print("💪 Muscle groups (comma-separated, e.g., 'chest, triceps, shoulders')")
        while True:
            muscles = input("💪 Muscles: ").strip()
            if self._validate_muscles(muscles):
                exercise_data['muscles'] = muscles
                break
            print("   ❌ Please enter valid muscle groups separated by commas.")
        
        # Unilateral flag
        print("🔄 Is this a unilateral exercise? (requires separate left/right execution)")
        while True:
            unilateral_input = input("🔄 Unilateral (y/n): ").strip().lower()
            if unilateral_input in ['y', 'yes', '1', 'true']:
                exercise_data['unilateral'] = True
                break
            elif unilateral_input in ['n', 'no', '0', 'false']:
                exercise_data['unilateral'] = False
                break
            print("   ❌ Please enter 'y' for yes or 'n' for no.")
        
        # Equipment requirements
        exercise_data['equipment'] = self._collect_equipment_data()
        
        # Skip flag (default False)
        exercise_data['skip'] = False
        
        # Auto-generate ID
        exercise_data['id'] = self._get_next_exercise_id()
        
        return exercise_data
    
    def _collect_equipment_data(self) -> Dict:
        """Collect equipment requirements for the exercise."""
        print("\n🛠️  Equipment Requirements")
        print("Enter equipment needed for this exercise.")
        print("Format: equipment_name (e.g., 'dumbbells_5kg', 'barbells', 'kettlebells_16kg')")
        print("Enter 'done' when finished, or 'none' if no equipment needed.")
        print()
        
        equipment = {}
        
        while True:
            eq_name = input("🛠️  Equipment name (or 'done'/'none'): ").strip()
            
            if eq_name.lower() in ['done', 'finish', 'complete']:
                break
            elif eq_name.lower() in ['none', 'no', 'nothing']:
                break
            elif eq_name:
                # Get count for this equipment
                while True:
                    try:
                        count_input = input(f"   📊 Count for {eq_name}: ").strip()
                        count = int(count_input)
                        if count > 0:
                            equipment[eq_name] = {"count": count}
                            print(f"   ✅ Added: {eq_name} × {count}")
                            break
                        else:
                            print("   ❌ Count must be greater than 0.")
                    except ValueError:
                        print("   ❌ Please enter a valid number.")
            else:
                print("   ❌ Please enter equipment name or 'done'.")
        
        return equipment
    
    def _select_equipment_file(self) -> str:
        """Allow user to select which equipment file to add the exercise to."""
        print("\n📁 Available Equipment Files:")
        print("=" * 30)
        
        file_options = list(self.equipment_files.keys())
        for i, filename in enumerate(file_options, 1):
            categories = self.equipment_files[filename]['categories']
            print(f"{i:2d}. {filename:<20} (categories: {', '.join(categories)})")
        
        print()
        while True:
            try:
                choice = input(f"📁 Select equipment file (1-{len(file_options)}): ").strip()
                index = int(choice) - 1
                if 0 <= index < len(file_options):
                    return file_options[index]
                else:
                    print(f"   ❌ Please enter a number between 1 and {len(file_options)}.")
            except ValueError:
                print("   ❌ Please enter a valid number.")
    
    def _select_category(self, equipment_file: str) -> str:
        """Allow user to select which category within the equipment file."""
        categories = self.equipment_files[equipment_file]['categories']
        
        print(f"\n📂 Available Categories in {equipment_file}:")
        print("=" * 40)
        
        for i, category in enumerate(categories, 1):
            print(f"{i:2d}. {category}")
        
        print()
        while True:
            try:
                choice = input(f"📂 Select category (1-{len(categories)}): ").strip()
                index = int(choice) - 1
                if 0 <= index < len(categories):
                    return categories[index]
                else:
                    print(f"   ❌ Please enter a number between 1 and {len(categories)}.")
            except ValueError:
                print("   ❌ Please enter a valid number.")
    
    def _preview_exercise(self, exercise_data: Dict, equipment_file: str, category: str) -> bool:
        """Show exercise preview and confirm before saving."""
        print("\n" + "=" * 60)
        print("📋 EXERCISE PREVIEW")
        print("=" * 60)
        print(f"Name:       {exercise_data['name']}")
        print(f"Link:       {exercise_data['link'] or '(none)'}")
        print(f"Area:       {exercise_data['area']}")
        print(f"Muscles:    {exercise_data['muscles']}")
        print(f"Unilateral: {'Yes' if exercise_data['unilateral'] else 'No'}")
        print(f"Equipment:  {json.dumps(exercise_data['equipment'], indent=12) if exercise_data['equipment'] else '(none)'}")
        print(f"ID:         {exercise_data['id']}")
        print(f"File:       {equipment_file}.json")
        print(f"Category:   {category}")
        print("=" * 60)
        
        while True:
            confirm = input("💾 Save this exercise? (y/n): ").strip().lower()
            if confirm in ['y', 'yes']:
                return True
            elif confirm in ['n', 'no']:
                return False
            print("   ❌ Please enter 'y' to save or 'n' to cancel.")
    
    def _save_exercise(self, exercise_data: Dict, equipment_file: str, category: str) -> bool:
        """Save the exercise to the appropriate equipment file."""
        try:
            file_info = self.equipment_files[equipment_file]
            file_path = file_info['path']
            data = file_info['data']
            
            # Add exercise to the specified category
            if 'lifts' not in data:
                data['lifts'] = {}
            if category not in data['lifts']:
                data['lifts'][category] = []
            
            data['lifts'][category].append(exercise_data)
            
            # Save the updated file
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
            
            print(f"✅ Exercise '{exercise_data['name']}' saved to {file_path.name}")
            print(f"🆔 Assigned ID: {exercise_data['id']}")
            return True
            
        except Exception as e:
            print(f"❌ Error saving exercise: {e}")
            return False


def add_exercise_cli():
    """Main CLI function for adding exercises."""
    try:
        manager = ExerciseManager()
        
        print("🎯 Interactive Exercise Addition Tool")
        print("=====================================")
        print()
        
        # Collect exercise data
        exercise_data = manager._collect_exercise_data()
        
        # Select equipment file and category
        equipment_file = manager._select_equipment_file()
        category = manager._select_category(equipment_file)
        
        # Preview and confirm
        if manager._preview_exercise(exercise_data, equipment_file, category):
            if manager._save_exercise(exercise_data, equipment_file, category):
                print("\n🎉 Exercise successfully added to the database!")
                print("   You can now use it in your workouts.")
            else:
                print("\n❌ Failed to save exercise.")
                sys.exit(1)
        else:
            print("\n🚫 Exercise addition cancelled.")
            sys.exit(0)
    
    except KeyboardInterrupt:
        print("\n\n🚫 Exercise addition cancelled by user.")
        sys.exit(0)
    except Exception as e:
        print(f"\n❌ Unexpected error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    add_exercise_cli()

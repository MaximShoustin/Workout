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
from config import EQUIP_DIR, load_json, load_plan


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
        """Generate the next available exercise ID using max_id from plan.json."""
        try:
            plan = load_plan()
            max_id = plan.get('max_id', 117)  # Default to 117 if not found
            return max_id + 1
        except Exception as e:
            print(f"⚠️  Warning: Could not read max_id from plan.json: {e}")
            print("   Falling back to scanning all exercise files...")
            
            # Fallback to old method
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
    
    def _validate_muscles(self, muscles_list: List[str]) -> bool:
        """Validate muscle groups against known muscle groups."""
        if not muscles_list:
            return False
        
        # Load muscle groups from classification file
        muscle_file = Path('muscle_groups_classification.json')
        if muscle_file.exists():
            try:
                with open(muscle_file, 'r', encoding='utf-8') as f:
                    muscle_data = json.load(f)
                valid_muscles = set()
                
                # Extract all muscle names from the classification
                for category, groups in muscle_data.get('muscle_groups', {}).items():
                    for group, info in groups.items():
                        valid_muscles.update(info.get('muscles', []))
                
                # Check if all provided muscles are valid
                for muscle in muscles_list:
                    if muscle and muscle.lower() not in valid_muscles:
                        print(f"   ⚠️  Unknown muscle: '{muscle}'. Consider adding it to muscle_groups_classification.json")
                        return False
                return True
            except Exception:
                pass
        
        # Fallback validation - just check that all entries are non-empty strings
        return all(isinstance(m, str) and m.strip() for m in muscles_list)
    
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
        print("💪 Muscle groups (enter one at a time, type 'done' when finished)")
        print("   Examples: chest, triceps, shoulders, biceps, quadriceps, etc.")
        muscles_list = []
        while True:
            muscle = input(f"💪 Muscle {len(muscles_list) + 1} (or 'done'): ").strip()
            if muscle.lower() in ['done', 'finish', 'complete']:
                if muscles_list:
                    if self._validate_muscles(muscles_list):
                        # Save as JSON array
                        exercise_data['muscles'] = muscles_list
                        break
                    else:
                        print("   ❌ Some muscle groups are invalid. Please check and try again.")
                        muscles_list = []  # Reset and start over
                        continue
                else:
                    print("   ❌ Please enter at least one muscle group.")
                    continue
            elif muscle:
                muscles_list.append(muscle)
                print(f"   ✅ Added: {muscle}")
            else:
                print("   ❌ Please enter a muscle group or 'done'.")
        
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
    
    def _get_available_equipment(self) -> Dict[str, int]:
        """Get all available equipment from plan.json."""
        try:
            plan = load_plan()
            equipment_inventory = plan.get('equipment', {})
            
            # Extract equipment names and their available counts
            available_equipment = {}
            for eq_name, eq_info in equipment_inventory.items():
                if isinstance(eq_info, dict) and 'count' in eq_info:
                    available_equipment[eq_name] = eq_info['count']
                elif isinstance(eq_info, int):
                    available_equipment[eq_name] = eq_info
            
            return available_equipment
        except Exception as e:
            print(f"⚠️  Warning: Could not load equipment from plan.json: {e}")
            return {}
    
    def _collect_equipment_data(self) -> Dict:
        """Collect equipment requirements for the exercise."""
        print("\n🛠️  Equipment Requirements")
        print("Enter equipment needed for this exercise.")
        print()
        
        # Show available equipment options
        available_equipment = self._get_available_equipment()
        if available_equipment:
            print("📋 Available Equipment (from plan.json):")
            print("=" * 50)
            
            # Sort equipment by type for better organization
            sorted_equipment = sorted(available_equipment.items())
            for i, (eq_name, available_count) in enumerate(sorted_equipment, 1):
                print(f"{i:2d}. {eq_name:<25} ({available_count}x available)")
            
            print()
            print("💡 You can enter equipment names from the list above, or type custom names.")
        else:
            print("⚠️  Could not load equipment list from plan.json")
            print("Format: equipment_name (e.g., 'dumbbells_5kg', 'barbells', 'kettlebells_16kg')")
        
        print("Enter 'done' when finished, or 'none' if no equipment needed.")
        print()
        
        equipment = {}
        
        while True:
            if available_equipment:
                eq_name = input("🛠️  Equipment name (from list above, custom name, or 'done'/'none'): ").strip()
            else:
                eq_name = input("🛠️  Equipment name (or 'done'/'none'): ").strip()
            
            if eq_name.lower() in ['done', 'finish', 'complete']:
                break
            elif eq_name.lower() in ['none', 'no', 'nothing']:
                break
            elif eq_name:
                # Check if it's a valid equipment name from plan.json
                if eq_name in available_equipment:
                    max_available = available_equipment[eq_name]
                    print(f"   📋 {eq_name}: {max_available}x available in inventory")
                
                # Get count for this equipment
                while True:
                    try:
                        count_input = input(f"   📊 Count needed for {eq_name}: ").strip()
                        count = int(count_input)
                        if count > 0:
                            # Warn if requesting more than available
                            if eq_name in available_equipment and count > available_equipment[eq_name]:
                                print(f"   ⚠️  Warning: Requesting {count}x but only {available_equipment[eq_name]}x available in inventory")
                                confirm = input("   Continue anyway? (y/n): ").strip().lower()
                                if confirm not in ['y', 'yes']:
                                    continue
                            
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
        muscles = exercise_data['muscles']
        if isinstance(muscles, list):
            print(f"Muscles:    {', '.join(muscles)}")
        else:
            print(f"Muscles:    {muscles}")
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
    
    def _update_max_id_in_plan(self, new_max_id: int) -> bool:
        """Update the max_id in plan.json."""
        try:
            plan_path = Path('config/plan.json')
            
            # Read current plan
            with open(plan_path, 'r', encoding='utf-8') as f:
                plan_data = json.load(f)
            
            # Update max_id
            plan_data['max_id'] = new_max_id
            
            # Save updated plan
            with open(plan_path, 'w', encoding='utf-8') as f:
                json.dump(plan_data, f, indent=2, ensure_ascii=False)
            
            print(f"📝 Updated max_id in plan.json to {new_max_id}")
            return True
            
        except Exception as e:
            print(f"⚠️  Warning: Could not update max_id in plan.json: {e}")
            return False
    
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
            
            # Update max_id in plan.json
            self._update_max_id_in_plan(exercise_data['id'])
            
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

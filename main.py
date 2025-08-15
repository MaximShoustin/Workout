#!/usr/bin/env python3
"""Main CLI for generating randomized workout plans."""

import sys
import time
import random
from pathlib import Path
import json

from config import load_plan, die, load_json, ACTIVE_REST_FILE
from equipment import parse_equipment, build_station_pool, get_equipment_validation_summary
from workout_planner import build_plan
from file_utils import save_workout_html
from workout_history import WorkoutHistoryManager, prioritize_exercises_by_variety


def setup_active_rest(plan: dict) -> tuple:
    """Set up active rest mode and return rest pool and modified plan."""
    # Set up active rest mode
    rest_mode = plan.get("active_rest", "auto")
    if rest_mode == "auto":
        plan["active_rest_mode"] = "all_active" if bool(random.getrandbits(1)) else "all_rest"
    elif rest_mode == "mix":
        plan["active_rest_mode"] = "mix"
    elif rest_mode:
        plan["active_rest_mode"] = "all_active"
    else:
        plan["active_rest_mode"] = "all_rest"

    # Check if active rest file exists when needed
    if plan["active_rest_mode"] in ["all_active", "mix"] and not ACTIVE_REST_FILE.exists():
        sys.stderr.write("⚠ active_rest.json not found; falling back to plain rest.\n")
        plan["active_rest_mode"] = "all_rest"

    # Load active rest data if needed
    if plan["active_rest_mode"] in ["all_active", "mix"]:
        rest_data = load_json(ACTIVE_REST_FILE)["rest"]
        # Handle both old string format and new object format for active rest
        rest_pool = []
        skipped_rest_exercises = []
        
        for activity in rest_data:
            if isinstance(activity, dict):
                # Check if exercise should be skipped
                if activity.get("skip", False):
                    skipped_rest_exercises.append(activity["name"])
                    continue  # Skip this exercise
                
                rest_pool.append({"name": activity["name"], "link": activity.get("link", "")})
            else:
                rest_pool.append({"name": activity, "link": ""})
        
        # Report skipped active rest exercises if any
        if skipped_rest_exercises:
            print(f"⏭️  Skipped {len(skipped_rest_exercises)} active rest exercises marked with skip=true:")
            for ex in skipped_rest_exercises:
                print(f"   • {ex}")
            print()
        
        # Shuffle the rest pool for variety
        random.shuffle(rest_pool)
    else:
        rest_pool = []
    
    return rest_pool, plan


def generate_workout_with_retries(max_retries=15):
    """
    Generate a workout with retry logic for equipment conflicts.
    
    Args:
        max_retries: Maximum number of attempts before giving up
        
    Returns:
        Tuple of (plan_result, validation_summary, seed_used)
    """
    plan = load_plan()
    equipment_inventory = plan.get("equipment", {})
    
    # Parse equipment and build station pool once (filtered for feasible exercises)
    gear = parse_equipment()
    station_pool = build_station_pool(gear, equipment_inventory if equipment_inventory else None)
    
    # Initialize workout history for variety optimization (if enabled)
    history_manager = None
    use_history = plan.get("use_workout_history", True)
    
    if use_history:
        history_manager = WorkoutHistoryManager()
        history_summary = history_manager.get_history_summary()
        
        if history_summary["total_workouts"] > 0:
            print(f"🔄 Workout History: {history_summary['total_workouts']} workouts generated, last on {history_summary['last_workout_date']}")
            
            # Apply variety prioritization to promote unused/less-used exercises
            print("🎯 Applying exercise variety optimization...")
            station_pool = prioritize_exercises_by_variety(station_pool, history_manager)
            
            recently_used = history_manager.get_recently_used_exercise_ids(last_n_sessions=2)
            if recently_used:
                print(f"   📉 Deprioritizing {len(recently_used)} recently used exercises")
            print()
        else:
            print("🆕 First workout generation - no history to apply")
            print()
    else:
        print("⚪ Workout history disabled - using random exercise selection")
        print()
    
    print(f"🔄 Attempting to generate workout (max {max_retries} attempts)...")
    print()
    
    for attempt in range(1, max_retries + 1):
        # Use a fixed random seed if edit_mode is true, else use time-based seed
        if plan.get('edit_mode', False):
            # Try to read the seed from LAST_WORKOUT_PLAN.json
            last_plan_path = Path('workout_store/LAST_WORKOUT_PLAN.json')
            seed = 42
            if last_plan_path.exists():
                try:
                    with last_plan_path.open('r', encoding='utf-8') as f:
                        last_plan_data = json.load(f)
                        if 'seed' in last_plan_data:
                            seed = last_plan_data['seed']
                        else:
                            print('⚠️  No seed found in LAST_WORKOUT_PLAN.json, using default seed 42.')
                except Exception as e:
                    print(f'⚠️  Could not read seed from LAST_WORKOUT_PLAN.json: {e}. Using default seed 42.')
            else:
                print('⚠️  LAST_WORKOUT_PLAN.json not found, using default seed 42.')
        else:
            seed = int(time.time() * 1000) % 2147483647  # Ensure it fits in 32-bit int
        random.seed(seed)
        random.shuffle(station_pool)
        
        print(f"🎲 Attempt {attempt}/{max_retries} - Using seed: {seed}")
        
        try:
            # Create fresh copies for this attempt
            station_pool_copy = station_pool.copy()
            plan_copy = plan.copy()  # Create fresh plan copy for each attempt
            rest_pool, plan_with_active_rest = setup_active_rest(plan_copy)
            
            # Try to build the plan (pass the plan with active_rest_mode set)
            plan_result = build_plan(plan_with_active_rest, station_pool_copy, rest_pool)
            
            # If we get here, the plan was successful
            print(f"🎉 Success on attempt {attempt}!")
            print()
            
            # Get validation summary
            validation_summary = get_equipment_validation_summary(
                plan_result["equipment_requirements"], 
                equipment_inventory
            )
            
            return plan_result, validation_summary, seed, plan_with_active_rest, history_manager
            
        except SystemExit as e:
            # Catch the die() call from build_plan when equipment is insufficient
            if attempt < max_retries:
                print(f"❌ Attempt {attempt} failed - trying different combination...")
                print("─" * 60)
            else:
                print(f"❌ All {max_retries} attempts failed!")
                print("💡 Consider:")
                print("   • Reducing number of stations")
                print("   • Adding more equipment to plan.json")
                print("   • Adding more exercise variety to equipment/*.json files")
                print()
                raise
        except Exception as e:
            print(f"❌ Attempt {attempt} failed with error: {e}")
            if attempt == max_retries:
                raise
    
    # This shouldn't be reached, but just in case
    die("Unable to generate valid workout after maximum retries")


def get_exercise_by_id(ex_id, pool):
    for ex in pool:
        if ex[-1] == ex_id:
            return ex
    return None

def get_base_exercise_name(name):
    import re
    return re.sub(r'\s*\((Left|Right)\)$', '', name, flags=re.IGNORECASE)

def reconstruct_stations_from_ids(stations_ids, pool, steps_per_station):
    import random
    station_letters = "ABCDEFGHIJKLMNOPQRSTUVWXYZ"
    stations = []
    # Build a mapping from base name to canonical ID from the pool
    base_name_to_id = {}
    id_to_name = {}
    for ex in pool:
        name = ex[2]
        ex_id = ex[-1]
        base_name = get_base_exercise_name(name)
        base_name_to_id[base_name] = ex_id
        id_to_name[ex_id] = name
    used_names = set()
    used_ids = set()
    for sidx, st in enumerate(stations_ids):
        letter = st.get('station', station_letters[sidx])
        ids = st.get('used_exercise_ids', [])
        station_data = {
            'area': '',
            'equipment': '',
        }
        for step_num, ex_id in enumerate(ids):
            ex = get_exercise_by_id(ex_id, pool)
            if ex is None:
                print(f'⚠️  Warning: Exercise ID {ex_id} not found in equipment database. Using random exercise.')
                ex = random.choice(pool)
            area, equip, name, link, equipment, muscles, unilateral, _ = ex
            base_name = get_base_exercise_name(name)
            canonical_id = base_name_to_id.get(base_name, ex_id)
            canonical_name = id_to_name.get(canonical_id, name)
            # Enforce: never allow two different IDs for the same name, or the same ID for different names
            if canonical_name in used_names or canonical_id in used_ids:
                # Find a unique candidate
                for alt_ex in pool:
                    alt_base = get_base_exercise_name(alt_ex[2])
                    alt_id = alt_ex[-1]
                    alt_name = alt_ex[2]
                    if alt_name not in used_names and alt_id not in used_ids:
                        area, equip, name, link, equipment, muscles, unilateral, _ = alt_ex
                        base_name = get_base_exercise_name(name)
                        canonical_id = alt_id
                        canonical_name = alt_name
                        break
            if step_num == 0:
                station_data['area'] = area
                station_data['equipment'] = equip
            station_data[f'step{step_num+1}'] = canonical_name
            station_data[f'step{step_num+1}_link'] = link
            station_data[f'step{step_num+1}_equipment'] = equipment
            station_data[f'step{step_num+1}_muscles'] = muscles
            station_data[f'step{step_num+1}_id'] = canonical_id
            used_names.add(canonical_name)
            used_ids.add(canonical_id)
        stations.append(station_data)
    return stations


def main():
    """Main entry point for workout generation."""
    plan = load_plan()
    if edit_ids is not None:
        if not plan.get('edit_mode', False):
            print('❌ Error: -edit flag can only be used when "edit_mode": true in plan.json.')
            sys.exit(1)
        # Validate edit_ids against LAST_WORKOUT_PLAN.json
        last_plan_path = Path('workout_store/LAST_WORKOUT_PLAN.json')
        if not last_plan_path.exists():
            print('❌ Error: LAST_WORKOUT_PLAN.json not found. Cannot use -edit.')
            sys.exit(1)
        with last_plan_path.open('r', encoding='utf-8') as f:
            last_plan_data = json.load(f)
        # Collect all used_exercise_ids from all stations
        used_ids = set()
        for st in last_plan_data.get('stations', []):
            used_ids.update(st.get('used_exercise_ids', []))
        filtered_edit_ids = []
        for eid in edit_ids:
            if eid not in used_ids:
                print(f'⚠️  Warning: Exercise ID {eid} not found in current workout. Skipping.')
            else:
                filtered_edit_ids.append(eid)
        if not filtered_edit_ids:
            print('❌ Error: None of the provided IDs to edit are present in the current workout.')
            sys.exit(1)
        # Store for use in next step
        edit_ids[:] = filtered_edit_ids

        # --- Begin replacement logic ---
        # 1. Build a set of all used exercise IDs (excluding those to be replaced)
        current_stations = last_plan_data['stations']
        ids_to_replace = set(edit_ids)
        # --- NEW: Expand edit_ids to include both sides of any unilateral exercise ---
        # Get all names and IDs from the pool
        plan_equipment = plan.get('equipment', {})
        gear = parse_equipment()
        pool = build_station_pool(gear, plan_equipment if plan_equipment else None)
        id_to_name = {ex[-1]: ex[2] for ex in pool if ex[-1] != -1}
        # Expand edit_ids to include both sides for any unilateral exercise
        expanded_edit_ids = set(edit_ids)
        for sidx, st in enumerate(current_stations):
            used_ids = st.get('used_exercise_ids', [])
            # Build a map of base name to all step indices for this station
            base_name_to_indices = {}
            for idx, eid in enumerate(used_ids):
                name = id_to_name.get(eid, None)
                if name:
                    base = get_base_exercise_name(name)
                    base_name_to_indices.setdefault(base, []).append((idx, eid))
            # If any eid in edit_ids is in this station, add all steps with the same base name
            for eid in edit_ids:
                name = id_to_name.get(eid, None)
                if name:
                    base = get_base_exercise_name(name)
                    for idx, eid2 in base_name_to_indices.get(base, []):
                        expanded_edit_ids.add(eid2)
        edit_ids[:] = list(expanded_edit_ids)
        # 2. Get all available exercises from the pool
        plan_equipment = plan.get('equipment', {})
        gear = parse_equipment()
        pool = build_station_pool(gear, plan_equipment if plan_equipment else None)
        # Map: exercise_id -> pool tuple
        pool_by_id = {ex[-1]: ex for ex in pool if ex[-1] != -1}
        # 3. Find all locations (station, step) for each ID to replace
        locations = []  # (station_idx, step_idx, old_id)
        for sidx, st in enumerate(current_stations):
            for step_idx, eid in enumerate(st['used_exercise_ids']):
                if eid in ids_to_replace:
                    locations.append((sidx, step_idx, eid))
        # 4. For each ID to replace, pick a new valid exercise
        import secrets
        new_seed = secrets.randbits(32)  # Generate a new seed for replacement randomness
        random.seed(new_seed)            # Reseed RNG for replacement selection
        replacement_map = {}
        keep_ids = set()
        for st in current_stations:
            for eid in st['used_exercise_ids']:
                if eid not in ids_to_replace:
                    keep_ids.add(eid)
        already_used = keep_ids.copy()
        # In replacement logic, only allow a replacement if the new exercise name is not already present in the workout, and never assign the same ID to two different names
        # Set stations_to_use depending on workflow
        if edit_ids is not None:
            rebuilt_stations = reconstruct_stations_from_ids(current_stations, pool, plan.get('steps_per_station', 2))
            stations_to_use = rebuilt_stations
        else:
            stations_to_use = plan_result["stations"]
        # Use stations_to_use everywhere below
        all_used_names = set()
        for st in stations_to_use:
            step_num = 1
            while True:
                key = f'step{step_num}'
                if key in st:
                    all_used_names.add(st[key])
                    step_num += 1
                else:
                    break
        for (sidx, step_idx, old_id) in locations:
            # Get the original exercise to determine its area for balance_order compliance
            old_ex = get_exercise_by_id(old_id, pool)
            if old_ex is None:
                print(f'⚠️  Warning: Original exercise ID {old_id} not found, allowing any area for replacement.')
                original_area = None
            else:
                original_area = old_ex[0]  # area is the first element in the tuple
            
            # Find a replacement not already in the workout (by name and ID) and from the same area
            if original_area is not None:
                candidates = [ex for exid, ex in pool_by_id.items()
                              if exid not in already_used and exid not in ids_to_replace and ex[2] not in all_used_names and ex[0] == original_area]
                print(f'   🎯 Looking for {original_area} replacement for exercise ID {old_id}...')
            else:
                candidates = [ex for exid, ex in pool_by_id.items()
                              if exid not in already_used and exid not in ids_to_replace and ex[2] not in all_used_names]
                print(f'   🎯 Looking for any area replacement for exercise ID {old_id}...')
            
            if not candidates:
                if original_area is not None:
                    print(f'❌ Error: No available {original_area} replacement for exercise ID {old_id}.')
                    print(f'   💡 Try expanding your {original_area} exercise database or reducing edit scope.')
                else:
                    print(f'❌ Error: No available replacement for exercise ID {old_id}.')
                sys.exit(1)
            new_ex = random.choice(candidates)
            new_id = new_ex[-1]
            new_name = new_ex[2]
            new_area = new_ex[0]
            replacement_map[old_id] = new_id
            # Update the station's used_exercise_ids
            current_stations[sidx]['used_exercise_ids'][step_idx] = new_id
            already_used.add(new_id)
            all_used_names.add(new_name)
            print(f'   ✅ Replaced {old_id} → {new_id} ({new_name}) [area: {new_area}]')
        # 5. Log the mapping
        print(f'🔄 Replacement summary (using new seed {new_seed}):')
        for old_id, new_id in replacement_map.items():
            print(f'   Replaced {old_id} → {new_id}')
        # 6. Regenerate the HTML and JSON outputs
        # Reconstruct full station dicts for HTML and JSON output
        steps_per_station = plan.get('steps_per_station', 2)
        rebuilt_stations = reconstruct_stations_from_ids(current_stations, pool, steps_per_station)
        # Save new LAST_WORKOUT_PLAN.json with updated stations (seed stays the same)
        for st in current_stations:
            if 'area' not in st:
                st['area'] = ''
        last_plan_data['stations'] = current_stations
        print('DEBUG: current_stations just before write:', current_stations)
        print('DEBUG: last_plan_data["stations"] just before write:', last_plan_data['stations'])
        print(f'📝 Attempting to write LAST_WORKOUT_PLAN.json to: {last_plan_path.absolute()}')
        try:
            with last_plan_path.open('w', encoding='utf-8') as f:
                json.dump(last_plan_data, f, indent=2)
                f.flush()
                import os
                os.fsync(f.fileno())
            print(f'✅ LAST_WORKOUT_PLAN.json updated with new stations (seed unchanged).')
            for st in current_stations:
                print(f"   Station {st.get('station', '?')}: {st.get('used_exercise_ids', [])}")
            # Immediately read back and print file contents
            with last_plan_path.open('r', encoding='utf-8') as f:
                print('DEBUG: File contents immediately after write:')
                print(f.read())
            # Regenerate the HTML report using the reconstructed station structure
            from workout_planner import get_station_equipment_requirements
            equipment_requirements = {}
            people_per_station = plan.get('people_per_station', 1)
            for st in rebuilt_stations:
                step_equipments = []
                step_num = 1
                while True:
                    key = f'step{step_num}_equipment'
                    if key in st:
                        step_equipments.append(st[key])
                        step_num += 1
                    else:
                        break
                req = get_station_equipment_requirements(step_equipments, people_per_station)
                for eq_type, eq_info in req.items():
                    if eq_type in equipment_requirements:
                        equipment_requirements[eq_type]['count'] += eq_info['count']
                    else:
                        equipment_requirements[eq_type] = dict(eq_info)
            global_active_rest_schedule = last_plan_data.get('global_active_rest_schedule')
            selected_active_rest_exercises = last_plan_data.get('selected_active_rest_exercises')
            # Use the existing seed from LAST_WORKOUT_PLAN.json for HTML
            filename = save_workout_html(plan, rebuilt_stations, equipment_requirements=equipment_requirements, global_active_rest_schedule=global_active_rest_schedule, selected_active_rest_exercises=selected_active_rest_exercises, update_index_html=True, seed=last_plan_data.get('seed'))
            print(f'✅ HTML report regenerated: {filename}')
            return  # Prevent further execution and overwriting in normal workflow
        except Exception as e:
            print(f'❌ Error writing LAST_WORKOUT_PLAN.json: {e}')
        # 7. Regenerate the HTML report using the updated station structure
        # Use the same plan and other parameters as before, but with updated stations and new seed
        steps_per_station = plan.get('steps_per_station', 2)
        rebuilt_stations = reconstruct_stations_from_ids(current_stations, pool, steps_per_station)
        # Compute equipment_requirements from rebuilt_stations
        from workout_planner import get_station_equipment_requirements
        equipment_requirements = {}
        people_per_station = plan.get('people_per_station', 1)
        for st in stations_to_use:
            step_equipments = []
            step_num = 1
            while True:
                key = f'step{step_num}_equipment'
                if key in st:
                    step_equipments.append(st[key])
                    step_num += 1
                else:
                    break
            req = get_station_equipment_requirements(step_equipments, people_per_station)
            for eq_type, eq_info in req.items():
                if eq_type in equipment_requirements:
                    equipment_requirements[eq_type]['count'] += eq_info['count']
                else:
                    equipment_requirements[eq_type] = dict(eq_info)
        # Try to reconstruct global_active_rest_schedule and selected_active_rest_exercises from plan if possible
        global_active_rest_schedule = None
        selected_active_rest_exercises = None
        if 'global_active_rest_schedule' in last_plan_data:
            global_active_rest_schedule = last_plan_data['global_active_rest_schedule']
        if 'selected_active_rest_exercises' in last_plan_data:
            selected_active_rest_exercises = last_plan_data['selected_active_rest_exercises']
        filename = save_workout_html(plan, stations_to_use, equipment_requirements=equipment_requirements, global_active_rest_schedule=global_active_rest_schedule, selected_active_rest_exercises=selected_active_rest_exercises, update_index_html=True, seed=new_seed)
        print(f'✅ HTML report regenerated: {filename}')
        return
    try:
        plan_result, validation_summary, seed_used, plan, history_manager = generate_workout_with_retries()
        
        # Print validation status
        if validation_summary["is_valid"]:
            print("✅ Equipment validation: All requirements can be satisfied")
        else:
            print("⚠️ Equipment validation: Some requirements exceed available inventory")
            for issue in validation_summary["issues"]:
                print(f"   • {issue}")
        
        # Save the HTML file  
        update_index_html = plan.get("use_workout_history", True)
        used_exercise_ids = plan_result.get("used_exercise_ids", [])
        filename = save_workout_html(plan, plan_result["stations"], plan_result["equipment_requirements"], validation_summary, plan_result["global_active_rest_schedule"], plan_result["selected_active_rest_exercises"], update_index_html=update_index_html, used_exercise_ids=used_exercise_ids, seed=seed_used)
        print(f"✅ Workout saved to: {filename}")
        print(f"🌐 Open in browser: file://{filename.absolute()}")
        print(f"🎲 Final seed used: {seed_used}")
        print()
        
        # Record workout session for variety tracking (if history is enabled)
        if history_manager is not None:
            workout_title = plan.get("title", "Workout")
            used_exercise_ids = plan_result.get("used_exercise_ids", [])
            
            # Record the session
            if used_exercise_ids:
                history_manager.record_workout_session(workout_title, used_exercise_ids)
        
    except KeyboardInterrupt:
        print("\n⚠️ Workout generation cancelled by user")
        sys.exit(1)
    except Exception as e:
        print(f"❌ Error generating workout: {e}")
        sys.exit(1)


def parse_edit_args():
    import sys
    edit_ids = None
    if '-edit' in sys.argv:
        idx = sys.argv.index('-edit')
        if idx + 1 >= len(sys.argv):
            print('❌ Error: -edit flag provided but no list of IDs given.')
            sys.exit(1)
        id_str = sys.argv[idx + 1]
        if not id_str.strip():
            print('❌ Error: -edit flag provided but list is empty.')
            sys.exit(1)
        try:
            edit_ids = [int(x) for x in id_str.split(',') if x.strip()]
            if not edit_ids:
                print('❌ Error: -edit flag provided but list is empty.')
                sys.exit(1)
        except Exception:
            print('❌ Error: -edit flag provided but list is malformed. Use comma-separated integers, e.g. -edit 1,2,3')
            sys.exit(1)
    return edit_ids


if __name__ == "__main__":
    edit_ids = parse_edit_args()
    main() 
#!/usr/bin/env python3
"""Core workout planning and generation logic."""

import random
from typing import Dict, List, Tuple

from equipment import merge_equipment_requirements


def next_active_rest(rest_pool: List[dict], used_rest: List[dict]) -> dict:
    """Get next active rest activity, cycling through pool when empty."""
    if len(rest_pool) == 0:
        rest_pool.extend(used_rest)
        random.shuffle(rest_pool)
        used_rest.clear()
    drill = rest_pool.pop()
    used_rest.append(drill)
    return drill


def get_station_equipment_requirements(step_equipments: list, people_per_station: int = 1) -> dict:
    """
    Calculate equipment requirements for a single station with N steps.
    
    The calculation depends on whether exercises happen simultaneously or sequentially:
    - If people_per_station > 1: All steps happen simultaneously (need sum of all step equipment)
    - If people_per_station = 1: All steps are sequential (need MAX of all step equipment)
    
    Args:
        step_equipments: List of equipment dicts for each step [step1_equipment, step2_equipment, ...]
        people_per_station: Number of people assigned to this station
        
    Returns:
        Dict with equipment requirements for the station
    """
    if not step_equipments:
        return {}
    
    station_requirements = {}
    
    # Get all equipment types from all steps
    all_equipment_types = set()
    for step_equipment in step_equipments:
        all_equipment_types.update(step_equipment.keys())
    
    for equipment_type in all_equipment_types:
        step_counts = []
        for step_equipment in step_equipments:
            count = step_equipment.get(equipment_type, {}).get("count", 0)
            step_counts.append(count)
        
        if people_per_station > 1:
            # Multiple people per station: all steps happen simultaneously
            # Need equipment for all exercises at the same time
            required_count = sum(step_counts)
        else:
            # Single person per station: all steps are sequential
            # Need the maximum of all exercises
            required_count = max(step_counts) if step_counts else 0
        
        if required_count > 0:
            station_requirements[equipment_type] = {"count": required_count}
    
    return station_requirements


def can_add_station_to_workout(step_equipments: list, cumulative_station_usage: dict, available_inventory: dict, people_per_station: int = 1) -> bool:
    """
    Check if adding a station with given step exercises would exceed equipment limits.
    
    Args:
        step_equipments: List of equipment dicts for each step [step1_equipment, step2_equipment, ...]
        cumulative_station_usage: Current total equipment usage across all stations
        available_inventory: Available equipment from plan.json
        people_per_station: Number of people assigned to each station
        
    Returns:
        True if station can be added without exceeding limits
    """
    if not available_inventory:
        return True  # No validation if no inventory defined
    
    # Get equipment requirements for this station (considering simultaneous vs sequential execution)
    station_requirements = get_station_equipment_requirements(step_equipments, people_per_station)
    
    # Simulate adding this station's requirements to cumulative usage
    test_usage = {}
    for equipment_type, equipment_info in cumulative_station_usage.items():
        test_usage[equipment_type] = {"count": equipment_info["count"]}  # Deep copy
    
    for equipment_type, equipment_info in station_requirements.items():
        if equipment_type in test_usage:
            test_usage[equipment_type]["count"] += equipment_info["count"]
        else:
            test_usage[equipment_type] = {"count": equipment_info["count"]}
    
    # Check if any equipment would be exceeded
    for equipment_type, usage_info in test_usage.items():
        required_count = usage_info.get("count", 0)
        available_count = available_inventory.get(equipment_type, {}).get("count", 0)
        
        if required_count > available_count:
            return False
    
    return True


def report_station_equipment_status(station_num: int, step_exercises: list, step_equipments: list, 
                                   cumulative_station_usage: dict, available_inventory: dict, people_per_station: int = 1) -> None:
    """Report equipment status after adding a complete station."""
    if not available_inventory:
        return
    
    # Calculate station requirements (considering simultaneous vs sequential execution)
    station_requirements = get_station_equipment_requirements(step_equipments, people_per_station)
    
    print(f"📊 Station {station_num} Equipment Summary:")
    for i, (exercise, equipment) in enumerate(zip(step_exercises, step_equipments), 1):
        print(f"   Step {i}: {exercise} → {equipment}")
    if people_per_station > 1:
        print(f"   Station needs: {station_requirements} (simultaneous execution with {people_per_station} people)")
    else:
        print(f"   Station needs: {station_requirements} (sequential execution)")
    print()
    
    # Show current utilization across all stations
    print("   🏢 Total Equipment Usage Across All Stations:")
    equipment_warnings = []
    
    for equipment_type in sorted(set(list(cumulative_station_usage.keys()) + list(available_inventory.keys()))):
        used = cumulative_station_usage.get(equipment_type, {}).get("count", 0)
        available = available_inventory.get(equipment_type, {}).get("count", 0)
        
        if used > 0 or available > 0:
            remaining = max(0, available - used)
            utilization_pct = (used / available * 100) if available > 0 else 0
            
            # Clean up equipment name for display
            display_name = equipment_type.replace("_", " ").replace("kg", " kg").title()
            display_name = display_name.replace("Dumbbells", "Dumbbell").replace("Kettlebells", "Kettlebell")
            
            status_line = f"   • {display_name}: {used}/{available} stations using it"
            
            if used > available:
                status_line += " ⚠️ EXCEEDED!"
                equipment_warnings.append(f"{display_name} exceeded capacity")
            elif remaining == 0:
                status_line += " ⚠️ FULL"
                equipment_warnings.append(f"{display_name} at full capacity")
            elif utilization_pct >= 80:
                status_line += f" ⚠️ {utilization_pct:.0f}% used"
                equipment_warnings.append(f"{display_name} approaching limit")
            elif used > 0:
                status_line += f" ({utilization_pct:.0f}% used, {remaining} remaining)"
            
            if used > 0 or available > 0:
                print(status_line)
    
    if equipment_warnings:
        print(f"   ⚠️  Warnings: {', '.join(equipment_warnings)}")
    
    print("─" * 60)


def select_best_equipment_option(exercise_equipment: dict, available_inventory: dict) -> dict:
    """
    Select the best available equipment option from alternatives.
    
    For exercises with multiple equipment options (e.g., different dumbbell weights),
    choose the most appropriate available option instead of requiring all options.
    
    Args:
        exercise_equipment: Dict of equipment alternatives
        available_inventory: Available equipment from plan.json
        
    Returns:
        Dict with single selected equipment option
    """
    if not exercise_equipment or not available_inventory:
        return exercise_equipment
    
    # Group equipment by base type (e.g., "dumbbells", "kettlebells")
    equipment_groups = {}
    other_equipment = {}
    
    for equipment_type, equipment_info in exercise_equipment.items():
        base_type = equipment_type.split('_')[0]  # e.g., "dumbbells" from "dumbbells_10kg"
        
        if base_type in ['dumbbells', 'kettlebells', 'slam_balls']:
            if base_type not in equipment_groups:
                equipment_groups[base_type] = []
            equipment_groups[base_type].append((equipment_type, equipment_info))
        else:
            # Non-weight equipment (bench, barbells, etc.) - keep as is
            other_equipment[equipment_type] = equipment_info
    
    selected_equipment = other_equipment.copy()
    
    # For each equipment group, select the best available option
    for base_type, options in equipment_groups.items():
        best_option = None
        best_score = -1
        
        for equipment_type, equipment_info in options:
            required_count = equipment_info.get("count", 1)
            available_count = available_inventory.get(equipment_type, {}).get("count", 0)
            
            # Score based on availability and efficiency
            if available_count >= required_count:
                # Prefer options that use equipment more efficiently
                efficiency_score = available_count - required_count
                utilization_score = required_count / max(available_count, 1)
                total_score = efficiency_score + utilization_score
                
                if total_score > best_score:
                    best_score = total_score
                    best_option = (equipment_type, equipment_info)
        
        # If we found a good option, use it
        if best_option:
            equipment_type, equipment_info = best_option
            selected_equipment[equipment_type] = equipment_info
        else:
            # No good options available, use the first one (for error reporting)
            equipment_type, equipment_info = options[0]
            selected_equipment[equipment_type] = equipment_info
    
    return selected_equipment


def check_must_use_equipment(plan: dict, stations: List[dict], available_inventory: dict) -> List[str]:
    """
    Check if must-use equipment types are being used in the workout.
    
    Args:
        plan: Workout plan configuration
        stations: List of completed stations
        available_inventory: Available equipment
        
    Returns:
        List of warnings about unused must-use equipment
    """
    # Define must-use equipment based on your requirements
    must_use_equipment = []
    
    # Only require equipment if it's available
    if available_inventory.get("plyo_box", {}).get("count", 0) > 0:
        must_use_equipment.append("plyo_box")
    if available_inventory.get("slam_balls_4kg", {}).get("count", 0) > 0 or \
       available_inventory.get("slam_balls_5kg", {}).get("count", 0) > 0 or \
       available_inventory.get("slam_balls_6kg", {}).get("count", 0) > 0:
        must_use_equipment.append("slam_balls")
    if available_inventory.get("dip_parallel_bars", {}).get("count", 0) > 0:
        must_use_equipment.append("dip_parallel_bars")
    if available_inventory.get("barbells", {}).get("count", 0) > 1:  # Only if we have both barbells
        must_use_equipment.append("barbells")
    
    warnings = []
    used_equipment = set()
    
    # Collect all used equipment types
    for station in stations:
        for equipment_dict in [station.get('step1_equipment', {}), station.get('step2_equipment', {})]:
            used_equipment.update(equipment_dict.keys())
    
    # Check for unused must-use equipment
    for must_use in must_use_equipment:
        if must_use == "slam_balls":
            # Check if any slam ball type is used
            slam_ball_used = any(eq_type.startswith("slam_balls_") for eq_type in used_equipment)
            if not slam_ball_used:
                warnings.append("Slam balls available but not used - consider adding slam ball exercises")
        elif must_use not in used_equipment:
            display_name = must_use.replace("_", " ").title()
            warnings.append(f"{display_name} available but not used - consider adding exercises that use it")
    
    return warnings


def filter_exercises_by_remaining_equipment(station_pool: List[Tuple[str, str, str, str, dict]], 
                                          cumulative_station_usage: dict, 
                                          available_inventory: dict, 
                                          people_per_station: int = 1) -> List[Tuple[str, str, str, str, dict]]:
    """
    Filter exercise pool to only include exercises that can be performed with remaining equipment.
    
    Args:
        station_pool: Current pool of available exercises
        cumulative_station_usage: Equipment already used by completed stations
        available_inventory: Total equipment inventory
        people_per_station: Number of people per station (affects equipment calculation)
        
    Returns:
        Filtered list of exercises that can still be performed
    """
    if not available_inventory:
        return station_pool
    
    filtered_pool = []
    
    for exercise_tuple in station_pool:
        area, equip_name, exercise_name, exercise_link, equipment_data, muscles, unilateral, exercise_id = exercise_tuple
        
        # Select best equipment option for this exercise
        selected_equipment = select_best_equipment_option(equipment_data, available_inventory)
        
        # Check if this exercise can be used in any step of a new station
        # For N-step stations, we need to check if this exercise could work as ANY step
        # The most optimistic scenario is that this exercise is the ONLY one requiring this equipment
        can_be_used = True
        
        # Check if adding this single exercise in a new station would exceed limits
        # For filtering, we only check if this individual exercise can be performed
        # The people_per_station multiplier is handled at the station level, not exercise level
        for equipment_type, equipment_info in selected_equipment.items():
            required_count = equipment_info.get("count", 0)
            current_usage = cumulative_station_usage.get(equipment_type, {}).get("count", 0)
            available_count = available_inventory.get(equipment_type, {}).get("count", 0)
            
            if current_usage + required_count > available_count:
                can_be_used = False
                break
        
        # If exercise can potentially be used, keep it in the pool
        if can_be_used:
            filtered_pool.append(exercise_tuple)
    
    return filtered_pool


def prioritize_must_use_exercises(station_pool: List[Tuple[str, str, str, str, dict, str, bool, int]], 
                                 must_use_equipment: List[str],
                                 cumulative_station_usage: dict,
                                 available_inventory: dict) -> List[str]:
    """
    Get list of must-use equipment that hasn't been used yet and prioritize exercises that use them.
    
    Args:
        station_pool: Available exercises  
        must_use_equipment: List of equipment types that must be used
        cumulative_station_usage: Equipment already used by completed stations
        available_inventory: Total equipment inventory
        
    Returns:
        List of unused must-use equipment types
    """
    if not must_use_equipment:
        return []
    
    unused_must_use = []
    
    for equipment_type in must_use_equipment:
        # Check if this equipment type has been used
        used_count = cumulative_station_usage.get(equipment_type, {}).get("count", 0)
        available_count = available_inventory.get(equipment_type, {}).get("count", 0)
        
        # If we have the equipment and haven't used it yet (or haven't fully utilized it), mark as unused
        if available_count > 0 and used_count < available_count:
            unused_must_use.append(equipment_type)
    
    # Sort unused must-use equipment to prioritize the most constrained ones first
    # plyo_box has the fewest exercises, so it should be tried first
    priority_order = ["plyo_box", "bench", "dip_parallel_bars", "barbells", "slam_balls_5kg", "dumbbells_3kg", "dumbbells_5kg"]
    
    def get_priority(equipment_type):
        if equipment_type in priority_order:
            return priority_order.index(equipment_type)
        return len(priority_order)  # Unknown equipment goes last
    
    unused_must_use.sort(key=get_priority)
    return unused_must_use


def find_exercise_using_equipment(station_pool: List[Tuple[str, str, str, str, dict, str, bool, int]], 
                                equipment_type: str,
                                area_target: str = None,
                                used_names: set = None) -> Tuple:
    """
    Find an exercise that uses specific equipment type.
    
    Args:
        station_pool: Available exercises
        equipment_type: Equipment type to find exercises for
        area_target: Preferred area (optional)
        used_names: Set of already used exercise names
        
    Returns:
        Exercise tuple or None if not found
    """
    if used_names is None:
        used_names = set()
    
    # Filter to unused exercises that use the target equipment
    candidates = []
    for exercise_tuple in station_pool:
        area, equip_name, exercise_name, exercise_link, equipment_data, muscles, unilateral, exercise_id = exercise_tuple
        if exercise_name not in used_names and equipment_type in equipment_data:
            candidates.append(exercise_tuple)
    
    if not candidates:
        return None
    
    # Prefer exercises from target area if specified
    if area_target:
        area_matches = [ex for ex in candidates if ex[0] == area_target]
        if area_matches:
            return random.choice(area_matches)
    
    # Return any compatible exercise
    return random.choice(candidates)


def find_compatible_exercises_for_station(station_pool: List[Tuple[str, str, str, str, dict]], 
                                        area_target: str,
                                        steps_per_station: int,
                                        cumulative_station_usage: dict, 
                                        available_inventory: dict, 
                                        people_per_station: int = 1,
                                        used_names: set = None,
                                        must_use_equipment: List[str] = None,
                                        use_workout_history: bool = True) -> List[Tuple]:
    """
    Find N compatible exercises for a station that can be performed with remaining equipment.
    
    Args:
        station_pool: Available exercises
        area_target: Preferred area for exercises
        steps_per_station: Number of exercises needed for this station
        cumulative_station_usage: Equipment already used
        available_inventory: Total equipment inventory  
        people_per_station: Number of people per station
        used_names: Set of already used exercise names
        must_use_equipment: List of equipment that should be prioritized
        
    Returns:
        List of exercise tuples or empty list if no valid combination found
    """
    if not available_inventory or steps_per_station <= 0:
        return []
    
    if used_names is None:
        used_names = set()
    
    # Filter pool to only exercises that haven't been used
    available_exercises = [ex for ex in station_pool if ex[2] not in used_names]
    
    if len(available_exercises) < steps_per_station:
        return []  # Not enough exercises available
    
    # Helper function to check if exercise uses must-use equipment
    def uses_must_use_equipment(exercise_tuple):
        if not must_use_equipment:
            return False
        _, _, _, _, equipment, _, _, _ = exercise_tuple
        return any(eq_type in equipment for eq_type in must_use_equipment)
    
    # Helper function for variety optimization (if enabled)
    def get_variety_score(exercise_tuple):
        if not use_workout_history:
            # If history is disabled, return random score
            import random
            return random.random()
        
        # Use workout history for variety optimization
        try:
            from workout_history import WorkoutHistoryManager
            history_manager = WorkoutHistoryManager()
            exercise_id = exercise_tuple[7] if exercise_tuple[7] != -1 else 0
            return history_manager.calculate_exercise_priority_score(exercise_id)
        except:
            # Fallback to random if history system unavailable
            import random
            return random.random()
    
    # Try to find N compatible exercises, prioritizing target area
    def try_combination(exercises_to_try, selected_exercises, remaining_steps):
        if remaining_steps <= 0:
            # Check if all selected exercises can work together
            step_equipments = []
            for exercise in selected_exercises:
                _, _, _, _, equipment, _, unilateral, _ = exercise
                selected_equipment = select_best_equipment_option(equipment, available_inventory)
                # For unilateral exercises, add equipment requirements twice (left + right)
                if unilateral:
                    step_equipments.append(selected_equipment)
                    step_equipments.append(selected_equipment)
                else:
                    step_equipments.append(selected_equipment)
            
            if can_add_station_to_workout(step_equipments, cumulative_station_usage, available_inventory, people_per_station):
                # If we're prioritizing must-use equipment, ensure at least one exercise actually uses it
                if must_use_equipment:
                    uses_must_use = False
                    for exercise in selected_exercises:
                        _, _, _, _, equipment, _, _, _ = exercise
                        if any(eq_type in equipment for eq_type in must_use_equipment):
                            uses_must_use = True
                            break
                    if not uses_must_use:
                        return []  # Reject combinations that don't use must-use equipment
                
                return selected_exercises[:]
            return []
        
        # Prioritize exercises from target area first
        target_area_exercises = [ex for ex in exercises_to_try if ex[0] == area_target]
        other_area_exercises = [ex for ex in exercises_to_try if ex[0] != area_target]
        
        # Try target area exercises first, then others as fallback
        ordered_exercises = target_area_exercises + other_area_exercises
        
        # Try each exercise in priority order
        for i, exercise in enumerate(ordered_exercises):
            area, equip, name, link, equipment, muscles, unilateral, exercise_id = exercise
            
            # Avoid duplicates within the station
            if name not in [ex[2] for ex in selected_exercises]:
                # Calculate how many steps this exercise will consume
                steps_consumed = 2 if unilateral else 1
                
                # Only try this exercise if we have enough remaining steps
                if steps_consumed <= remaining_steps:
                    # Try this exercise
                    new_selected = selected_exercises + [exercise]
                    # For remaining exercises, maintain the same priority order but exclude this one
                    remaining_exercises = [ex for ex in ordered_exercises[i+1:] if ex != exercise]
                    
                    result = try_combination(remaining_exercises, new_selected, remaining_steps - steps_consumed)
                    if result:
                        return result
        
        return []
    
    # Strategy 0: PRIORITIZE must-use equipment first, preferring target area AND variety
    if must_use_equipment:
        must_use_exercises = [ex for ex in available_exercises if uses_must_use_equipment(ex)]
        if must_use_exercises:
            print(f"   🎯 Found {len(must_use_exercises)} exercises using must-use equipment")
            
            # Apply variety optimization to must-use exercises - prioritize least recently used
            must_use_exercises.sort(key=get_variety_score, reverse=True)
            
            # First, try must-use exercises from the target area (variety-optimized within area)
            # But only if the best target area option has reasonable variety (score >= 0.8)
            target_area_must_use = [ex for ex in must_use_exercises if ex[0] == area_target]
            if target_area_must_use:
                # Apply variety optimization to the area-filtered exercises
                target_area_must_use.sort(key=get_variety_score, reverse=True)
                best_target_area_score = get_variety_score(target_area_must_use[0]) if target_area_must_use else 0
                # Only try target area first if the best option has decent variety (>= 0.8)
                if best_target_area_score >= 0.8:
                    for must_use_ex in target_area_must_use:
                        remaining_exercises = [ex for ex in available_exercises if ex != must_use_ex]
                        result = try_combination(remaining_exercises, [must_use_ex], steps_per_station - 1)
                        if result:
                            print(f"   ✅ Successfully prioritized must-use equipment in: {must_use_ex[2]}")
                            return result
            
            # If no target area must-use exercises work, or if target area has poor variety options,
            # try any area (variety-optimized order) - prioritize variety over area matching for must-use equipment
            for must_use_ex in must_use_exercises:
                # Start with the variety-optimized must-use exercise and try to build a complete station
                remaining_exercises = [ex for ex in available_exercises if ex != must_use_ex]
                result = try_combination(remaining_exercises, [must_use_ex], steps_per_station - 1)
                if result:
                    print(f"   ✅ Successfully prioritized must-use equipment in: {must_use_ex[2]}")
                    return result
    
    # Strategy 1: Try exercises from target area first (variety-optimized)
    area_exercises = [ex for ex in available_exercises if ex[0] == area_target]
    if len(area_exercises) >= steps_per_station:
        # Apply variety optimization to area exercises
        area_exercises.sort(key=get_variety_score, reverse=True)
        result = try_combination(area_exercises, [], steps_per_station)
        if result:
            return result
    
    # Strategy 2: Mix target area with other areas (variety-optimized)
    other_exercises = [ex for ex in available_exercises if ex[0] != area_target]
    other_exercises.sort(key=get_variety_score, reverse=True)
    mixed_exercises = area_exercises + other_exercises
    result = try_combination(mixed_exercises, [], steps_per_station)
    if result:
        return result
    
    return []


def find_compatible_exercise_pair(station_pool: List[Tuple[str, str, str, str, dict]], 
                                area_target: str,
                                cumulative_station_usage: dict, 
                                available_inventory: dict, 
                                people_per_station: int = 1,
                                used_names: set = None,
                                must_use_equipment: List[str] = None) -> Tuple[Tuple, Tuple]:
    """
    Find a compatible main+aux exercise pair that can be performed with remaining equipment.
    
    Args:
        station_pool: Available exercises
        area_target: Preferred area for main exercise
        cumulative_station_usage: Equipment already used
        available_inventory: Total equipment inventory  
        people_per_station: Number of people per station
        used_names: Set of already used exercise names
        must_use_equipment: List of equipment that should be prioritized
        
    Returns:
        Tuple of (main_exercise_tuple, aux_exercise_tuple) or (None, None) if no valid pair found
    """
    if not available_inventory:
        # Fallback to old random selection if no inventory
        return None, None
    
    if used_names is None:
        used_names = set()
    
    # Filter pool to only exercises that haven't been used
    available_exercises = [ex for ex in station_pool if ex[2] not in used_names]
    
    # Strategy 1: Try to find main exercise in target area first
    main_candidates = [ex for ex in available_exercises if ex[0] == area_target]
    if not main_candidates:
        main_candidates = available_exercises  # Fallback to any area
    
    for main_exercise in main_candidates:
        main_area, main_equip, main_name, main_link, main_equipment, main_muscles, main_unilateral = main_exercise
        selected_main_equipment = select_best_equipment_option(main_equipment, available_inventory)
        
        # Find compatible aux exercises that are DIFFERENT from main
        remaining_exercises = [ex for ex in available_exercises if ex[2] != main_name]
        
        # Strategy 1: Prefer aux from same area
        aux_candidates = [ex for ex in remaining_exercises if ex[0] == main_area]
        for aux_exercise in aux_candidates:
            aux_area, aux_equip, aux_name, aux_link, aux_equipment, aux_muscles, aux_unilateral = aux_exercise
            selected_aux_equipment = select_best_equipment_option(aux_equipment, available_inventory)
            
            # Check if this step1+step2 combination can be performed with remaining equipment
            if can_add_station_to_workout([selected_main_equipment, selected_aux_equipment], 
                                        cumulative_station_usage, available_inventory, people_per_station):
                return main_exercise, aux_exercise
        
        # Strategy 2: Try aux from ANY area if same area didn't work
        for aux_exercise in remaining_exercises:
            aux_area, aux_equip, aux_name, aux_link, aux_equipment, aux_muscles, aux_unilateral = aux_exercise
            selected_aux_equipment = select_best_equipment_option(aux_equipment, available_inventory)
            
            # Check if this step1+step2 combination can be performed with remaining equipment
            if can_add_station_to_workout([selected_main_equipment, selected_aux_equipment], 
                                        cumulative_station_usage, available_inventory, people_per_station):
                return main_exercise, aux_exercise
    
    # Strategy 3: If target area didn't work, try main from ANY area
    if area_target and main_candidates != available_exercises:
        for main_exercise in available_exercises:
            main_area, main_equip, main_name, main_link, main_equipment, main_muscles, main_unilateral = main_exercise
            selected_main_equipment = select_best_equipment_option(main_equipment, available_inventory)
            
            # Find compatible aux exercises that are DIFFERENT from main
            remaining_exercises = [ex for ex in available_exercises if ex[2] != main_name]
            
            for aux_exercise in remaining_exercises:
                aux_area, aux_equip, aux_name, aux_link, aux_equipment, aux_muscles, aux_unilateral = aux_exercise
                selected_aux_equipment = select_best_equipment_option(aux_equipment, available_inventory)
                
                # Check if this step1+step2 combination can be performed with remaining equipment
                if can_add_station_to_workout([selected_main_equipment, selected_aux_equipment], 
                                            cumulative_station_usage, available_inventory, people_per_station):
                    return main_exercise, aux_exercise
    
    return None, None


def build_plan(plan: dict, station_pool: List[Tuple[str, str, str, str, dict]], rest_pool: List[dict]) -> dict:
    """Build workout plan with corrected station-based equipment tracking."""
    stations_needed = plan["stations"]
    people_count = plan.get("people", stations_needed)  # Default to 1 person per station if not specified
    steps_per_station = plan.get("steps_per_station", 2)  # Default to 2 steps if not specified
    
    # Calculate people per station with maximum of 2 people per station
    max_people_per_station = 2
    people_per_station = min(max_people_per_station, people_count // stations_needed) if stations_needed > 0 else 1
    
    # Check if we can accommodate all people with this configuration
    max_people_accommodated = stations_needed * max_people_per_station
    if people_count > max_people_accommodated:
        from config import die
        die(f"Cannot accommodate {people_count} people with {stations_needed} stations. "
            f"Maximum possible: {max_people_accommodated} people (2 per station). "
            f"Please increase stations to at least {(people_count + 1) // 2} or reduce people count.")
    
    # Add people_per_station to plan for use in other functions
    plan["people_per_station"] = people_per_station
    
    # Create global active rest schedule - everyone does the same exercise at the same time
    active_rest_count = plan.get("active_rest_count", 4)  # Default to 4 active rest exercises
    selected_exercises = []
    global_active_rest_schedule = []
    
    if plan["active_rest_mode"] in ["all_active", "mix"] and rest_pool:
        # Select the specified number of exercises from the rest pool for global use
        if len(rest_pool) >= active_rest_count:
            selected_exercises = random.sample(rest_pool, active_rest_count)
        else:
            # If fewer exercises available than requested, use all of them and pad with "Rest"
            selected_exercises = rest_pool.copy()
            while len(selected_exercises) < active_rest_count:
                selected_exercises.append({"name": "Rest", "link": ""})
        
        print(f"📋 Selected {active_rest_count} Active Rest Exercises for Global Use:")
        for i, exercise in enumerate(selected_exercises, 1):
            print(f"   {i}. {exercise['name']}")
        print()
        
        print(f"📋 Global Active Rest Schedule (everyone does these together):")
        for step_idx in range(steps_per_station):
            # Cycle through the selected exercises
            exercise_idx = step_idx % len(selected_exercises)
            
            if plan["active_rest_mode"] == "all_active":
                rest_exercise = selected_exercises[exercise_idx]
            elif plan["active_rest_mode"] == "mix":
                # For mix mode, randomly decide each step
                if random.choice([True, False]):
                    rest_exercise = selected_exercises[exercise_idx]
                else:
                    rest_exercise = {"name": "Rest", "link": ""}
            else:
                rest_exercise = {"name": "Rest", "link": ""}
            
            global_active_rest_schedule.append(rest_exercise)
            print(f"   Step {step_idx + 1}: {rest_exercise['name']}")
        print()
    else:
        # All rest mode - just use regular rest
        for step_idx in range(steps_per_station):
            global_active_rest_schedule.append({"name": "Rest", "link": ""})
    
    order_cycle = plan["balance_order"]
    stations: List[dict] = []
    used_names = set()
    used_exercise_ids = []  # Track exercise IDs for history
    equipment_requirements = {}  # Track max equipment needed across all stations (for display)
    cumulative_station_usage = {}  # Track equipment usage across all stations (stations run simultaneously)
    available_inventory = plan.get("equipment", {})
    excluded_exercises = []  # Track exercises excluded due to equipment conflicts
    cycle_idx = 0
    
    # Show initial equipment status
    if available_inventory:
        print("🏋️  Starting workout generation with equipment inventory:")
        for equipment_type in sorted(available_inventory.keys()):
            count = available_inventory[equipment_type].get("count", 0)
            display_name = equipment_type.replace("_", " ").replace("kg", " kg").title()
            display_name = display_name.replace("Dumbbells", "Dumbbell").replace("Kettlebells", "Kettlebell")
            print(f"   • {display_name}: {count}x available")
        print()
        
        print(f"👥 Workout Configuration:")
        print(f"   • {people_count} people across {stations_needed} stations")
        print(f"   • {people_per_station} people per station (max 2 allowed)")
        
        # Show if some people won't fit
        people_accommodated = stations_needed * people_per_station
        if people_accommodated < people_count:
            people_waiting = people_count - people_accommodated
            print(f"   • {people_waiting} people will need to wait or join in later rounds")
        
        if people_per_station > 1:
            steps_desc = ", ".join([f"Step {i+1}" for i in range(steps_per_station)])
            print(f"   • {steps_desc} exercises happen SIMULTANEOUSLY ({people_per_station} people per station)")
        else:
            steps_desc = ", ".join([f"Step {i+1}" for i in range(steps_per_station)])
            print(f"   • {steps_desc} exercises happen SEQUENTIALLY (same person does all steps)")
        print()
    
    while len(stations) < stations_needed:
        if not station_pool:
            from config import die
            die("Ran out of unique exercises before filling stations; add more JSON lifts.")
        area_target = order_cycle[cycle_idx % len(order_cycle)]
        cycle_idx += 1
        
        print(f"🎯 Building Station {len(stations)+1} (targeting {area_target})...")
        
        # Get must-use equipment that hasn't been used yet
        must_use_equipment = plan.get("must_use", [])
        unused_must_use = prioritize_must_use_exercises(station_pool, must_use_equipment, cumulative_station_usage, available_inventory)
        
        # Try each unused must-use equipment type until one works
        station_exercises = None
        for priority_equipment in unused_must_use:
            print(f"   🎯 Trying to prioritize must-use equipment: {priority_equipment}")
            
            station_exercises = find_compatible_exercises_for_station(
                station_pool, area_target, steps_per_station, cumulative_station_usage, 
                available_inventory, plan["people_per_station"], used_names, [priority_equipment],
                plan.get("use_workout_history", True)
            )
            
            if station_exercises:
                print(f"   ✅ Successfully prioritized must-use equipment: {priority_equipment}")
                break
            else:
                print(f"   ⚠️ Could not build complete station with {priority_equipment}, trying next...")
        
        # If no must-use equipment worked, try without prioritization
        if not station_exercises:
            print(f"   🔄 No must-use equipment could build complete station, trying without prioritization...")
            station_exercises = find_compatible_exercises_for_station(
                station_pool, area_target, steps_per_station, cumulative_station_usage, 
                available_inventory, plan["people_per_station"], used_names, [],
                plan.get("use_workout_history", True)
            )
            
        if not station_exercises:
            from config import die
            die(f"Cannot complete workout - no compatible exercises available for Station {len(stations)+1} with {steps_per_station} steps. "
                f"Try reducing stations, adding more equipment, or adding more exercise variety.")
        
        # Process selected exercises
        step_names = []
        step_links = []
        step_equipments = []
        step_muscles = []
        
        for exercise in station_exercises:
            area, equip, name, link, equipment, muscles, unilateral, exercise_id = exercise
            used_names.add(name)
            
            # Track exercise ID for history (only if it's a valid ID)
            if exercise_id != -1:
                used_exercise_ids.append(exercise_id)
            
            selected_equipment = select_best_equipment_option(equipment, available_inventory)
            
            if unilateral:
                # Add both left and right variations for unilateral exercises
                step_names.append(f"{name} (Left)")
                step_links.append(link)
                step_equipments.append(selected_equipment)
                step_muscles.append(muscles)
                
                step_names.append(f"{name} (Right)")
                step_links.append(link)
                step_equipments.append(selected_equipment)
                step_muscles.append(muscles)
            else:
                # Regular bilateral exercise
                step_names.append(name)
                step_links.append(link)
                step_equipments.append(selected_equipment)
                step_muscles.append(muscles)
            
            # Remove exercise from pool
            for idx, ex_tuple in enumerate(station_pool):
                if ex_tuple[2] == name:  # Match by exercise name
                    station_pool.pop(idx)
                    break
        
        # Handle case where we need more steps than available exercises (duplicate last exercise)
        # Note: With unilateral exercises, we might have fewer exercise objects but still fill all steps
        while len(step_names) < steps_per_station:
            print(f"   ⚠️  Only found {len(step_names)} step variations, duplicating last exercise for step {len(step_names)+1}")
            step_names.append(step_names[-1])
            step_links.append(step_links[-1])
            step_equipments.append(step_equipments[-1])
            step_muscles.append(step_muscles[-1])
        
        # Add this station's equipment requirements to cumulative usage
        station_requirements = get_station_equipment_requirements(step_equipments, plan["people_per_station"])
        for equipment_type, equipment_info in station_requirements.items():
            if equipment_type in cumulative_station_usage:
                cumulative_station_usage[equipment_type]["count"] += equipment_info["count"]
            else:
                cumulative_station_usage[equipment_type] = {"count": equipment_info["count"]}
        
        # Update global equipment requirements (for display purposes)
        merge_equipment_requirements(equipment_requirements, station_requirements)
        
        # Create flexible station structure
        station_data = {
            "area": area_target,
            "equipment": "",  # Will be populated by display logic
        }
        
        # Add each step to the station
        for step_idx in range(steps_per_station):
            step_num = step_idx + 1
            station_data[f"step{step_num}"] = step_names[step_idx]
            station_data[f"step{step_num}_link"] = step_links[step_idx]
            station_data[f"step{step_num}_equipment"] = step_equipments[step_idx]
            station_data[f"step{step_num}_muscles"] = step_muscles[step_idx]
            station_data[f"rest_step{step_num}"] = global_active_rest_schedule[step_idx]["name"]
            station_data[f"rest_step{step_num}_link"] = global_active_rest_schedule[step_idx]["link"]
        
        stations.append(station_data)
        
        # Report station equipment status
        report_station_equipment_status(len(stations), step_names, step_equipments,
                                       cumulative_station_usage, available_inventory, plan["people_per_station"])
        
        # CRITICAL: Filter station pool to remove exercises that can no longer be performed
        # This prevents trying to use bench exercises after bench is full
        if available_inventory:
            original_pool_size = len(station_pool)
            
            station_pool = filter_exercises_by_remaining_equipment(
                station_pool, cumulative_station_usage, available_inventory, plan["people_per_station"]
            )
            filtered_count = original_pool_size - len(station_pool)
            
            if filtered_count > 0:
                print(f"   🔧 Filtered out {filtered_count} exercises that can no longer be performed with remaining equipment")
                print()
    
    # Check for must-use equipment warnings
    if available_inventory:
        must_use_warnings = check_must_use_equipment(plan, stations, available_inventory)
        if must_use_warnings:
            print("💡 Equipment Usage Suggestions:")
            for warning in must_use_warnings:
                print(f"   • {warning}")
            print()
    
    # Create a deep copy to prevent reference issues
    final_equipment_requirements = {}
    for equipment_type, equipment_info in cumulative_station_usage.items():
        final_equipment_requirements[equipment_type] = {"count": equipment_info["count"]}
    
    return {
        "stations": stations,
        "equipment_requirements": final_equipment_requirements,  # Use clean copy for validation
        "global_active_rest_schedule": global_active_rest_schedule,  # Global rest schedule for all stations
        "selected_active_rest_exercises": selected_exercises,  # All selected active rest exercises (for display)
        "used_exercise_ids": used_exercise_ids  # Exercise IDs used in this workout (for history tracking)
    } 
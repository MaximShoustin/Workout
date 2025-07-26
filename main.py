#!/usr/bin/env python3
"""Main CLI for generating randomized workout plans."""

import sys
import time
import random
from pathlib import Path

from config import load_plan, die, load_json, ACTIVE_REST_FILE
from equipment import parse_equipment, build_station_pool, get_equipment_validation_summary
from workout_planner import build_plan
from file_utils import save_workout_html


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
        for activity in rest_data:
            if isinstance(activity, dict):
                rest_pool.append({"name": activity["name"], "link": activity.get("link", "")})
            else:
                rest_pool.append({"name": activity, "link": ""})
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
    
    print(f"🔄 Attempting to generate workout (max {max_retries} attempts)...")
    print()
    
    for attempt in range(1, max_retries + 1):
        # Use a new random seed for each attempt
        seed = int(time.time() * 1000) % 2147483647  # Ensure it fits in 32-bit int
        random.seed(seed)
        
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
            
            return plan_result, validation_summary, seed, plan_with_active_rest
            
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


def main():
    """Main entry point for workout generation."""
    try:
        plan_result, validation_summary, seed_used, plan = generate_workout_with_retries()
        
        # Print validation status
        if validation_summary["is_valid"]:
            print("✅ Equipment validation: All requirements can be satisfied")
        else:
            print("⚠️ Equipment validation: Some requirements exceed available inventory")
            for issue in validation_summary["issues"]:
                print(f"   • {issue}")
        
        # Save the HTML file  
        filename = save_workout_html(plan, plan_result["stations"], plan_result["equipment_requirements"], validation_summary, plan_result["global_active_rest_schedule"], plan_result["selected_active_rest_exercises"])
        print(f"✅ Workout saved to: {filename}")
        print(f"🌐 Open in browser: file://{filename.absolute()}")
        print(f"🎲 Final seed used: {seed_used}")
        
    except KeyboardInterrupt:
        print("\n⚠️ Workout generation cancelled by user")
        sys.exit(1)
    except Exception as e:
        print(f"❌ Error generating workout: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main() 
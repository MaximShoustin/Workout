#!/usr/bin/env python3
"""Equipment parsing and station pool management."""

import random
from pathlib import Path
from typing import Dict, List, Tuple, Optional

from config import EQUIP_DIR, AREA_MAP, load_json, die


def classify_area(category: str) -> str:
    """Classify exercise category into area (upper/lower/core)."""
    cat_lower = category.lower()
    for area, keywords in AREA_MAP.items():
        if any(kw in cat_lower for kw in keywords):
            return area
    return "core"  # fallback


def validate_equipment_requirements(requirements: dict, available_inventory: dict) -> Tuple[bool, List[str]]:
    """
    Validate if equipment requirements can be satisfied with available inventory.
    
    Args:
        requirements: Dict of equipment requirements (e.g., {"dumbbells_10kg": {"count": 4}})
        available_inventory: Dict of available equipment from plan.json
        
    Returns:
        Tuple of (is_valid, list_of_issues)
    """
    issues = []
    
    for equipment_type, req_info in requirements.items():
        required_count = req_info.get("count", 1)
        
        if equipment_type not in available_inventory:
            issues.append(f"Missing equipment: {equipment_type} (need {required_count}x)")
        else:
            available_count = available_inventory[equipment_type].get("count", 0)
            if required_count > available_count:
                issues.append(f"Insufficient {equipment_type}: need {required_count}x, have {available_count}x")
    
    return len(issues) == 0, issues


def can_exercise_be_performed(exercise_equipment: dict, available_inventory: dict) -> bool:
    """
    Check if a single exercise can be performed with available equipment.
    
    Args:
        exercise_equipment: Equipment requirements for one exercise
        available_inventory: Available equipment from plan.json
        
    Returns:
        True if exercise can be performed, False otherwise
    """
    is_valid, _ = validate_equipment_requirements(exercise_equipment, available_inventory)
    return is_valid


def filter_feasible_exercises(pool: List[Tuple[str, str, str, str, dict]], available_inventory: dict) -> List[Tuple[str, str, str, str, dict]]:
    """
    Filter exercise pool to only include exercises that can be performed with available equipment.
    
    Args:
        pool: List of (area, equip_name, exercise_name, exercise_link, equipment_data)
        available_inventory: Available equipment from plan.json
        
    Returns:
        Filtered list containing only feasible exercises
    """
    feasible_pool = []
    excluded_exercises = []
    
    for exercise_tuple in pool:
        area, equip_name, exercise_name, exercise_link, equipment_data = exercise_tuple
        
        if can_exercise_be_performed(equipment_data, available_inventory):
            feasible_pool.append(exercise_tuple)
        else:
            excluded_exercises.append(exercise_name)
    
    if excluded_exercises:
        print(f"⚠️  Excluded {len(excluded_exercises)} exercises due to insufficient equipment:")
        for ex in excluded_exercises[:5]:  # Show first 5
            print(f"   • {ex}")
        if len(excluded_exercises) > 5:
            print(f"   ... and {len(excluded_exercises) - 5} more")
    
    return feasible_pool


def parse_equipment() -> Dict[str, dict]:
    """Parse all equipment JSON files."""
    gear: Dict[str, dict] = {}
    for f in EQUIP_DIR.glob("*.json"):
        if f.name == "active_rest.json":
            continue
        data = load_json(f)
        # Use filename (without .json) as equipment name since we removed root-level equipment field
        equip_name = f.stem.replace("_", " ").title()
        gear[equip_name] = data
    if not gear:
        die("No equipment JSON files found in ./equipment/")
    return gear


def build_station_pool(gear: Dict[str, dict], available_inventory: Optional[dict] = None) -> List[Tuple[str, str, str, str, dict]]:
    """Return list of (area, equip_name, exercise_name, exercise_link, equipment_data)"""
    pool = []
    for equip_name, data in gear.items():
        for cat, lst in data["lifts"].items():
            area = classify_area(cat)
            for ex in lst:
                # Handle both old string format and new object format
                if isinstance(ex, dict):
                    exercise_name = ex["name"]
                    exercise_link = ex.get("link", "")
                    equipment_data = ex.get("equipment", {})
                else:
                    exercise_name = ex
                    exercise_link = ""
                    equipment_data = {}
                pool.append((area, equip_name, exercise_name, exercise_link, equipment_data))
    if not pool:
        die("Equipment JSONs contained no lifts!")
    
    # Filter pool based on available equipment if inventory is provided
    if available_inventory:
        pool = filter_feasible_exercises(pool, available_inventory)
        if not pool:
            die("No exercises can be performed with available equipment! Check your equipment inventory in plan.json")
    
    random.shuffle(pool)
    return pool


def merge_equipment_requirements(requirements: dict, exercise_equipment: dict) -> None:
    """Merge exercise equipment into the global requirements, taking max counts."""
    for equipment_type, equipment_info in exercise_equipment.items():
        if equipment_type in requirements:
            # Take the maximum count needed
            requirements[equipment_type]["count"] = max(
                requirements[equipment_type].get("count", 0),
                equipment_info.get("count", 0)
            )
        else:
            # Add new equipment type
            requirements[equipment_type] = equipment_info.copy()


def get_equipment_validation_summary(requirements: dict, available_inventory: dict) -> dict:
    """
    Get a comprehensive equipment validation summary for reporting.
    
    Returns:
        Dict with validation status, issues, and statistics
    """
    is_valid, issues = validate_equipment_requirements(requirements, available_inventory)
    
    # Calculate equipment utilization
    total_required_items = sum(req.get("count", 0) for req in requirements.values())
    total_available_items = sum(inv.get("count", 0) for inv in available_inventory.values())
    
    utilization_by_type = {}
    for eq_type, req_info in requirements.items():
        if eq_type in available_inventory:
            required = req_info.get("count", 0)
            available = available_inventory[eq_type].get("count", 0)
            utilization_by_type[eq_type] = {
                "required": required,
                "available": available,
                "utilization_pct": (required / available * 100) if available > 0 else 0,
                "sufficient": required <= available
            }
    
    return {
        "is_valid": is_valid,
        "issues": issues,
        "total_equipment_types_required": len(requirements),
        "total_equipment_types_available": len(available_inventory),
        "total_items_required": total_required_items,
        "total_items_available": total_available_items,
        "utilization_by_type": utilization_by_type
    } 
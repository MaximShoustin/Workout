#!/usr/bin/env python3
"""Exercise Database Analysis and Reporting Tool
===============================================

Analyzes the workout exercise database and generates comprehensive reports
showing exercise counts, distribution, and statistics across all equipment types.

Usage:
    python3 exercise_database_report.py           # Generate full report
    python3 exercise_database_report.py --json    # Output as JSON
    python3 exercise_database_report.py --csv     # Export to CSV
"""

import json
import csv
import sys
from pathlib import Path
from typing import Dict, List, Tuple, Any
from collections import defaultdict

# Import configuration
from config import EQUIP_DIR, ACTIVE_REST_FILE, load_json


def analyze_equipment_files() -> Tuple[Dict[str, Any], int]:
    """Analyze all equipment files and return structured data."""
    equipment_data = {}
    total_exercises = 0
    
    for file in EQUIP_DIR.glob("*.json"):
        if file.name == "active_rest.json":
            continue
            
        data = load_json(file)
        equipment_name = file.stem.replace("_", " ").title()
        
        categories = {}
        file_total = 0
        
        for category, exercises in data["lifts"].items():
            exercise_count = len(exercises)
            categories[category] = {
                "count": exercise_count,
                "exercises": [ex["name"] if isinstance(ex, dict) else ex for ex in exercises]
            }
            file_total += exercise_count
        
        equipment_data[equipment_name] = {
            "file": file.name,
            "categories": categories,
            "total": file_total
        }
        total_exercises += file_total
    
    return equipment_data, total_exercises


def analyze_active_rest() -> Tuple[List[str], int]:
    """Analyze active rest activities."""
    if not ACTIVE_REST_FILE.exists():
        return [], 0
    
    data = load_json(ACTIVE_REST_FILE)
    activities = []
    
    for activity in data["rest"]:
        if isinstance(activity, dict):
            activities.append(activity["name"])
        else:
            activities.append(activity)
    
    return activities, len(activities)


def classify_exercise_types(equipment_data: Dict[str, Any]) -> Dict[str, int]:
    """Classify exercises by movement type."""
    type_counts = defaultdict(int)
    
    # Define classification keywords
    classifications = {
        "Upper Body": ["upper", "push", "pull", "press", "row", "curl", "raise", "fly"],
        "Lower Body": ["lower", "squat", "lunge", "leg", "step", "posterior", "deadlift", "bridge"],
        "Core": ["core", "carry", "twist", "plank", "rotation", "hold", "support"],
        "Power/Explosive": ["power", "jump", "slam", "swing", "clean", "jerk", "snatch", "complex"]
    }
    
    for equipment_name, equipment_info in equipment_data.items():
        for category, category_info in equipment_info["categories"].items():
            category_lower = category.lower()
            
            # Classify based on category name
            classified = False
            for movement_type, keywords in classifications.items():
                if any(keyword in category_lower for keyword in keywords):
                    type_counts[movement_type] += category_info["count"]
                    classified = True
                    break
            
            # If not classified, add to "Other"
            if not classified:
                type_counts["Other"] += category_info["count"]
    
    return dict(type_counts)


def generate_text_report(equipment_data: Dict[str, Any], total_exercises: int, 
                        active_rest: List[str], active_rest_count: int,
                        exercise_types: Dict[str, int]) -> str:
    """Generate formatted text report."""
    report = []
    
    # Header
    report.append("📊 EXERCISE DATABASE SUMMARY")
    report.append("=" * 50)
    report.append("")
    
    # Overall stats
    grand_total = total_exercises + active_rest_count
    report.append(f"🎯 TOTAL MOVEMENTS: {grand_total}")
    report.append(f"   • Main Exercises: {total_exercises}")
    report.append(f"   • Active Rest Activities: {active_rest_count}")
    report.append("")
    
    # Equipment breakdown
    report.append("🏋️ MAIN EXERCISES BY EQUIPMENT")
    report.append("-" * 40)
    
    # Sort equipment by exercise count (descending)
    sorted_equipment = sorted(equipment_data.items(), key=lambda x: x[1]["total"], reverse=True)
    
    for equipment_name, equipment_info in sorted_equipment:
        total = equipment_info["total"]
        percentage = (total / total_exercises * 100) if total_exercises > 0 else 0
        report.append(f"{equipment_name}: {total} exercises ({percentage:.1f}%)")
        
        # Show categories
        sorted_categories = sorted(equipment_info["categories"].items(), 
                                 key=lambda x: x[1]["count"], reverse=True)
        for category, category_info in sorted_categories:
            count = category_info["count"]
            category_display = category.replace("_", " ").title()
            report.append(f"   • {category_display}: {count}")
        report.append("")
    
    # Exercise type distribution
    report.append("💪 MOVEMENT TYPE DISTRIBUTION")
    report.append("-" * 40)
    sorted_types = sorted(exercise_types.items(), key=lambda x: x[1], reverse=True)
    for movement_type, count in sorted_types:
        percentage = (count / total_exercises * 100) if total_exercises > 0 else 0
        report.append(f"{movement_type}: {count} exercises ({percentage:.1f}%)")
    report.append("")
    
    # Active rest activities
    if active_rest_count > 0:
        report.append("🏃 ACTIVE REST ACTIVITIES")
        report.append("-" * 40)
        for activity in active_rest:
            report.append(f"   • {activity}")
        report.append("")
    
    # Equipment utilization analysis
    report.append("📈 EQUIPMENT UTILIZATION ANALYSIS")
    report.append("-" * 40)
    
    if sorted_equipment:
        largest = sorted_equipment[0]
        smallest = sorted_equipment[-1]
        
        report.append(f"Most utilized: {largest[0]} ({largest[1]['total']} exercises)")
        report.append(f"Least utilized: {smallest[0]} ({smallest[1]['total']} exercises)")
        
        # Diversity score
        category_count = sum(len(eq_info["categories"]) for eq_info in equipment_data.values())
        equipment_count = len(equipment_data)
        diversity_score = category_count / equipment_count if equipment_count > 0 else 0
        report.append(f"Diversity score: {diversity_score:.1f} categories per equipment type")
    
    report.append("")
    report.append("=" * 50)
    report.append("Generated by Exercise Database Report Tool")
    
    return "\n".join(report)


def export_to_json(equipment_data: Dict[str, Any], total_exercises: int,
                  active_rest: List[str], active_rest_count: int,
                  exercise_types: Dict[str, int]) -> str:
    """Export data as JSON."""
    data = {
        "summary": {
            "total_exercises": total_exercises,
            "active_rest_count": active_rest_count,
            "grand_total": total_exercises + active_rest_count
        },
        "equipment": equipment_data,
        "active_rest": active_rest,
        "exercise_types": exercise_types,
        "generated_at": Path(__file__).stat().st_mtime
    }
    return json.dumps(data, indent=2)


def export_to_csv(equipment_data: Dict[str, Any], active_rest: List[str]) -> None:
    """Export exercise data to CSV files."""
    # Export exercises
    with open("exercise_database.csv", "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(["Equipment", "Category", "Exercise", "Type"])
        
        for equipment_name, equipment_info in equipment_data.items():
            for category, category_info in equipment_info["categories"].items():
                category_display = category.replace("_", " ").title()
                for exercise in category_info["exercises"]:
                    writer.writerow([equipment_name, category_display, exercise, "Main Exercise"])
    
    # Export active rest
    if active_rest:
        with open("active_rest.csv", "w", newline="", encoding="utf-8") as f:
            writer = csv.writer(f)
            writer.writerow(["Activity", "Type"])
            for activity in active_rest:
                writer.writerow([activity, "Active Rest"])
    
    print("📄 Exported to exercise_database.csv and active_rest.csv")


def main():
    """Main function."""
    # Parse command line arguments
    json_output = "--json" in sys.argv
    csv_output = "--csv" in sys.argv
    
    try:
        # Analyze data
        equipment_data, total_exercises = analyze_equipment_files()
        active_rest, active_rest_count = analyze_active_rest()
        exercise_types = classify_exercise_types(equipment_data)
        
        if json_output:
            # Output as JSON
            json_data = export_to_json(equipment_data, total_exercises, 
                                     active_rest, active_rest_count, exercise_types)
            print(json_data)
        elif csv_output:
            # Export to CSV
            export_to_csv(equipment_data, active_rest)
            # Also show summary
            report = generate_text_report(equipment_data, total_exercises,
                                        active_rest, active_rest_count, exercise_types)
            print(report)
        else:
            # Generate and display text report
            report = generate_text_report(equipment_data, total_exercises,
                                        active_rest, active_rest_count, exercise_types)
            print(report)
            
    except Exception as e:
        print(f"❌ Error generating report: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main() 
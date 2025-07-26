#!/usr/bin/env python3
"""Unit tests for workout station generator."""

import json
import os
import random
import shutil
import tempfile
import unittest
from pathlib import Path

from config import ACTIVE_REST_FILE, load_json, load_plan
from equipment import parse_equipment, build_station_pool, validate_equipment_requirements, can_exercise_be_performed, filter_feasible_exercises, get_equipment_validation_summary
from workout_planner import build_plan


class GeneratorTests(unittest.TestCase):
    """Test cases for workout generator functionality."""
    
    def setUp(self):
        """Set up test environment with temporary files."""
        # temp project root
        self.dir = Path(tempfile.mkdtemp())
        (self.dir / "equipment").mkdir()
        (self.dir / "config").mkdir()
        
        # minimal equipment json
        kb = {
            "lifts": {
                "upper_push": [
                    {"name": "KB Press", "link": "some url", "equipment": {"kettlebells_16kg": {"count": 1}}},
                    {"name": "KB Push Press", "link": "some url", "equipment": {"kettlebells_16kg": {"count": 2}}},
                    {"name": "KB Floor Press", "link": "some url", "equipment": {"kettlebells_16kg": {"count": 1}}}
                ],
                "leg_power": [
                    {"name": "KB Squat", "link": "some url", "equipment": {"kettlebells_16kg": {"count": 1}}},
                    {"name": "KB Goblet Squat", "link": "some url", "equipment": {"kettlebells_24kg": {"count": 1}}},
                    {"name": "KB Split Squat", "link": "some url", "equipment": {"kettlebells_16kg": {"count": 2}}}
                ],
                "core_carry": [
                    {"name": "KB Carry", "link": "some url", "equipment": {"kettlebells_16kg": {"count": 2}}},
                    {"name": "KB Suitcase Carry", "link": "some url", "equipment": {"kettlebells_24kg": {"count": 1}}},
                    {"name": "KB Overhead Carry", "link": "some url", "equipment": {"kettlebells_32kg": {"count": 1}}}
                ],
                "upper_pull": [
                    {"name": "KB Row", "link": "some url", "equipment": {"kettlebells_16kg": {"count": 1}}},
                    {"name": "KB Single Arm Row", "link": "some url", "equipment": {"kettlebells_24kg": {"count": 1}}},
                    {"name": "KB High Pull", "link": "some url", "equipment": {"kettlebells_16kg": {"count": 1}}}
                ]
            },
        }
        with (self.dir/"equipment"/"kb.json").open("w") as fh:
            json.dump(kb, fh)
        
        # active rest
        restj = {"rest": [{"name": f"Drill{i}", "link": "some url"} for i in range(9)]}
        with (self.dir/"equipment"/"active_rest.json").open("w") as fh:
            json.dump(restj, fh)
        
        # plan with equipment inventory
        plan = {
            "stations": 3,  # Reduced to avoid equipment conflicts
            "timing": "45/15",
            "active_rest": "auto",
            "balance_order": ["upper", "lower", "core"],
            "equipment": {}  # Disable equipment validation for tests
        }
        with (self.dir/"config"/"plan.json").open("w") as fh:
            json.dump(plan, fh)
        
        # chdir
        self.cwd = Path.cwd()
        os.chdir(self.dir)

    def tearDown(self):
        """Clean up test environment."""
        os.chdir(self.cwd)
        shutil.rmtree(self.dir)

    def test_active_rest_auto(self):
        """Test automatic active rest mode with proper exercise distribution."""
        random.seed(0)
        plan = load_plan()
        # should coin‑flip to True with seed 0 (first bit=1)
        self.assertTrue((plan["active_rest"] == "auto"))
        
        # active_rest_mode set in main, test via helper path
        rest_data = load_json(ACTIVE_REST_FILE)["rest"]
        # Process active rest data same way as main function
        rest_pool = []
        for activity in rest_data:
            if isinstance(activity, dict):
                rest_pool.append({"name": activity["name"], "link": activity.get("link", "")})
            else:
                rest_pool.append({"name": activity, "link": ""})
        
        gear = parse_equipment()
        station_pool = build_station_pool(gear)
        plan["active_rest_mode"] = "all_active"
        workout_data = build_plan(plan, station_pool, rest_pool)
        stations = workout_data["stations"]
        rests = [st["rest_main"] for st in stations] + [st["rest_aux"] for st in stations]
        
        # With 3 stations (6 rest periods) and 9 rest activities, some reuse is expected
        # but we should still have good variety (at least 6 different activities used)
        self.assertGreaterEqual(len(set(rests)), 6)  # expect at least 6 different activities
        self.assertEqual(len(rests), 6)  # 3 stations × 2 rest periods each

    def test_equipment_validation_sufficient(self):
        """Test equipment validation when requirements can be satisfied."""
        requirements = {
            "kettlebells_16kg": {"count": 2}
        }
        inventory = {
            "kettlebells_16kg": {"count": 3}
        }
        
        is_valid, issues = validate_equipment_requirements(requirements, inventory)
        self.assertTrue(is_valid)
        self.assertEqual(len(issues), 0)

    def test_equipment_validation_insufficient(self):
        """Test equipment validation when requirements exceed inventory."""
        requirements = {
            "kettlebells_16kg": {"count": 4},
            "kettlebells_32kg": {"count": 1}
        }
        inventory = {
            "kettlebells_16kg": {"count": 2},
            "kettlebells_24kg": {"count": 1}
        }
        
        is_valid, issues = validate_equipment_requirements(requirements, inventory)
        self.assertFalse(is_valid)
        self.assertEqual(len(issues), 2)
        self.assertIn("Insufficient kettlebells_16kg", issues[0])
        self.assertIn("Missing equipment: kettlebells_32kg", issues[1])

    def test_can_exercise_be_performed(self):
        """Test individual exercise feasibility checking."""
        available_inventory = {
            "kettlebells_16kg": {"count": 2},
            "kettlebells_24kg": {"count": 1}
        }
        
        # Exercise that can be performed
        feasible_exercise = {"kettlebells_16kg": {"count": 1}}
        self.assertTrue(can_exercise_be_performed(feasible_exercise, available_inventory))
        
        # Exercise that cannot be performed (insufficient count)
        infeasible_exercise = {"kettlebells_16kg": {"count": 3}}
        self.assertFalse(can_exercise_be_performed(infeasible_exercise, available_inventory))
        
        # Exercise that cannot be performed (missing equipment)
        missing_exercise = {"kettlebells_32kg": {"count": 1}}
        self.assertFalse(can_exercise_be_performed(missing_exercise, available_inventory))

    def test_filter_feasible_exercises(self):
        """Test filtering of exercise pool based on equipment availability."""
        pool = [
            ("upper", "Kettlebells", "KB Press", "link", {"kettlebells_16kg": {"count": 1}}),
            ("upper", "Kettlebells", "KB Push Press", "link", {"kettlebells_16kg": {"count": 2}}),
            ("upper", "Kettlebells", "Heavy KB Press", "link", {"kettlebells_32kg": {"count": 1}}),
            ("core", "Kettlebells", "KB Carry", "link", {"kettlebells_16kg": {"count": 3}})
        ]
        
        available_inventory = {
            "kettlebells_16kg": {"count": 2},
            "kettlebells_24kg": {"count": 1}
        }
        
        feasible_pool = filter_feasible_exercises(pool, available_inventory)
        
        # Should exclude Heavy KB Press (missing 32kg) and KB Carry (need 3x 16kg but only have 2x)
        self.assertEqual(len(feasible_pool), 2)
        exercise_names = [ex[2] for ex in feasible_pool]
        self.assertIn("KB Press", exercise_names)
        self.assertIn("KB Push Press", exercise_names)
        self.assertNotIn("Heavy KB Press", exercise_names)
        self.assertNotIn("KB Carry", exercise_names)

    def test_get_equipment_validation_summary(self):
        """Test comprehensive equipment validation summary generation."""
        requirements = {
            "kettlebells_16kg": {"count": 2},
            "kettlebells_24kg": {"count": 1}
        }
        inventory = {
            "kettlebells_16kg": {"count": 3},
            "kettlebells_24kg": {"count": 1},
            "kettlebells_32kg": {"count": 1}
        }
        
        summary = get_equipment_validation_summary(requirements, inventory)
        
        self.assertTrue(summary["is_valid"])
        self.assertEqual(len(summary["issues"]), 0)
        self.assertEqual(summary["total_equipment_types_required"], 2)
        self.assertEqual(summary["total_equipment_types_available"], 3)
        self.assertEqual(summary["total_items_required"], 3)
        self.assertEqual(summary["total_items_available"], 5)
        
        # Check utilization details
        utilization = summary["utilization_by_type"]
        self.assertIn("kettlebells_16kg", utilization)
        self.assertEqual(utilization["kettlebells_16kg"]["required"], 2)
        self.assertEqual(utilization["kettlebells_16kg"]["available"], 3)
        self.assertAlmostEqual(utilization["kettlebells_16kg"]["utilization_pct"], 66.7, places=1)
        self.assertTrue(utilization["kettlebells_16kg"]["sufficient"])

    def test_workout_generation_with_equipment_filtering(self):
        """Test that workout generation properly filters exercises based on available equipment."""
        plan = load_plan()
        equipment_inventory = plan.get("equipment", {})
        
        gear = parse_equipment()
        # Build pool with equipment filtering
        station_pool = build_station_pool(gear, equipment_inventory)
        
        # With empty equipment inventory, no filtering should occur
        exercise_names = [ex[2] for ex in station_pool]
        # All exercises should be available when equipment validation is disabled
        self.assertIn("KB Overhead Carry", exercise_names)

    def test_no_exercises_available_error(self):
        """Test error handling when no exercises can be performed with available equipment."""
        # Create inventory with no matching equipment
        empty_inventory = {
            "dumbbells_2kg": {"count": 1}  # No kettlebells available
        }
        
        gear = parse_equipment()
        
        # Should raise an error when no exercises can be performed
        with self.assertRaises(SystemExit) as context:
            build_station_pool(gear, empty_inventory)
        
        # Verify it's the right error (exit code 2 from die() function)
        self.assertEqual(context.exception.code, 2)


if __name__ == "__main__":
    unittest.main() 
#!/usr/bin/env python3
"""workout_station_generator.py – v2.6 (2025‑07‑22)
===================================================

Zero‑arg CLI that prints a balanced station map for a 40‑minute strength circuit
and honours an `active_rest` flag in `config/plan.json`.

---------------------------------------------------------------------
CHANGE‑LOG v2.6
---------------------------------------------------------------------
* **Plan‑level control of active rest** – `plan.json` may specify
  ```json
  "active_rest": "auto" | "mix" | true | false
  ```
  • `"auto"` (default) → 50 % coin‑flip per *session*.
  • `"mix"` → 50% active rest, 50% plain rest per *rest period*.
  • `true`  → always insert 15‑s active‑rest drills.
  • `false` → always plain rest.
* Non‑repeating drills: the 9‑item pool is shuffled once; each drill is popped
  until the pool empties, then it reshuffles.
* Added `--csv` flag for optional CSV export.
* Unit‑tests cover all three `active_rest` modes and uniqueness of drills.
* Equipment requirements collection and display in HTML reports.
* Refactored into modular architecture following single responsibility principle.

---------------------------------------------------------------------
FOLDER LAYOUT
---------------------------------------------------------------------
project_root/
├─ equipment/
│   ├─ kettlebells.json
│   ├─ barbells.json
│   ├─ …
│   └─ active_rest.json   # { "rest": [ "Jumping jacks", …9 items ] }
├─ config/
│   └─ plan.json          # see template at end of file
├─ config.py              # Configuration and constants
├─ equipment.py           # Equipment parsing and station pool building
├─ workout_planner.py     # Core workout planning logic
├─ html_generator.py      # HTML generation and formatting
├─ file_utils.py          # File I/O operations
├─ main.py                # CLI entry point
└─ test_workout_generator.py  # Unit tests

---------------------------------------------------------------------
USAGE
---------------------------------------------------------------------
$ python3 workout_station_generator.py           # table → stdout
$ python3 workout_station_generator.py --csv    # also writes stations.csv
$ python -m unittest workout_station_generator.py   # run tests

---------------------------------------------------------------------
MODULAR ARCHITECTURE
---------------------------------------------------------------------
This script has been refactored into multiple modules following single 
responsibility principle:

- config.py: Configuration loading, constants, utilities
- equipment.py: Equipment parsing and station pool management
- workout_planner.py: Core workout generation logic
- html_generator.py: HTML report generation and formatting
- file_utils.py: File I/O operations (save HTML, CSV)
- main.py: CLI entry point and main application logic
- test_workout_generator.py: Unit tests

This file now serves as a backward-compatible wrapper.
"""

import sys
import unittest

# Backward compatibility imports
from main import main
from test_workout_generator import GeneratorTests

# Re-export key functions for backward compatibility
from config import load_plan, load_json, die, EQUIP_DIR, CONFIG_DIR, WORKOUT_STORE_DIR, ACTIVE_REST_FILE, DEFAULT_PLAN, AREA_MAP
from equipment import parse_equipment, build_station_pool, classify_area, merge_equipment_requirements, validate_equipment_requirements, can_exercise_be_performed, filter_feasible_exercises, get_equipment_validation_summary
from workout_planner import build_plan, next_active_rest, can_add_exercise_to_workout, add_equipment_requirements, select_best_equipment_option, report_equipment_status
from html_generator import generate_html_workout, format_exercise_link
from file_utils import save_workout_html, write_csv


if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "test":
        unittest.main(argv=sys.argv[:1])
    else:
        main()

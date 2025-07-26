#!/usr/bin/env python3
"""Configuration management for workout station generator."""

import json
import sys
from pathlib import Path
from typing import Dict, Any

# ----------------------------------------------------------------------------
# CONSTANTS & DEFAULTS
# ----------------------------------------------------------------------------

EQUIP_DIR = Path("equipment")
CONFIG_DIR = Path("config")
WORKOUT_STORE_DIR = Path("workout_store")
ACTIVE_REST_FILE = EQUIP_DIR / "active_rest.json"

DEFAULT_PLAN = {
    "stations": 6,
    "rounds": 3,
    "timing": {
        "work": 45,
        "rest": 15,
    },
    "balance_order": ["upper", "lower", "core"],
    "title": "40‑Minute Swim‑Strength Block",
    "notes": "Auto‑generated plan.",
    "active_rest": "auto",  # true | false | "auto" | "mix"
}

AREA_MAP = {
    "upper": ["push", "pull", "overhead", "vertical", "horizontal", "shoulders", "triceps", "biceps", "upper_core"],
    "lower": ["leg", "posterior", "hinge", "squat", "lunge", "power_leg"],
    "core": ["core", "carry", "rotation", "posterior_chain"],
}

# ----------------------------------------------------------------------------
# UTILITIES
# ----------------------------------------------------------------------------

def die(msg: str) -> None:
    """Print error message and exit."""
    sys.stderr.write(f"✖ {msg}\n")
    sys.exit(2)


def load_json(path: Path) -> Dict[str, Any]:
    """Load and parse JSON file."""
    try:
        with path.open("r") as fh:
            return json.load(fh)
    except (OSError, json.JSONDecodeError) as e:
        die(f"Failed to load {path}: {e}")


def load_plan() -> Dict[str, Any]:
    """Load workout plan configuration."""
    plan_path = CONFIG_DIR / "plan.json"
    if plan_path.exists():
        plan = load_json(plan_path)
        # merge with defaults, shallow‑first then deep for timing
        merged = {**DEFAULT_PLAN, **plan}
        if isinstance(merged["timing"], str):
            w, r = merged["timing"].split("/")
            merged["timing"] = {"work": int(w), "rest": int(r)}
        merged.setdefault("active_rest", "auto")
        return merged
    else:
        sys.stderr.write("⚠ plan.json not found; using defaults.\n")
        return DEFAULT_PLAN.copy() 
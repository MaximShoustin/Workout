"""
Workout History Management Module

This module handles tracking exercise usage history to promote workout variety
by deprioritizing recently used exercises in future workout generations.
"""

import json
import os
from datetime import datetime
from typing import List, Dict, Set, Tuple
from pathlib import Path


class WorkoutHistoryManager:
    """Manages exercise history for workout variety optimization."""
    
    def __init__(self, history_file: str = "workout_history.json"):
        self.history_file = history_file
        self.history_data = self._load_history()
    
    def _load_history(self) -> dict:
        """Load workout history from JSON file."""
        if os.path.exists(self.history_file):
            try:
                with open(self.history_file, 'r') as f:
                    return json.load(f)
            except (json.JSONDecodeError, IOError) as e:
                print(f"⚠️  Warning: Could not load workout history ({e}). Starting fresh.")
        
        # Return default structure if file doesn't exist or is corrupted
        return {
            "workout_sessions": [],
            "exercise_usage_count": {},
            "last_session_date": None,
            "total_workouts_generated": 0,
            "metadata": {
                "created": datetime.now().strftime("%Y-%m-%d"),
                "description": "Exercise usage history for workout variety optimization",
                "version": "1.0"
            }
        }
    
    def _save_history(self) -> None:
        """Save workout history to JSON file."""
        try:
            with open(self.history_file, 'w') as f:
                json.dump(self.history_data, f, indent=2)
        except IOError as e:
            print(f"⚠️  Warning: Could not save workout history ({e})")
    
    def record_workout_session(self, title: str, used_exercise_ids: List[int]) -> None:
        """
        Record a completed workout session with the exercises used.
        
        Args:
            title: Workout title/description
            used_exercise_ids: List of exercise IDs that were used in this workout
        """
        session_date = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        # Add new session
        session = {
            "date": session_date,
            "title": title,
            "used_exercise_ids": used_exercise_ids,
            "exercise_count": len(used_exercise_ids)
        }
        
        self.history_data["workout_sessions"].append(session)
        self.history_data["last_session_date"] = session_date
        self.history_data["total_workouts_generated"] += 1
        
        # Update exercise usage counts
        for exercise_id in used_exercise_ids:
            exercise_id_str = str(exercise_id)
            if exercise_id_str in self.history_data["exercise_usage_count"]:
                self.history_data["exercise_usage_count"][exercise_id_str] += 1
            else:
                self.history_data["exercise_usage_count"][exercise_id_str] = 1
        
        # Keep only last 10 sessions to prevent file from growing too large
        if len(self.history_data["workout_sessions"]) > 10:
            self.history_data["workout_sessions"] = self.history_data["workout_sessions"][-10:]
        
        self._save_history()
        
        print(f"📝 Recorded workout session: {len(used_exercise_ids)} exercises used")
        print(f"📊 Total workouts generated: {self.history_data['total_workouts_generated']}")
    
    def get_recently_used_exercise_ids(self, last_n_sessions: int = 2) -> Set[int]:
        """
        Get exercise IDs that were used in the last N workout sessions.
        
        Args:
            last_n_sessions: Number of recent sessions to consider
            
        Returns:
            Set of exercise IDs used in recent sessions
        """
        recent_sessions = self.history_data["workout_sessions"][-last_n_sessions:]
        recently_used = set()
        
        for session in recent_sessions:
            recently_used.update(session["used_exercise_ids"])
        
        return recently_used
    
    def get_exercise_usage_count(self, exercise_id: int) -> int:
        """
        Get how many times an exercise has been used historically.
        
        Args:
            exercise_id: Exercise ID to check
            
        Returns:
            Number of times this exercise has been used
        """
        return self.history_data["exercise_usage_count"].get(str(exercise_id), 0)
    
    def calculate_exercise_priority_score(self, exercise_id: int, base_priority: float = 1.0) -> float:
        """
        Calculate priority score for an exercise based on usage history.
        Lower scores mean lower priority (less likely to be selected).
        
        Args:
            exercise_id: Exercise ID to score
            base_priority: Base priority score (1.0 = normal)
            
        Returns:
            Priority score (0.1 = very low, 1.0 = normal, higher = preferred)
        """
        # Check if exercise was used recently (last 2 sessions)
        recently_used = self.get_recently_used_exercise_ids(last_n_sessions=2)
        if exercise_id in recently_used:
            return base_priority * 0.1  # Very low priority for recently used
        
        # Check if exercise was used in last 3-5 sessions (moderate penalty)
        moderately_recent = self.get_recently_used_exercise_ids(last_n_sessions=5)
        if exercise_id in moderately_recent:
            return base_priority * 0.5  # Moderate priority reduction
        
        # Favor exercises that haven't been used much historically
        usage_count = self.get_exercise_usage_count(exercise_id)
        if usage_count == 0:
            return base_priority * 1.5  # Prefer never-used exercises
        elif usage_count == 1:
            return base_priority * 1.2  # Slightly prefer rarely used
        
        return base_priority  # Normal priority for other exercises
    
    def get_history_summary(self) -> dict:
        """Get a summary of workout history."""
        total_sessions = len(self.history_data["workout_sessions"])
        total_unique_exercises = len(self.history_data["exercise_usage_count"])
        
        if total_sessions > 0:
            recent_session = self.history_data["workout_sessions"][-1]
            last_workout_date = recent_session["date"]
            last_workout_exercises = len(recent_session["used_exercise_ids"])
        else:
            last_workout_date = "None"
            last_workout_exercises = 0
        
        return {
            "total_workouts": self.history_data["total_workouts_generated"],
            "sessions_tracked": total_sessions,
            "unique_exercises_used": total_unique_exercises,
            "last_workout_date": last_workout_date,
            "last_workout_exercises": last_workout_exercises
        }


def prioritize_exercises_by_variety(exercise_pool: List[Tuple], history_manager: WorkoutHistoryManager) -> List[Tuple]:
    """
    Sort exercise pool by variety score, promoting exercises that haven't been used recently.
    
    Args:
        exercise_pool: List of exercise tuples (area, equip_name, exercise_name, exercise_link, equipment_data, muscles, unilateral, exercise_id)
        history_manager: WorkoutHistoryManager instance
        
    Returns:
        Sorted exercise pool with variety-optimized order
    """
    def get_variety_score(exercise_tuple):
        # Extract exercise ID (last element of tuple)
        exercise_id = exercise_tuple[-1]
        if exercise_id == -1:  # Handle exercises without IDs
            return 1.0
        return history_manager.calculate_exercise_priority_score(exercise_id)
    
    # Sort by variety score (descending - higher scores first)
    return sorted(exercise_pool, key=get_variety_score, reverse=True) 
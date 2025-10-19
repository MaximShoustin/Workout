#!/usr/bin/env python3
"""Test script to demonstrate the muscle groups display functionality."""

from exercise_manager import ExerciseManager

def test_muscle_display():
    """Test the muscle groups display functionality."""
    print("🧪 Testing Muscle Groups Display")
    print("=" * 40)
    
    manager = ExerciseManager()
    manager._print_available_muscles()
    
    print("✅ Test completed!")

if __name__ == "__main__":
    test_muscle_display()

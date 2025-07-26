#!/usr/bin/env python3
"""
Test script to verify:
1. No duplicate active rest activities within the same station
2. Different rest activities between workout runs
"""

import subprocess
import re
import sys

def extract_station_rest_activities(html_file):
    """Extract rest activities by station from HTML file"""
    with open(html_file, 'r') as f:
        content = f.read()
    
    rows = re.findall(r'<tr>.*?</tr>', content, re.DOTALL)
    stations = {}
    
    for row in rows[1:]:  # Skip header row
        station_match = re.search(r'station-letter\">([A-Z])</span>', row)
        rest_activities = re.findall(r'rest-activity\"[^>]*>([^<]+|<a[^>]*>([^<]+)</a>)', row)
        
        if station_match:
            station = station_match.group(1)
            activities = []
            for match in rest_activities:
                if match[1]:  # It's a link
                    activities.append(match[1])
                else:  # It's plain text
                    activities.append(match[0])
            
            if len(activities) >= 2:
                stations[station] = activities[:2]  # Take first two
    
    return stations

def test_duplicates_within_stations(stations):
    """Test for duplicates within each station"""
    duplicates_found = False
    for station, activities in stations.items():
        if len(activities) >= 2 and activities[0] == activities[1]:
            print(f"❌ DUPLICATE in Station {station}: {activities[0]} | {activities[1]}")
            duplicates_found = True
        else:
            print(f"✅ Station {station}: {activities[0]} | {activities[1]}")
    
    return not duplicates_found

def main():
    print("🧪 Testing active rest duplicate prevention...")
    print("=" * 60)
    
    # Generate 3 workouts and test each
    all_workouts = {}
    all_passed = True
    
    for i in range(1, 4):
        print(f"\n📋 Generating workout {i}...")
        
        # Generate workout
        result = subprocess.run(['python3', 'workout_station_generator.py'], 
                              capture_output=True, text=True)
        
        if result.returncode != 0:
            print(f"❌ Failed to generate workout {i}")
            continue
        
        # Extract HTML file path from output
        html_match = re.search(r'workout_store/(WORKOUT_\d+_\d+\.html)', result.stdout)
        if not html_match:
            print(f"❌ Could not find HTML file path for workout {i}")
            continue
        
        html_file = html_match.group(1)
        full_path = f'workout_store/{html_file}'
        
        # Extract station data
        stations = extract_station_rest_activities(full_path)
        all_workouts[i] = stations
        
        print(f"\n🔍 Checking workout {i} for duplicates within stations:")
        workout_passed = test_duplicates_within_stations(stations)
        
        if not workout_passed:
            all_passed = False
    
    # Test for variety between workouts
    print(f"\n🔄 Checking variety between workouts...")
    if len(all_workouts) >= 2:
        workout1_activities = set()
        workout2_activities = set()
        
        for station, activities in all_workouts[1].items():
            workout1_activities.update(activities)
        
        for station, activities in all_workouts[2].items():
            workout2_activities.update(activities)
        
        if workout1_activities == workout2_activities:
            print("❌ Same activities used in both workouts - no variety!")
            all_passed = False
        else:
            common = workout1_activities & workout2_activities
            different1 = workout1_activities - workout2_activities
            different2 = workout2_activities - workout1_activities
            
            print(f"✅ Variety detected!")
            print(f"   Common activities: {len(common)}")
            print(f"   Unique to workout 1: {len(different1)}")
            print(f"   Unique to workout 2: {len(different2)}")
    
    print("\n" + "=" * 60)
    if all_passed:
        print("🎉 ALL TESTS PASSED!")
        print("   ✅ No duplicates within stations")
        print("   ✅ Variety between workout runs")
    else:
        print("❌ SOME TESTS FAILED!")
        sys.exit(1)

if __name__ == "__main__":
    main() 
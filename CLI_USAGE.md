# Workout CLI Commands

You now have a comprehensive command-line interface for your workout program! Here's how to use it:

## Basic Usage

### Generate a Workout
```bash
./workout
```
This generates a new workout using the current settings in `config/plan.json`.

### Show Help
```bash
./workout -help
```
Displays all available commands and options.

### List All Exercises
```bash
./workout -status
```
Shows a comprehensive list of all exercises in your database, organized by:
- Area (upper, lower, core)
- Equipment type
- Exercise IDs for use with other commands

## Advanced Commands

### Add New Exercise
```bash
./workout -add
```
Interactive tool to add new exercises to your database. Guides you through:
- Exercise name and video link
- Muscle groups and area
- Equipment requirements
- Unilateral vs bilateral movement

### Edit Current Workout
```bash
./workout -edit <exercise_ids>
```
Replace specific exercises in your current workout by ID.

**Examples:**
```bash
./workout -edit 101,102,103    # Replace exercises 101, 102, and 103
./workout -edit 88             # Replace just exercise 88
```

**Requirements:**
- Must have a previously generated workout
- IDs must exist in current workout

### Force Include Exercises
```bash
./workout -include <exercise_ids>
```
Generate a new workout that guarantees specific exercises are included.

**Examples:**
```bash
./workout -include 9,10,11     # Must include exercises 9, 10, and 11
./workout -include 29          # Must include exercise 29
```

## Configuration

Edit `config/plan.json` to customize:
- Number of stations and people
- Equipment inventory
- Active rest settings
- Balance order (upper/lower/core)
- Exercise history tracking
- Edit mode enabled/disabled

## Files Generated

- `index.html` - Current workout display
- `workout_store/WORKOUT_*.html` - Individual workout files
- `workout_store/LAST_WORKOUT_PLAN.json` - Current workout data for editing

## Tips

1. **Finding Exercise IDs**: Use `./workout -status` to see all available exercise IDs
2. **Equipment Constraints**: The system respects your equipment inventory from `plan.json`
3. **Exercise Variety**: The system tracks workout history to promote exercise variety
4. **Unilateral Exercises**: Marked with `[U]` in status - require left/right execution
5. **Troubleshooting**: If workout generation fails, try reducing stations or adding more equipment

## Example Workflow

```bash
# See what exercises are available
./workout -status

# Generate a workout
./workout

# If you want to replace exercise 29 with something else
./workout -edit 29

# Generate a new workout that must include exercises 9 and 10
./workout -include 9,10

# Add a new exercise to the database
./workout -add
```

The CLI maintains all the existing functionality while providing a much cleaner interface than running Python commands directly!

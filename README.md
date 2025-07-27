# 🏋️ Workout Generator

> A smart, randomized workout planner that creates personalized fitness routines based on your available equipment

Transform your home gym chaos into structured, varied workouts! This tool intelligently generates workout plans that adapt to whatever equipment you have, ensuring you never get bored and always have a balanced routine.

## ✨ Why This Tool?

- **No More Decision Fatigue**: Generates complete workouts instantly
- **Equipment-Smart**: Only suggests exercises you can actually do
- **Always Different**: Randomized selection keeps workouts fresh
- **Gym-Quality Programming**: Balanced muscle groups and proper progression
- **Beautiful Output**: Clean HTML reports you can print or view on any device

## 🚀 Quick Start

### Prerequisites
- Python 3.7+
- No additional dependencies required (uses only standard library)

### Generate Your First Workout

1. **Clone and run:**
   ```bash
   git clone <your-repo-url>
   cd Workout
   python main.py
   ```

2. **View your workout:**
   ```bash
   # Opens in your default browser
   open workout_store/workout_[timestamp].html
   ```

That's it! Your first workout is ready.

## ⚙️ Configuration Guide

### Basic Setup: `config/plan.json`

The magic happens in your configuration file. Here's how to customize it:

```json
{
    "stations": 5,              // Number of exercise stations
    "people": 10,               // How many people will use this workout
    "rounds": 2,                // How many times through all stations
    "steps_per_station": 2,     // Exercises per station
    
    "timing": {
        "work": 40,             // Seconds of work
        "rest": 20              // Seconds of rest
    },
    
    "active_rest": "true",      // Include active recovery exercises
    "active_rest_count": 4,     // Number of active rest exercises
    
    "title": "My Awesome Workout",
    "notes": "Remember to warm up!"
}
```

### Equipment Inventory

Tell the system what you have available:

```json
"equipment": {
    "kettlebells_16kg": { "count": 2 },
    "dumbbells_10kg": { "count": 4 },
    "bench": { "count": 1 },
    "plyo_box": { "count": 1 }
}
```

**Supported Equipment:**
- **Kettlebells**: 2kg, 4kg, 6kg, 16kg, 24kg, 32kg
- **Dumbbells**: 3kg, 5kg, 6kg, 7kg, 10kg, 15kg, 22kg
- **Other**: bench, plyo_box, barbells, slam_balls_5kg, dip_parallel_bars

### Smart Features

**Must-Use Equipment** (guarantee certain equipment appears):
```json
"must_use": ["kettlebells_16kg", "bench", "plyo_box"]
```

**Muscle Group Balance** (order of priority):
```json
"balance_order": ["upper", "lower", "core"]
```

## 💡 Usage Examples

### Generate Different Workout Styles

```bash
# Quick 15-minute session
python main.py  # Edit config: 3 stations, 1 round

# Long gym session  
python main.py  # Edit config: 8 stations, 3 rounds

# Upper body focus
python main.py  # Edit balance_order: ["upper", "upper", "lower", "core"]
```

### Equipment-Based Workouts

**Home Gym (Limited Equipment):**
```json
{
    "stations": 4,
    "equipment": {
        "kettlebells_16kg": { "count": 1 },
        "dumbbells_10kg": { "count": 2 }
    }
}
```

**Full Gym Setup:**
```json
{
    "stations": 8,
    "equipment": {
        "kettlebells_16kg": { "count": 4 },
        "barbells": { "count": 2 },
        "bench": { "count": 2 },
        "plyo_box": { "count": 1 },
        "slam_balls_5kg": { "count": 10 }
    }
}
```

## 📊 Understanding Your Workout Output

The generated HTML includes:

### 🎯 Workout Overview
- **Equipment Check**: ✅ All requirements satisfied
- **Timing Structure**: Work/rest intervals
- **Total Duration**: Complete workout time estimate

### 🏃 Station Details
Each station shows:
- **Exercise Name** with instructional video link
- **Target Muscles** (e.g., "quadriceps, glutes, core")
- **Equipment Required** with quantities
- **Area Focus** (upper/lower/core)

### 🔄 Active Rest Options
Between stations, optional activities like:
- Light stretching
- Mobility work  
- Breathing exercises

## 🛠️ Advanced Usage

### Reproducible Workouts
```bash
# The tool shows the seed used
🎲 Final seed used: 1735123456

# Modify the code to use a specific seed for repeating workouts
```

### Multiple Configurations
```bash
# Create different config files
cp config/plan.json config/cardio.json
cp config/plan.json config/strength.json

# Modify config.py to load different plans
```

### Batch Generation
```bash
# Generate multiple workouts
for i in {1..5}; do python main.py; done
```

## 🤝 Adding New Exercises

Exercise databases are in `equipment/*.json`. Each exercise includes:

```json
{
    "name": "Goblet Squat",
    "link": "https://youtube.com/...",
    "area": "lower",
    "muscles": "quadriceps, glutes, core",
    "equipment": {
        "kettlebells_16kg": { "count": 1 }
    }
}
```

**Categories:**
- `hinge_power`: Hip hinge movements
- `squat_lunge`: Squatting patterns  
- `upper_body`: Pushing/pulling
- `core_carry`: Core and stability
- `shoulders`: Shoulder-specific
- `triceps`: Tricep isolation
- `biceps`: Bicep isolation

## 🐞 Troubleshooting

**"All X attempts failed!"**
- Reduce number of stations
- Add more equipment to your inventory
- Check that equipment counts are realistic

**"Equipment validation: Some requirements exceed available inventory"**
- Increase equipment counts in config
- Use different equipment types
- The workout will still generate but flag potential conflicts

**Empty workout stations**
- Add more exercises to equipment JSON files
- Verify equipment names match between config and exercise files

## 📄 Legal & Safety

> **Important**: See [LEGAL.md](LEGAL.md) for disclaimers, video attribution, and safety information.

## 🤝 Contributing

Contributions welcome! Areas that need help:
- **New Exercise Variations**: Add to equipment JSON files
- **Equipment Support**: New equipment types
- **Output Formats**: PDF, mobile-friendly views
- **Workout Templates**: Pre-built configurations

## 📧 Support

- **🐛 Bug Reports**: Open an issue
- **💡 Feature Requests**: Start a discussion
- **❓ Usage Questions**: Check existing issues first

---

**Ready to get stronger?** Run `python main.py` and let's build something great! 💪
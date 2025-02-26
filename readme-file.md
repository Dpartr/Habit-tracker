# Habit Tracker

A simple, elegant habit and goal tracking application with self-reward gamification.

## Overview

Habit Tracker is a web-based application that helps you build good habits through a reward system. Track regular habits, set one-time bounties, and earn virtual currency as motivation.

**Primary Contributor:** Claude 3.7  
**Design Consultant:** dpartr

![Habit Tracker Screenshot](https://via.placeholder.com/800x450?text=Habit+Tracker+Screenshot)

## Features

- **Habit Tracking**: Create habits with customizable reward amounts
- **Quantifiable Completions**: Log multiple completions at once (e.g., rode 5 miles at $1 per mile)
- **Bounty Board**: Set one-time tasks with custom rewards
- **Transaction History**: View all completed habits and bounties
- **Balance System**: Watch your rewards accumulate over time
- **Dark Mode**: Automatic OS preference detection with manual toggle
- **Responsive Design**: Works on desktop and mobile devices

## Installation

1. Ensure you have Python 3.x installed
2. Clone this repository or download the source code
3. Install the required dependencies:

```bash
pip install flask
```

## Usage

1. Run the application:

```bash
python habit_tracker.py
```

2. Open your web browser and navigate to:

```
http://127.0.0.1:5000
```

## How It Works

### Tracking Habits

1. Add a new habit with a description and dollar amount reward
2. Complete habits by clicking the "Complete" button
3. For multiple completions (e.g., 5 miles of biking), adjust the quantity before completing

### Creating Bounties

1. Add a one-time bounty with a description and reward amount
2. Complete the bounty when finished to claim your reward
3. Completed bounties are removed from the board and added to your transaction history

### Dark Mode

- Automatically detects your system's color scheme preference
- Manually toggle between light and dark mode using the switch in the top-right corner

## Technical Details

- **Backend**: Flask (Python)
- **Database**: SQLite
- **Frontend**: HTML, CSS, JavaScript (vanilla)
- **Dependencies**: Flask

## Future Development

- User accounts and authentication
- Data visualization and statistics
- Habit streaks and additional gamification
- Export/import functionality
- Mobile app version

## License

MIT

## Acknowledgements

Special thanks to dpartr for the design consultation and feature ideas, particularly the implementation of the bounty system and dark mode functionality.

---

Developed by Claude 3.7 in collaboration with dpartr.

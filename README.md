# AI Personal Trainer

This application uses computer vision to detect your body position and count exercise repetitions. It's like having a personal trainer that watches your form and keeps track of your workout progress.

## Features

- BMI calculator with personalized feedback
- Fitness goal setting (gain, maintain, or lose weight)
- Weekly workout plan with push/pull/legs split
- Daily exercise tracking and progress monitoring
- Interactive exercise selection screen
- Customizable workout goals (reps and sets)
- Rest periods between sets with timer
- Real-time pose detection using MediaPipe
- Automatic rep counting for multiple exercises:
  - Squats
  - Push-ups
  - Bicep curls
  - Shoulder press
  - Tricep extensions
  - Rows
  - Lat pulldowns
  - Lunges
  - Calf raises
- Visual feedback on your form
- Set tracking and completion notifications
- Easy switching between exercise types

## Requirements

- Python 3.7+
- Webcam
- The packages listed in `requirements.txt`

## Installation

1. Clone or download this repository
2. Install the required packages:

```
pip install -r requirements.txt
```

## Usage

Run the main application:

```
python ai_trainer.py
```

### Controls

- On the BMI calculation screen:
  - Use the '+' and '-' buttons to adjust your weight and height
  - Click 'CALCULATE BMI' to see your BMI result and health category
  - Click 'CONTINUE' to proceed to the fitness goal screen
- On the fitness goal screen:
  - Select your fitness goal (maintain, gain, or lose weight)
  - The app will recommend a goal based on your BMI
  - Click 'CONTINUE' to proceed to the workout setup
- On the goal setting screen:
  - Review the recommended workout plan based on your fitness goal
  - Customize rep and set counts if desired
  - Click 'CONTINUE' to proceed to the weekly plan
- On the weekly workout plan screen:
  - View your weekly workout schedule (Push/Pull/Legs split)
  - Click on a day to see the exercises for that day
  - Track your progress with completed days highlighted in green
- On the daily exercises screen:
  - View the exercises scheduled for the selected day
  - Click on an exercise to begin training
  - Completed exercises are marked in green
- During training:
  - The app counts your reps automatically using pose detection
  - Press 'b' to go back to the daily exercises screen
  - Press 'w' to go back to the weekly plan screen
  - Press 'q' or ESC to quit the application
- During rest periods:
  - Wait for the timer to complete or click "START NEXT SET" to continue
  - Press 's' to skip the rest period
  - Press 'b' to go back to daily exercises
  - Press 'w' to go back to weekly plan

## How It Works

The application uses MediaPipe's pose estimation to track 33 key points on your body. Based on the angles between specific joints, it can determine if you've completed a repetition of an exercise. When you reach your rep goal for a set, the application automatically shows a rest screen with a timer and tips. After the rest period or when you click the button, it advances to the next set until all sets are completed.

The BMI calculator uses the standard formula (weight in kg / height in meters squared) to calculate your Body Mass Index and provides feedback on your body composition status, helping you understand your fitness starting point. Based on your BMI, the application recommends a fitness goal (maintain, gain, or lose weight) to guide your workout journey.

The weekly workout plan follows a Push/Pull/Legs split routine with two rest days, which is a scientifically proven approach for balanced muscle development. The app tracks your progress throughout the week, marking completed exercises and workout days, helping you stay consistent with your fitness routine.

## Future Improvements

- Add more exercise types
- Improve accuracy of rep counting
- Add form feedback and suggestions
- Create a user profile to track progress over time
- Add a graphical user interface for better interaction
- Implement workout history and statistics

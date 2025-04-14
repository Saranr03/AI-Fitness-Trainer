import streamlit as st
import cv2
import mediapipe as mp
import numpy as np
import time
from ai_trainer import AITrainer

# Set page configuration
st.set_page_config(page_title="AI Personal Trainer", layout="wide")

# App title and description
st.title("AI Personal Trainer")
st.markdown("""
This application uses computer vision to detect your body position and count exercise repetitions.
It's like having a personal trainer that watches your form and keeps track of your workout progress.
""")

# Initialize session state variables if they don't exist
if 'trainer' not in st.session_state:
    st.session_state.trainer = AITrainer()

if 'current_screen' not in st.session_state:
    st.session_state.current_screen = "bmi"

if 'rep_goal' not in st.session_state:
    st.session_state.rep_goal = 15

if 'set_goal' not in st.session_state:
    st.session_state.set_goal = 3

# Function to render BMI screen
def render_bmi_screen():
    st.header("BMI Calculator")
    
    col1, col2 = st.columns(2)
    
    with col1:
        # Weight input with + and - buttons
        st.subheader("Weight (kg)")
        weight_col1, weight_col2, weight_col3 = st.columns([1, 2, 1])
        with weight_col1:
            if st.button("-", key="weight_minus"):
                if st.session_state.trainer.weight_kg > 1:
                    st.session_state.trainer.weight_kg -= 1
        
        with weight_col2:
            st.session_state.trainer.weight_kg = st.number_input(
                "", 
                min_value=1, 
                max_value=300, 
                value=st.session_state.trainer.weight_kg,
                label_visibility="collapsed"
            )
        
        with weight_col3:
            if st.button("+", key="weight_plus"):
                st.session_state.trainer.weight_kg += 1
    
    with col2:
        # Height input with + and - buttons
        st.subheader("Height (cm)")
        height_col1, height_col2, height_col3 = st.columns([1, 2, 1])
        with height_col1:
            if st.button("-", key="height_minus"):
                if st.session_state.trainer.height_cm > 1:
                    st.session_state.trainer.height_cm -= 1
        
        with height_col2:
            st.session_state.trainer.height_cm = st.number_input(
                "", 
                min_value=1, 
                max_value=300, 
                value=st.session_state.trainer.height_cm,
                label_visibility="collapsed"
            )
        
        with height_col3:
            if st.button("+", key="height_plus"):
                st.session_state.trainer.height_cm += 1
    
    # Calculate BMI button
    if st.button("CALCULATE BMI", use_container_width=True):
        st.session_state.trainer.calculate_bmi()
    
    # Display BMI result if calculated
    if st.session_state.trainer.bmi > 0:
        st.subheader(f"Your BMI: {st.session_state.trainer.bmi} ({st.session_state.trainer.bmi_category})")
        
        # BMI category explanation
        if st.session_state.trainer.bmi_category == "Underweight":
            st.info("You are underweight. Consider gaining some weight for better health.")
        elif st.session_state.trainer.bmi_category == "Normal weight":
            st.success("You have a healthy weight. Keep it up!")
        elif st.session_state.trainer.bmi_category == "Overweight":
            st.warning("You are overweight. Consider losing some weight for better health.")
        elif st.session_state.trainer.bmi_category == "Obese":
            st.error("You are obese. It's recommended to consult with a healthcare professional.")
        
        # Continue button
        if st.button("CONTINUE TO FITNESS GOALS", use_container_width=True):
            st.session_state.current_screen = "fitness_goal"
            st.rerun()

# Function to render fitness goal screen
def render_fitness_goal_screen():
    st.header("Select Your Fitness Goal")
    
    # Display BMI information
    st.subheader(f"Your BMI: {st.session_state.trainer.bmi} ({st.session_state.trainer.bmi_category})")
    
    # Determine recommended goal based on BMI
    recommended_goal = ""
    if st.session_state.trainer.bmi_category == "Underweight":
        recommended_goal = "gain"
    elif st.session_state.trainer.bmi_category == "Overweight" or st.session_state.trainer.bmi_category == "Obese":
        recommended_goal = "lose"
    elif st.session_state.trainer.bmi_category == "Normal weight":
        recommended_goal = "maintain"
    
    # Goal selection
    goal_options = {
        "maintain": "Maintain weight",
        "gain": "Gain weight",
        "lose": "Lose weight"
    }
    
    # Display goal options with recommendation
    st.write("Select your fitness goal:")
    for goal_key, goal_text in goal_options.items():
        button_text = goal_text
        if goal_key == recommended_goal:
            button_text += " (Recommended)"
        
        if st.button(button_text, key=f"goal_{goal_key}", use_container_width=True):
            st.session_state.trainer.fitness_goal = goal_key
            st.success(f"Fitness goal set to: {goal_text}")
    
    # Continue button
    if st.session_state.trainer.fitness_goal:
        if st.button("CONTINUE TO WORKOUT PLAN", use_container_width=True):
            st.session_state.current_screen = "weekly_plan"
            st.rerun()

# Function to render weekly plan screen
def render_weekly_plan_screen():
    st.header("Weekly Workout Plan")
    
    # Show weekly progress
    completed_days, total_days = st.session_state.trainer.get_weekly_progress()
    progress_percentage = int((completed_days / total_days) * 100) if total_days > 0 else 0
    
    st.progress(progress_percentage / 100)
    st.write(f"Weekly Progress: {completed_days}/{total_days} days ({progress_percentage}%)")
    
    # Display days of the week with their workout types and completion status
    st.subheader("Select a day to view exercises:")
    
    for day_idx, day_name in enumerate(st.session_state.trainer.days_of_week):
        day_plan = st.session_state.trainer.workout_plan[day_idx]
        day_type = day_plan["type"]
        is_completed = day_plan["completed"]
        is_current = day_idx == st.session_state.trainer.current_day
        
        # Determine button style based on status
        button_text = f"{day_name}: {day_type}"
        if is_completed:
            button_text += " \u2713"  # Checkmark symbol
        if is_current:
            button_text += " (Current Day)"
        
        # Create button for each day
        if st.button(button_text, key=f"day_{day_idx}", use_container_width=True):
            st.session_state.trainer.set_current_day(day_idx)
            st.session_state.current_screen = "daily_exercises"
            st.rerun()

# Function to render daily exercises screen
def render_daily_exercises_screen():
    # Get current day plan
    day_plan = st.session_state.trainer.get_current_day_plan()
    day_name = st.session_state.trainer.days_of_week[st.session_state.trainer.current_day]
    day_type = day_plan["type"]
    
    st.header(f"{day_name} - {day_type} Day")
    
    # If it's a rest day
    if day_type == "Rest":
        st.success("REST DAY - No exercises scheduled")
        st.info("Take time to recover and stretch!")
    else:
        # Show exercises for the day
        exercises = day_plan["exercises"]
        
        st.subheader("Today's Exercises")
        st.write("Click on an exercise to begin or mark as completed:")
        
        for exercise in exercises:
            is_completed = st.session_state.trainer.is_exercise_completed(exercise)
            
            # Format exercise name for display
            exercise_display_name = exercise.replace('_', ' ').title()
            
            # Create button for each exercise
            button_text = f"{exercise_display_name}"
            if is_completed:
                button_text += " \u2713"  # Checkmark symbol
            
            if st.button(button_text, key=f"exercise_{exercise}", use_container_width=True):
                if not is_completed:
                    # Set the selected exercise
                    st.session_state.trainer.exercise_type = exercise
                    st.session_state.current_screen = "training"
                    st.rerun()
                else:
                    st.info(f"{exercise_display_name} already completed!")
    
    # Back button
    if st.button("BACK TO WEEKLY PLAN", use_container_width=True):
        st.session_state.current_screen = "weekly_plan"
        st.rerun()

# Function to render training screen
def render_training_screen():
    st.header("Exercise Training")
    
    # Display exercise information
    exercise_name = st.session_state.trainer.exercise_type.replace('_', ' ').title()
    st.subheader(f"Current Exercise: {exercise_name}")
    
    # Display rep and set information
    col1, col2 = st.columns(2)
    with col1:
        st.metric("Reps", f"{st.session_state.trainer.counter}/{st.session_state.trainer.rep_goal}")
    with col2:
        st.metric("Set", f"{st.session_state.trainer.current_set}/{st.session_state.trainer.set_goal}")
    
    # Start the webcam
    cap = cv2.VideoCapture(0)
    stframe = st.empty()
    
    # Stop button
    stop_button = st.button("STOP EXERCISE")
    
    # Main training loop
    while not stop_button:
        ret, frame = cap.read()
        if not ret:
            st.error("Failed to grab frame from camera")
            break
        
        # Process frame for pose detection and rep counting
        image = st.session_state.trainer.process_frame(frame)
        
        # Convert BGR to RGB for Streamlit
        image_rgb = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
        
        # Display the frame
        stframe.image(image_rgb, channels="RGB")
        
        # Check if set is complete and transition to rest
        if st.session_state.trainer.is_set_complete() and not st.session_state.trainer.is_workout_complete():
            cap.release()
            st.session_state.trainer.rest_start_time = time.time()
            st.session_state.current_screen = "rest"
            st.rerun()
            break
        
        # Check if workout is complete
        if st.session_state.trainer.is_workout_complete():
            cap.release()
            # Mark the exercise as completed
            st.session_state.trainer.mark_exercise_completed(st.session_state.trainer.exercise_type)
            
            # Check if there are more exercises for the day
            current_day_plan = st.session_state.trainer.get_current_day_plan()
            current_exercises = current_day_plan["exercises"]
            all_completed = True
            next_exercise = None
            
            # Find the next uncompleted exercise
            for exercise in current_exercises:
                if not st.session_state.trainer.is_exercise_completed(exercise):
                    all_completed = False
                    next_exercise = exercise
                    break
            
            # If all exercises are completed, mark the day as completed
            if all_completed:
                st.session_state.trainer.mark_day_completed()
                st.session_state.current_screen = "daily_exercises"
            else:
                # Move to the next exercise
                st.session_state.trainer.exercise_type = next_exercise
                st.session_state.trainer.counter = 0
                st.session_state.trainer.current_set = 1
                st.session_state.current_screen = "training"
            
            st.rerun()
            break
    
    # Release resources when stopped
    cap.release()
    
    # Back button
    if st.button("BACK TO EXERCISES"):
        st.session_state.current_screen = "daily_exercises"
        st.rerun()

# Function to render rest screen
def render_rest_screen():
    st.header("Rest Period")
    
    # Calculate remaining rest time
    if st.session_state.trainer.rest_start_time > 0:
        elapsed_time = time.time() - st.session_state.trainer.rest_start_time
        remaining_seconds = max(0, int(st.session_state.trainer.rest_time - elapsed_time))
    else:
        remaining_seconds = 0
    
    # Display rest information
    st.subheader(f"Set {st.session_state.trainer.current_set} of {st.session_state.trainer.set_goal} completed!")
    st.subheader(f"Rest Time Remaining: {remaining_seconds} seconds")
    
    # Progress bar for rest time
    progress = 1.0 - (remaining_seconds / st.session_state.trainer.rest_time) if st.session_state.trainer.rest_time > 0 else 1.0
    st.progress(min(1.0, max(0.0, progress)))
    
    # Rest tips
    st.info("Take deep breaths and hydrate during your rest period.")
    
    # Skip rest button
    if st.button("SKIP REST", use_container_width=True):
        st.session_state.trainer.start_next_set()
        st.session_state.trainer.rest_start_time = 0
        st.session_state.current_screen = "training"
        st.rerun()
    
    # Auto transition if rest time is over
    if remaining_seconds <= 0 and st.session_state.trainer.rest_start_time > 0:
        st.session_state.trainer.start_next_set()
        st.session_state.trainer.rest_start_time = 0
        st.session_state.current_screen = "training"
        st.rerun()

# Main app logic - render the appropriate screen based on current state
if st.session_state.current_screen == "bmi":
    render_bmi_screen()
elif st.session_state.current_screen == "fitness_goal":
    render_fitness_goal_screen()
elif st.session_state.current_screen == "weekly_plan":
    render_weekly_plan_screen()
elif st.session_state.current_screen == "daily_exercises":
    render_daily_exercises_screen()
elif st.session_state.current_screen == "training":
    render_training_screen()
elif st.session_state.current_screen == "rest":
    render_rest_screen()

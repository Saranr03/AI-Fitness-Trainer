import cv2
import mediapipe as mp
import numpy as np
import time

class AITrainer:
    def __init__(self):
        # Initialize MediaPipe Pose
        self.mp_pose = mp.solutions.pose
        self.pose = self.mp_pose.Pose(min_detection_confidence=0.5, min_tracking_confidence=0.5)
        self.mp_drawing = mp.solutions.drawing_utils
        
        # Exercise counter variables
        self.counter = 0
        self.stage = None  # up or down for exercises like squats, pushups
        self.exercise_type = "squat"  # Default exercise
        
        # Set and rep tracking
        self.current_set = 1
        self.rep_goal = 15  # Default rep goal
        self.set_goal = 3   # Default set goal
        self.rest_between_sets = True  # Enable rest between sets
        self.rest_time = 60  # Rest time in seconds
        self.rest_start_time = 0
        
        # User profile data
        self.weight_kg = 70  # Default weight in kg
        self.height_cm = 170  # Default height in cm
        self.bmi = 0.0  # BMI value
        self.bmi_category = ""  # BMI category
        self.fitness_goal = "maintain"  # Default fitness goal (maintain, gain, lose)
        
        # Available exercises
        self.exercises = ["squat", "pushup", "bicep_curl", "shoulder_press"]
        self.current_exercise_index = 0
        
        # Weekly workout plan
        self.current_day = 0  # 0-6 (Monday-Sunday)
        self.days_of_week = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
        
        # Track completed exercises
        self.completed_exercises = []
        
        # Initialize workout plan
        self.workout_plan = {
            0: {"type": "Push", "exercises": ["pushup", "shoulder_press", "tricep_extension"], "completed": False},
            1: {"type": "Pull", "exercises": ["bicep_curl", "row", "lat_pulldown"], "completed": False},
            2: {"type": "Legs", "exercises": ["squat", "lunge", "calf_raise"], "completed": False},
            3: {"type": "Rest", "exercises": [], "completed": True},
            4: {"type": "Push", "exercises": ["pushup", "shoulder_press", "tricep_extension"], "completed": False},
            5: {"type": "Pull", "exercises": ["bicep_curl", "row", "lat_pulldown"], "completed": False},
            6: {"type": "Rest", "exercises": [], "completed": True}
        }
        
    def get_current_day_plan(self):
        """Get the workout plan for the current day"""
        return self.workout_plan[self.current_day]
    
    def get_current_day_exercises(self):
        """Get the exercises for the current day"""
        return self.workout_plan[self.current_day]["exercises"]
    
    def is_exercise_completed(self, exercise_name):
        """Check if an exercise is completed"""
        return exercise_name in self.completed_exercises
    
    def mark_exercise_completed(self, exercise_name):
        """Mark an exercise as completed"""
        if exercise_name not in self.completed_exercises:
            self.completed_exercises.append(exercise_name)
    
    def mark_day_completed(self):
        """Mark the current day as completed"""
        self.workout_plan[self.current_day]["completed"] = True
    
    def set_current_day(self, day):
        """Set the current day (0-6 for Monday-Sunday)"""
        if 0 <= day <= 6:
            self.current_day = day
    
    def get_weekly_progress(self):
        """Get the progress for the entire week"""
        completed_days = sum(1 for day in range(7) if self.workout_plan[day]["completed"])
        total_days = sum(1 for day in range(7) if self.workout_plan[day]["type"] != "Rest")
        return completed_days, total_days
    
    def calculate_angle(self, a, b, c):
        """Calculate the angle between three points"""
        a = np.array(a)  # First point
        b = np.array(b)  # Mid point
        c = np.array(c)  # End point
        
        radians = np.arctan2(c[1] - b[1], c[0] - b[0]) - np.arctan2(a[1] - b[1], a[0] - b[0])
        angle = np.abs(radians * 180.0 / np.pi)
        
        if angle > 180.0:
            angle = 360 - angle
            
        return angle
    
    def calculate_bmi(self):
        """Calculate BMI based on weight and height"""
        height_m = self.height_cm / 100.0  # Convert cm to m
        self.bmi = round(self.weight_kg / (height_m * height_m), 1)
        
        # Determine BMI category
        if self.bmi < 18.5:
            self.bmi_category = "Underweight"
        elif 18.5 <= self.bmi < 25:
            self.bmi_category = "Normal weight"
        elif 25 <= self.bmi < 30:
            self.bmi_category = "Overweight"
        else:
            self.bmi_category = "Obese"
        
        return self.bmi, self.bmi_category
    
    def set_user_data(self, weight_kg, height_cm):
        """Set user's weight and height and calculate BMI"""
        self.weight_kg = weight_kg
        self.height_cm = height_cm
        self.calculate_bmi()
        print(f"User data set: Weight: {weight_kg}kg, Height: {height_cm}cm, BMI: {self.bmi} ({self.bmi_category})")
    
    def change_exercise(self):
        """Cycle through available exercises"""
        self.current_exercise_index = (self.current_exercise_index + 1) % len(self.exercises)
        self.exercise_type = self.exercises[self.current_exercise_index]
        self.counter = 0
        self.current_set = 1
        self.stage = None
        print(f"Exercise changed to: {self.exercise_type}")
    
    def set_exercise(self, exercise_type):
        """Set the exercise type directly"""
        if exercise_type in self.exercises:
            self.exercise_type = exercise_type
            self.counter = 0
            self.current_set = 1
            self.stage = None
            print(f"Exercise set to: {self.exercise_type}")
    
    def set_goals(self, rep_goal, set_goal):
        """Set rep and set goals"""
        self.rep_goal = rep_goal
        self.set_goal = set_goal
        print(f"Goals set: {rep_goal} reps, {set_goal} sets")
    
    def start_next_set(self):
        """Start the next set after rest"""
        self.counter = 0
        print(f"Starting set {self.current_set} of {self.set_goal}")
    
    def is_set_complete(self):
        """Check if the current set is complete"""
        return self.counter >= self.rep_goal
    
    def is_workout_complete(self):
        """Check if all sets are complete"""
        return self.current_set > self.set_goal
    
    def count_reps(self, landmarks):
        """Count repetitions based on the current exercise type"""
        previous_counter = self.counter
        
        if self.exercise_type == "squat":
            self._count_squats(landmarks)
        elif self.exercise_type == "pushup":
            self._count_pushups(landmarks)
        elif self.exercise_type == "bicep_curl":
            self._count_bicep_curls(landmarks)
        elif self.exercise_type == "shoulder_press":
            self._count_shoulder_press(landmarks)
        
        # Check if rep goal reached and update set
        if self.counter > previous_counter and self.counter >= self.rep_goal:
            print(f"Set {self.current_set} completed! {self.counter} reps done.")
            if self.current_set < self.set_goal:
                self.current_set += 1
                if self.rest_between_sets:
                    self.rest_start_time = time.time()
                else:
                    self.counter = 0  # Reset counter if not resting between sets
                return True  # Signal that a set was completed
            else:
                print(f"All {self.set_goal} sets completed! Great job!")
                return True  # Signal that all sets were completed
        
        return False  # No set completed this rep
    
    def is_resting(self):
        """Check if the trainer is currently resting"""
        if self.rest_between_sets and self.rest_start_time != 0:
            elapsed_time = time.time() - self.rest_start_time
            if elapsed_time < self.rest_time:
                return True
            else:
                self.rest_start_time = 0
                self.start_next_set()
        return False
    
    def process_frame(self, frame):
        """Process a video frame and return the annotated frame"""
        # Recolor image to RGB
        image = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        image.flags.writeable = False
      
        # Make detection
        results = self.pose.process(image)
    
        # Recolor back to BGR
        image.flags.writeable = True
        image = cv2.cvtColor(image, cv2.COLOR_RGB2BGR)
        
        # Extract landmarks
        try:
            landmarks = results.pose_landmarks.landmark
            
            # Count reps
            if not self.is_resting():
                self.count_reps(landmarks)
            
        except:
            pass
        
        # Render detections
        self.mp_drawing.draw_landmarks(
            image, 
            results.pose_landmarks, 
            self.mp_pose.POSE_CONNECTIONS,
            self.mp_drawing.DrawingSpec(color=(245,117,66), thickness=2, circle_radius=2), 
            self.mp_drawing.DrawingSpec(color=(245,66,230), thickness=2, circle_radius=2)
        )
        
        # Display status box
        cv2.rectangle(image, (0, 0), (225, 120), (245, 117, 16), -1)
        
        # Display exercise type
        cv2.putText(image, 'EXERCISE', (15, 12), 
                    cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 0, 0), 1, cv2.LINE_AA)
        cv2.putText(image, self.exercise_type.replace('_', ' ').title(), 
                    (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 1, cv2.LINE_AA)
        
        # Display count
        cv2.putText(image, 'COUNT', (15, 50), 
                    cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 0, 0), 1, cv2.LINE_AA)
        cv2.putText(image, f"{self.counter}/{self.rep_goal}", 
                    (10, 70), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 1, cv2.LINE_AA)
        
        # Display set
        cv2.putText(image, 'SET', (15, 90), 
                    cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 0, 0), 1, cv2.LINE_AA)
        cv2.putText(image, f"{self.current_set}/{self.set_goal}", 
                    (10, 110), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 1, cv2.LINE_AA)
        
        # Display stage if available
        if self.stage:
            cv2.putText(image, 'STAGE', (100, 50), 
                        cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 0, 0), 1, cv2.LINE_AA)
            cv2.putText(image, self.stage, 
                        (100, 70), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 1, cv2.LINE_AA)
        
        # Display rest time if resting
        if self.is_resting():
            elapsed_time = time.time() - self.rest_start_time
            remaining_time = self.rest_time - int(elapsed_time)
            cv2.putText(image, 'REST', (100, 90), 
                        cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 0, 0), 1, cv2.LINE_AA)
            cv2.putText(image, f"{remaining_time} seconds", 
                        (100, 110), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 1, cv2.LINE_AA)
        
        return image


    def _count_squats(self, landmarks):
        """Count squat repetitions"""
        # Get coordinates
        hip = [landmarks[self.mp_pose.PoseLandmark.LEFT_HIP.value].x, 
               landmarks[self.mp_pose.PoseLandmark.LEFT_HIP.value].y]
        knee = [landmarks[self.mp_pose.PoseLandmark.LEFT_KNEE.value].x, 
                landmarks[self.mp_pose.PoseLandmark.LEFT_KNEE.value].y]
        ankle = [landmarks[self.mp_pose.PoseLandmark.LEFT_ANKLE.value].x, 
                 landmarks[self.mp_pose.PoseLandmark.LEFT_ANKLE.value].y]
        
        # Calculate angle
        angle = self.calculate_angle(hip, knee, ankle)
        
        # Squat counter logic
        if angle > 160:
            self.stage = "up"
        if angle < 100 and self.stage == "up":
            self.stage = "down"
            self.counter += 1
    
    def _count_pushups(self, landmarks):
        """Count pushup repetitions"""
        # Get coordinates
        shoulder = [landmarks[self.mp_pose.PoseLandmark.LEFT_SHOULDER.value].x, 
                    landmarks[self.mp_pose.PoseLandmark.LEFT_SHOULDER.value].y]
        elbow = [landmarks[self.mp_pose.PoseLandmark.LEFT_ELBOW.value].x, 
                 landmarks[self.mp_pose.PoseLandmark.LEFT_ELBOW.value].y]
        wrist = [landmarks[self.mp_pose.PoseLandmark.LEFT_WRIST.value].x, 
                 landmarks[self.mp_pose.PoseLandmark.LEFT_WRIST.value].y]
        
        # Calculate angle
        angle = self.calculate_angle(shoulder, elbow, wrist)
        
        # Pushup counter logic
        if angle > 160:
            self.stage = "up"
        if angle < 90 and self.stage == "up":
            self.stage = "down"
            self.counter += 1
    
    def _count_bicep_curls(self, landmarks):
        """Count bicep curl repetitions"""
        # Get coordinates
        shoulder = [landmarks[self.mp_pose.PoseLandmark.RIGHT_SHOULDER.value].x, 
                    landmarks[self.mp_pose.PoseLandmark.RIGHT_SHOULDER.value].y]
        elbow = [landmarks[self.mp_pose.PoseLandmark.RIGHT_ELBOW.value].x, 
                 landmarks[self.mp_pose.PoseLandmark.RIGHT_ELBOW.value].y]
        wrist = [landmarks[self.mp_pose.PoseLandmark.RIGHT_WRIST.value].x, 
                 landmarks[self.mp_pose.PoseLandmark.RIGHT_WRIST.value].y]
        
        # Calculate angle
        angle = self.calculate_angle(shoulder, elbow, wrist)
        
        # Curl counter logic
        if angle > 160:
            self.stage = "down"
        if angle < 30 and self.stage == "down":
            self.stage = "up"
            self.counter += 1
    
    def _count_shoulder_press(self, landmarks):
        """Count shoulder press repetitions"""
        # Get coordinates for both arms
        # Right arm
        r_shoulder = [landmarks[self.mp_pose.PoseLandmark.RIGHT_SHOULDER.value].x,
                     landmarks[self.mp_pose.PoseLandmark.RIGHT_SHOULDER.value].y]
        r_elbow = [landmarks[self.mp_pose.PoseLandmark.RIGHT_ELBOW.value].x,
                  landmarks[self.mp_pose.PoseLandmark.RIGHT_ELBOW.value].y]
        r_wrist = [landmarks[self.mp_pose.PoseLandmark.RIGHT_WRIST.value].x,
                  landmarks[self.mp_pose.PoseLandmark.RIGHT_WRIST.value].y]
        
        # Left arm
        l_shoulder = [landmarks[self.mp_pose.PoseLandmark.LEFT_SHOULDER.value].x,
                     landmarks[self.mp_pose.PoseLandmark.LEFT_SHOULDER.value].y]
        l_elbow = [landmarks[self.mp_pose.PoseLandmark.LEFT_ELBOW.value].x,
                  landmarks[self.mp_pose.PoseLandmark.LEFT_ELBOW.value].y]
        l_wrist = [landmarks[self.mp_pose.PoseLandmark.LEFT_WRIST.value].x,
                  landmarks[self.mp_pose.PoseLandmark.LEFT_WRIST.value].y]
        
        # Calculate angles for both arms
        r_angle = self.calculate_angle(r_shoulder, r_elbow, r_wrist)
        l_angle = self.calculate_angle(l_shoulder, l_elbow, l_wrist)
        
        # Use the average angle of both arms
        angle = (r_angle + l_angle) / 2
        
        # Visualize angles for debugging
        cv2.putText(self.image, f"R Angle: {int(r_angle)}", 
                    (10, 150), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 1, cv2.LINE_AA)
        cv2.putText(self.image, f"L Angle: {int(l_angle)}", 
                    (10, 180), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 1, cv2.LINE_AA)
        cv2.putText(self.image, f"Avg Angle: {int(angle)}", 
                    (10, 210), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 1, cv2.LINE_AA)
        
        # Also check vertical position of wrists relative to elbows
        wrists_above_elbows = (r_wrist[1] < r_elbow[1]) and (l_wrist[1] < l_elbow[1])
        wrists_below_elbows = (r_wrist[1] > r_elbow[1]) and (l_wrist[1] > l_elbow[1])
        
        # Display position status
        position_text = "UP" if wrists_above_elbows else "DOWN" if wrists_below_elbows else "MID"
        cv2.putText(self.image, f"Position: {position_text}", 
                    (10, 240), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 1, cv2.LINE_AA)
        
        # Shoulder press counter logic - using both angle and position
        if angle < 90 and wrists_above_elbows:  # Arms extended overhead
            if self.stage != "up":
                print("Detected UP position")
            self.stage = "up"
        elif angle > 120 and wrists_below_elbows:  # Arms lowered to starting position
            if self.stage == "up":
                self.counter += 1
                print(f"Shoulder press rep counted! Total: {self.counter}")
            self.stage = "down"
        
        # Display current stage
        cv2.putText(self.image, f"Stage: {self.stage if self.stage else 'None'}", 
                    (10, 270), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 1, cv2.LINE_AA)


def create_exercise_selection_screen():
    """Create a selection screen for exercises"""
    # Create a black image for the selection screen
    selection_screen = np.zeros((480, 640, 3), dtype=np.uint8)
    
    # Add title
    cv2.putText(selection_screen, 'AI PERSONAL TRAINER', (150, 50), 
                cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 255, 255), 2, cv2.LINE_AA)
    cv2.putText(selection_screen, 'Select an exercise to begin:', (180, 90), 
                cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 1, cv2.LINE_AA)
    
    # Create exercise buttons
    button_height = 60
    button_width = 300
    button_x = (640 - button_width) // 2
    button_y_start = 130
    button_spacing = 80
    
    # Exercise options
    exercises = ["Squat", "Push-up", "Bicep Curl", "Shoulder Press"]
    exercise_keys = ["squat", "pushup", "bicep_curl", "shoulder_press"]
    button_positions = []
    
    # Draw buttons
    for i, exercise in enumerate(exercises):
        button_y = button_y_start + i * button_spacing
        cv2.rectangle(selection_screen, (button_x, button_y), 
                     (button_x + button_width, button_y + button_height), 
                     (0, 120, 255), -1)
        cv2.rectangle(selection_screen, (button_x, button_y), 
                     (button_x + button_width, button_y + button_height), 
                     (255, 255, 255), 2)
        
        # Center text in button
        text_size = cv2.getTextSize(exercise, cv2.FONT_HERSHEY_SIMPLEX, 0.8, 2)[0]
        text_x = button_x + (button_width - text_size[0]) // 2
        text_y = button_y + (button_height + text_size[1]) // 2
        
        cv2.putText(selection_screen, exercise, (text_x, text_y), 
                    cv2.FONT_HERSHEY_SIMPLEX, 0.8, (255, 255, 255), 2, cv2.LINE_AA)
        
        # Store button position and corresponding exercise
        button_positions.append({
            'exercise': exercise_keys[i],
            'x1': button_x,
            'y1': button_y,
            'x2': button_x + button_width,
            'y2': button_y + button_height
        })
    
    # Instructions at the bottom
    cv2.putText(selection_screen, 'Click on an exercise to begin training', (150, 420), 
                cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 1, cv2.LINE_AA)
    cv2.putText(selection_screen, 'Press ESC to exit', (240, 450), 
                cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 1, cv2.LINE_AA)
    
    return selection_screen, button_positions


def create_goal_setting_screen(rep_goal=15, set_goal=3):
    """Create a screen for setting rep and set goals"""
    # Create a black image for the goal setting screen
    goal_screen = np.zeros((480, 640, 3), dtype=np.uint8)
    
    # Add title
    cv2.putText(goal_screen, 'SET YOUR WORKOUT GOALS', (150, 50), 
                cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 255, 255), 2, cv2.LINE_AA)
    
    # Rep goal section
    cv2.putText(goal_screen, 'REPETITION GOAL:', (100, 120), 
                cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 1, cv2.LINE_AA)
    
    # Rep goal buttons
    rep_options = [5, 10, 15, 20, 25]
    rep_button_positions = []
    
    for i, reps in enumerate(rep_options):
        button_x = 100 + i * 90
        button_y = 150
        button_width = 70
        button_height = 50
        
        # Highlight selected rep goal
        if reps == rep_goal:
            button_color = (0, 255, 0)  # Green for selected
        else:
            button_color = (0, 120, 255)  # Orange for unselected
        
        cv2.rectangle(goal_screen, (button_x, button_y), 
                     (button_x + button_width, button_y + button_height), 
                     button_color, -1)
        cv2.rectangle(goal_screen, (button_x, button_y), 
                     (button_x + button_width, button_y + button_height), 
                     (255, 255, 255), 2)
        
        # Center text in button
        text_size = cv2.getTextSize(str(reps), cv2.FONT_HERSHEY_SIMPLEX, 0.8, 2)[0]
        text_x = button_x + (button_width - text_size[0]) // 2
        text_y = button_y + (button_height + text_size[1]) // 2
        
        cv2.putText(goal_screen, str(reps), (text_x, text_y), 
                    cv2.FONT_HERSHEY_SIMPLEX, 0.8, (255, 255, 255), 2, cv2.LINE_AA)
        
        # Store button position and corresponding rep value
        rep_button_positions.append({
            'value': reps,
            'x1': button_x,
            'y1': button_y,
            'x2': button_x + button_width,
            'y2': button_y + button_height
        })
    
    # Set goal section
    cv2.putText(goal_screen, 'SET GOAL:', (100, 250), 
                cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 1, cv2.LINE_AA)
    
    # Set goal buttons
    set_options = [1, 2, 3, 4, 5]
    set_button_positions = []
    
    for i, sets in enumerate(set_options):
        button_x = 100 + i * 90
        button_y = 280
        button_width = 70
        button_height = 50
        
        # Highlight selected set goal
        if sets == set_goal:
            button_color = (0, 255, 0)  # Green for selected
        else:
            button_color = (0, 120, 255)  # Orange for unselected
        
        cv2.rectangle(goal_screen, (button_x, button_y), 
                     (button_x + button_width, button_y + button_height), 
                     button_color, -1)
        cv2.rectangle(goal_screen, (button_x, button_y), 
                     (button_x + button_width, button_y + button_height), 
                     (255, 255, 255), 2)
        
        # Center text in button
        text_size = cv2.getTextSize(str(sets), cv2.FONT_HERSHEY_SIMPLEX, 0.8, 2)[0]
        text_x = button_x + (button_width - text_size[0]) // 2
        text_y = button_y + (button_height + text_size[1]) // 2
        
        cv2.putText(goal_screen, str(sets), (text_x, text_y), 
                    cv2.FONT_HERSHEY_SIMPLEX, 0.8, (255, 255, 255), 2, cv2.LINE_AA)
        
        # Store button position and corresponding set value
        set_button_positions.append({
            'value': sets,
            'x1': button_x,
            'y1': button_y,
            'x2': button_x + button_width,
            'y2': button_y + button_height
        })
    
    # Continue button
    continue_button_x = 270
    continue_button_y = 350
    continue_button_width = 100
    continue_button_height = 50
    
    cv2.rectangle(goal_screen, (continue_button_x, continue_button_y), 
                 (continue_button_x + continue_button_width, continue_button_y + continue_button_height), 
                 (0, 255, 0), -1)
    cv2.rectangle(goal_screen, (continue_button_x, continue_button_y), 
                 (continue_button_x + continue_button_width, continue_button_y + continue_button_height), 
                 (255, 255, 255), 2)
    
    # Center text in button
    text_size = cv2.getTextSize("CONTINUE", cv2.FONT_HERSHEY_SIMPLEX, 0.6, 2)[0]
    text_x = continue_button_x + (continue_button_width - text_size[0]) // 2
    text_y = continue_button_y + (continue_button_height + text_size[1]) // 2
    
    cv2.putText(goal_screen, "CONTINUE", (text_x, text_y), 
                cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 2, cv2.LINE_AA)
    
    continue_button = {
        'x1': continue_button_x,
        'y1': continue_button_y,
        'x2': continue_button_x + continue_button_width,
        'y2': continue_button_y + continue_button_height
    }
    
    # Summary of selected goals
    cv2.putText(goal_screen, f"You will do {rep_goal} reps for {set_goal} sets", (150, 430), 
                cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 1, cv2.LINE_AA)
    
    return goal_screen, rep_button_positions, set_button_positions, continue_button


def create_bmi_screen(weight_kg=70, height_cm=170, bmi=0.0, bmi_category="", show_result=False):
    """Create a screen for calculating BMI"""
    # Create a black image for the BMI screen
    bmi_screen = np.zeros((480, 640, 3), dtype=np.uint8)
    
    # Add title
    cv2.putText(bmi_screen, 'CALCULATE YOUR BMI', (150, 50), 
                cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 255, 255), 2, cv2.LINE_AA)
    
    # Weight input section
    cv2.putText(bmi_screen, 'WEIGHT (kg):', (100, 120), 
                cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 1, cv2.LINE_AA)
    cv2.putText(bmi_screen, str(weight_kg), (250, 120), 
                cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 1, cv2.LINE_AA)
    
    # Weight adjustment buttons
    weight_inc_button = {'x1': 300, 'y1': 110, 'x2': 330, 'y2': 130, 'text': '+', 'value': 1}
    weight_dec_button = {'x1': 200, 'y1': 110, 'x2': 230, 'y2': 130, 'text': '-', 'value': -1}
    
    cv2.rectangle(bmi_screen, (weight_inc_button['x1'], weight_inc_button['y1']), 
                 (weight_inc_button['x2'], weight_inc_button['y2']), (0, 120, 255), -1)
    cv2.putText(bmi_screen, weight_inc_button['text'], (weight_inc_button['x1'] + 10, weight_inc_button['y1'] + 15), 
                cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 1, cv2.LINE_AA)
    
    cv2.rectangle(bmi_screen, (weight_dec_button['x1'], weight_dec_button['y1']), 
                 (weight_dec_button['x2'], weight_dec_button['y2']), (0, 120, 255), -1)
    cv2.putText(bmi_screen, weight_dec_button['text'], (weight_dec_button['x1'] + 10, weight_dec_button['y1'] + 15), 
                cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 1, cv2.LINE_AA)
    
    # Height input section
    cv2.putText(bmi_screen, 'HEIGHT (cm):', (100, 170), 
                cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 1, cv2.LINE_AA)
    cv2.putText(bmi_screen, str(height_cm), (250, 170), 
                cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 1, cv2.LINE_AA)
    
    # Height adjustment buttons
    height_inc_button = {'x1': 300, 'y1': 160, 'x2': 330, 'y2': 180, 'text': '+', 'value': 1}
    height_dec_button = {'x1': 200, 'y1': 160, 'x2': 230, 'y2': 180, 'text': '-', 'value': -1}
    
    cv2.rectangle(bmi_screen, (height_inc_button['x1'], height_inc_button['y1']), 
                 (height_inc_button['x2'], height_inc_button['y2']), (0, 120, 255), -1)
    cv2.putText(bmi_screen, height_inc_button['text'], (height_inc_button['x1'] + 10, height_inc_button['y1'] + 15), 
                cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 1, cv2.LINE_AA)
    
    cv2.rectangle(bmi_screen, (height_dec_button['x1'], height_dec_button['y1']), 
                 (height_dec_button['x2'], height_dec_button['y2']), (0, 120, 255), -1)
    cv2.putText(bmi_screen, height_dec_button['text'], (height_dec_button['x1'] + 10, height_dec_button['y1'] + 15), 
                cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 1, cv2.LINE_AA)
    
    # Calculate BMI button
    calculate_button_x = 150
    calculate_button_y = 220
    calculate_button_width = 150
    calculate_button_height = 50
    
    cv2.rectangle(bmi_screen, (calculate_button_x, calculate_button_y), 
                 (calculate_button_x + calculate_button_width, calculate_button_y + calculate_button_height), 
                 (0, 255, 0), -1)
    cv2.rectangle(bmi_screen, (calculate_button_x, calculate_button_y), 
                 (calculate_button_x + calculate_button_width, calculate_button_y + calculate_button_height), 
                 (255, 255, 255), 2)
    
    # Center text in button
    text_size = cv2.getTextSize("CALCULATE BMI", cv2.FONT_HERSHEY_SIMPLEX, 0.6, 2)[0]
    text_x = calculate_button_x + (calculate_button_width - text_size[0]) // 2
    text_y = calculate_button_y + (calculate_button_height + text_size[1]) // 2
    
    cv2.putText(bmi_screen, "CALCULATE BMI", (text_x, text_y), 
                cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 2, cv2.LINE_AA)
    
    calculate_button = {
        'x1': calculate_button_x,
        'y1': calculate_button_y,
        'x2': calculate_button_x + calculate_button_width,
        'y2': calculate_button_y + calculate_button_height
    }
    
    # Continue button (to proceed to next screen)
    continue_button_x = 340
    continue_button_y = 220
    continue_button_width = 150
    continue_button_height = 50
    
    cv2.rectangle(bmi_screen, (continue_button_x, continue_button_y), 
                 (continue_button_x + continue_button_width, continue_button_y + continue_button_height), 
                 (0, 120, 255), -1)
    cv2.rectangle(bmi_screen, (continue_button_x, continue_button_y), 
                 (continue_button_x + continue_button_width, continue_button_y + continue_button_height), 
                 (255, 255, 255), 2)
    
    # Center text in button
    text_size = cv2.getTextSize("CONTINUE", cv2.FONT_HERSHEY_SIMPLEX, 0.6, 2)[0]
    text_x = continue_button_x + (continue_button_width - text_size[0]) // 2
    text_y = continue_button_y + (continue_button_height + text_size[1]) // 2
    
    cv2.putText(bmi_screen, "CONTINUE", (text_x, text_y), 
                cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 2, cv2.LINE_AA)
    
    continue_button = {
        'x1': continue_button_x,
        'y1': continue_button_y,
        'x2': continue_button_x + continue_button_width,
        'y2': continue_button_y + continue_button_height
    }
    
    # Display BMI result if available
    if show_result and bmi > 0:
        # Display BMI value
        cv2.putText(bmi_screen, f"Your BMI: {bmi}", (220, 300), 
                    cv2.FONT_HERSHEY_SIMPLEX, 0.9, (255, 255, 255), 2, cv2.LINE_AA)
        
        # Display BMI category with color coding
        if bmi_category == "Underweight":
            category_color = (255, 255, 0)  # Yellow
        elif bmi_category == "Normal weight":
            category_color = (0, 255, 0)  # Green
        elif bmi_category == "Overweight":
            category_color = (0, 165, 255)  # Orange
        else:  # Obese
            category_color = (0, 0, 255)  # Red
        
        cv2.putText(bmi_screen, f"Category: {bmi_category}", (190, 340), 
                    cv2.FONT_HERSHEY_SIMPLEX, 0.9, category_color, 2, cv2.LINE_AA)
        
        # Display BMI interpretation
        if bmi_category == "Underweight":
            cv2.putText(bmi_screen, "You may need to gain some weight", (150, 380), 
                        cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 1, cv2.LINE_AA)
        elif bmi_category == "Normal weight":
            cv2.putText(bmi_screen, "You have a healthy weight", (180, 380), 
                        cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 1, cv2.LINE_AA)
        elif bmi_category == "Overweight":
            cv2.putText(bmi_screen, "You may need to lose some weight", (150, 380), 
                        cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 1, cv2.LINE_AA)
        else:  # Obese
            cv2.putText(bmi_screen, "You should consider weight loss for health", (120, 380), 
                        cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 1, cv2.LINE_AA)
    
    # BMI scale at the bottom
    scale_width = 400
    scale_height = 20
    scale_x = (640 - scale_width) // 2
    scale_y = 420
    
    # Draw BMI scale
    cv2.rectangle(bmi_screen, (scale_x, scale_y), (scale_x + scale_width, scale_y + scale_height), (255, 255, 255), 1)
    
    # Draw scale segments with colors
    segment_width = scale_width // 4
    # Underweight (blue)
    cv2.rectangle(bmi_screen, (scale_x, scale_y), (scale_x + segment_width, scale_y + scale_height), (255, 255, 0), -1)
    # Normal weight (green)
    cv2.rectangle(bmi_screen, (scale_x + segment_width, scale_y), (scale_x + segment_width * 2, scale_y + scale_height), (0, 255, 0), -1)
    # Overweight (orange)
    cv2.rectangle(bmi_screen, (scale_x + segment_width * 2, scale_y), (scale_x + segment_width * 3, scale_y + scale_height), (0, 165, 255), -1)
    # Obese (red)
    cv2.rectangle(bmi_screen, (scale_x + segment_width * 3, scale_y), (scale_x + segment_width * 4, scale_y + scale_height), (0, 0, 255), -1)
    
    # Add labels
    cv2.putText(bmi_screen, "18.5", (scale_x + segment_width - 20, scale_y + scale_height + 20), 
                cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 1, cv2.LINE_AA)
    cv2.putText(bmi_screen, "25", (scale_x + segment_width * 2 - 10, scale_y + scale_height + 20), 
                cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 1, cv2.LINE_AA)
    cv2.putText(bmi_screen, "30", (scale_x + segment_width * 3 - 10, scale_y + scale_height + 20), 
                cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 1, cv2.LINE_AA)
    
    # Mark user's BMI on the scale if calculated
    if show_result and bmi > 0:
        # Calculate position on scale
        position = 0
        if bmi < 18.5:
            position = scale_x + (bmi / 18.5) * segment_width
        elif bmi < 25:
            position = scale_x + segment_width + ((bmi - 18.5) / 6.5) * segment_width
        elif bmi < 30:
            position = scale_x + segment_width * 2 + ((bmi - 25) / 5) * segment_width
        else:
            position = min(scale_x + segment_width * 3 + ((bmi - 30) / 10) * segment_width, scale_x + scale_width - 5)
        
        # Draw marker
        cv2.circle(bmi_screen, (int(position), scale_y + scale_height // 2), 5, (255, 255, 255), -1)
    
    return bmi_screen, calculate_button, continue_button, weight_inc_button, weight_dec_button, height_inc_button, height_dec_button


def create_fitness_goal_screen(bmi=0.0, bmi_category="", selected_goal=""):
    """Create a screen for selecting fitness goals"""
    # Create a black image for the fitness goal screen
    fitness_goal_screen = np.zeros((480, 640, 3), dtype=np.uint8)
    
    # Add title
    cv2.putText(fitness_goal_screen, 'SELECT YOUR FITNESS GOAL', (150, 50), 
                cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 255, 255), 2, cv2.LINE_AA)
    
    # Display BMI information
    if bmi > 0:
        cv2.putText(fitness_goal_screen, f"Your BMI: {bmi} ({bmi_category})", (200, 90), 
                    cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 1, cv2.LINE_AA)
    
    # Goal options
    goal_options = ["Maintain weight", "Gain weight", "Lose weight"]
    goal_keys = ["maintain", "gain", "lose"]
    button_positions = []
    
    # Recommended goal based on BMI
    recommended_goal = ""
    if bmi_category == "Underweight":
        recommended_goal = "gain"
    elif bmi_category == "Overweight" or bmi_category == "Obese":
        recommended_goal = "lose"
    elif bmi_category == "Normal weight":
        recommended_goal = "maintain"
    
    # Draw buttons
    for i, goal in enumerate(goal_options):
        button_x = 150
        button_y = 120 + i * 80
        button_width = 300
        button_height = 50
        
        # Determine button color based on selection and recommendation
        if goal_keys[i] == selected_goal:
            button_color = (0, 0, 255)  # Red for selected
            status_text = "SELECTED"
        elif goal_keys[i] == recommended_goal:
            button_color = (0, 255, 0)  # Green for recommended
            status_text = "(Recommended)"
        else:
            button_color = (0, 120, 255)  # Orange for other options
            status_text = ""
        
        cv2.rectangle(fitness_goal_screen, (button_x, button_y), 
                     (button_x + button_width, button_y + button_height), 
                     button_color, -1)
        cv2.rectangle(fitness_goal_screen, (button_x, button_y), 
                     (button_x + button_width, button_y + button_height), 
                     (255, 255, 255), 2)
        
        # Center text in button
        text_size = cv2.getTextSize(goal, cv2.FONT_HERSHEY_SIMPLEX, 0.7, 2)[0]
        text_x = button_x + (button_width - text_size[0]) // 2
        text_y = button_y + (button_height + text_size[1]) // 2
        
        cv2.putText(fitness_goal_screen, goal, (text_x, text_y), 
                    cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2, cv2.LINE_AA)
        
        # Add status text (Selected or Recommended)
        if status_text:
            cv2.putText(fitness_goal_screen, status_text, (button_x + button_width + 10, button_y + 30), 
                        cv2.FONT_HERSHEY_SIMPLEX, 0.6, button_color, 1, cv2.LINE_AA)
        
        # Store button position and corresponding goal
        button_positions.append({
            'goal': goal_keys[i],
            'x1': button_x,
            'y1': button_y,
            'x2': button_x + button_width,
            'y2': button_y + button_height
        })
    
    # Continue button
    continue_button_x = 220
    continue_button_y = 370
    continue_button_width = 200
    continue_button_height = 50
    
    cv2.rectangle(fitness_goal_screen, (continue_button_x, continue_button_y), 
                 (continue_button_x + continue_button_width, continue_button_y + continue_button_height), 
                 (0, 255, 0), -1)
    cv2.rectangle(fitness_goal_screen, (continue_button_x, continue_button_y), 
                 (continue_button_x + continue_button_width, continue_button_y + continue_button_height), 
                 (255, 255, 255), 2)
    
    # Center text in button
    text_size = cv2.getTextSize("CONTINUE", cv2.FONT_HERSHEY_SIMPLEX, 0.7, 2)[0]
    text_x = continue_button_x + (continue_button_width - text_size[0]) // 2
    text_y = continue_button_y + (continue_button_height + text_size[1]) // 2
    
    cv2.putText(fitness_goal_screen, "CONTINUE", (text_x, text_y), 
                cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2, cv2.LINE_AA)
    
    continue_button = {
        'x1': continue_button_x,
        'y1': continue_button_y,
        'x2': continue_button_x + continue_button_width,
        'y2': continue_button_y + continue_button_height
    }
    
    return fitness_goal_screen, button_positions, continue_button


def create_rest_screen(current_set, set_goal, exercise_type, seconds_left=0):
    """Create a rest screen to display between sets"""
    # Create a black image for the rest screen
    rest_screen = np.zeros((480, 640, 3), dtype=np.uint8)
    
    # Add title
    cv2.putText(rest_screen, 'REST TIME', (250, 70), 
                cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 255, 255), 2, cv2.LINE_AA)
    
    # Exercise info
    cv2.putText(rest_screen, f"Exercise: {exercise_type.replace('_', ' ').title()}", (200, 120), 
                cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 1, cv2.LINE_AA)
    
    # Set info
    cv2.putText(rest_screen, f"Completed Set {current_set-1} of {set_goal}", (200, 160), 
                cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 1, cv2.LINE_AA)
    
    # Rest timer
    if seconds_left > 0:
        cv2.putText(rest_screen, f"Rest Time Remaining: {seconds_left} seconds", (170, 200), 
                    cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 1, cv2.LINE_AA)
    
    # Create start next set button
    button_x = 220
    button_y = 250
    button_width = 200
    button_height = 60
    
    cv2.rectangle(rest_screen, (button_x, button_y), 
                 (button_x + button_width, button_y + button_height), 
                 (0, 255, 0), -1)
    cv2.rectangle(rest_screen, (button_x, button_y), 
                 (button_x + button_width, button_y + button_height), 
                 (255, 255, 255), 2)
    
    # Center text in button
    text_size = cv2.getTextSize("START NEXT SET", cv2.FONT_HERSHEY_SIMPLEX, 0.7, 2)[0]
    text_x = button_x + (button_width - text_size[0]) // 2
    text_y = button_y + (button_height + text_size[1]) // 2
    
    cv2.putText(rest_screen, "START NEXT SET", (text_x, text_y), 
                cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 0, 0), 2, cv2.LINE_AA)
    
    # Rest tips
    cv2.putText(rest_screen, "Tips during rest:", (150, 350), 
                cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 1, cv2.LINE_AA)
    cv2.putText(rest_screen, "- Take deep breaths", (170, 380), 
                cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 1, cv2.LINE_AA)
    cv2.putText(rest_screen, "- Stay hydrated", (170, 410), 
                cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 1, cv2.LINE_AA)
    cv2.putText(rest_screen, "- Stretch lightly if needed", (170, 440), 
                cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 1, cv2.LINE_AA)
    
    # Return the rest screen and the button position
    start_button = {
        'x1': button_x,
        'y1': button_y,
        'x2': button_x + button_width,
        'y2': button_y + button_height
    }
    
    return rest_screen, start_button


def create_weekly_plan_screen(trainer):
    """Create a screen showing the weekly workout plan and progress"""
    # Create a black image for the weekly plan screen
    weekly_plan_screen = np.zeros((480, 640, 3), dtype=np.uint8)
    
    # Add title
    cv2.putText(weekly_plan_screen, 'WEEKLY WORKOUT PLAN', (150, 50), 
                cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 255, 255), 2, cv2.LINE_AA)
    
    # Show weekly progress
    completed_days, total_days = trainer.get_weekly_progress()
    progress_percentage = int((completed_days / total_days) * 100) if total_days > 0 else 0
    
    cv2.putText(weekly_plan_screen, f"Weekly Progress: {completed_days}/{total_days} days ({progress_percentage}%)", 
                (150, 90), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 1, cv2.LINE_AA)
    
    # Display days of the week with their workout types and completion status
    day_buttons = []
    day_y_start = 120
    day_height = 40
    day_spacing = 10
    
    for day_idx, day_name in enumerate(trainer.days_of_week):
        day_plan = trainer.workout_plan[day_idx]
        day_type = day_plan["type"]
        is_completed = day_plan["completed"]
        is_current = day_idx == trainer.current_day
        
        # Determine button color based on status
        if is_completed:
            button_color = (0, 255, 0)  # Green for completed
        elif is_current:
            button_color = (0, 120, 255)  # Orange for current day
        else:
            button_color = (100, 100, 100)  # Gray for other days
        
        # Draw day button
        day_y = day_y_start + day_idx * (day_height + day_spacing)
        button_x = 100
        button_width = 440
        
        cv2.rectangle(weekly_plan_screen, (button_x, day_y), 
                     (button_x + button_width, day_y + day_height), 
                     button_color, -1)
        cv2.rectangle(weekly_plan_screen, (button_x, day_y), 
                     (button_x + button_width, day_y + day_height), 
                     (255, 255, 255), 2)
        
        # Add day text
        cv2.putText(weekly_plan_screen, f"{day_name}: {day_type}", 
                    (button_x + 20, day_y + day_height//2 + 5), 
                    cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 1, cv2.LINE_AA)
        
        # Add completion status
        status_text = "COMPLETED" if is_completed else "CURRENT DAY" if is_current else ""
        if status_text:
            cv2.putText(weekly_plan_screen, status_text, 
                        (button_x + button_width - 120, day_y + day_height//2 + 5), 
                        cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 1, cv2.LINE_AA)
        
        # Store button position
        day_buttons.append({
            'day_idx': day_idx,
            'x1': button_x,
            'y1': day_y,
            'x2': button_x + button_width,
            'y2': day_y + day_height
        })
    
    # Continue button
    continue_button_x = 270
    continue_button_y = 420
    continue_button_width = 100
    continue_button_height = 40
    
    cv2.rectangle(weekly_plan_screen, (continue_button_x, continue_button_y), 
                 (continue_button_x + continue_button_width, continue_button_y + continue_button_height), 
                 (0, 255, 0), -1)
    cv2.rectangle(weekly_plan_screen, (continue_button_x, continue_button_y), 
                 (continue_button_x + continue_button_width, continue_button_y + continue_button_height), 
                 (255, 255, 255), 2)
    
    # Center text in button
    text_size = cv2.getTextSize("CONTINUE", cv2.FONT_HERSHEY_SIMPLEX, 0.6, 2)[0]
    text_x = continue_button_x + (continue_button_width - text_size[0]) // 2
    text_y = continue_button_y + (continue_button_height + text_size[1]) // 2
    
    cv2.putText(weekly_plan_screen, "CONTINUE", (text_x, text_y), 
                cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 2, cv2.LINE_AA)
    
    continue_button = {
        'x1': continue_button_x,
        'y1': continue_button_y,
        'x2': continue_button_x + continue_button_width,
        'y2': continue_button_y + continue_button_height
    }
    
    return weekly_plan_screen, day_buttons, continue_button


def create_daily_exercises_screen(trainer):
    """Create a screen showing the exercises for the current day"""
    # Create a black image for the daily exercises screen
    daily_exercises_screen = np.zeros((480, 640, 3), dtype=np.uint8)
    
    # Get current day plan
    day_plan = trainer.get_current_day_plan()
    day_name = trainer.days_of_week[trainer.current_day]
    day_type = day_plan["type"]
    
    # Add title
    cv2.putText(daily_exercises_screen, f'{day_name.upper()} - {day_type.upper()} DAY', (150, 50), 
                cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 255, 255), 2, cv2.LINE_AA)
    
    # If it's a rest day
    if day_type == "Rest":
        cv2.putText(daily_exercises_screen, "REST DAY - No exercises scheduled", (150, 150), 
                    cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 255, 0), 2, cv2.LINE_AA)
        
        cv2.putText(daily_exercises_screen, "Take time to recover and stretch!", (150, 200), 
                    cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 1, cv2.LINE_AA)
        
        exercise_buttons = []
    else:
        # Show exercises for the day
        exercises = day_plan["exercises"]
        
        # Display instructions
        cv2.putText(daily_exercises_screen, "Click on an exercise to begin or mark as completed:", (100, 90), 
                    cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 1, cv2.LINE_AA)
        
        # Exercise buttons
        exercise_buttons = []
        exercise_y_start = 120
        exercise_height = 60
        exercise_spacing = 20
        
        for i, exercise in enumerate(exercises):
            is_completed = trainer.is_exercise_completed(exercise)
            
            # Determine button color based on completion status
            if is_completed:
                button_color = (0, 255, 0)  # Green for completed
            else:
                button_color = (0, 120, 255)  # Orange for not completed
            
            # Draw exercise button
            exercise_y = exercise_y_start + i * (exercise_height + exercise_spacing)
            button_x = 100
            button_width = 440
            
            cv2.rectangle(daily_exercises_screen, (button_x, exercise_y), 
                         (button_x + button_width, exercise_y + exercise_height), 
                         button_color, -1)
            cv2.rectangle(daily_exercises_screen, (button_x, exercise_y), 
                         (button_x + button_width, exercise_y + exercise_height), 
                         (255, 255, 255), 2)
            
            # Format exercise name for display
            exercise_display_name = exercise.replace('_', ' ').title()
            
            # Add exercise text
            cv2.putText(daily_exercises_screen, exercise_display_name, 
                        (button_x + 20, exercise_y + 25), 
                        cv2.FONT_HERSHEY_SIMPLEX, 0.8, (255, 255, 255), 2, cv2.LINE_AA)
            
            # Add completion status
            status_text = "COMPLETED" if is_completed else "START"
            status_color = (0, 255, 0) if is_completed else (255, 255, 255)
            
            cv2.putText(daily_exercises_screen, status_text, 
                        (button_x + button_width - 120, exercise_y + 35), 
                        cv2.FONT_HERSHEY_SIMPLEX, 0.7, status_color, 1, cv2.LINE_AA)
            
            # Store button position
            exercise_buttons.append({
                'exercise': exercise,
                'x1': button_x,
                'y1': exercise_y,
                'x2': button_x + button_width,
                'y2': exercise_y + exercise_height
            })
    
    # Back button to weekly plan
    daily_back_button_x = 150
    daily_back_button_y = 420
    daily_back_button_width = 150
    daily_back_button_height = 40
    
    cv2.rectangle(daily_exercises_screen, (daily_back_button_x, daily_back_button_y), 
                 (daily_back_button_x + daily_back_button_width, daily_back_button_y + daily_back_button_height), 
                 (100, 100, 100), -1)
    cv2.rectangle(daily_exercises_screen, (daily_back_button_x, daily_back_button_y), 
                 (daily_back_button_x + daily_back_button_width, daily_back_button_y + daily_back_button_height), 
                 (255, 255, 255), 2)
    
    # Center text in button
    text_size = cv2.getTextSize("BACK TO PLAN", cv2.FONT_HERSHEY_SIMPLEX, 0.6, 2)[0]
    text_x = daily_back_button_x + (daily_back_button_width - text_size[0]) // 2
    text_y = daily_back_button_y + (daily_back_button_height + text_size[1]) // 2
    
    cv2.putText(daily_exercises_screen, "BACK TO PLAN", (text_x, text_y), 
                cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 2, cv2.LINE_AA)
    
    daily_back_button = {
        'x1': daily_back_button_x,
        'y1': daily_back_button_y,
        'x2': daily_back_button_x + daily_back_button_width,
        'y2': daily_back_button_y + daily_back_button_height
    }
    
    return daily_exercises_screen, exercise_buttons, daily_back_button


def main():
    # Initialize the AI Trainer
    trainer = AITrainer()
    
    # Initialize webcam
    cap = cv2.VideoCapture(0)
    
    # Create screens
    selection_screen, exercise_buttons = create_exercise_selection_screen()
    goal_screen, rep_buttons, set_buttons, continue_button = create_goal_setting_screen()
    bmi_screen, calculate_button, continue_button_bmi, weight_inc_button, weight_dec_button, height_inc_button, height_dec_button = create_bmi_screen()
    fitness_goal_screen, fitness_goal_buttons, fitness_goal_continue_button = create_fitness_goal_screen(trainer.bmi, trainer.bmi_category)
    weekly_plan_screen, day_buttons, weekly_plan_continue_button = create_weekly_plan_screen(trainer)
    daily_exercises_screen, exercise_buttons_daily, daily_back_button = create_daily_exercises_screen(trainer)
    
    # Screen states
    bmi_setting_mode = True
    fitness_goal_mode = False
    goal_setting_mode = False
    selection_mode = False
    training_mode = False
    rest_mode = False
    weekly_plan_mode = False
    daily_exercises_mode = False
    
    # Current selected goals
    current_rep_goal = 15
    current_set_goal = 3
    
    # Print instructions
    print("AI Personal Trainer Started!")
    print("Set your BMI and workout goals and select an exercise to begin.")
    
    while cap.isOpened():
        ret, frame = cap.read()
        
        if not ret:
            print("Failed to grab frame")
            break
        
        if bmi_setting_mode:
            # Display BMI setting screen with current state
            show_bmi_result = trainer.bmi > 0
            bmi_screen, calculate_button, continue_button_bmi, weight_inc_button, weight_dec_button, height_inc_button, height_dec_button = create_bmi_screen(
                weight_kg=trainer.weight_kg, 
                height_cm=trainer.height_cm, 
                bmi=trainer.bmi, 
                bmi_category=trainer.bmi_category, 
                show_result=show_bmi_result)
            
            cv2.imshow('AI Personal Trainer', bmi_screen)
            
            # Handle mouse clicks for BMI setting
            def bmi_mouse_callback(event, x, y, flags, param):
                nonlocal bmi_setting_mode, fitness_goal_mode
                nonlocal calculate_button, continue_button_bmi, weight_inc_button, weight_dec_button, height_inc_button, height_dec_button, bmi_screen
                
                if event == cv2.EVENT_LBUTTONDOWN:
                    # Check calculate button
                    if (calculate_button['x1'] <= x <= calculate_button['x2'] and 
                        calculate_button['y1'] <= y <= calculate_button['y2']):
                        # Calculate BMI
                        bmi, bmi_category = trainer.calculate_bmi()
                        print(f"BMI: {bmi} ({bmi_category})")
                        # Update screen with results
                        bmi_screen, calculate_button, continue_button_bmi, weight_inc_button, weight_dec_button, height_inc_button, height_dec_button = create_bmi_screen(
                            weight_kg=trainer.weight_kg, 
                            height_cm=trainer.height_cm, 
                            bmi=bmi, 
                            bmi_category=bmi_category, 
                            show_result=True)
                        cv2.imshow('AI Personal Trainer', bmi_screen)
                    
                    # Check weight adjustment buttons
                    if (weight_inc_button['x1'] <= x <= weight_inc_button['x2'] and 
                        weight_inc_button['y1'] <= y <= weight_inc_button['y2']):
                        trainer.weight_kg += weight_inc_button['value']
                        bmi_screen, calculate_button, continue_button_bmi, weight_inc_button, weight_dec_button, height_inc_button, height_dec_button = create_bmi_screen(
                            weight_kg=trainer.weight_kg, 
                            height_cm=trainer.height_cm, 
                            bmi=trainer.bmi, 
                            bmi_category=trainer.bmi_category, 
                            show_result=show_bmi_result)
                        cv2.imshow('AI Personal Trainer', bmi_screen)
                    elif (weight_dec_button['x1'] <= x <= weight_dec_button['x2'] and 
                          weight_dec_button['y1'] <= y <= weight_dec_button['y2']):
                        trainer.weight_kg = max(1, trainer.weight_kg + weight_dec_button['value'])
                        bmi_screen, calculate_button, continue_button_bmi, weight_inc_button, weight_dec_button, height_inc_button, height_dec_button = create_bmi_screen(
                            weight_kg=trainer.weight_kg, 
                            height_cm=trainer.height_cm, 
                            bmi=trainer.bmi, 
                            bmi_category=trainer.bmi_category, 
                            show_result=show_bmi_result)
                        cv2.imshow('AI Personal Trainer', bmi_screen)
                    
                    # Check height adjustment buttons
                    if (height_inc_button['x1'] <= x <= height_inc_button['x2'] and 
                        height_inc_button['y1'] <= y <= height_inc_button['y2']):
                        trainer.height_cm += height_inc_button['value']
                        bmi_screen, calculate_button, continue_button_bmi, weight_inc_button, weight_dec_button, height_inc_button, height_dec_button = create_bmi_screen(
                            weight_kg=trainer.weight_kg, 
                            height_cm=trainer.height_cm, 
                            bmi=trainer.bmi, 
                            bmi_category=trainer.bmi_category, 
                            show_result=show_bmi_result)
                        cv2.imshow('AI Personal Trainer', bmi_screen)
                    elif (height_dec_button['x1'] <= x <= height_dec_button['x2'] and 
                          height_dec_button['y1'] <= y <= height_dec_button['y2']):
                        trainer.height_cm = max(1, trainer.height_cm + height_dec_button['value'])
                        bmi_screen, calculate_button, continue_button_bmi, weight_inc_button, weight_dec_button, height_inc_button, height_dec_button = create_bmi_screen(
                            weight_kg=trainer.weight_kg, 
                            height_cm=trainer.height_cm, 
                            bmi=trainer.bmi, 
                            bmi_category=trainer.bmi_category, 
                            show_result=show_bmi_result)
                        cv2.imshow('AI Personal Trainer', bmi_screen)
                    
                    # Check continue button
                    if (continue_button_bmi['x1'] <= x <= continue_button_bmi['x2'] and 
                        continue_button_bmi['y1'] <= y <= continue_button_bmi['y2']):
                        bmi_setting_mode = False
                        fitness_goal_mode = True
            
            # Set the mouse callback
            cv2.setMouseCallback('AI Personal Trainer', bmi_mouse_callback)
            
            # Check for key press to exit
            key = cv2.waitKey(10) & 0xFF
            if key == 27:  # ESC key
                break
                
        elif fitness_goal_mode:
            # Display fitness goal screen with current BMI information
            fitness_goal_screen, fitness_goal_buttons, fitness_goal_continue_button = create_fitness_goal_screen(
                bmi=trainer.bmi, bmi_category=trainer.bmi_category, selected_goal=trainer.fitness_goal)
            
            cv2.imshow('AI Personal Trainer', fitness_goal_screen)
            
            # Handle mouse clicks for fitness goal selection
            def fitness_goal_mouse_callback(event, x, y, flags, param):
                nonlocal fitness_goal_mode, goal_setting_mode
                nonlocal fitness_goal_buttons, fitness_goal_continue_button
                
                if event == cv2.EVENT_LBUTTONDOWN:
                    # Check goal buttons
                    for button in fitness_goal_buttons:
                        if (button['x1'] <= x <= button['x2'] and 
                            button['y1'] <= y <= button['y2']):
                            trainer.fitness_goal = button['goal']
                            print(f"Fitness goal set to: {trainer.fitness_goal}")
                            # Recreate screen to show selection
                            fitness_goal_screen, fitness_goal_buttons, fitness_goal_continue_button = create_fitness_goal_screen(
                                bmi=trainer.bmi, bmi_category=trainer.bmi_category, selected_goal=trainer.fitness_goal)
                            cv2.imshow('AI Personal Trainer', fitness_goal_screen)
                    
                    # Check continue button
                    if (fitness_goal_continue_button['x1'] <= x <= fitness_goal_continue_button['x2'] and 
                        fitness_goal_continue_button['y1'] <= y <= fitness_goal_continue_button['y2']):
                        fitness_goal_mode = False
                        goal_setting_mode = True
            
            # Set the mouse callback
            cv2.setMouseCallback('AI Personal Trainer', fitness_goal_mouse_callback)
            
            # Check for key press to exit
            key = cv2.waitKey(10) & 0xFF
            if key == 27:  # ESC key
                break
                
        elif goal_setting_mode:
            # Display goal setting screen
            goal_screen, rep_buttons, set_buttons, continue_button = create_goal_setting_screen(
                rep_goal=current_rep_goal, set_goal=current_set_goal)
            
            cv2.imshow('AI Personal Trainer', goal_screen)
            
            # Handle mouse clicks for goal setting
            def goal_mouse_callback(event, x, y, flags, param):
                nonlocal current_rep_goal, current_set_goal, goal_setting_mode, weekly_plan_mode
                
                if event == cv2.EVENT_LBUTTONDOWN:
                    # Check rep buttons
                    for button in rep_buttons:
                        if (button['x1'] <= x <= button['x2'] and 
                            button['y1'] <= y <= button['y2']):
                            current_rep_goal = button['value']
                            print(f"Rep goal set to: {current_rep_goal}")
                    
                    # Check set buttons
                    for button in set_buttons:
                        if (button['x1'] <= x <= button['x2'] and 
                            button['y1'] <= y <= button['y2']):
                            current_set_goal = button['value']
                            print(f"Set goal set to: {current_set_goal}")
                    
                    # Check continue button
                    if (continue_button['x1'] <= x <= continue_button['x2'] and 
                        continue_button['y1'] <= y <= continue_button['y2']):
                        trainer.set_goals(current_rep_goal, current_set_goal)
                        goal_setting_mode = False
                        weekly_plan_mode = True
            
            # Set the mouse callback
            cv2.setMouseCallback('AI Personal Trainer', goal_mouse_callback)
            
            # Check for key press to exit
            key = cv2.waitKey(10) & 0xFF
            if key == 27:  # ESC key
                break
                
        elif weekly_plan_mode:
            # Recreate weekly plan screen with latest data
            weekly_plan_screen, day_buttons, weekly_plan_continue_button = create_weekly_plan_screen(trainer)
            
            # Display weekly plan screen
            cv2.imshow('AI Personal Trainer', weekly_plan_screen)
            
            # Handle mouse clicks for weekly plan
            def weekly_plan_mouse_callback(event, x, y, flags, param):
                nonlocal weekly_plan_mode, daily_exercises_mode
                nonlocal weekly_plan_screen, day_buttons, weekly_plan_continue_button
                
                if event == cv2.EVENT_LBUTTONDOWN:
                    # Check day buttons
                    for button in day_buttons:
                        if (button['x1'] <= x <= button['x2'] and 
                            button['y1'] <= y <= button['y2']):
                            # Set the selected day
                            trainer.set_current_day(button['day_idx'])
                            print(f"Selected day: {trainer.days_of_week[button['day_idx']]}")
                            weekly_plan_mode = False
                            daily_exercises_mode = True
                            # Update daily exercises screen
                            daily_exercises_screen, exercise_buttons_daily, daily_back_button = create_daily_exercises_screen(trainer)
                    
                    # Check continue button
                    if (weekly_plan_continue_button['x1'] <= x <= weekly_plan_continue_button['x2'] and 
                        weekly_plan_continue_button['y1'] <= y <= weekly_plan_continue_button['y2']):
                        weekly_plan_mode = False
                        daily_exercises_mode = True
                        # Update daily exercises screen
                        daily_exercises_screen, exercise_buttons_daily, daily_back_button = create_daily_exercises_screen(trainer)
            
            # Set the mouse callback
            cv2.setMouseCallback('AI Personal Trainer', weekly_plan_mouse_callback)
            
            # Check for key press to exit
            key = cv2.waitKey(10) & 0xFF
            if key == 27:  # ESC key
                break
        
        elif daily_exercises_mode:
            # Recreate daily exercises screen with latest data
            daily_exercises_screen, exercise_buttons_daily, daily_back_button = create_daily_exercises_screen(trainer)
            
            # Display daily exercises screen
            cv2.imshow('AI Personal Trainer', daily_exercises_screen)
            
            # Handle mouse clicks for daily exercises
            def daily_exercises_mouse_callback(event, x, y, flags, param):
                nonlocal daily_exercises_mode, weekly_plan_mode, training_mode
                nonlocal daily_exercises_screen, exercise_buttons_daily, daily_back_button
                
                if event == cv2.EVENT_LBUTTONDOWN:
                    # Check exercise buttons
                    for button in exercise_buttons_daily:
                        if (button['x1'] <= x <= button['x2'] and 
                            button['y1'] <= y <= button['y2']):
                            exercise = button['exercise']
                            
                            # If exercise is not completed, start training
                            if not trainer.is_exercise_completed(exercise):
                                # Set the selected exercise
                                trainer.exercise_type = exercise
                                daily_exercises_mode = False
                                training_mode = True
                            else:
                                # If already completed, just refresh the screen
                                daily_exercises_screen, exercise_buttons_daily, daily_back_button = create_daily_exercises_screen(trainer)
                                cv2.imshow('AI Personal Trainer', daily_exercises_screen)
                    
                    # Check back button
                    if (daily_back_button['x1'] <= x <= daily_back_button['x2'] and 
                        daily_back_button['y1'] <= y <= daily_back_button['y2']):
                        print("Back to weekly plan clicked")
                        daily_exercises_mode = False
                        weekly_plan_mode = True
                        # Update weekly plan screen
                        weekly_plan_screen, day_buttons, weekly_plan_continue_button = create_weekly_plan_screen(trainer)
            
            # Set the mouse callback
            cv2.setMouseCallback('AI Personal Trainer', daily_exercises_mouse_callback)
            
            # Check for key press to exit
            key = cv2.waitKey(10) & 0xFF
            if key == 27:  # ESC key
                break
                
        elif training_mode:
            # Process frame for training
            ret, frame = cap.read()
            if not ret:
                print("Failed to grab frame")
                break
                
            image = trainer.process_frame(frame)
            
            # Check if set is complete and transition to rest mode
            if trainer.is_set_complete() and not trainer.is_workout_complete():
                rest_mode = True
                training_mode = False
                # Set rest start time
                trainer.rest_start_time = time.time()
                # Reset the mouse callback
                cv2.setMouseCallback('AI Personal Trainer', lambda *args: None)
                continue
            elif trainer.is_workout_complete():
                # Mark the exercise as completed
                trainer.mark_exercise_completed(trainer.exercise_type)
                print(f"Exercise completed: {trainer.exercise_type}")
                # Update daily exercises screen
                daily_exercises_screen, exercise_buttons_daily, daily_back_button = create_daily_exercises_screen(trainer)
                # Return to daily exercises screen
                daily_exercises_mode = True
                training_mode = False
                # Reset the mouse callback
                cv2.setMouseCallback('AI Personal Trainer', lambda *args: None)
                continue
            
            # Display the frame
            cv2.imshow('AI Personal Trainer', image)
            
            # Handle key presses
            key = cv2.waitKey(10) & 0xFF
            if key == ord('b'):
                # Go back to daily exercises screen
                daily_exercises_mode = True
                training_mode = False
                # Reset the mouse callback
                cv2.setMouseCallback('AI Personal Trainer', lambda *args: None)
            elif key == ord('w'):
                # Go back to weekly plan
                weekly_plan_mode = True
                training_mode = False
                # Reset the mouse callback
                cv2.setMouseCallback('AI Personal Trainer', lambda *args: None)
            elif key == ord('q') or key == 27:  # q or ESC
                break
    
        elif rest_mode:
            # Calculate remaining rest time
            if trainer.rest_start_time > 0:
                elapsed_time = time.time() - trainer.rest_start_time
                remaining_seconds = max(0, int(trainer.rest_time - elapsed_time))
            else:
                remaining_seconds = 0
            
            # Create and display rest screen
            rest_screen, start_button = create_rest_screen(
                trainer.current_set, trainer.set_goal, trainer.exercise_type, remaining_seconds)
            
            cv2.imshow('AI Personal Trainer', rest_screen)
            
            # Handle mouse clicks for rest screen
            def rest_mouse_callback(event, x, y, flags, param):
                nonlocal rest_mode, training_mode, daily_exercises_mode, weekly_plan_mode
                
                if event == cv2.EVENT_LBUTTONDOWN:
                    # Check start next set button
                    if (start_button['x1'] <= x <= start_button['x2'] and 
                        start_button['y1'] <= y <= start_button['y2']):
                        # Start next set
                        trainer.start_next_set()
                        trainer.rest_start_time = 0  # Reset rest timer
                        rest_mode = False
                        training_mode = True
            
            # Set the mouse callback
            cv2.setMouseCallback('AI Personal Trainer', rest_mouse_callback)
            
            # Check for key press to exit or skip rest
            key = cv2.waitKey(10) & 0xFF
            if key == ord('s'):  # Skip rest
                trainer.start_next_set()
                trainer.rest_start_time = 0
                rest_mode = False
                training_mode = True
            elif key == ord('b'):  # Back to daily exercises
                rest_mode = False
                daily_exercises_mode = True
                # Update daily exercises screen
                daily_exercises_screen, exercise_buttons_daily, daily_back_button = create_daily_exercises_screen(trainer)
            elif key == ord('w'):  # Back to weekly plan
                rest_mode = False
                weekly_plan_mode = True
                # Update weekly plan screen
                weekly_plan_screen, day_buttons, weekly_plan_continue_button = create_weekly_plan_screen(trainer)
            elif key == 27:  # ESC key
                break
            
            # Auto transition if rest time is over
            if remaining_seconds <= 0 and trainer.rest_start_time > 0:
                trainer.start_next_set()
                trainer.rest_start_time = 0
                rest_mode = False
                training_mode = True
    
    # Release resources
    cap.release()
    cv2.destroyAllWindows()
    trainer.pose.close()


if __name__ == "__main__":
    main()

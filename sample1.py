import cv2
import numpy as np
import mediapipe as mp
from matplotlib import pyplot as plt

# Initialize Mediapipe Holistic model
mp_holistic = mp.solutions.holistic
mp_drawing = mp.solutions.drawing_utils

# Function to process image and detect landmarks
def mediapipe_detection(image, model):
    image = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)  # Convert color space
    image.flags.writeable = False                   # Image is no longer writeable
    results = model.process(image)                  # Make prediction
    image.flags.writeable = True                    # Image is now writeable
    image = cv2.cvtColor(image, cv2.COLOR_RGB2BGR) # Convert color space back
    return image, results

# Function to draw styled landmarks on the image
def draw_styled_landmarks(image, results):
    # Draw face connections with custom styles
    if results.face_landmarks:
        mp_drawing.draw_landmarks(image, results.face_landmarks, mp_holistic.FACEMESH_TESSELATION,
                                 mp_drawing.DrawingSpec(color=(80, 110, 10), thickness=1, circle_radius=1),
                                 mp_drawing.DrawingSpec(color=(80, 256, 121), thickness=1, circle_radius=1))
    
    # Draw pose connections with custom styles
    if results.pose_landmarks:
        mp_drawing.draw_landmarks(image, results.pose_landmarks, mp_holistic.POSE_CONNECTIONS,
                                 mp_drawing.DrawingSpec(color=(80, 22, 10), thickness=2, circle_radius=4),
                                 mp_drawing.DrawingSpec(color=(80, 44, 121), thickness=2, circle_radius=2))
    
    # Draw left hand connections with custom styles
    if results.left_hand_landmarks:
        mp_drawing.draw_landmarks(image, results.left_hand_landmarks, mp_holistic.HAND_CONNECTIONS,
                                 mp_drawing.DrawingSpec(color=(121, 22, 76), thickness=2, circle_radius=4),
                                 mp_drawing.DrawingSpec(color=(121, 44, 250), thickness=2, circle_radius=2))
    
    # Draw right hand connections with custom styles
    if results.right_hand_landmarks:
        mp_drawing.draw_landmarks(image, results.right_hand_landmarks, mp_holistic.HAND_CONNECTIONS,
                                 mp_drawing.DrawingSpec(color=(245, 117, 66), thickness=2, circle_radius=4),
                                 mp_drawing.DrawingSpec(color=(245, 66, 230), thickness=2, circle_radius=2))

# Capture video from the default camera
cap = cv2.VideoCapture(0)

# Set Mediapipe model
with mp_holistic.Holistic(min_detection_confidence=0.5, min_tracking_confidence=0.5) as holistic:
    while cap.isOpened():
        # Read frame from the video feed
        ret, frame = cap.read()

        # Make detections
        image, results = mediapipe_detection(frame, holistic)
        print(results)
        
        # Draw landmarks on the image
        draw_styled_landmarks(image, results)

        # Display the processed image
        cv2.imshow('OpenCV Feed', image)

        # Break the loop if 'q' is pressed
        if cv2.waitKey(10) & 0xFF == ord('q'):
            break

# Release the video capture object and close all OpenCV windows
cap.release()
cv2.destroyAllWindows()
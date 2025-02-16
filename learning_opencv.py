#you need to download these librarys through running on terminal:
#     pip install opencv-python matplotlib tensorflow torch torchvision torchaudio mediapipe

import cv2  # OpenCV for handling webcam and image processing
import mediapipe as mp  # MediaPipe for hand tracking

# Initialize MediaPipe Hands module
mp_hands = mp.solutions.hands  # Hands detection module
mp_draw = mp.solutions.drawing_utils  # Utility to draw landmarks on the hand

# Open the webcam (0 = default webcam)
cap = cv2.VideoCapture(0)

# Initialize the MediaPipe Hands model with confidence thresholds
with mp_hands.Hands(
    min_detection_confidence=0.5,  # Minimum confidence to detect a hand
    min_tracking_confidence=0.5  # Minimum confidence to track the hand
) as hands:
    
    while cap.isOpened():  # Keep running while webcam is open
        ret, frame = cap.read()  # Read a frame from the webcam
        if not ret:
            break  # If the frame isn't captured properly, exit the loop

        # Flip the image horizontally (so it doesn't look mirrored)
        frame = cv2.flip(frame, 1)

        # Convert the frame from BGR (OpenCV default) to RGB (MediaPipe requires RGB)
        rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)

        # Process the frame with MediaPipe to detect hands
        results = hands.process(rgb_frame)

        # If any hands are detected in the frame
        if results.multi_hand_landmarks:
            for hand_landmarks in results.multi_hand_landmarks:
                # Draw the landmarks (points) and connections on the hand
                mp_draw.draw_landmarks(frame, hand_landmarks, mp_hands.HAND_CONNECTIONS)

                # Extract and print the coordinates of fingertips
                # Indexes: 4 (thumb tip), 8 (index tip), 12 (middle tip), 16 (ring tip), 20 (pinky tip)
                for i, landmark in enumerate(hand_landmarks.landmark):
                    h, w, _ = frame.shape  # Get frame dimensions
                    cx, cy = int(landmark.x * w), int(landmark.y * h)  # Convert normalized coordinates to pixel values

                    if i in [4, 8, 12, 16, 20]:  # Only print fingertips
                        print(f"Finger {i}: (X: {cx}, Y: {cy})")  # Print fingertip coordinates

                        # Draw a circle on the fingertip
                        cv2.circle(frame, (cx, cy), 10, (0, 255, 0), -1)

        # Display the webcam feed with hand tracking
        cv2.imshow("Hand Tracking", frame)

        # Press 'q' to exit the program
        if cv2.waitKey(1) & 0xFF == ord('q'):
            break

# Release the webcam and close all OpenCV windows
cap.release()
cv2.destroyAllWindows()

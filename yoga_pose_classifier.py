import cv2
import mediapipe as mp
import numpy as np
import time
import streamlit as st

def run_yoga_pose(user_weight, target_time, pose_name, video_path=0):
    MET_VALUES = {"Tree Pose": 2.5, "Warrior II Pose": 3.0, "Chair Pose": 3.5}
    MET = MET_VALUES.get(pose_name, 3.0)

    # Initialize session state variables
    if 'pose_active' not in st.session_state:
        st.session_state.pose_active = False
    if 'pose_held_time' not in st.session_state:
        st.session_state.pose_held_time = 0
    if 'start_time' not in st.session_state:
        st.session_state.start_time = None
    if 'success' not in st.session_state:
        st.session_state.success = False
    if 'pause_message_shown' not in st.session_state:
        st.session_state.pause_message_shown = False

    mp_pose = mp.solutions.pose
    mp_drawing = mp.solutions.drawing_utils

    def calculate_angle(a, b, c):
        a = np.array([a.x, a.y])
        b = np.array([b.x, b.y])
        c = np.array([c.x, c.y])
        radians = np.arctan2(c[1]-b[1], c[0]-b[0]) - np.arctan2(a[1]-b[1], a[0]-b[0])
        angle = np.abs(np.degrees(radians))
        return 360 - angle if angle > 180 else angle

    def is_target_pose(pose_name, landmarks):
        if not landmarks:
            return False
        lmk = mp_pose.PoseLandmark
        angles = {
            "left_hip": calculate_angle(landmarks[lmk.LEFT_SHOULDER.value], landmarks[lmk.LEFT_HIP.value], landmarks[lmk.LEFT_KNEE.value]),
            "right_hip": calculate_angle(landmarks[lmk.RIGHT_SHOULDER.value], landmarks[lmk.RIGHT_HIP.value], landmarks[lmk.RIGHT_KNEE.value]),
            "left_elbow": calculate_angle(landmarks[lmk.LEFT_SHOULDER.value], landmarks[lmk.LEFT_ELBOW.value], landmarks[lmk.LEFT_WRIST.value]),
            "right_elbow": calculate_angle(landmarks[lmk.RIGHT_SHOULDER.value], landmarks[lmk.RIGHT_ELBOW.value], landmarks[lmk.RIGHT_WRIST.value]),
            "left_shoulder": calculate_angle(landmarks[lmk.LEFT_ELBOW.value], landmarks[lmk.LEFT_SHOULDER.value], landmarks[lmk.LEFT_HIP.value]),
            "right_shoulder": calculate_angle(landmarks[lmk.RIGHT_HIP.value], landmarks[lmk.RIGHT_SHOULDER.value], landmarks[lmk.RIGHT_ELBOW.value]),
            "left_knee": calculate_angle(landmarks[lmk.LEFT_HIP.value], landmarks[lmk.LEFT_KNEE.value], landmarks[lmk.LEFT_ANKLE.value]),
            "right_knee": calculate_angle(landmarks[lmk.RIGHT_HIP.value], landmarks[lmk.RIGHT_KNEE.value], landmarks[lmk.RIGHT_ANKLE.value])
        }

        if pose_name == 'Tree Pose':
            return (165 < angles["left_elbow"] < 195 and 165 < angles["right_elbow"] < 195 and
                    80 < angles["left_shoulder"] < 110 and 80 < angles["right_shoulder"] < 110 and
                    160 < angles["left_knee"] < 195 and 160 < angles["right_knee"] < 195)
        elif pose_name == 'Warrior II Pose':
            return ((150 < angles["left_elbow"] < 210 and 150 < angles["right_elbow"] < 210 and
                     70 < angles["left_shoulder"] < 120 and 70 < angles["right_shoulder"] < 120) and
                    ((80 < angles["left_knee"] < 130 and 150 < angles["right_knee"] < 210) or
                     (80 < angles["right_knee"] < 130 and 150 < angles["left_knee"] < 210)))
        elif pose_name == 'Chair Pose':
            knees_bent = (70 < angles["left_knee"] < 140 and 70 < angles["right_knee"] < 140)
            hips_bent = (70 < angles["left_hip"] < 130 and 70 < angles["right_hip"] < 130)
            wrists_above_shoulders = (
                landmarks[lmk.LEFT_WRIST.value].y < landmarks[lmk.LEFT_SHOULDER.value].y and
                landmarks[lmk.RIGHT_WRIST.value].y < landmarks[lmk.RIGHT_SHOULDER.value].y)
            elbows_straight = (150 < angles["left_elbow"] < 195 and 150 < angles["right_elbow"] < 195)
            return knees_bent and hips_bent and wrists_above_shoulders and elbows_straight
        return False

    frame_placeholder = st.empty()
    cap = cv2.VideoCapture(video_path)

    with mp_pose.Pose(min_detection_confidence=0.7, min_tracking_confidence=0.7) as pose:
        while cap.isOpened():
            ret, frame = cap.read()
            if not ret:
                break

            if st.session_state.get('workout_status') == "paused":
                if not st.session_state.pause_message_shown:
                    st.warning("⏸ Workout Paused. Press Resume to continue.")
                    st.session_state.pause_message_shown = True
                time.sleep(1)
                continue
            else:
                st.session_state.pause_message_shown = False

            frame = cv2.flip(frame, 1)
            rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            results = pose.process(rgb)
            frame = cv2.cvtColor(rgb, cv2.COLOR_RGB2BGR)

            if results.pose_landmarks:
                mp_drawing.draw_landmarks(frame, results.pose_landmarks, mp_pose.POSE_CONNECTIONS)
                landmarks = results.pose_landmarks.landmark

                if is_target_pose(pose_name, landmarks):
                    if not st.session_state.pose_active:
                        st.session_state.pose_active = True
                        st.session_state.start_time = time.time()
                    else:
                        st.session_state.pose_held_time = time.time() - st.session_state.start_time
                else:
                    st.session_state.pose_active = False
                    st.session_state.pose_held_time = 0
                    st.session_state.start_time = None

                # Overlay pose time and status
                cv2.putText(frame, f'Held: {int(st.session_state.pose_held_time)}s / {int(target_time)}s',
                            (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 255, 0), 2)
                cv2.putText(frame, f'Pose: {pose_name}', (10, 60),
                            cv2.FONT_HERSHEY_SIMPLEX, 0.8, (255, 255, 0), 2)

                if st.session_state.pose_held_time >= target_time:
                    st.session_state.success = True
                    break

            frame_placeholder.image(frame, channels='BGR')
            if cv2.waitKey(10) & 0xFF == ord('q'):
                break

    cap.release()
    cv2.destroyAllWindows()

    duration = st.session_state.pose_held_time
    calories = MET * user_weight * (duration / 3600)

    return {
        "exercise": "Yoga",
        "pose": pose_name,
        "duration": round(duration, 2),
        "calories": round(calories, 2),
        "success": st.session_state.success,
        "status": "Success" if st.session_state.success else "Fail"
    }

# # Example usage like the lunges code
# if __name__ == "__main__":
#     weight = float(input("Enter your weight (kg): "))
#     hold_time = float(input("Enter target hold time (seconds): "))
#     pose = input("Enter pose name (Tree Pose / Warrior II Pose / Chair Pose): ")
#     result = run_yoga_pose(weight, hold_time, pose)
#     print(result)

    

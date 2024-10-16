from flask import Flask, render_template, Response, jsonify
import time
import threading
from ultralytics import YOLO
import cv2

app = Flask(__name__)

# Load the YOLOv8 model
detection_model = YOLO("yolov8n.pt")

# Video sources for the two lanes
video_sources = {
    "lane1": "Video/lane1.mp4",
    "lane2": "Video/lane2.mp4"
}

# Real camera sources for the two lanes (update with actual camera streams)
real_camera_sources = {
    "lane1": 0,
    "lane2": 0
}

# Traffic signal and vehicle counts for each lane
signal_states = {"lane1": "red", "lane2": "red"}
vehicle_counts = {"lane1": 0, "lane2": 0}
remaining_green_time = {"lane1": 0, "lane2": 0}
waiting_time = {"lane1": 0, "lane2": 0}

# Traffic timing parameters
BASE_GREEN_TIME = 10
VEHICLE_TIME_MULTIPLIER = 1
YELLOW_TIME = 3

# Vehicle class IDs for YOLO
vehicle_class_ids = [2, 3, 5, 7]


def detect_vehicles(frame):
    results = detection_model(frame, conf=0.3)[0]
    vehicle_count = sum(1 for box in results.boxes if int(
        box.cls[0]) in vehicle_class_ids)
    annotated_frame = results.plot()
    return vehicle_count, annotated_frame


def gen_frames(lane, feed_type):
    cap = cv2.VideoCapture(
        real_camera_sources[lane] if feed_type == "camera" else video_sources[lane])

    while cap.isOpened():
        ret, frame = cap.read()
        if not ret:
            break

        # Skip detection for the lane with a green signal
        if signal_states[lane] == "green":
            vehicle_counts[lane] = 0  # Ensure vehicle count is set to 0
            annotated_frame = frame  # Use the original frame
        else:
            vehicle_count, annotated_frame = detect_vehicles(frame)
            vehicle_counts[lane] = vehicle_count

        ret, buffer = cv2.imencode('.jpg', annotated_frame)
        frame = buffer.tobytes()
        yield (b'--frame\r\n'
               b'Content-Type: image/jpeg\r\n\r\n' + frame + b'\r\n')


def manage_traffic_signals():
    lanes = list(vehicle_counts.keys())

    while True:
        for i in range(len(lanes)):
            current_lane = lanes[i]
            other_lane = lanes[1 - i]  # The other lane is the one not green

            # Calculate green time for the current lane
            green_time = BASE_GREEN_TIME + \
                vehicle_counts[current_lane] * VEHICLE_TIME_MULTIPLIER
            # Enforce minimum/maximum green light durations
            green_time = max(10, min(green_time, 60))

            # Set current lane green, others red
            signal_states[current_lane] = "green"
            remaining_green_time[current_lane] = green_time
            signal_states[other_lane] = "red"
            waiting_time[other_lane] = green_time

            print(f"{current_lane} green for {green_time} seconds, {
                  other_lane} waiting for {green_time} seconds")

            # Countdown for green time in current lane and waiting time in other lane
            for t in range(green_time, 0, -1):
                remaining_green_time[current_lane] = t
                waiting_time[other_lane] = t
                time.sleep(1)

            # Set current lane to yellow after green
            signal_states[current_lane] = "yellow"
            remaining_green_time[current_lane] = YELLOW_TIME

            for t in range(YELLOW_TIME, 0, -1):
                remaining_green_time[current_lane] = t
                time.sleep(1)

            # After yellow, set the current lane to red
            signal_states[current_lane] = "red"
            remaining_green_time[current_lane] = 0

            time.sleep(1)  # Sleep to prevent busy-waiting


# Start traffic signal control in a separate thread
signal_thread = threading.Thread(target=manage_traffic_signals)
signal_thread.daemon = True
signal_thread.start()


@app.route('/video')
def index_video():
    return render_template('two.html')


@app.route('/video_feed/<lane>/<feed_type>')
def video_feed(lane, feed_type):
    return Response(gen_frames(lane, feed_type), mimetype='multipart/x-mixed-replace; boundary=frame')


@app.route('/vehicle_data')
def vehicle_data():
    return jsonify({
        'lane1_vehicles': vehicle_counts['lane1'],
        'lane2_vehicles': vehicle_counts['lane2'],

        'lane1_signal': signal_states['lane1'],
        'lane2_signal': signal_states['lane2'],

        'lane1_remaining_time': remaining_green_time['lane1'],
        'lane2_remaining_time': remaining_green_time['lane2'],

        'lane1_waiting_time': waiting_time['lane1'],
        'lane2_waiting_time': waiting_time['lane2'],
    })


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8000)

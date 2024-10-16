import time
import threading
from flask import Flask, render_template, Response, jsonify
from ultralytics import YOLO
import cv2

app = Flask(__name__)

# Load the YOLOv8 model
detection_model = YOLO("yolov8n.pt")

# Video sources for the three lanes
video_sources = {
    "lane1": "Video/lane1.mp4",
    "lane2": "Video/lane2.mp4",
    "lane3": "Video/lane3.mp4",
    "lane4": "Video/lane4.mp4"
}

# Set camera sources for real-time feeds (replace with actual camera URLs or indices)
camera_sources = {
    "lane1": 0,  # Camera index for lane 1
    "lane2": 0,  # Camera index for lane 2
    "lane3": 0,  # Camera index for lane 3
    "lane4": 0   # Camera index for lane 4
}

# Traffic signal and vehicle counts for each lane
signal_states = {"lane1": "red", "lane2": "red",
                 "lane3": "red", "lane4": "red"}
vehicle_counts = {"lane1": 0, "lane2": 0, "lane3": 0, "lane4": 0}
remaining_green_time = {"lane1": 0, "lane2": 0, "lane3": 0, "lane4": 0}

# Traffic timing parameters
BASE_GREEN_TIME = 10
VEHICLE_TIME_MULTIPLIER = 1
YELLOW_TIME = 3

# Vehicle class IDs for YOLO
vehicle_class_ids = [2, 3, 5, 7]

# Current feed type (video or camera)
current_feed_type = "video"  # Default is video

# Waiting time for next green signal for each lane
next_green_waiting_time = {"lane1": 0, "lane2": 0, "lane3": 0, "lane4": 0}


def detect_vehicles(frame):
    results = detection_model(frame, conf=0.3)[0]
    vehicle_count = sum(1 for box in results.boxes if int(
        box.cls[0]) in vehicle_class_ids)
    annotated_frame = results.plot()
    return vehicle_count, annotated_frame


def gen_frames(lane):
    global current_feed_type

    if current_feed_type == "video":
        cap = cv2.VideoCapture(video_sources[lane])
    else:
        cap = cv2.VideoCapture(camera_sources[lane])  # Use the camera feed

    while cap.isOpened():
        ret, frame = cap.read()
        if not ret:
            break

        if signal_states[lane] == "green":  # Skip detection if the signal is green
            vehicle_count = 0
            annotated_frame = frame  # No annotation, just pass the original frame
        else:
            vehicle_count, annotated_frame = detect_vehicles(
                frame)  # Detect for other lanes

        vehicle_counts[lane] = vehicle_count

        ret, buffer = cv2.imencode('.jpg', annotated_frame)
        frame = buffer.tobytes()
        yield (b'--frame\r\n'
               b'Content-Type: image/jpeg\r\n\r\n' + frame + b'\r\n')


def manage_traffic_signals():
    global next_green_waiting_time  # Declare global to update next_green_waiting_time

    lanes = list(vehicle_counts.keys())

    while True:
        total_cycle_time = 0
        for i in range(len(lanes)):
            current_lane = lanes[i]

            # Calculate green time for the current lane
            green_time = BASE_GREEN_TIME + \
                vehicle_counts[current_lane] * VEHICLE_TIME_MULTIPLIER

            # Enforce minimum and maximum green light durations
            green_time = max(10, min(green_time, 60))

            # Calculate total cycle time for waiting time calculations
            total_cycle_time += green_time + YELLOW_TIME

        # Loop through the lanes and update signals
        for i in range(len(lanes)):
            current_lane = lanes[i]

            # Calculate green time for the current lane
            green_time = BASE_GREEN_TIME + \
                vehicle_counts[current_lane] * VEHICLE_TIME_MULTIPLIER

            # Enforce minimum and maximum green light durations
            green_time = max(10, min(green_time, 60))

            # Set current lane green, others red
            for lane in lanes:
                if lane == current_lane:
                    signal_states[lane] = "green"
                    remaining_green_time[lane] = green_time
                    print(f"{lane} green for {green_time} seconds")

                    # Update waiting time for next green signal
                    next_green_waiting_time.update(update_waiting_times(
                        lanes, current_lane, green_time + YELLOW_TIME))

                    for t in range(green_time, 0, -1):
                        remaining_green_time[lane] = t
                        time.sleep(1)

                    # After green, set to yellow
                    signal_states[lane] = "yellow"
                    remaining_green_time[lane] = YELLOW_TIME
                    for t in range(YELLOW_TIME, 0, -1):
                        remaining_green_time[lane] = t
                        time.sleep(1)

                    # After yellow, set to red
                    signal_states[lane] = "red"
                else:
                    remaining_green_time[lane] = 0

            time.sleep(1)  # Sleep to prevent busy-waiting


def update_waiting_times(lanes, current_lane, current_cycle_time):
    """
    Update the waiting time for the next green signal for each lane.
    """
    global next_green_waiting_time  # Ensure global is updated
    total_time = 0

    for lane in lanes:
        if lane == current_lane:
            next_green_waiting_time[lane] = 0
        else:
            next_green_waiting_time[lane] = current_cycle_time + total_time
            total_time += remaining_green_time[lane] + YELLOW_TIME

    return next_green_waiting_time


# Start traffic signal control in a separate thread
signal_thread = threading.Thread(target=manage_traffic_signals)
signal_thread.daemon = True
signal_thread.start()


@app.route('/video')
def index_video():
    return render_template('video.html')


@app.route('/video_feed/<lane>')
def video_feed(lane):
    return Response(gen_frames(lane), mimetype='multipart/x-mixed-replace; boundary=frame')


@app.route('/set_feed_type/<feed_type>')
def set_feed_type(feed_type):
    global current_feed_type
    current_feed_type = feed_type
    return jsonify(success=True)


@app.route('/vehicle_data')
def vehicle_data():
    return jsonify({
        'lane1_vehicles': vehicle_counts['lane1'],
        'lane2_vehicles': vehicle_counts['lane2'],
        'lane3_vehicles': vehicle_counts['lane3'],
        'lane4_vehicles': vehicle_counts['lane4'],
        'lane1_signal': signal_states['lane1'],
        'lane2_signal': signal_states['lane2'],
        'lane3_signal': signal_states['lane3'],
        'lane4_signal': signal_states['lane4'],
        'lane1_remaining_time': remaining_green_time['lane1'],
        'lane2_remaining_time': remaining_green_time['lane2'],
        'lane3_remaining_time': remaining_green_time['lane3'],
        'lane4_remaining_time': remaining_green_time['lane4'],
        'lane1_next_green': next_green_waiting_time['lane1'],
        'lane2_next_green': next_green_waiting_time['lane2'],
        'lane3_next_green': next_green_waiting_time['lane3'],
        'lane4_next_green': next_green_waiting_time['lane4'],
    })


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8000)

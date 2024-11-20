import cv2
import os
import time
from datetime import datetime
from flask import Flask, Response, render_template, jsonify
from ultralytics import YOLO
import threading

model = YOLO("best1.pt")

video_sources = {
    "Lane1": "Video/lane4.mp4",
    "Lane2": "Video/lane3.mp4",
    "Lane3": "Video/lane2.mp4",
    "Lane4": "Video/lane1.mp4"
}
vehicle_counts = {
    "Lane1": 0,
    "Lane2": 0,
    "Lane3": 0,
    "Lane4": 0
}

green_times = {
    "Lane1": 0,
    "Lane2": 0,
    "Lane3": 0,
    "Lane4": 0
}
lane_states = {
    "Lane1": False,
    "Lane2": False,
    "Lane3": False,
    "Lane4": False
}

vehicle_class_ids = [2, 3, 5, 7]

# Flask app
app = Flask(__name__)

# Global video captures for each lane
video_captures = {lane: cv2.VideoCapture(
    path) for lane, path in video_sources.items()}


def update_lane_states(active_lane):
    """
    Update lane states so that only the active lane is True, and others are False.
    """
    for lane in lane_states:
        lane_states[lane] = (lane == active_lane)


def detect_vehicles_in_frame(frame):
    """
    Detect vehicles in a single frame using YOLOv8.
    Returns the vehicle count and the annotated frame.
    """
    results = model(frame)
    detections = results[0].boxes if results else []
    vehicle_count = sum(1 for box in detections if int(
        box.cls[0]) in vehicle_class_ids)
    annotated_frame = results[0].plot() if results else frame
    return vehicle_count, annotated_frame


def process_lane(lane, video_path):
    """
    Process a single lane: capture one frame, detect vehicles, and calculate green light time.
    """
    cap = cv2.VideoCapture(video_path)
    if not cap.isOpened():
        print(f"Error: Cannot open video for {lane}.")
        return 0

    ret, frame = cap.read()
    if not ret:
        print(f"Error: Cannot read frame for {lane}.")
        cap.release()
        return 0

    vehicle_count, annotated_frame = detect_vehicles_in_frame(frame)
    print(f"{lane}: Vehicle count = {vehicle_count}")

    vehicle_counts[lane] = vehicle_count

    save_dir = "detected_images"
    os.makedirs(save_dir, exist_ok=True)

    timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    filename = f"{lane}_{timestamp}_{vehicle_count}.jpg"
    save_path = os.path.join(save_dir, filename)
    cv2.imwrite(save_path, annotated_frame)
    print(f"{lane}: Detection image saved as {save_path}")

    cap.release()

    green_time = max(vehicle_count, 10)
    green_times[lane] = green_time
    return green_time


def main_detection():
    """
    Main detection logic runs in a separate thread.
    """
    while True:
        for lane, video_path in video_sources.items():
            green_time = process_lane(lane, video_path)
            update_lane_states(lane)
            print(f"{lane}: Green light ON for {green_time} seconds.")
            time.sleep(green_time)
            update_lane_states(None)
            print(f"{lane}: Yellow light ON for 5 seconds.")
            time.sleep(5)


def generate_video_feed(lane):
    """
    Generate video feed for the given lane at the original frame rate.
    """
    cap = video_captures[lane]
    if not cap.isOpened():
        return

    fps = cap.get(cv2.CAP_PROP_FPS)
    frame_delay = 1 / fps if fps > 0 else 0.03

    while True:
        ret, frame = cap.read()
        if not ret:
            cap.set(cv2.CAP_PROP_POS_FRAMES, 0)
            continue

        _, buffer = cv2.imencode(".jpg", frame)
        frame_bytes = buffer.tobytes()

        yield (b"--frame\r\n"
               b"Content-Type: image/jpeg\r\n\r\n" + frame_bytes + b"\r\n")

        time.sleep(frame_delay)


@app.route("/")
def index():
    """
    Render the HTML page with the video feeds.
    """
    return render_template("index.html")


@app.route("/video_feed/<lane>")
def video_feed(lane):
    """
    Route to serve the video feed for a specific lane.
    """
    return Response(generate_video_feed(lane), mimetype="multipart/x-mixed-replace; boundary=frame")


@app.route('/vehicle_data')
def vehicle_data():

    return jsonify({
        'Lane1': {
            'vehicle_count': vehicle_counts["Lane1"],
            'green_time': green_times["Lane1"],
            'is_active': lane_states["Lane1"]
        },
        'Lane2': {
            'vehicle_count': vehicle_counts["Lane2"],
            'green_time': green_times["Lane2"],
            'is_active': lane_states["Lane2"]
        },
        'Lane3': {
            'vehicle_count': vehicle_counts["Lane3"],
            'green_time': green_times["Lane3"],
            'is_active': lane_states["Lane3"]
        },
        'Lane4': {
            'vehicle_count': vehicle_counts["Lane4"],
            'green_time': green_times["Lane4"],
            'is_active': lane_states["Lane4"]
        },
    })


if __name__ == "__main__":
    detection_thread = threading.Thread(target=main_detection, daemon=True)
    detection_thread.start()

    app.run(host="0.0.0.0", port=8800)

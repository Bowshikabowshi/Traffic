import cv2
import os
import time
from datetime import datetime
from flask import Flask, Response, render_template, jsonify
from ultralytics import YOLO
import threading
from threading import Lock

model = YOLO("Model/yolov8s.pt")
shared_resource_lock = Lock()

video_sources = {
    "Lane1": "Video/newlane1.mp4",
    "Lane2": "Video/newlane2.mp4",
    "Lane3": "Video/newlane3.mp4",
    "Lane4": "Video/newlane4.mp4"
}

vehicle_counts = {lane: 0 for lane in video_sources}
green_times = {lane: 0 for lane in video_sources}
lane_states = {lane: False for lane in video_sources}

vehicle_class_ids = [2, 3, 5, 7]

app = Flask(__name__)

video_captures = {lane: cv2.VideoCapture(
    path) for lane, path in video_sources.items()}


def release_all_captures():
    for cap in video_captures.values():
        if cap.isOpened():
            cap.release()


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
    with shared_resource_lock:
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
    vehicle_counts[lane] = vehicle_count

    save_dir = "detected_images"
    os.makedirs(save_dir, exist_ok=True)

    timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    filename = f"{lane}_{timestamp}_{vehicle_count}.jpg"
    save_path = os.path.join(save_dir, filename)
    cv2.imwrite(save_path, annotated_frame)

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
            print(f"{lane}: Green light ON for {
                  green_time} seconds. Lane states: {lane_states}")
            time.sleep(green_time - 5)
            print(f"{lane}: Yellow light ON for 5 seconds. Lane states: {
                  lane_states}")
            time.sleep(5)
            update_lane_states(None)


def generate_video_feed(lane):
    cap = video_captures.get(lane)
    if not cap or not cap.isOpened():
        print(f"Error: Video capture for lane '{lane}' is not opened.")
        return

    try:
        fps = cap.get(cv2.CAP_PROP_FPS)
        frame_delay = 1 / fps if fps > 0 else 0.03

        while True:
            with shared_resource_lock:
                ret, frame = cap.read()

            if not ret:
                with shared_resource_lock:
                    cap.set(cv2.CAP_PROP_POS_FRAMES, 0)
                continue

            _, buffer = cv2.imencode(".jpg", frame)
            frame_bytes = buffer.tobytes()

            yield (b"--frame\r\n"
                   b"Content-Type: image/jpeg\r\n\r\n" + frame_bytes + b"\r\n")

            time.sleep(frame_delay)
    except GeneratorExit:
        print(f"Video feed for lane '{lane}' closed by the client.")


def green_time_countdown():
    """
    Background thread to decrement green time for the active lane only.
    Runs every second.
    """
    while True:
        active_lane = None
        for lane, state in lane_states.items():
            if state:
                active_lane = lane
                break

        if active_lane and green_times[active_lane] > 0:
            green_times[active_lane] -= 1

        time.sleep(1)


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
    """
    Return the vehicle data (vehicle count, green time, signal status)
    for the active lane only.
    """
    active_lane = None

    for lane, state in lane_states.items():
        if state:
            active_lane = lane
            break

    if not active_lane:
        return jsonify({"message": "No active lane"})

    signal_status = (
        'green' if green_times[active_lane] > 5 else
        'yellow' if green_times[active_lane] > 0 else
        'red'
    )

    lane_data = {
        'lane': active_lane,
        'vehicle_count': vehicle_counts[active_lane],
        'green_time': green_times[active_lane],
        'is_active': True,
        'signal_status': signal_status
    }

    return jsonify(lane_data)


@app.route('/get_image_files')
def get_image_files():
    """
    Return a list of image filenames in the detected_images folder.
    """
    image_folder = 'static/detected_images'
    image_files = [f for f in os.listdir(
        image_folder) if f.endswith('.jpg')]
    return jsonify(image_files)


if __name__ == "__main__":
    try:
        detection_thread = threading.Thread(target=main_detection, daemon=True)
        detection_thread.start()

        countdown_thread = threading.Thread(
            target=green_time_countdown, daemon=True)
        countdown_thread.start()

        app.run(host="0.0.0.0", port=8800)
    finally:
        release_all_captures()

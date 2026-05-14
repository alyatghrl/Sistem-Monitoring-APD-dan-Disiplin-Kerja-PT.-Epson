import os
import time
import requests
import cv2  # Added to handle saving the image
from datetime import datetime

# API Configuration
API_URL = "http://localhost:8000/api/v1/violations"
CAMERA_ID = "CAM_NORTH_GATE_01"
SAVE_DIR = "storage/clips"

# Ensure the directory exists
os.makedirs(SAVE_DIR, exist_ok=True)

# Track cooldowns: { violation_type: last_timestamp }
last_reported = {}
COOLDOWN_SECONDS = 60 

def report_violation(type_id, conf, frame):
    """
    Saves the image and sends the metadata to the FastAPI server.
    """
    # 1. Create a unique filename using timestamp
    timestamp_str = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"event_{type_id}_{timestamp_str}.jpg" # Using .jpg for frame capture
    relative_path = os.path.join(SAVE_DIR, filename)
    
    # 2. Save the frame as evidence
    cv2.imwrite(relative_path, frame)
    
    # 3. Prepare payload (must match your Pydantic Schema in main.py)
    payload = {
        "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "violation_type": int(type_id),
        "confidence_score": round(float(conf), 2),
        "video_directory": relative_path,
        "camera_id": CAMERA_ID
    }
    
    # 4. Send to API
    try:
        response = requests.post(API_URL, json=payload, timeout=5)
        if response.status_code == 201:
            print(f"✅ Reported violation {type_id} successfully.")
        else:
            print(f"❌ API Error {response.status_code}: {response.text}")
    except Exception as e:
        print(f"⚠️ Connection failed: {e}")

def process_detections(detections, frame):
    """
    Called every frame from your YOLO loop.
    detections: list of dicts like [{'class_id': 0, 'conf': 0.95}]
    """
    current_time = time.time()
    
    for det in detections:
        v_type = det['class_id']
        conf = det['conf']
        
        # Check Cooldown
        if v_type not in last_reported or (current_time - last_reported[v_type]) > COOLDOWN_SECONDS:
            report_violation(v_type, conf, frame)
            last_reported[v_type] = current_time
        else:
            # Optional: print to console for debugging
            # print(f"Skipping violation {v_type} (cooldown active)")
            pass

# --- INTEGRATION EXAMPLE ---
# This is how you'd use it with your actual YOLO code
def run_yolo_loop():
    # cap = cv2.VideoCapture(0)
    # while True:
    #     ret, frame = cap.read()
    #     results = model(frame) # YOLO inference
    #     detections = results_to_list(results) # Convert results to list of dicts
    #     process_detections(detections, frame)
    pass
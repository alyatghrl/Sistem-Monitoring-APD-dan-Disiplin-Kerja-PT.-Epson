import requests
from datetime import datetime

# Make sure Uvicorn is running before you execute this!
url = "http://127.0.0.1:8000/api/v1/violations"

payload = {
    "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
    "violation_type": 0,
    "confidence_score": 0.99,
    "video_directory": "storage/clips/test_video.mp4",
    "camera_id": "TEST_SCRIPT"
}

try:
    response = requests.post(url, json=payload)
    print(f"Status Code: {response.status_code}")
    if response.status_code == 201:
        print("✅ Success! The data was sent to FastAPI.")
    else:
        print(f"❌ Failed: {response.text}")
except Exception as e:
    print(f"⚠️ Connection Error: {e}")
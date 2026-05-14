from fastapi import BackgroundTasks, Depends
from streamlit import App
from database import DBViolation
from schema import ViolationCreate
from main import VIOLATION_MAP, get_db

import requests

def send_telegram_msg(violation_name, confidence, camera_id):
    token = "YOUR_BOT_TOKEN"
    chat_id = "YOUR_CHAT_ID"
    message = (
        f"🚨 *Violation Detected!*\n"
        f"Type: {violation_name}\n"
        f"Confidence: {confidence*100:.1f}%\n"
        f"Camera: {camera_id}"
    )
    url = f"https://api.telegram.org/bot{token}/sendMessage"
    payload = {"chat_id": chat_id, "text": message, "parse_mode": "Markdown"}
    
    try:
        requests.post(url, data=payload)
    except Exception as e:
        print(f"Telegram failed: {e}")

        from fastapi import BackgroundTasks

@App.post("/api/v1/violations", status_code=201)
def create_violation(
    violation: ViolationCreate, 
    background_tasks: BackgroundTasks, 
    db: requests.Session = Depends(get_db)
):
    # 1. Save to Database
    db_violation = DBViolation(**violation.model_dump())
    db.add(db_violation)
    db.commit()
    db.refresh(db_violation)

    # 2. Get readable name for the alert
    v_name = VIOLATION_MAP.get(violation.violation_type, "Unknown")

    # 3. Add notification to background tasks
    # This prevents the AI inference from lagging while waiting for the SMS/Chat API
    background_tasks.add_task(send_telegram_msg, v_name, violation.confidence_score, violation.camera_id)
    # background_tasks.add_task(send_whatsapp_msg, v_name, violation.camera_id)

    return {"message": "Violation recorded and alerts sent"}
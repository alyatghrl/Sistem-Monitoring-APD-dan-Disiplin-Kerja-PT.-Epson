from fastapi import BackgroundTasks, Depends, APIRouter, HTTPException
from sqlalchemy.orm import Session
from database import DBViolation
from tests.main import VIOLATION_MAP, get_db
from datetime import datetime
import requests

router = APIRouter(tags=["Violations Notification"])

def send_telegram_msg(violation_name, confidence, camera_id):
    # Menggunakan Token dan Chat ID asli pilihan Alya yang sudah tervalidasi bener
    token = "8766052639:AAHjNaXTMMMJjcfDAaubPhXACiPSWUGEw3U"
    chat_id = "1565124447"
    
    message = (
        f"🚨 ALERT PELANGGARAN K3 (SISTEM BACKEND) 🚨\n\n"
        f"Jenis Pelanggaran: {violation_name}\n"
        f"Sumber Kamera: {camera_id}\n"
        f"Akurasi Deteksi: {confidence*100:.2f}%\n\n"
        f"⚠️ Data dan visual bukti telah aman tersimpan di Database Utama."
    )
    url = f"https://api.telegram.org/bot{token}/sendMessage"
    payload = {"chat_id": chat_id, "text": message}
    
    try:
        requests.post(url, json=payload, timeout=5)
        print(f"🚀 [BACKEND] Telegram alert '{violation_name}' sukses dikirim via Background Task.")
    except Exception as e:
        print(f"❌ [BACKEND] Telegram failed: {e}")

@router.post("/api/v1/violations", status_code=201)
def create_violation(
    data: dict, # <--- DIUBAH JADI DICT BIAR COCOK SAMA KIRIMAN KAMERA AI
    background_tasks: BackgroundTasks, 
    db: Session = Depends(get_db)
):
    try:
        v_type = data.get("violation_type")
        if v_type is None:
            v_list = data.get("violations", [])
            if "Helmet Missing" in v_list: v_type = 0
            elif "Vest Missing" in v_list: v_type = 1
            else: v_type = 2

        v_dir = (
            data.get("video_directory")
            or data.get("evidence_image")
            or "storage/clips/default.jpg"
        )

        # 1. Simpan ke database SQLite
        db_violation = DBViolation(
            timestamp       = data.get("timestamp", datetime.now().strftime("%Y-%m-%d %H:%M:%S")),
            violation_type  = int(v_type),
            confidence_score=float(data.get("confidence_score", 0.0)),
            video_directory = v_dir,
            camera_id       = data.get("camera_id", "CAM_UNKNOWN"),
        )
        db.add(db_violation)
        db.commit()
        db.refresh(db_violation)

        # 2. Ambil nama pelanggaran
        v_name = VIOLATION_MAP.get(int(v_type), "Unknown")

        # 3. Tugaskan kirim Telegram di latar belakang via Thread Pool (Aman & Stabil)
        background_tasks.add_task(send_telegram_msg, v_name, db_violation.confidence_score, db_violation.camera_id)

        return {"message": "Violation recorded and alerts sent via background task", "id": db_violation.id}
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=400, detail=f"Gagal simpan data: {e}")
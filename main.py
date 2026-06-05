from datetime import datetime, timedelta
import os
import logging
import bcrypt
import requests
from fastapi import FastAPI, Depends, HTTPException, WebSocket, WebSocketDisconnect, BackgroundTasks
from fastapi.security import OAuth2PasswordBearer
from fastapi.staticfiles import StaticFiles
from sqlalchemy.orm import Session
from jose import JWTError, jwt
from dotenv import load_dotenv
from typing import List

from database import DBUser, DBViolation, SessionLocal
from schema import (
    LoginRequest,
    ViolationResponse, ViolationUpdate, ViolationCreate,
    UserCreate, UserUpdate, UserResponse,
)

load_dotenv()

app = FastAPI(title="Sistem Monitoring K3")

SECRET_KEY                 = os.getenv("SECRET_KEY", "capstone-alya-2026")
ALGORITHM                  = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/auth/login")

VIOLATION_MAP = {
    0: "Tidak Memakai Helm",
    1: "Tidak Pakai Rompi",
    2: "Pelanggaran Lainnya",
}


# ==========================================
# NOTIFIKASI TELEGRAM (BACKGROUND TASK)
# ==========================================

def send_telegram_msg(violation_name: str, confidence: float, camera_id: str):
    """
    Fungsi internal untuk mengirim notifikasi ke Telegram pekerja.
    Berjalan di thread pool latar belakang agar tidak membebani performa API utama.
    """
    token = "8766052639:AAHjNaXTMMMJjcfDAaubPhXACiPSWUGew3U"
    chat_id = "6190691763"
    
    message = (
        f"🚨 ALERT PELANGGARAN K3 (SERVER BACKEND) 🚨\n\n"
        f"Jenis Pelanggaran: {violation_name}\n"
        f"Sumber Kamera: {camera_id}\n"
        f"Akurasi Deteksi: {confidence * 100:.2f}%\n\n"
        f"⚠️ Bukti visual pelanggaran telah aman tersimpan di Database Utama."
    )
    url = f"https://api.telegram.org/bot{token}/sendMessage"
    payload = {"chat_id": chat_id, "text": message}
    
    try:
        requests.post(url, json=payload, timeout=5)
        print(f"🚀 [BACKEND] Telegram alert '{violation_name}' berhasil dikirim via Background Task.")
    except Exception as e:
        print(f"❌ [BACKEND] Gagal mengirim notifikasi Telegram: {e}")


# ==========================================
# UTILS
# ==========================================

def verify_password(plain: str, hashed: str) -> bool:
    try:
        return bcrypt.checkpw(plain.encode("utf-8"), hashed.encode("utf-8"))
    except Exception as e:
        print(f"Auth Error: {e}")
        return False

def hash_password(plain: str) -> str:
    return bcrypt.hashpw(plain.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')

def create_access_token(data: dict) -> str:
    to_encode = data.copy()
    to_encode["exp"] = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


# ==========================================
# STATIC FILE MOUNTS
# ==========================================

os.makedirs("storage/clips", exist_ok=True)
os.makedirs("storage/live",  exist_ok=True)

app.mount("/clips", StaticFiles(directory="storage/clips"), name="clips")
app.mount("/live",  StaticFiles(directory="storage/live"),  name="live")


# ==========================================
# WEBSOCKET MANAGER
# ==========================================

class ConnectionManager:
    def __init__(self):
        self.active_connections: list[WebSocket] = []

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)

    def disconnect(self, websocket: WebSocket):
        self.active_connections.remove(websocket)

    async def broadcast(self, message: str):
        for conn in self.active_connections:
            await conn.send_text(message)

manager = ConnectionManager()

@app.post("/api/v1/auth/login")
def login(data: LoginRequest, db: Session = Depends(get_db)):
    user = db.query(DBUser).filter(DBUser.username == data.username).first()
    if not user:
        raise HTTPException(status_code=401, detail="User tidak ditemukan")
    if not verify_password(data.password, user.hashed_password):
        raise HTTPException(status_code=401, detail="Password salah")

    token = create_access_token({
        "sub"        : user.username,
        "permissions": user.permissions,
        "role"       : user.role,
    })
    return {
        "access_token": token,
        "token_type"  : "bearer",
        "user": {
            "name"       : user.full_name,
            "role"       : user.role,
            "permissions": user.permissions,
        },
    }


@app.post("/api/v1/violations", status_code=201)
def create_violation(
    data: dict, 
    background_tasks: BackgroundTasks, 
    db: Session = Depends(get_db)
):
    """
    Endpoint Synchronous (def) agar background tasks yang menggunakan 
    library blocking (requests) bisa tereksekusi sempurna tanpa terputus.
    """
    try:
        v_type = data.get("violation_type")
        if v_type is None:
            v_list = data.get("violations", [])
            if "Helmet Missing" in v_list:
                v_type = 0
            elif "Vest Missing" in v_list:
                v_type = 1
            else:
                v_type = 2

        v_dir = (
            data.get("video_directory")
            or data.get("evidence_image")
            or "storage/clips/default.jpg"
        )

        # 1. Simpan data pelanggaran ke Database SQLite
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
        
        # 2. Ambil nama string bahasa manusia dari map
        v_name = VIOLATION_MAP.get(int(v_type), "Unknown")
        
        # 3. Pemicu Tugas Latar Belakang (Kirim Notifikasi Bot Telegram)
        background_tasks.add_task(send_telegram_msg, v_name, db_violation.confidence_score, db_violation.camera_id)

        # 4. Memicu WebSocket broadcast ke Dashboard via background task thread pool
        background_tasks.add_task(manager.broadcast, "update")
        
        return {"message": "success", "id": db_violation.id}
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=400, detail=f"Gagal simpan data: {e}")


@app.get("/api/v1/violations/logs", response_model=ViolationResponse)
def get_logs(db: Session = Depends(get_db)):
    violations = db.query(DBViolation).order_by(DBViolation.timestamp.desc()).all()
    logs = []
    for v in violations:
        filename = os.path.basename(v.video_directory) if v.video_directory else "default.jpg"
        logs.append({
            "id"              : v.id,
            "timestamp"       : v.timestamp,
            "violation_name"  : VIOLATION_MAP.get(v.violation_type, "Unknown"),
            "camera_id"       : v.camera_id,
            "confidence_score": v.confidence_score,
            "status"          : bool(v.status),
            "notes"           : v.notes or "",
            "video_url"       : f"http://localhost:8000/clips/{filename}",
        })
    return {"status": "success", "data_count": len(logs), "logs": logs}


@app.put("/api/v1/violations/{violation_id}")
def update_violation(violation_id: int, data: ViolationUpdate, db: Session = Depends(get_db)):
    v = db.query(DBViolation).filter(DBViolation.id == violation_id).first()
    if not v:
        raise HTTPException(status_code=404, detail="Data tidak ditemukan")
    if data.status is not None:
        v.status = data.status
    if data.notes is not None:
        v.notes = data.notes
    db.commit()
    return {"message": "Update berhasil"}


@app.get("/api/v1/violations/status")
def get_status(db: Session = Depends(get_db)):
    latest = db.query(DBViolation).order_by(DBViolation.id.desc()).first()
    return {"version": str(latest.id) if latest else "empty"}

@app.get("/api/v1/users", response_model=List[UserResponse])
def list_users(db: Session = Depends(get_db)):
    return db.query(DBUser).order_by(DBUser.id).all()


@app.get("/api/v1/users/{user_id}", response_model=UserResponse)
def get_user(user_id: int, db: Session = Depends(get_db)):
    user = db.query(DBUser).filter(DBUser.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User tidak ditemukan")
    return user


@app.post("/api/v1/users", response_model=UserResponse, status_code=201)
def create_user(data: UserCreate, db: Session = Depends(get_db)):
    if db.query(DBUser).filter(DBUser.username == data.username).first():
        raise HTTPException(status_code=409, detail="Username sudah digunakan")
    new_user = DBUser(
        username       =data.username,
        hashed_password=hash_password(data.password),
        full_name      =data.full_name,
        role           =data.role,
        permissions    =data.permissions,
    )
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    return new_user


@app.put("/api/v1/users/{user_id}", response_model=UserResponse)
def update_user(user_id: int, data: UserUpdate, db: Session = Depends(get_db)):
    user = db.query(DBUser).filter(DBUser.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User tidak ditemukan")
    if data.full_name   is not None: user.full_name    = data.full_name
    if data.role        is not None: user.role         = data.role
    if data.permissions is not None: user.permissions  = data.permissions
    if data.password    is not None: user.hashed_password = hash_password(data.password)
    db.commit()
    db.refresh(user)
    return user


@app.delete("/api/v1/users/{user_id}", status_code=204)
def delete_user(user_id: int, db: Session = Depends(get_db)):
    user = db.query(DBUser).filter(DBUser.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User tidak ditemukan")
    db.delete(user)
    db.commit()

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await manager.connect(websocket)
    try:
        while True:
            await websocket.receive_text()
    except WebSocketDisconnect:
        manager.disconnect(websocket)

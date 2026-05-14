from datetime import datetime, timedelta
import os
import logging
import bcrypt  # Digunakan langsung untuk stabilitas login di Windows
from fastapi import FastAPI, Depends, HTTPException, WebSocket, WebSocketDisconnect
from fastapi.security import OAuth2PasswordBearer
from fastapi.staticfiles import StaticFiles
from sqlalchemy.orm import Session
from jose import JWTError, jwt
from passlib.context import CryptContext
from dotenv import load_dotenv

# Import internal
from database import DBUser, DBViolation, SessionLocal
from tests.schema import LoginRequest, ViolationResponse

load_dotenv()

# Konfigurasi Logging
logging.getLogger('passlib').setLevel(logging.ERROR)

app = FastAPI(title="Sistem Monitoring K3 - Alya")

# Ambil Secret Key dari .env
SECRET_KEY = os.getenv("SECRET_KEY", "capstone-alya-2026")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/auth/login")

# --- AUTHENTICATION UTILS ---

def verify_password(plain_password, hashed_password):
    """Verifikasi password menggunakan bcrypt langsung untuk stabilitas"""
    try:
        return bcrypt.checkpw(
            plain_password.encode('utf-8'), 
            hashed_password.encode('utf-8')
        )
    except Exception as e:
        print(f"Auth Error: {e}")
        return False

def create_access_token(data: dict):
    to_encode = data.copy()
    expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# --- FOLDER SETUP ---
if not os.path.exists("storage/clips"):
    os.makedirs("storage/clips", exist_ok=True)

# Mounting folder agar gambar bisa diakses via URL http://localhost:8000/clips/nama_file.jpg
app.mount("/clips", StaticFiles(directory="storage/clips"), name="clips")

# --- REAL-TIME NOTIFICATION (WEBSOCKET) ---
class ConnectionManager:
    def __init__(self):
        self.active_connections: list[WebSocket] = []
    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)
    def disconnect(self, websocket: WebSocket):
        self.active_connections.remove(websocket)
    async def broadcast(self, message: str):
        for connection in self.active_connections:
            await connection.send_text(message)

manager = ConnectionManager()

# Mapping Tipe Pelanggaran sesuai Capstone Lya
VIOLATION_MAP = {
    0: "Tidak Memakai Helm",
    1: "Tidak Pakai Rompi",
    2: "Pelanggaran Lainnya"
}

# --- API ENDPOINTS ---

@app.post("/api/v1/violations", status_code=201)
async def create_violation(data: dict, db: Session = Depends(get_db)):
    """Menerima data deteksi dari skrip AI Alya secara fleksibel"""
    try:
        # Menentukan Tipe Pelanggaran
        v_type = data.get("violation_type")
        if v_type is None:
            v_list = data.get("violations", [])
            if "Helmet Missing" in v_list: v_type = 0
            elif "Vest Missing" in v_list: v_type = 1
            else: v_type = 2

        # Menentukan Lokasi Gambar Bukti
        v_dir = data.get("video_directory") or data.get("evidence_image") or "storage/clips/default.jpg"

        # Simpan ke Database (SQLite)
        db_violation = DBViolation(
            timestamp=data.get("timestamp", datetime.now().strftime("%Y-%m-%d %H:%M:%S")),
            violation_type=int(v_type),
            confidence_score=float(data.get("confidence_score", 0.0)),
            video_directory=v_dir,
            camera_id=data.get("camera_id", "CAM_ALYA_01")
        )

        db.add(db_violation)
        db.commit()
        
        # Kirim sinyal update ke Dashboard
        await manager.broadcast("update")
        
        return {"message": "success", "id": db_violation.id}
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=400, detail=f"Gagal simpan data: {str(e)}")

@app.get("/api/v1/violations/logs", response_model=ViolationResponse)
def get_logs(db: Session = Depends(get_db)):
    """Mengambil riwayat pelanggaran untuk Dashboard"""
    violations = db.query(DBViolation).order_by(DBViolation.timestamp.desc()).all()
    logs = []
    for v in violations:
        filename = os.path.basename(v.video_directory) if v.video_directory else "no_video.jpg"
        logs.append({
            "id": str(v.id),
            "timestamp": v.timestamp,
            "violation_name": VIOLATION_MAP.get(v.violation_type, "Unknown"),
            "video_url": f"http://localhost:8000/clips/{filename}"
        })
    return {"status": "success", "data_count": len(logs), "logs": logs}

@app.post("/api/v1/auth/login")
def login(data: LoginRequest, db: Session = Depends(get_db)):
    """Login User dan mengirimkan data profil lengkap ke Dashboard"""
    user = db.query(DBUser).filter(DBUser.username == data.username).first()
    
    if not user:
        raise HTTPException(status_code=401, detail="User tidak ditemukan")
    
    if not verify_password(data.password, user.hashed_password):
        raise HTTPException(status_code=401, detail="Password salah")
    
    token = create_access_token({
        "sub": user.username, 
        "permissions": user.permissions, 
        "role": user.role
    })
    
    # Respon ini harus lengkap agar dashboard.py tidak KeyError
    return {
        "access_token": token, 
        "token_type": "bearer", 
        "user": {
            "name": user.full_name, 
            "role": user.role,
            "permissions": user.permissions  # KRUSIAL: Agar dashboard tidak error
        }
    }

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await manager.connect(websocket)
    try:
        while True:
            await websocket.receive_text()
    except WebSocketDisconnect:
        manager.disconnect(websocket)

@app.get("/api/v1/violations/status")
def get_status(db: Session = Depends(get_db)):
    latest = db.query(DBViolation).order_by(DBViolation.id.desc()).first()
    return {"version": f"{latest.id}" if latest else "empty"}
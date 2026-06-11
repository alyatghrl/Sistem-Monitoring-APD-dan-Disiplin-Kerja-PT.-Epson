import cv2
import numpy as np
import onnxruntime as ort
import os
import time
import requests
import threading  
from datetime import datetime
from tests.config import API_BASE_URL

API_URL  = f"{API_BASE_URL}/api/v1/violations"
SAVE_DIR = "storage/clips"   # direktori bukti foto pelanggaran
LIVE_DIR = "storage/live"    # direktori buffer live feed dashboard

os.makedirs(SAVE_DIR, exist_ok=True)
os.makedirs(LIVE_DIR, exist_ok=True)

# Path model ONNX Capstone Project kamu
MODEL_PATH = r"E:\Semester-6\Capstone Project\runs\Vision Models\100 Epochs with early stopping\best.onnx"

# --- CONFIG BOT TELEGRAM (BYPASS LANGSUNG) ---
TELEGRAM_TOKEN = "8766052639:AAHjNaXTMMMJjcfDAaubPhXACiPSWUGEw3U"
TELEGRAM_CHAT_ID = "1565124447"

last_telegram_time: dict[str, float] = {}
TELEGRAM_COOLDOWN = 10.0  # Jeda 10 detik biar gak spam chat ke HP

class_names = [
    "helmet", "gloves", "vest", "boots", "goggles",
    "none", "person", "no_helmet", "no_goggle", "no_gloves", "no_boots"
]

CONF_THRESHOLD = 0.45  
IOS_THRESHOLD  = 0.30
SAVE_COOLDOWN  = 5.0   

session    = ort.InferenceSession(MODEL_PATH)
input_name = session.get_inputs()[0].name

def send_to_api(payload: dict) -> None:
    """Kirim data pelanggaran ke FastAPI backend agar masuk tabel Streamlit."""
    try:
        response = requests.post(API_URL, json=payload, timeout=2.0)
        if response.status_code == 201:
            print(f"✅ [API] Data sukses masuk Dashboard Backend.")
    except requests.exceptions.RequestException:
        print("⚠️ [API] Gagal terhubung ke server backend.")

def send_telegram_photo_worker(violation_name, camera_id, confidence, image_path):
    """Fungsi pekerja di background thread untuk mengirim media gambar."""
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendPhoto"
    message = (
        f"🚨 ALERT PELANGGARAN K3 🚨\n\n"
        f"Jenis Pelanggaran: {violation_name}\n"
        f"Sumber Kamera: {camera_id}\n"
        f"Akurasi Deteksi: {confidence * 100:.2f}%\n"
        f"Waktu Kejadian: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n"
        f"⚠️ Notifikasi real-time + Bukti Foto terkirim sukses!"
    )
    try:
        with open(image_path, 'rb') as photo_file:
            payload = {"chat_id": TELEGRAM_CHAT_ID, "caption": message}
            files   = {"photo": photo_file}
            requests.post(url, data=payload, files=files, timeout=10)
        print(f"🚀 [TELEGRAM PHOTO] Lampiran bukti foto sukses terkirim ke Telegram HP!")
    except Exception as e:
        print(f"❌ [TELEGRAM PHOTO] Gagal kirim lampiran Telegram: {e}")

def send_telegram_bypass(violation_name, camera_id, confidence, image_path):
    """Fungsi utama bypass yang bertugas melakukan split task ke background thread."""
    threading.Thread(
        target=send_telegram_photo_worker,
        args=(violation_name, camera_id, confidence, image_path),
        daemon=True
    ).start()

def ios(small_box: list, big_box: list) -> float:
    """Intersection over Small-box area — mengecek apakah APD berada di ROI tubuh."""
    ix1 = max(small_box[0], big_box[0])
    iy1 = max(small_box[1], big_box[1])
    ix2 = min(small_box[2], big_box[2])
    iy2 = min(small_box[3], big_box[3])
    
    inter      = max(0, ix2 - ix1) * max(0, iy2 - iy1)
    area_small = (small_box[2] - small_box[0]) * (small_box[3] - small_box[1])
    return inter / (area_small + 1e-6)

def nms(detections: list, iou_threshold: float = 0.45) -> list:
    """Non-Maximum Suppression sederhana."""
    if not detections: return []
    dets   = np.array([d[:5] for d in detections], dtype=float)
    x1, y1, x2, y2, scores = dets[:, 0], dets[:, 1], dets[:, 2], dets[:, 3], dets[:, 4]
    areas  = (x2 - x1) * (y2 - y1)
    order  = scores.argsort()[::-1]
    keep   = []
    while order.size > 0:
        i = order[0]
        keep.append(detections[int(i)])
        xx1 = np.maximum(x1[i], x1[order[1:]])
        yy1 = np.maximum(y1[i], y1[order[1:]])
        xx2 = np.minimum(x2[i], x2[order[1:]])
        yy2 = np.minimum(y2[i], y2[order[1:]])
        w   = np.maximum(0.0, xx2 - xx1)
        h   = np.maximum(0.0, yy2 - yy1)
        ovr = (w * h) / (areas[i] + areas[order[1:]] - (w * h) + 1e-6)
        order = order[np.where(ovr <= iou_threshold)[0] + 1]
    return keep

def preprocess(frame: np.ndarray):
    """Resize + pad frame ke 640x640 dan normalisasi ke float32."""
    h0, w0 = frame.shape[:2]
    img     = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
    scale   = min(640 / w0, 640 / h0)
    nw, nh  = int(w0 * scale), int(h0 * scale)
    dw, dh  = (640 - nw) // 2, (640 - nh) // 2
    img_padded = np.full((640, 640, 3), 114, dtype=np.uint8)
    img_padded[dh:dh + nh, dw:dw + nw] = cv2.resize(img, (nw, nh))
    img_input = (img_padded / 255.0).transpose(2, 0, 1)
    img_input = np.expand_dims(img_input, 0).astype(np.float32)
    return img_input, scale, dw, dh

def postprocess(outputs, frame: np.ndarray, scale: float, dw: int, dh: int):
    """Logika murni evaluasi kelengkapan APD Helm & Rompi proyek."""
    h_img, w_img = frame.shape[:2]
    preds        = outputs[0][0]
    dets_by_label: dict[str, list] = {}

    for pred in preds:
        x1_p, y1_p, x2_p, y2_p, conf, cls_id = pred
        if conf < CONF_THRESHOLD: continue
        x1 = int(np.clip((x1_p - dw) / scale, 0, w_img))
        y1 = int(np.clip((y1_p - dh) / scale, 0, h_img))
        x2 = int(np.clip((x2_p - dw) / scale, 0, w_img))
        y2 = int(np.clip((y2_p - dh) / scale, 0, h_img))
        label = class_names[int(cls_id)]
        if label in ("person", "helmet", "vest"):
            dets_by_label.setdefault(label, []).append([x1, y1, x2, y2, float(conf)])

    persons = nms(dets_by_label.get("person", []))
    helmets = nms(dets_by_label.get("helmet", []))
    vests   = nms(dets_by_label.get("vest",   []))

    any_violation = False
    violation_id  = 2          
    status_h      = "OK"
    status_v      = "OK"
    person_confs  = []

    for p in persons:
        px1, py1, px2, py2, p_conf = p[:4] + [p[4]]
        person_confs.append(p_conf)

        head_roi = [px1, py1,                           px2, py1 + int((py2 - py1) * 0.35)]
        body_roi = [px1, py1 + int((py2 - py1) * 0.20), px2, py2]

        has_h = any(ios(h[:4], head_roi) > IOS_THRESHOLD for h in helmets)
        has_v = any(ios(v[:4], body_roi) > IOS_THRESHOLD for v in vests)

        if not has_h:
            status_h      = "NOT OK"
            any_violation = True
            violation_id  = 0           

        if not has_v:
            status_v      = "NOT OK"
            any_violation = True
            if not has_h: violation_id = 2        
            else: violation_id = 1        

        cv2.rectangle(frame, (px1, py1), (px2, py2), (0, 0, 255), 2)
        cv2.putText(frame, f"person {p_conf:.2f}", (px1, py1 - 5), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 0, 255), 2)

    for h in helmets: cv2.rectangle(frame, (h[0], h[1]), (h[2], h[3]), (0, 255, 255), 2)
    for v in vests: cv2.rectangle(frame, (v[0], v[1]), (v[2], v[3]), (0, 255, 0), 2)

    cv2.putText(frame, f"HELMET : {status_h}", (w_img - 280,  50), cv2.FONT_HERSHEY_SIMPLEX, 0.9, (0, 255, 255), 3)
    cv2.putText(frame, f"VEST   : {status_v}", (w_img - 280, 100), cv2.FONT_HERSHEY_SIMPLEX, 0.9, (0, 255,   0), 3)

    max_conf = max(person_confs) if person_confs else 0.0
    return frame, any_violation, violation_id, max_conf

os.system('cls' if os.name == 'nt' else 'clear')
print("=" * 60)
print("       SISTEM MONITORING K3 & DISIPLIN KERJA AI       ")
print("=" * 60)
print(" Silakan pilih perangkat kamera yang ingin digunakan:")
print(" [1] Webcam Bawaan Laptop Saja (Kamera 1)")
print(" [2] DroidCam HP Saja (Kamera 2)")
print(" [3] Gunakan Keduanya Sekaligus (Multi-Kamera)")
print("=" * 60)

pilihan = input(" Masukkan pilihan Anda (1/2/3): ").strip()

cameras = {}
if pilihan == "1":
    cameras = {"CAM_WEBCAM": 0}
elif pilihan == "2":
    cameras = {"CAM_DROIDCAM": 1}
elif pilihan == "3":
    cameras = {"CAM_WEBCAM": 0, "CAM_DROIDCAM": 1}
else:
    print("⚠️ Pilihan tidak valid! Otomatis menggunakan Webcam Laptop.")
    cameras = {"CAM_WEBCAM": 0}

caps: dict[str, cv2.VideoCapture] = {}
last_save_time: dict[str, float] = {}

print("\n🔍 Memulai inisialisasi perangkat kamera pilihan Anda...")
for cam_name, cam_source in cameras.items():
    cap = cv2.VideoCapture(cam_source)
    time.sleep(0.5) 
    if cap.isOpened():
        ret, test_frame = cap.read()
        if ret:
            caps[cam_name] = cap
            last_save_time[cam_name] = 0.0
            print(f"📡 [CONNECTED] Perangkat {cam_name} terhubung aktif.")
        else:
            cap.release()

if not caps:
    print("❌ [ERROR] Perangkat kamera pilihan gagal dibuka! Pastikan DroidCam sudah klik START.")
    exit()

print(f"🚀 Sistem Berhasil Jalan Menggunakan {len(caps)} Kamera.\n")

while True:
    current_time = time.time()
    for cam_name, cap in list(caps.items()):
        ret, frame = cap.read()
        if not ret: 
            print(f"⚠️ [WARNING] Kehilangan sinyal dari {cam_name}.")
            cap.release()
            del caps[cam_name]
            continue

        input_tensor, scale, dw, dh = preprocess(frame)
        outputs = session.run(None, {input_name: input_tensor})
        annotated_frame, any_violation, violation_id, max_conf = postprocess(outputs, frame, scale, dw, dh)

        live_path = os.path.join(LIVE_DIR, f"{cam_name}.jpg")
        cv2.imwrite(live_path, annotated_frame)

        cooldown_passed = (current_time - last_save_time[cam_name]) > SAVE_COOLDOWN
        if any_violation and cooldown_passed:
            file_ts = datetime.now().strftime("%Y%m%d_%H%M%S")
            db_ts   = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            file_name = f"{cam_name}_{file_ts}.jpg"
            filepath  = os.path.join(SAVE_DIR, file_name)
            cv2.imwrite(filepath, annotated_frame)

            payload = {
                "timestamp"       : db_ts,
                "violation_type"  : violation_id,
                "confidence_score": round(float(max_conf), 4),
                "video_directory" : f"storage/clips/{file_name}",
                "camera_id"       : cam_name,
            }

            # 1. Kirim data string path ke database backend SQLite
            send_to_api(payload)
            
            # 2. Kirim notifikasi real-time beserta foto fisik via Background Thread
            v_maps = {0: "Tidak Memakai Helm", 1: "Tidak Pakai Rompi", 2: "Pelanggaran Ganda"}
            v_name = v_maps.get(violation_id, "Pelanggaran K3")
            
            if cam_name not in last_telegram_time or (current_time - last_telegram_time[cam_name] > TELEGRAM_COOLDOWN):
                # REVISI FINAL: Sekarang ikut menyertakan 'filepath' lokasi gambar untuk dikirim ke Telegram!
                send_telegram_bypass(v_name, cam_name, float(max_conf), filepath)
                last_telegram_time[cam_name] = current_time

            last_save_time[cam_name] = current_time

        cv2.imshow(f"Feed: {cam_name}", annotated_frame)

    if cv2.waitKey(1) & 0xFF == ord("q"): break

for cap in caps.values(): cap.release()
cv2.destroyAllWindows()

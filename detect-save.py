import cv2
import numpy as np
import onnxruntime as ort
import sys
import os
import time
import json  
from datetime import datetime

# =========================
# PATH - SESUAIKAN INI
# =========================
MODEL_PATH = r"E:\Semester-6\Capstone Project\runs\Vision Models\100 Epochs with early stopping\best.onnx"

# =========================
# BIKIN FOLDER BUKTI OTOMATIS
# =========================
DIR_LENGKAP = "bukti/lengkap"
DIR_PELANGGARAN = "bukti/pelanggaran"
os.makedirs(DIR_LENGKAP, exist_ok=True)
os.makedirs(DIR_PELANGGARAN, exist_ok=True)

# =========================
# CLASS MAP & THRESHOLD
# =========================
class_names = [
    "helmet", "gloves", "vest", "boots", "goggles",
    "none", "person", "no_helmet", "no_goggle", "no_gloves", "no_boots"
]
PERSON_IDX = class_names.index("person")   
HELMET_IDX = class_names.index("helmet")   
VEST_IDX   = class_names.index("vest")     

CONF_THRESHOLD  = 0.25   
IOS_THRESHOLD   = 0.30   

COLORS = {
    "person": (0, 0, 255),    # Merah
    "helmet": (0, 255, 255),  # Kuning
    "vest":   (0, 255, 0),    # Hijau
}
DEFAULT_COLOR = (200, 200, 200)

# =========================
# LOAD MODEL
# =========================
session    = ort.InferenceSession(MODEL_PATH)
input_name = session.get_inputs()[0].name

# =========================
# HELPER FUNCTIONS
# =========================
def ios(small_box, big_box):
    ix1 = max(small_box[0], big_box[0])
    iy1 = max(small_box[1], big_box[1])
    ix2 = min(small_box[2], big_box[2])
    iy2 = min(small_box[3], big_box[3])
    inter = max(0, ix2 - ix1) * max(0, iy2 - iy1)
    area_small = (small_box[2] - small_box[0]) * (small_box[3] - small_box[1])
    return inter / (area_small + 1e-6)

def nms(detections, iou_threshold=0.45):
    if not detections: return []
    dets = np.array([d[:5] for d in detections], dtype=float)
    x1, y1, x2, y2, scores = dets[:, 0], dets[:, 1], dets[:, 2], dets[:, 3], dets[:, 4]
    areas = (x2 - x1) * (y2 - y1)
    order = scores.argsort()[::-1]
    keep = []
    while order.size > 0:
        i = order[0]
        keep.append(detections[int(i)])
        xx1 = np.maximum(x1[i], x1[order[1:]])
        yy1 = np.maximum(y1[i], y1[order[1:]])
        xx2 = np.minimum(x2[i], x2[order[1:]])
        yy2 = np.minimum(y2[i], y2[order[1:]])
        w = np.maximum(0.0, xx2 - xx1)
        h = np.maximum(0.0, yy2 - yy1)
        inter = w * h
        iou = inter / (areas[i] + areas[order[1:]] - inter + 1e-6)
        inds = np.where(iou <= iou_threshold)[0]
        order = order[inds + 1]
    return keep

def preprocess(frame):
    h0, w0 = frame.shape[:2]
    img = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
    scale = min(640 / w0, 640 / h0)
    nw, nh = int(w0 * scale), int(h0 * scale)
    img_padded = np.full((640, 640, 3), 114, dtype=np.uint8)
    dw, dh = (640 - nw) // 2, (640 - nh) // 2
    img_padded[dh:dh + nh, dw:dw + nw] = cv2.resize(img, (nw, nh))
    img_input = (img_padded / 255.0).transpose(2, 0, 1)
    img_input = np.expand_dims(img_input, 0).astype(np.float32)
    return img_input, scale, dw, dh

# =========================
# POSTPROCESS
# =========================
def postprocess(outputs, frame, scale, dw, dh):
    h_img, w_img = frame.shape[:2]
    preds = outputs[0][0]   

    detections_by_label = {}
    for pred in preds:
        x1_p, y1_p, x2_p, y2_p, conf, cls_raw = pred
        cls_id = int(cls_raw)
        if conf < CONF_THRESHOLD: continue
        if cls_id not in {PERSON_IDX, HELMET_IDX, VEST_IDX}: continue

        x1 = int(np.clip((x1_p - dw) / scale, 0, w_img))
        y1 = int(np.clip((y1_p - dh) / scale, 0, h_img))
        x2 = int(np.clip((x2_p - dw) / scale, 0, w_img))
        y2 = int(np.clip((y2_p - dh) / scale, 0, h_img))

        label = class_names[cls_id]
        color = COLORS.get(label, DEFAULT_COLOR)
        detections_by_label.setdefault(label, []).append([x1, y1, x2, y2, float(conf), cls_id, label, color])

    persons, helmets, vests, final_detections = [], [], [], []
    for label, dets in detections_by_label.items():
        kept = nms(dets, iou_threshold=0.45)
        final_detections.extend(kept)
        if label == "person": persons = kept
        elif label == "helmet": helmets = kept
        elif label == "vest": vests = kept

    for x1, y1, x2, y2, conf, cls_id, label, color in final_detections:
        cv2.rectangle(frame, (x1, y1), (x2, y2), color, 2)
        cv2.putText(frame, f"{label} {conf:.2f}", (x1, max(y1 - 10, 15)),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.7, color, 2)

    person_detected = len(persons) > 0
    helmet_global_ok = True if person_detected else False
    vest_global_ok = True if person_detected else False
    
    violation_list = []

    for pentry in persons:
        px1, py1, px2, py2 = pentry[:4]
        tinggi_person = py2 - py1
        # Logika Anatomi (Head & Body)
        head_box = [px1, py1, px2, py1 + (tinggi_person * 0.35)]
        body_box = [px1, py1 + (tinggi_person * 0.20), px2, py2]

        has_helmet = any(ios(h[:4], head_box) > IOS_THRESHOLD for h in helmets)
        has_vest = any(ios(v[:4], body_box) > IOS_THRESHOLD for v in vests)

        if not has_helmet: 
            helmet_global_ok = False
            violation_list.append("Helmet Missing")
        if not has_vest: 
            vest_global_ok = False
            violation_list.append("Vest Missing")

    is_compliant = helmet_global_ok and vest_global_ok
    text_x = w_img - 220  
    cv2.putText(frame, "HELMET : OK" if helmet_global_ok else "HELMET : NOT OK", (text_x, 40), cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 255, 255) if helmet_global_ok else (0, 0, 255), 2)
    cv2.putText(frame, "VEST : OK" if vest_global_ok else "VEST : NOT OK", (text_x, 80), cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 255, 0) if vest_global_ok else (0, 0, 255), 2)

    return frame, person_detected, is_compliant, len(persons), list(set(violation_list))

# =========================
# MAIN - WEBCAM DETECTION
# =========================
cap = cv2.VideoCapture(0)
if not cap.isOpened():
    print("Error: Could not open webcam.")
    sys.exit(1)

print("Starting webcam detection. Press 'q' to quit.")

last_save_time = 0
SAVE_COOLDOWN = 5.0  

while True:
    ret, frame = cap.read()
    if not ret: break

    input_tensor, scale, dw, dh = preprocess(frame)
    outputs = session.run(None, {input_name: input_tensor})
    
    result, person_detected, is_compliant, num_people, violations = postprocess(outputs, frame, scale, dw, dh)

    # =========================
    # LOGIKA SAVE BUKTI & JSON
    # =========================
    current_time = time.time()
    
    if person_detected and (current_time - last_save_time > SAVE_COOLDOWN):
        now = datetime.now()
        timestamp_str = now.strftime("%Y-%m-%d %H:%M:%S")
        file_timestamp = now.strftime("%Y%m%d_%H%M%S")
        
        status_str = "OK" if is_compliant else "NOT OK"
        filename = f"{status_str}_{file_timestamp}.jpg"
        save_path = os.path.join(DIR_LENGKAP if is_compliant else DIR_PELANGGARAN, filename)
        
        # 1. Simpan Gambar Fisik
        cv2.imwrite(save_path, result)

        # 2. Susun Data JSON
        data_json = {
            "timestamp": timestamp_str,
            "status": status_str,
            "location": "Project Site A",
            "total_person": num_people,
            "violations": violations if not is_compliant else None,
            "evidence_image": filename
        }

        # 3. CETAK JSON KE TERMINAL
        print("\n--- NEW DETECTION DATA ---")
        print(json.dumps(data_json, indent=4))
        print(f"Bukti tersimpan di: {save_path}")
        print("--------------------------\n")
        
        last_save_time = current_time

    cv2.imshow('PPE Detection', result)
    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

cap.release()
cv2.destroyAllWindows()
print("Webcam detection stopped.")
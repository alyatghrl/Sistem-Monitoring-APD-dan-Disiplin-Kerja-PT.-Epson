# Sistem-Monitoring-APD-dan-Disiplin-Kerja-PT.-Epson
Proyek ini adalah sistem pemantauan Alat Pelindung Diri (APD) berbasis Computer Vision. Sistem dirancang untuk mendeteksi secara otomatis kepatuhan penggunaan Alat Pelindung Diri (APD) pada lingkungan kerja industri. Fokus utama deteksi meliputi Helm Keselamatan (Safety Helmet) dan Rompi Kerja (Safety Vest).

## ✨ Fitur  Sistem
* **Core AI Object Detection (YOLOv8 ONNX):** Inferensi model deteksi objek menggunakan arsitektur ONNX Runtime berlatensi rendah dengan *Confidence Threshold* optimal (0.45).
* **Anatomy-Based IoU Logic:** Algoritma cerdas mengevaluasi posisi APD berdasarkan area anatomi tubuh manusia (ROI Kepala & ROI Tubuh) untuk menghindari salah deteksi (*False Positive*).
* **Menu Interaktif Pemilihan Kamera:** Mekanisme pemilihan *video stream input* secara dinamis lewat terminal (Webcam Internal, DroidCam HP, atau Multi-Kamera sekaligus).
* **Multi-Threaded Telegram Photo Alerts:** Pengiriman pesan darurat *real-time* ke HP pengawas lengkap dengan **lampiran foto fisik bukti pelanggaran** menggunakan background thread (*anti-stuttering* pada loop kamera utama).
* **Robust Backend API (FastAPI & Uvicorn):** Sistem penyimpanan metadata pelanggaran terstruktur berbasis JSON yang terintegrasi langsung dengan database relasional **SQLite**.
* **Role-Based Access Control (RBAC):** Otentikasi keamanan login multi-pengguna yang memisahkan hak akses antarmuka antara **Administrator** (akses penuh & manajemen user) dan **Supervisor** (akses log lapangan).
* **Interactive Table Dashboard (Auto-Save):** Panel rekapitulasi data menggunakan `st.data_editor` yang mendukung pencentangan status "Ditangani?" dan pengisian catatan lapangan dengan fitur penyimpanan otomatis (*Auto-Save*) ke database.
* **Cetak Laporan Instan (PDF/CSV):** Fungsionalitas ekspor rekapitulasi riwayat data pelanggaran K3 secara fisik dalam format dokumen `.csv` dan `.pdf` (`fpdf2`).

Langkah-Langkah:
1. Instalasi Dependensi:
   pip install fastapi uvicorn streamlit sqlalchemy opencv-python numpy onnxruntime requests python-jose python-dotenv bcrypt passlib

2. Jalankan Server Backend (FastAPI):
   uvicorn main:app --host localhost --port 8000 --reload
   
4. Jalankan Dasbor Monitoring (Streamlit):
   streamlit run dashboard.py
   
6. Jalankan Sistem Deteksi:
   python detect-save.py
   

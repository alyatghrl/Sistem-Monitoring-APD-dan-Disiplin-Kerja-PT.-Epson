# Sistem-Monitoring-APD-dan-Disiplin-Kerja-PT.-Epson
Proyek ini adalah sistem pemantauan Alat Pelindung Diri (APD) berbasis Computer Vision. Sistem dirancang untuk mendeteksi secara otomatis kepatuhan penggunaan Alat Pelindung Diri (APD) pada lingkungan kerja industri. Fokus utama deteksi meliputi Helm Keselamatan (Safety Helmet) dan Rompi Kerja (Safety Vest).

Langkah-Langkah:
1. Instalasi Dependensi
   pip install fastapi uvicorn streamlit sqlalchemy opencv-python numpy onnxruntime requests python-jose python-dotenv bcrypt passlib

2. Jalankan Server Backend (FastAPI)
   uvicorn main:app --host localhost --port 8000 --reload
   
4. Jalankan Dasbor Monitoring (Streamlit)
   streamlit run dashboard.py
   
6. Jalankan Sistem Deteksi
   python detect-save.py
   

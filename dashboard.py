import streamlit as st
import os
import requests
from streamlit_autorefresh import st_autorefresh

st.set_page_config(layout="wide", page_title="K3 Safety Compliance")

st_autorefresh(interval=3000, key="datacheck") # Diubah ke 3 detik agar lebih stabil

st.title("🛡️ K3 Safety Compliance Log")

API_BASE = "http://127.0.0.1:8000/api/v1/violations"
API_LOGIN = "http://127.0.0.1:8000/api/v1/auth/login"
LOGS_URL = f"{API_BASE}/logs"
STATUS_URL = f"{API_BASE}/status"

# --- INIT STATE ---
if "data" not in st.session_state:
    st.session_state.data = []
if "status_raw" not in st.session_state:
    st.session_state.status_raw = "Belum mengecek"
if "authenticated" not in st.session_state:
    st.session_state.authenticated = False
if "user" not in st.session_state:
    st.session_state.user = None
if "token" not in st.session_state:
    st.session_state.token = None
if not st.session_state.authenticated:

    st.title("🔐 Login Dashboard K3")

    username = st.text_input("Username")
    password = st.text_input("Password", type="password")

    if st.button("Login"):

        response = requests.post(
            API_LOGIN,
            json={
                "username": username,
                "password": password
            }
        )

        if response.status_code == 200:
            data = response.json()
            st.session_state.authenticated = True
            st.session_state.token = data["access_token"]
            st.session_state.user = data["user"]
            st.success("Login berhasil")
            st.rerun()
        else:
            # TAMPILKAN STATUS CODE ASLI AGAR MUDAH DIDEBUG
            st.error(f"Gagal Login! Status Code: {response.status_code}")
            st.write(response.text) # Menampilkan detail error dari FastAPI

    st.stop()

user = st.session_state.user

st.sidebar.success(
    f"👤 {user['name']}"
)

st.sidebar.info(
    f"Role: {user['role']}"
)

# admin access
st.sidebar.warning(
    f"Permission: {user['permissions']}"
)

if user["permissions"] == "full_access":

    st.sidebar.title("🛠 Admin Panel")

    if st.sidebar.button("Export CSV"):
        st.success("Fitur export dijalankan")

    if st.sidebar.button("Manage Users"):
        st.info("Halaman manajemen user")

#supervisor access
if user["permissions"] == "view_only":

    st.info("Mode Supervisor: Monitoring saja")

# --- MULAI DARI SINI: FITUR LOGOUT ---
st.sidebar.divider() # Memberikan garis pembatas biar rapi

if st.sidebar.button("🚪 Logout", use_container_width=True):
    # 1. Hapus semua data sesi pengguna
    st.session_state.authenticated = False
    st.session_state.token = None
    st.session_state.user = None
    
    # 2. Refresh paksa aplikasi agar kembali ke layar Login
    st.rerun()
# -------------------------------------

# --- FUNGSI FETCH TANPA TIMEOUT KETAT ---
# --- FUNGSI FETCH DENGAN TIMEOUT (PENCEGAH HANG) ---
def fetch_logs_direct():
    try:
        # Tambahkan timeout=3 di sini!
        r = requests.get(LOGS_URL, timeout=3) 
        if r.status_code == 200:
            return r.json().get("logs", [])
        else:
            st.error(f"Terjadi error dari API: {r.status_code}")
            return []
    except Exception as e:
        st.error(f"Streamlit gagal menghubungi FastAPI: {e}")
        return []

def check_status_direct():
    try:
        # Tambahkan timeout=3 di sini juga!
        r = requests.get(STATUS_URL, timeout=3)
        if r.status_code == 200:
            return str(r.json()) 
    except Exception as e:
        return f"Error API Status: {e}"
    return "Unknown"

# --- LOGIK UPDATE PAKSA (Bypass last_version) ---
# Untuk sementara, kita paksa Streamlit mendownload data setiap 3 detik
# tanpa mempedulikan versi. Ini untuk membuktikan apakah data bisa masuk.
st.session_state.data = fetch_logs_direct()
st.session_state.status_raw = check_status_direct()

# --- PANEL DEBUGGING (Akan terlihat di layar) ---
st.info(f"**🔍 DEBUG PANEL (Bantuan Sistem):** \n\n"
        f"**1. Hasil tembakan ke /status:** `{st.session_state.status_raw}` \n\n"
        f"**2. Jumlah data yang berhasil ditarik dari /logs:** `{len(st.session_state.data)}` baris")

st.divider()

# --- UI RENDERING ---
cols = st.columns([1, 2, 3, 4])
cols[0].write("**ID**")
cols[1].write("**Violation Type**")
cols[2].write("**Timestamp**")
cols[3].write("**Footage Recovery**")
st.divider()

if st.session_state.data and len(st.session_state.data) > 0:
    with st.container():
        for log in st.session_state.data:
            row_cols = st.columns([1, 2, 3, 4])
            row_cols[0].write(log.get("id", "N/A"))
            row_cols[1].write(f"⚠️ {log.get('violation_name', 'Unknown')}")
            row_cols[2].write(log.get("timestamp", "N/A"))
            
            with row_cols[3]:
                media_url = log.get("video_url", "")

                with st.expander("Proof", expanded=False):

                    if media_url:

                        # DEBUG TEXT
                        filename = os.path.basename(media_url)
                        st.caption(f"📁 File: {filename}")

                        # GET EXTENSION
                        ext = filename.split(".")[-1].lower()

                        # IMAGE SUPPORT
                        if ext in ["jpg", "jpeg", "png"]:
                            st.image(media_url, caption=filename, use_container_width=True)

                        # VIDEO SUPPORT
                        elif ext in ["mp4", "mov", "avi"]:
                            st.video(media_url)

                        # UNKNOWN FORMAT
                        else:
                            st.warning(f"Format file tidak didukung: .{ext}")

                    else:
                        st.write("Tidak ada media URL.")
else:
    st.warning("Data log (st.session_state.data) saat ini KOSONG. Lihat panel debug di atas.")

if st.button('🔄 Refresh Ulang'):
    st.rerun()
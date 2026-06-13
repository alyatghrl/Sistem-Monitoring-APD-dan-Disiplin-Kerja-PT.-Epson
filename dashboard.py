import streamlit as st
import requests
import pandas as pd
from datetime import datetime
from io import BytesIO
from config import API_BASE_URL
import time
import os

# ==========================================
# 1. PREMIUM METRO INDUSTRIAL THEME (CSS)
# ==========================================
st.set_page_config(layout="wide", page_title="K3 Safety Compliance")

st.markdown(
    """
    <style>
    /* Mengunci halaman agar terang benderang sesuai mockup */
    *, [data-testid="stAppViewBlockContainer"], [data-testid="stApp"] {
        opacity: 1.0 !important;
        filter: none !important;
        transition: none !important;
    }
    .stApp, main {
        background-color: #F8F9FA !important;
    }
    
    /* FIX ABSOLUT: Menghapus total tombol kotak fullscreen pada gambar/logo */
    div[data-testid="stImage"] {
        pointer-events: none !important;
    }
    [data-testid="stImageFullscreenButton"], 
    button[data-testid="stImageFullscreenButton"],
    button[title="View fullscreen"],
    div[data-testid="stElementToolbar"] {
        display: none !important;
        opacity: 0 !important;
        visibility: hidden !important;
    }
    
    /* ==========================================
       FIX REVOLUSIONER SIDEBAR: TEKS MUNCUL & BULATAN GAIB
       ========================================== */
    /* 1. Hilangkan Judul Label Navigasi bawaan Streamlit */
    div[data-testid="stSidebarUserContent"] div[data-testid="stWidgetLabel"] {
        display: none !important;
    }
    
    /* 2. Style Kotak Navigasi Utama (label) sebagai Kapsul Panjang Minimalis */
    div[data-testid="stSidebarUserContent"] div[data-testid="stRadio"] div[role="radiogroup"] label {
        padding: 12px 20px !important;
        border-radius: 25px !important;
        margin-bottom: 8px !important;
        width: 100% !important;
        display: flex !important;
        align-items: center !important;
        background-color: transparent !important;
        color: #000000 !important;
        cursor: pointer !important;
        border: none !important;
        transition: all 0.2s ease-in-out !important;
    }
    
    /* 3. Efek Hover Halus saat Kursor Lewat di Menu Pasif */
    div[data-testid="stSidebarUserContent"] div[data-testid="stRadio"] div[role="radiogroup"] label:hover {
        background-color: #EAECEE !important;
    }
    
    /* 4. Menu Aktif (Checked): Berubah Jadi Kapsul Ungu-Muda Sesuai Desain Figma */
    div[data-testid="stSidebarUserContent"] div[data-testid="stRadio"] div[role="radiogroup"] label[data-checked="true"] {
        background-color: #E8EBF8 !important; 
        color: #050B2C !important;
        font-weight: 600 !important;
    }
    
    /* 5. Trik membuat bulatan radio gaib transparan */
    div[data-testid="stSidebarUserContent"] div[data-testid="stRadio"] div[role="radiogroup"] label *:not([data-testid="stMarkdownContainer"]):not([data-testid="stMarkdownContainer"] *) {
        background: transparent !important;
        background-color: transparent !important;
        border-color: transparent !important;
        box-shadow: none !important;
    }
    
    /* 6. Mengunci Teks Navigasi agar Selalu Muncul Sempurna */
    div[data-testid="stSidebarUserContent"] div[data-testid="stRadio"] div[role="radiogroup"] label [data-testid="stMarkdownContainer"] {
        display: block !important;
        visibility: visible !important;
        opacity: 1 !important;
        width: 100% !important;
    }
    div[data-testid="stSidebarUserContent"] div[data-testid="stRadio"] div[role="radiogroup"] label p {
        font-size: 15px !important;
        margin: 0 !important;
        color: inherit !important;
        font-weight: inherit !important;
        display: block !important;
        visibility: visible !important;
        opacity: 1 !important;
    }
    
    /* Target Utama Kontainer st.form (Screen 01) */
    div[data-testid="stForm"] {
        background-color: #ffffff !important;
        padding: 40px 45px !important;
        border-radius: 12px !important;
        box-shadow: 0 10px 30px rgba(0,0,0,0.06) !important;
        border: 1px solid #EAECEE !important;
    }
    
    /* Hanya mewarnai tombol "Sign In" saja, mengabaikan ikon mata */
    div[data-testid="stForm"] button[data-testid="stFormSubmitButton"] {
        background-color: #8A1C1C !important;
        color: white !important;
        border-radius: 6px !important;
        border: none !important;
        font-weight: 600 !important;
        padding: 12px 0px !important;
        font-size: 16px !important;
        width: 100% !important;
    }
    div[data-testid="stForm"] button[data-testid="stFormSubmitButton"]:hover {
        background-color: #6B1515 !important;
    }
    
    /* Judul halaman dengan Garis Bawah Tegas */
    .page-title {
        font-size: 26px;
        font-weight: 700;
        color: #000000;
        margin-bottom: 6px;
        display: inline-block;
        border-bottom: 3px solid #000000;
        padding-bottom: 4px;
    }
    
    /* Tiga Kotak Widget Atas Sejajar */
    .metric-container {
        background-color: #ffffff;
        padding: 20px;
        border-radius: 10px;
        box-shadow: 0 4px 12px rgba(0,0,0,0.03);
        border: 1px solid #EAECEE;
        min-height: 90px;
        display: flex;
        align-items: center;
    }
    
    /* Kotak Live Feed Kamera Bawah */
    .camera-card {
        background-color: #ffffff;
        padding: 15px;
        border-radius: 10px;
        box-shadow: 0 4px 12px rgba(0,0,0,0.03);
        border: 1px solid #EAECEE;
        margin-top: 15px;
        text-align: center;
    }
    .camera-card img {
        max-height: 320px !important;
        object-fit: contain !important;
        border-radius: 6px !important;
        width: auto !important;
        margin: 0 auto !important;
    }

    /* Modal overlay style for Add / Edit / Delete User */
    div[role="dialog"] {
        background-color: rgba(248, 249, 250, 0.98) !important;
        border-radius: 22px !important;
        padding: 0 !important;
        max-width: 760px !important;
        min-width: 420px !important;
        box-shadow: 0 24px 90px rgba(0, 0, 0, 0.18) !important;
        border: 1px solid rgba(0, 0, 0, 0.08) !important;
    }
    div[role="dialog"] > div {
        padding: 30px 30px 24px !important;
    }
    div[role="dialog"] .stForm {
        background: transparent !important;
        border: none !important;
        box-shadow: none !important;
        padding: 0 !important;
    }
    div[role="dialog"] .stMarkdown p {
        margin: 0 !important;
    }
    div[role="dialog"] .stButton>button,
    div[role="dialog"] button {
        border-radius: 12px !important;
        padding: 14px 0 !important;
        font-weight: 600 !important;
    }
    div[role="dialog"] .stTextInput>div>div>input,
    div[role="dialog"] .stSelectbox>div>div,
    div[role="dialog"] .stTextArea>div>div>textarea {
        border-radius: 12px !important;
        border: 1px solid #D1D5DB !important;
        background-color: #FFFFFF !important;
    }
    div[role="dialog"] button:hover {
        opacity: 0.95 !important;
    }
    div[role="dialog"] .stButton>button[data-testid="stFormSubmitButton"] {
        background-color: #DDE4FF !important;
        color: #12263A !important;
        border: 1px solid #B0C4FF !important;
    }
    div[role="dialog"] .stButton>button[data-testid="stFormSubmitButton"]:hover {
        background-color: #C7D6FF !important;
    }
    div[role="dialog"] .stButton>button[style*="background-color: rgb(255, 255, 255)"] {
        background-color: #F8D7DA !important;
        color: #7A1818 !important;
        border: 1px solid #F5C2C7 !important;
    }
    </style>
    """,
    unsafe_allow_html=True
)

# Inisialisasi Auto-Refresh
try:
    from streamlit_autorefresh import st_autorefresh
    _autorefresh_available = True
except ImportError:
    _autorefresh_available = False

# Configuration & URL Endpoints
API_BASE       = f"{API_BASE_URL}/api/v1"
API_VIOLATIONS = f"{API_BASE}/violations"
API_LOGIN      = f"{API_BASE}/auth/login"
API_USERS      = f"{API_BASE}/users"
LOGS_URL       = f"{API_VIOLATIONS}/logs"
LIVE_BASE      = "http://127.0.0.1:8000/live"

# Inisialisasi Lokasi File Logo di Level Global
FOLDER_SEKARANG = os.path.dirname(os.path.abspath(__file__))
PATH_LOGO       = os.path.join(FOLDER_SEKARANG, "logo_k3.png")

for key, default in [("authenticated", False), ("user", None), ("token", None)]:
    if key not in st.session_state:
        st.session_state[key] = default

_no_proxy     = {"http": None, "https": None}
_req_headers  = {"User-Agent": "Streamlit/1.0", "Connection": "close"}


@st.cache_data(ttl=3, show_spinner=False)
def fetch_logs() -> list:
    try:
        r = requests.get(LOGS_URL, timeout=3, headers=_req_headers, proxies=_no_proxy)
        if r.status_code == 200: return r.json().get("logs", [])
    except Exception: pass
    return []

def update_violation(log_id: int, status_bool: bool, notes_str: str) -> None:
    try: 
        requests.put(f"{API_VIOLATIONS}/{log_id}", json={"status": 1 if status_bool else 0, "notes": notes_str}, timeout=2)
        # ---> TAMBAHAN BARU: Membersihkan cache log agar tabel ter-refresh <---
        fetch_logs.clear() 
    except Exception: pass

@st.cache_data(ttl=10, show_spinner=False)
def fetch_users() -> list:
    try:
        r = requests.get(API_USERS, timeout=3, headers=_req_headers, proxies=_no_proxy)
        if r.status_code == 200: return r.json()
    except Exception: pass
    return []

def create_user_api(payload: dict) -> tuple[bool, str]:
    try:
        r = requests.post(API_USERS, json=payload, timeout=3)
        if r.status_code == 201:

            fetch_users.clear() 
            return True, "Akun berhasil dibuat."
        return False, r.json().get("detail", "Gagal.")
    except Exception as e: return False, str(e)

def update_user_api(user_id: int, payload: dict) -> tuple[bool, str]:
    try:
        r = requests.put(f"{API_USERS}/{user_id}", json=payload, timeout=3)
        if r.status_code == 200:
            # ---> TAMBAHAN BARU: Membersihkan cache saat user diedit <---
            fetch_users.clear() 
            return True, "Akun berhasil diperbarui."
        return False, r.json().get("detail", "Gagal.")
    except Exception as e: return False, str(e)

def delete_user_api(user_id: int) -> tuple[bool, str]:
    try:
        r = requests.delete(f"{API_USERS}/{user_id}", timeout=3)
        if r.status_code == 204:
            fetch_users.clear() 
            return True, "Akun berhasil dihapus."
        return False, r.json().get("detail", "Gagal.")
    except Exception as e: return False, str(e)

def build_form_button(button_label: str, button_type: str = "primary"):
    if button_type == "danger":
        return st.button(button_label, use_container_width=True, help="Hapus akun secara permanen.")
    return st.form_submit_button(button_label, use_container_width=True)

def generate_pdf(dataframe: pd.DataFrame) -> bytes:
    try:
        from fpdf import FPDF
        from fpdf.enums import XPos, YPos
    except ImportError: 
        return b""
    
    pdf = FPDF(orientation="L") 
    pdf.set_auto_page_break(auto=True, margin=15)
    pdf.add_page()
    
    pdf.set_font("Helvetica", "B", 16)
    pdf.cell(0, 10, "Laporan Pelanggaran K3", new_x=XPos.LMARGIN, new_y=YPos.NEXT, align="C")
    pdf.ln(5)
    
    if dataframe.empty:
        pdf.set_font("Helvetica", "", 12)
        pdf.cell(0, 10, "Tidak ada data pelanggaran.", new_x=XPos.LMARGIN, new_y=YPos.NEXT, align="C")
        return bytes(pdf.output())

    headers = ["Waktu Pelanggaran", "Sumber Kamera", "Jenis", "Akurasi", "Status", "Catatan SPV"]
    col_widths = [45, 40, 35, 20, 35, 95] 
    
    pdf.set_font("Helvetica", "B", 10)
    for i, header in enumerate(headers):
        pdf.cell(col_widths[i], 10, str(header), border=1, align="C")
    pdf.ln()
    
    pdf.set_font("Helvetica", "", 9)
    for _, row in dataframe.iterrows():
        waktu = str(row.get("timestamp", ""))
        kamera = str(row.get("camera_id", ""))
        jenis = str(row.get("violation_name", ""))
        akurasi = f"{row.get('confidence_score', 0):.4f}"
        
        status_raw = row.get("status", False)
        status = "Sudah ditangani" if status_raw else "Belum ditangani"
        
        catatan = str(row.get("notes", ""))
        if catatan in ["nan", "None", ""]: 
            catatan = "-"
        
        # Memotong catatan jika teks terlalu panjang agar tidak tumpah merusak tabel
        if len(catatan) > 60:
            catatan = catatan[:57] + "..."
            
        data_row = [waktu, kamera, jenis, akurasi, status, catatan]
        
        for i, text in enumerate(data_row):
            # Encode ke latin-1 agar FPDF tidak error saat menjumpai karakter aneh (emoji/spesial)
            safe_text = text.encode('latin-1', 'replace').decode('latin-1')
            pdf.cell(col_widths[i], 8, safe_text, border=1)
        
        pdf.ln() 
        
    return bytes(pdf.output())

@st.dialog("MINI WINDOWS - INSPEKSI FOTO BUKTI")
def tampilkan_mini_window_bukti(data):
    st.markdown(f"**Waktu Kejadian:** `{data['Waktu Pelanggaran']}`")
    st.markdown(f"**Sumber Kamera:** `{data['Sumber Kamera']}` | **Jenis Pelanggaran:** `{data['Jenis Pelanggaran']}`")
    st.markdown(f"**Akurasi Model:** `{data['Akurasi'] * 100:.2f}%` | **Status Saat Ini:** `{data['Status']}`")
    st.divider()
    
    st.image(data["video_url"], use_container_width=True)
    
    st.markdown("<br>", unsafe_allow_html=True)
  
    user_role = st.session_state.user.get("role", "") if st.session_state.user else ""
    
    current_status_bool = True if data['Status'] == "Sudah ditangani" else False
    current_notes = data['Catatan SPV']
    if pd.isna(current_notes) or current_notes is None:
        current_notes = ""
        
    if user_role == "Supervisor":
        st.markdown("### 📝 Tindakan Supervisor")
        # Form aktif untuk SPV
        with st.form(key=f"form_update_log_{data['ID']}"):
            new_status = st.checkbox("Tandai sebagai 'Sudah ditangani'", value=current_status_bool)
            new_notes = st.text_area("Tambahkan Catatan SPV:", value=str(current_notes), placeholder="Ketik tindakan yang telah dilakukan...")
            
            if st.form_submit_button("Simpan Perubahan", use_container_width=True):
                update_violation(int(data['ID']), new_status, new_notes)
                st.success("Tindakan berhasil disimpan!")
                time.sleep(1)
                st.rerun()
    else:
        # Tampilan Read-Only (Hanya Baca) untuk Admin
        st.markdown("### 📝 Catatan Supervisor")
        st.info("Anda login sebagai Admin. Hanya Supervisor yang dapat mengubah status dan memberikan catatan.")
        
        status_label = "✅ Sudah ditangani" if current_status_bool else "⏳ Belum ditangani"
        st.markdown(f"**Status:** {status_label}")
        
        catatan_tampil = current_notes if current_notes != "" else "*(Belum ada catatan)*"
        st.text_area("Isi Catatan:", value=str(catatan_tampil), disabled=True)

@st.dialog("Tambah Akun Baru")
def modal_tambah_user():
    with st.form("tambah_akun_form", clear_on_submit=True):
        c1, c2 = st.columns(2)
        with c1: new_u = st.text_input("Username", key="new_username")
        with c2: new_p = st.text_input("Password", type="password", key="new_password")
        
        c3, c4 = st.columns(2)
        with c3: new_f = st.text_input("Nama Lengkap", key="new_fullname")
        with c4: new_r = st.selectbox("Role", ["Supervisor", "Admin"], key="new_role")
        
        perms = "full_access" if new_r == "Admin" else "view_only"
        st.markdown(f"<p style='font-size:14px; margin-top:10px; color:#000000;'>Akses otomatis: <strong>{perms}</strong></p>", unsafe_allow_html=True)
        st.markdown("<br>", unsafe_allow_html=True)
        
        if st.form_submit_button("Buat Akun", use_container_width=True):
            if new_u and new_p and new_f:
                ok, msg = create_user_api({"username": new_u, "password": new_p, "full_name": new_f, "role": new_r, "permissions": perms})
                if ok: st.success(msg); time.sleep(1); st.rerun()
                else: st.error(msg)
            else: st.error("Harap lengkapi semua bidang isian data.")

@st.dialog("Edit Akun")
def modal_edit_user(opts, raw_list):
    pilihan_edit = st.selectbox("Pilih Akun", list(opts.keys()), key="edit_user_select")
    target_id = opts[pilihan_edit]
    user_meta = next(u for u in raw_list if u["id"] == target_id)
    
    with st.form("edit_akun_form"):
        c1, c2 = st.columns(2)
        with c1: e_f = st.text_input("Nama Lengkap", value=user_meta["full_name"], key="edit_fullname")
        with c2: e_p = st.text_input("Password Baru", type="password", placeholder="Kosongkan jika sandi tidak diubah", key="edit_password")
        
        e_r = st.selectbox("Role", ["Supervisor", "Admin"], index=0 if user_meta["role"] == "Supervisor" else 1, key="edit_role")
        perms = "full_access" if e_r == "Admin" else "view_only"
        st.markdown(f"<p style='font-size:14px; margin-top:10px; color:#000000;'>Akses otomatis: <strong>{perms}</strong></p>", unsafe_allow_html=True)
        st.markdown("<br>", unsafe_allow_html=True)
        
        if st.form_submit_button("Simpan Perubahan", use_container_width=True):
            payload = {"full_name": e_f, "role": e_r, "permissions": perms}
            if e_p: payload["password"] = e_p
            ok, msg = update_user_api(target_id, payload)
            if ok: st.success(msg); time.sleep(1); st.rerun()
            else: st.error(msg)

@st.dialog("Hapus Akun")
def modal_hapus_user(opts):
    pilihan_del = st.selectbox("Pilih Akun", list(opts.keys()), key="delete_user_select")
    target_id = opts[pilihan_del]
    
    st.markdown(f"<p style='color: #CD6155; font-size: 14px; margin-top: 10px;'>Tindakan ini tidak dapat dibatalkan. Akun <strong>{pilihan_del}</strong> akan dihapus permanen.</p>", unsafe_allow_html=True)
    st.markdown("<br>", unsafe_allow_html=True)
    
    if st.button("Hapus Akun", use_container_width=True, help="Hapus akun terpilih dari sistem."):
        ok, msg = delete_user_api(target_id)
        if ok: st.success(msg); time.sleep(1); st.rerun()
        else: st.error(msg)

if not st.session_state.authenticated:
    _, center_col, _ = st.columns([1.1, 1.2, 1.1])
    with center_col:
        st.markdown("<div style='margin-top: 15%;'></div>", unsafe_allow_html=True)
        with st.form("login_form", clear_on_submit=False):
            logo_box_1, logo_box_2 = st.columns([1, 4])
            with logo_box_1: st.image(PATH_LOGO, width=52)
            with logo_box_2: st.markdown("<h3 style='margin-top: 6px; margin-left: -15px; color: #1C2833; font-weight: 700; font-size: 23px;'>K3 Safety Compliance</h3>", unsafe_allow_html=True)
            st.markdown("<div style='margin-bottom: 15px;'></div>", unsafe_allow_html=True)
            username = st.text_input("Username")
            password = st.text_input("Password", type="password")
            col_rem, col_forgot = st.columns([1.2, 1])
            with col_rem: st.checkbox("Remember me", key="remember_me")
            with col_forgot: st.markdown("<div style='text-align: right; margin-top: 5px; font-size: 14px;'><a href='#' style='color: #566573; text-decoration: none;'>Forgot Password</a></div>", unsafe_allow_html=True)
            st.markdown("<div style='margin-bottom: 15px;'></div>", unsafe_allow_html=True)
            submitted = st.form_submit_button("Sign In", use_container_width=True)
            if submitted:
                try:
                    r = requests.post(API_LOGIN, json={"username": username, "password": password}, timeout=5)
                    if r.status_code == 200:
                        data = r.json()
                        st.session_state.authenticated = True
                        st.session_state.token         = data["access_token"]
                        st.session_state.user          = data["user"]
                        st.rerun()
                    else: st.error("Akses ditolak. Periksa kembali kredensial Anda.")
                except Exception as e: st.error(f"Gagal terhubung ke server backend: {e}")
    st.stop()

raw_data = fetch_logs()
df       = pd.DataFrame(raw_data) if raw_data else pd.DataFrame()
user = st.session_state.user
# Pastikan pemeriksaan admin aman jika `user` None atau key tidak ada
is_admin = bool(user and user.get("permissions") == "full_access")

KNOWN_CAMS = ["CAM_WEBCAM", "CAM_DROIDCAM"]
if not df.empty and "camera_id" in df.columns:
    KNOWN_CAMS = list(set(KNOWN_CAMS + df["camera_id"].unique().tolist()))

sidebar_logo_col, sidebar_title_col = st.sidebar.columns([1, 4])
with sidebar_logo_col: st.image(PATH_LOGO, width=40)
with sidebar_title_col: st.markdown("<h4 style='margin-top: 6px; margin-left: -15px; font-weight: 700; color: #1C2833; font-size: 16px;'>K3 Safety Compliance</h4>", unsafe_allow_html=True)

st.sidebar.markdown("<hr style='margin-top: 5px; margin-bottom: 20px; border-top: 1px solid #FADBD8;'>", unsafe_allow_html=True)

user_role_display = "Admin" if is_admin else "Supervisor"
st.sidebar.markdown(f"<div style='background-color: #050B2C; color: white; padding: 12px 0px; text-align: center; border-radius: 25px; font-weight: bold; font-size: 16px; margin-bottom: 25px; letter-spacing: 0.5px;'>{user_role_display}</div>", unsafe_allow_html=True)

tabs_list = ["📸 Live Monitoring", "📝 Violations Log", "🛠 Manage Users"] if is_admin else ["📸 Live Monitoring", "📝 Violations Log"]
selected_tab = st.sidebar.radio("", tabs_list)

user_role = st.session_state.user.get("role", "") if st.session_state.user else ""

if selected_tab == "📸 Live Monitoring" and user_role == "Supervisor":
    st.sidebar.markdown("<hr style='margin-top: 10px; margin-bottom: 10px; border-top: 1px dashed #BDC3C7;'>", unsafe_allow_html=True)
    st.sidebar.markdown("<span style='font-size:14px; font-weight:700; color:#2C3E50;'>⚙️ Pengaturan Auto-Capture</span>", unsafe_allow_html=True)
    
    # Setup default value di session state
    if 'capture_interval' not in st.session_state:
        st.session_state['capture_interval'] = 10
        
    opsi_durasi = ["10 Detik", "20 Detik", "30 Detik", "40 Detik", "50 Detik", "60 Detik", "Custom..."]
    durasi_opt = st.sidebar.selectbox("Interval Waktu:", opsi_durasi, key="durasi_opt")
    
    custom_val = 0
    if durasi_opt == "Custom...":
        custom_val = st.sidebar.number_input("Input Custom (Detik):", min_value=1, max_value=3600, value=15, step=1, key="durasi_custom")
        
    if st.sidebar.button("💾 Simpan", use_container_width=True):
        final_val = custom_val if durasi_opt == "Custom..." else int(durasi_opt.split()[0])
        
        # === INTEGRASI BACKEND (OPSIONAL) ===
        # requests.post(f"{API_BASE}/cameras/settings", json={"capture_interval": final_val}, timeout=2)
        
        st.session_state['capture_interval'] = final_val
        st.sidebar.success(f"Disimpan: {final_val} detik")
        time.sleep(1)
        st.rerun()

if _autorefresh_available and selected_tab == "📸 Live Monitoring":
    st_autorefresh(interval=3000, key="datacheck")

st.sidebar.markdown("<div style='position: fixed; bottom: 0; width: 260px; background-color: #ffffff;'>", unsafe_allow_html=True)
st.sidebar.markdown("<hr style='border-top: 1px solid #FADBD8; margin-bottom: 15px;'>", unsafe_allow_html=True)
if st.sidebar.button("↪ Logout", use_container_width=True):
    for k in ["authenticated", "user", "token"]: st.session_state[k] = None if k != "authenticated" else False
    st.rerun()
st.sidebar.markdown("</div>", unsafe_allow_html=True)

def screen_live_monitoring():
    st.markdown("<span class='page-title'>Live Monitoring</span>", unsafe_allow_html=True)
    waktu_sekarang = datetime.now()
    nama_hari = waktu_sekarang.strftime("%A").upper()
    tanggal_str = waktu_sekarang.strftime("%d/%m/%Y")
    total_violations = len(df) if not df.empty else 0
    
    m1, m2, m3 = st.columns(3)
    
    with m1: 
        st.markdown(f"<div class='metric-container'><div style='font-size: 18px; color: #5D6D7E; font-weight: 500; letter-spacing: 1px;'>{nama_hari} &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp; <strong>{tanggal_str}</strong></div></div>", unsafe_allow_html=True)
    
    with m2: 
        # Inject JavaScript HTML agar jam berdetik real-time
        st.components.v1.html(
            """
            <style>
                @import url('https://fonts.googleapis.com/css2?family=Source+Sans+Pro:wght@400;600;700&display=swap');
                body {
                    margin: 0;
                    padding: 4px;
                    font-family: 'Source Sans Pro', sans-serif;
                    overflow: hidden;
                }
                .metric-container {
                    background-color: #ffffff;
                    padding: 20px;
                    border-radius: 10px;
                    box-shadow: 0 4px 12px rgba(0,0,0,0.03);
                    border: 1px solid #EAECEE;
                    height: 90px;
                    display: flex;
                    align-items: center;
                    justify-content: center;
                    box-sizing: border-box;
                }
                .clock-text {
                    font-size: 36px; 
                    font-weight: 700; 
                    color: #000000; 
                    letter-spacing: 1px;
                }
            </style>
            <div class="metric-container">
                <div id="clock" class="clock-text"></div>
            </div>
            <script>
                function updateClock() {
                    const now = new Date();
                    const h = String(now.getHours()).padStart(2, '0');
                    const m = String(now.getMinutes()).padStart(2, '0');
                    const s = String(now.getSeconds()).padStart(2, '0');
                    document.getElementById('clock').innerText = h + '.' + m + '.' + s;
                }
                setInterval(updateClock, 1000); 
                updateClock(); 
            </script>
            """,
            height=100
        )
        
    with m3: 
        st.markdown(f"<div class='metric-container' style='gap: 15px;'><div style='background-color: #FDEDEC; padding: 10px; border-radius: 8px;'>⚠️</div><div><div style='font-size: 11px; color: #7F8C8D; font-weight: 600;'>Total Pelanggaran</div><div style='font-size: 24px; font-weight: 700; color: #000000;'>{total_violations}</div></div></div>", unsafe_allow_html=True)
        
    st.markdown("<br>", unsafe_allow_html=True)
    
    # Langsung menampilkan kamera tanpa elemen yang mengganggu layout
    _, col_cam1, col_cam2, _ = st.columns([0.4, 2, 2, 0.4])
    with col_cam1:
        st.markdown(f"<div class='camera-card'><p style='font-weight: 600; margin-bottom: 8px; color: #000000;'>Webcam 1</p>", unsafe_allow_html=True)
        st.image(f"{LIVE_BASE}/CAM_WEBCAM.jpg?t={time.time()}", use_container_width=True)
        st.markdown("</div>", unsafe_allow_html=True)
    with col_cam2:
        st.markdown(f"<div class='camera-card'><p style='font-weight: 600; margin-bottom: 8px; color: #000000;'>Droidcam</p>", unsafe_allow_html=True)
        st.image(f"{LIVE_BASE}/CAM_DROIDCAM.jpg?t={time.time()}", use_container_width=True)
        st.markdown("</div>", unsafe_allow_html=True)

def screen_violations_log():
    header_col, f_col1, f_col2, f_col3 = st.columns([1.5, 1, 1, 1])
    with header_col: st.markdown("<span class='page-title'>Violations Log</span>", unsafe_allow_html=True)
        
    if df.empty:
        st.markdown("Log data transaksi masih kosong.")
        return
    
    with f_col1: filter_cam = st.selectbox("📷 Sumber Kamera:", ["Semua"] + KNOWN_CAMS, key="filter_cam_violations")
    with f_col2: filter_status = st.selectbox("📋 Status Tindakan:", ["Semua", "Belum ditangani", "Sudah ditangani"], key="filter_status_violations")
    with f_col3: filter_date = st.selectbox("📅 Tanggal Kejadian:", ["Today", "All History"], key="filter_date_violations")
    
    filtered_df = df.copy()
    if filter_cam != "Semua": filtered_df = filtered_df[filtered_df["camera_id"] == filter_cam]
    if filter_status == "Belum ditangani": filtered_df = filtered_df[filtered_df["status"] == False]
    elif filter_status == "Sudah ditangani": filtered_df = filtered_df[filtered_df["status"] == True]
        
    filtered_df = filtered_df.sort_values("timestamp", ascending=False)
    
    display_table_df = pd.DataFrame()
    # Menambahkan primary key (ID) secara diam-diam agar bisa ditangkap oleh fungsi update pop-up
    display_table_df["ID"]                = filtered_df.get("id", filtered_df.index)
    display_table_df["Waktu Pelanggaran"] = filtered_df["timestamp"]
    display_table_df["Sumber Kamera"]     = filtered_df["camera_id"]
    display_table_df["Jenis Pelanggaran"] = filtered_df["violation_name"]
    display_table_df["Akurasi"]           = filtered_df["confidence_score"].round(4)
    display_table_df["Status"]            = filtered_df["status"].map({True: "Sudah ditangani", False: "Belum ditangani"})
    display_table_df["Catatan SPV"]       = filtered_df["notes"]
    display_table_df["Bukti"]             = "👁️ Lihat Bukti"
    display_table_df["video_url"]         = filtered_df["video_url"]
    
    # Kolom 'ID' tidak dimasukkan ke dalam list pemanggilan ini agar tersembunyi dari layar pengguna
    event = st.dataframe(
        display_table_df[["Waktu Pelanggaran", "Sumber Kamera", "Jenis Pelanggaran", "Akurasi", "Status", "Catatan SPV", "Bukti"]],
        column_config={
            "Waktu Pelanggaran": st.column_config.TextColumn("Waktu Pelanggaran"),
            "Akurasi": st.column_config.NumberColumn("Akurasi", format="%.4f"),
            "Bukti": st.column_config.TextColumn("Bukti"),
        }, use_container_width=True, hide_index=True, on_select="rerun", selection_mode="single-cell"
    )
    
    if 'last_selected_cell_violations' not in st.session_state: st.session_state.last_selected_cell_violations = None
    if event.selection.cells:
        selected_cell = event.selection.cells[0]
        if selected_cell != st.session_state.last_selected_cell_violations:
            st.session_state.last_selected_cell_violations = selected_cell
            selected_row_idx = selected_cell[0]
            # Menangkap seluruh data pada baris yang diklik (termasuk kolom ID yang tersembunyi)
            row_data = display_table_df.iloc[selected_row_idx]
            tampilkan_mini_window_bukti(row_data)
    else: st.session_state.last_selected_cell_violations = None
        
    exp_col, _ = st.columns([1, 4])
    with exp_col:
        export_action = st.selectbox("📥 Export as...", ["Pilih Format...", "Unduh File CSV", "Unduh Dokumen PDF"], label_visibility="collapsed", key="export_action_violations")
        
        if export_action == "Unduh File CSV":
            # 1. Gunakan data tabel yang sudah rapi bahasanya, hilangkan kolom "Bukti" yang isinya cuma teks ikon
            export_csv_df = display_table_df.drop(columns=["Bukti"])
            
            # 2. Gunakan sep=';' untuk region lokal dan 'utf-8-sig' agar karakter Excel tidak rusak
            csv_data = export_csv_df.to_csv(index=False, sep=';').encode("utf-8-sig")
            
            st.download_button("Klik untuk Ambil CSV", data=csv_data, file_name="K3_Log_Compliance.csv", mime="text/csv", use_container_width=True)
            
        elif export_action == "Unduh Dokumen PDF": 
            st.download_button("Klik untuk Ambil PDF", data=generate_pdf(filtered_df), file_name="K3_Log_Compliance.pdf", mime="application/pdf", use_container_width=True)

def screen_manage_users():
    if not is_admin:
        st.warning("Anda tidak memiliki izin admin untuk mengakses halaman Manage Users.")
        return
        
    col_title, col_b1, col_b2, col_b3 = st.columns([1.8, 0.7, 0.7, 0.7])
    
    with col_title:
        st.markdown("<h3 style='margin:0; font-weight:700; color:#000000;'>User Management</h3>", unsafe_allow_html=True)
        st.markdown("<p style='color:#566573; font-size:14px; margin-top:2px;'>Manage and triage incoming reports from customers.</p>", unsafe_allow_html=True)
        
    users_data = fetch_users()
    users_df   = pd.DataFrame(users_data) if users_data else pd.DataFrame()
    
    # Menyusun opsi pilihan drop-down "username (Nama Lengkap)"
    map_options = {}
    if not users_df.empty:
        for r in users_data:
            label_opsi = f"{r['username']} ({r['full_name']})"
            map_options[label_opsi] = r["id"]
    
    with col_b1:
        st.markdown("<div style='margin-top: 10px;'></div>", unsafe_allow_html=True)
        if st.button("👥+ Tambah Akun", use_container_width=True):
            modal_tambah_user()
            
    with col_b2:
        st.markdown("<div style='margin-top: 10px;'></div>", unsafe_allow_html=True)
        if st.button("✏️ Edit Akun", use_container_width=True):
            if map_options:
                modal_edit_user(map_options, users_data)
            else:
                st.warning("Database kosong.")
                
    with col_b3:
        st.markdown("<div style='margin-top: 10px;'></div>", unsafe_allow_html=True)
        if st.button("🗑️ Hapus Akun", use_container_width=True):
            if map_options:
                modal_hapus_user(map_options)
            else:
                st.warning("Database kosong.")
        
    st.markdown("<br>", unsafe_allow_html=True)
    
    if not users_df.empty:
        display_user_df = pd.DataFrame()
        display_user_df["ID"]           = users_df["id"]
        display_user_df["Username"]     = users_df["username"]
        display_user_df["Nama Lengkap"] = users_df["full_name"]
        display_user_df["Role"]         = users_df["role"]
        display_user_df["Akses"]        = users_df["permissions"]
        
        st.dataframe(display_user_df[["ID", "Username", "Nama Lengkap", "Role", "Akses"]], use_container_width=True, hide_index=True)
    else:
        st.info("Belum ada data user terdaftar dalam sistem backend.")

if selected_tab == "📸 Live Monitoring":
    screen_live_monitoring()
elif selected_tab == "📝 Violations Log":
    screen_violations_log()
elif selected_tab == "🛠 Manage Users":
    screen_manage_users()

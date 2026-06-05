import streamlit as st
import requests
import pandas as pd
from datetime import date, time as dtime
from io import BytesIO
from config import API_BASE_URL
import time

# ==========================================
# KONFIGURASI HALAMAN & STATE
# ==========================================
st.set_page_config(layout="wide", page_title="K3 Safety Compliance")

# TRIK SAKTI VERSI 2: Mengunci TOTAL seluruh elemen agar anti-redup & anti-blur
st.markdown(
    """
    <style>
    /* Hantam semua elemen tanpa terkecuali agar tetap terang benderang */
    *, [data-testid="stAppViewBlockContainer"], [data-testid="stApp"] {
        opacity: 1.0 !important;
        filter: none !important;
        transition: none !important;
    }
    
    /* Matikan background gelap atau abu-abu transparan yang suka muncul di latar belakang */
    .stApp, main, .st-emotion-cache-1vq4p4l, .st-emotion-cache-z5fcl4 {
        background-color: #ffffff !important;
    }
    </style>
    """,
    unsafe_allow_html=True
)

# Auto-refresh setiap 3 detik (hanya setelah login)
try:
    from streamlit_autorefresh import st_autorefresh
    _autorefresh_available = True
except ImportError:
    _autorefresh_available = False

API_BASE       = f"{API_BASE_URL}/api/v1"
API_VIOLATIONS = f"{API_BASE}/violations"
API_LOGIN      = f"{API_BASE}/auth/login"
API_USERS      = f"{API_BASE}/users"
LOGS_URL       = f"{API_VIOLATIONS}/logs"

# Harus selalu 127.0.0.1 karena dirender oleh Browser lokal
LIVE_BASE      = "http://127.0.0.1:8000/live"

for key, default in [
    ("authenticated", False),
    ("user", None),
    ("token", None),
]:
    if key not in st.session_state:
        st.session_state[key] = default

# ==========================================
# HALAMAN LOGIN
# ==========================================
if not st.session_state.authenticated:
    st.title("🔐 Login Dashboard K3")
    with st.form("login_form"):
        username  = st.text_input("Username")
        password  = st.text_input("Password", type="password")
        submitted = st.form_submit_button("Login", width='stretch')
        if submitted:
            try:
                r = requests.post(
                    API_LOGIN,
                    json={"username": username, "password": password},
                    timeout=5
                )
                if r.status_code == 200:
                    data = r.json()
                    st.session_state.authenticated = True
                    st.session_state.token         = data["access_token"]
                    st.session_state.user          = data["user"]
                    st.success("Login berhasil!")
                    st.rerun()
                else:
                    st.error(f"Gagal login. Periksa username dan password. (Status: {r.status_code})")
            except Exception as e:
                st.error(f"Gagal menghubungi server: {e}")
    st.stop()

# Aktifkan auto-refresh setelah login
if _autorefresh_available:
    st_autorefresh(interval=3000, key="datacheck")

# ==========================================
# HELPER FUNCTIONS
# ==========================================
_no_proxy     = {"http": None, "https": None}
_req_headers  = {"User-Agent": "Streamlit/1.0", "Connection": "close"}

def fetch_logs() -> list:
    try:
        r = requests.get(LOGS_URL, timeout=3, headers=_req_headers, proxies=_no_proxy)
        if r.status_code == 200:
            return r.json().get("logs", [])
    except Exception:
        pass
    return []

def update_violation(log_id: int, status_bool: bool, notes_str: str) -> None:
    try:
        requests.put(
            f"{API_VIOLATIONS}/{log_id}",
            json={"status": 1 if status_bool else 0, "notes": notes_str},
            timeout=2,
        )
    except Exception:
        pass

def fetch_users() -> list:
    try:
        r = requests.get(API_USERS, timeout=3, headers=_req_headers, proxies=_no_proxy)
        if r.status_code == 200:
            return r.json()
    except Exception:
        pass
    return []

def create_user_api(payload: dict) -> tuple[bool, str]:
    try:
        r = requests.post(API_USERS, json=payload, timeout=3)
        if r.status_code == 201:
            return True, "Akun berhasil dibuat."
        return False, r.json().get("detail", "Gagal membuat akun.")
    except Exception as e:
        return False, str(e)

def update_user_api(user_id: int, payload: dict) -> tuple[bool, str]:
    try:
        r = requests.put(f"{API_USERS}/{user_id}", json=payload, timeout=3)
        if r.status_code == 200:
            return True, "Akun berhasil diperbarui."
        return False, r.json().get("detail", "Gagal memperbarui akun.")
    except Exception as e:
        return False, str(e)

def delete_user_api(user_id: int) -> tuple[bool, str]:
    try:
        r = requests.delete(f"{API_USERS}/{user_id}", timeout=3)
        if r.status_code == 204:
            return True, "Akun berhasil dihapus."
        return False, r.json().get("detail", "Gagal menghapus akun.")
    except Exception as e:
        return False, str(e)

def generate_pdf(dataframe: pd.DataFrame) -> bytes:
    """Buat PDF laporan dari DataFrame menggunakan fpdf2."""
    try:
        from fpdf import FPDF
    except ImportError:
        return b""
    pdf = FPDF()
    pdf.set_auto_page_break(auto=True, margin=15)
    pdf.add_page()
    pdf.set_font("Helvetica", "B", 14)
    pdf.cell(0, 10, "Laporan Pelanggaran K3", ln=True, align="C")
    pdf.set_font("Helvetica", size=8)
    pdf.cell(0, 6, f"Diekspor: {pd.Timestamp.now().strftime('%Y-%m-%d %H:%M')}", ln=True, align="C")
    pdf.ln(4)

    cols     = ["timestamp", "camera_id", "violation_name", "confidence_score", "status", "notes"]
    headers  = ["Waktu", "Kamera", "Pelanggaran", "Akurasi", "Ditangani", "Catatan"]
    col_w    = [38, 28, 38, 18, 20, 48]

    pdf.set_fill_color(30, 30, 30)
    pdf.set_text_color(255, 255, 255)
    pdf.set_font("Helvetica", "B", 8)
    for h, w in zip(headers, col_w):
        pdf.cell(w, 7, h, border=1, fill=True)
    pdf.ln()

    pdf.set_text_color(0, 0, 0)
    pdf.set_font("Helvetica", size=7)
    for _, row in dataframe[cols].iterrows():
        for col, w in zip(cols, col_w):
            val = row[col]
            if col == "status":
                val = "Ya" if val else "Tidak"
            elif col == "confidence_score":
                val = f"{float(val):.2f}"
            cell_text = str(val)[:30]
            pdf.cell(w, 6, cell_text, border=1)
        pdf.ln()

    return bytes(pdf.output())

# ==========================================
# DATA & STATE
# ==========================================
raw_data = fetch_logs()
df       = pd.DataFrame(raw_data) if raw_data else pd.DataFrame()
user     = st.session_state.user
is_admin = user["permissions"] == "full_access"

# Daftar kamera yang diketahui (gabungkan dari data + kamera bawaan)
KNOWN_CAMS = ["CAM_WEBCAM", "CAM_DROIDCAM"]
if not df.empty and "camera_id" in df.columns:
    extra = [c for c in df["camera_id"].unique().tolist() if c not in KNOWN_CAMS]
    KNOWN_CAMS = KNOWN_CAMS + extra

# ==========================================
# SIDEBAR
# ==========================================
st.sidebar.title("🛡️ K3 Safety System")
st.sidebar.success(f"👤 {user['name']}")
st.sidebar.info(f"Role: {user['role']}")
st.sidebar.divider()
if st.sidebar.button("🚪 Logout", width='stretch'):
    for k in ["authenticated", "user", "token"]:
        st.session_state[k] = None if k != "authenticated" else False
    st.rerun()

# ==========================================
# TABS (berdasarkan role)
# ==========================================
if is_admin:
    tab_live, tab_log, tab_admin = st.tabs([
        "🎥 Live Feeds",
        "📋 Violations Log",
        "🛠 Manage Users",
    ])
else:
    tab_live, tab_log = st.tabs([
        "🎥 Live Feeds",
        "📋 Violations Log",
    ])


# ------------------------------------------
# TAB 1: LIVE FEEDS
# ------------------------------------------
with tab_live:
    st.subheader("🔴 Real-Time Camera Monitoring")
    # Grid 2 kolom; tambah baris otomatis jika ada lebih dari 2 kamera
    cols_per_row = 2
    for i in range(0, len(KNOWN_CAMS), cols_per_row):
        row_cams = KNOWN_CAMS[i : i + cols_per_row]
        cols = st.columns(len(row_cams))
        for col, cam in zip(cols, row_cams):
            with col:
                st.markdown(f"**{cam}**")
                st.image(
                    f"{LIVE_BASE}/{cam}.jpg?t={time.time()}", 
                    width='stretch'
                )


# ------------------------------------------
# TAB 2: VIOLATIONS LOG
# ------------------------------------------
with tab_log:
    # Baris atas: kamera fokus (kiri) + tabel (kanan)
    col_feed, col_data = st.columns([1, 2.5])

    with col_feed:
        st.markdown("##### 🔍 Fokus Pemantauan")
        selected_cam = st.selectbox(
            "Pilih Kamera:", KNOWN_CAMS, label_visibility="collapsed"
        )
        st.image(f"{LIVE_BASE}/{selected_cam}.jpg?t={time.time()}", width='stretch')
        st.caption(f"Live feed — {selected_cam}")

    with col_data:
        if df.empty:
            st.info("Belum ada log pelanggaran yang terekam.")
        else:
            # ---- FILTER PANEL ----
            if is_admin:
                f1, f2, f3 = st.columns(3)
            else:
                f1, f2, f3, f4 = st.columns(4)

            with f1:
                cam_opts   = df["camera_id"].unique().tolist()
                filter_cam = st.multiselect("Kamera:", cam_opts, default=cam_opts)

            with f2:
                filter_status = st.selectbox(
                    "Status:", ["Semua", "Belum Ditangani", "Sudah Ditangani"]
                )

            if not is_admin:
                # Supervisor mendapat filter tanggal & jam
                with f3:
                    filter_date_from = st.date_input("Dari tanggal:", value=None)
                with f4:
                    filter_date_to   = st.date_input("Sampai tanggal:", value=None)

            # ---- TERAPKAN FILTER ----
            filtered_df = df[df["camera_id"].isin(filter_cam)].copy()

            if filter_status == "Belum Ditangani":
                filtered_df = filtered_df[filtered_df["status"] == False]
            elif filter_status == "Sudah Ditangani":
                filtered_df = filtered_df[filtered_df["status"] == True]

            if not is_admin:
                if filter_date_from:
                    filtered_df = filtered_df[
                        filtered_df["timestamp"] >= str(filter_date_from)
                    ]
                if filter_date_to:
                    # inklusif: ambil semua hingga akhir hari filter_date_to
                    filtered_df = filtered_df[
                        filtered_df["timestamp"] <= str(filter_date_to) + " 23:59:59"
                    ]

            # Pastikan urutan: terbaru di atas
            filtered_df = filtered_df.sort_values("timestamp", ascending=False)

            # ---- ADMIN: export buttons di atas tabel ----
            if is_admin:
                exp_col1, exp_col2, exp_spacer = st.columns([1, 1, 4])
                with exp_col1:
                    csv_bytes = filtered_df.to_csv(index=False).encode("utf-8")
                    st.download_button(
                        label="📥 Unduh CSV",
                        data=csv_bytes,
                        file_name=f"K3_Log_{pd.Timestamp.now().strftime('%Y%m%d')}.csv",
                        mime="text/csv",
                        width='stretch',
                    )
                with exp_col2:
                    pdf_bytes = generate_pdf(filtered_df)
                    if pdf_bytes:
                        st.download_button(
                            label="📄 Unduh PDF",
                            data=pdf_bytes,
                            file_name=f"K3_Log_{pd.Timestamp.now().strftime('%Y%m%d')}.pdf",
                            mime="application/pdf",
                            width='stretch',
                        )
                    else:
                        st.button(
                            "📄 Unduh PDF",
                            disabled=True,
                            width='stretch',
                            help="Install fpdf2: pip install fpdf2",
                        )

            st.markdown("##### 📑 Riwayat Pelanggaran")

            # ---- SUPERVISOR: tabel editable ----
            if not is_admin:
                st.caption(
                    "💡 Centang 'Ditangani?' dan isi 'Catatan' setelah memberikan teguran, "
                    "lalu klik Simpan Perubahan."
                )
                edited_df = st.data_editor(
                    filtered_df[[
                        "id", "timestamp", "camera_id",
                        "violation_name", "status", "notes", "video_url"
                    ]],
                    column_config={
                        "id"            : None,
                        "timestamp"     : "Waktu Kejadian",
                        "camera_id"     : "Kamera",
                        "violation_name": "Jenis Pelanggaran",
                        "status"        : st.column_config.CheckboxColumn("Ditangani?", default=False),
                        "notes"         : st.column_config.TextColumn("Catatan Tindakan", max_chars=200),
                        "video_url"     : st.column_config.LinkColumn("Bukti", display_text="Lihat Foto"),
                    },
                    disabled=["timestamp", "camera_id", "violation_name", "video_url"],
                    width='stretch',
                    hide_index=True,
                    key="supervisor_editor",
                )
                if st.button("💾 Simpan Perubahan", width='stretch'):
                    changed = 0
                    for idx, row in edited_df.iterrows():
                        orig = filtered_df.loc[idx]
                        if row["status"] != orig["status"] or row["notes"] != orig["notes"]:
                            update_violation(orig["id"], row["status"], row["notes"])
                            changed += 1
                    st.success(f"{'Tidak ada' if changed == 0 else changed} baris diperbarui.")

            # ---- ADMIN: tabel read-only ----
            else:
                st.dataframe(
                    filtered_df[[
                        "timestamp", "camera_id", "violation_name",
                        "confidence_score", "status", "notes", "video_url"
                    ]],
                    column_config={
                        "timestamp"       : "Waktu Kejadian",
                        "camera_id"       : "Sumber Kamera",
                        "violation_name"  : "Jenis Pelanggaran",
                        "confidence_score": st.column_config.NumberColumn("Akurasi AI", format="%.2f"),
                        "status"          : st.column_config.CheckboxColumn("Ditangani?"),
                        "notes"           : "Catatan Supervisor",
                        "video_url"       : st.column_config.LinkColumn("Bukti", display_text="Lihat Foto"),
                    },
                    width='stretch',
                    hide_index=True,
                )

    # ---- INSPEKSI BUKTI VISUAL (kedua role) ----
    if not df.empty and not filtered_df.empty:
        st.divider()
        st.markdown("#### 🔎 Inspeksi Bukti Visual")
        inspect_ts = st.selectbox(
            "Pilih kejadian:", filtered_df["timestamp"].tolist()
        )
        if inspect_ts:
            row = filtered_df[filtered_df["timestamp"] == inspect_ts].iloc[0]
            with st.expander(f"Foto: {row['violation_name']}  —  {row['camera_id']}", expanded=True):
                st.image(row["video_url"], width='stretch')


# ------------------------------------------
# TAB 3: MANAGE USERS (Admin only)
# ------------------------------------------
if is_admin:
    with tab_admin:
        st.subheader("Manajemen Akun Sistem")

        users_data = fetch_users()
        users_df   = pd.DataFrame(users_data) if users_data else pd.DataFrame()

        # ---- Daftar Akun ----
        st.markdown("##### 👥 Daftar Akun Aktif")
        if users_df.empty:
            st.info("Belum ada akun di database.")
        else:
            display_df = users_df[["id", "username", "full_name", "role", "permissions"]].copy()
            display_df.columns = ["ID", "Username", "Nama Lengkap", "Role", "Akses"]
            st.dataframe(display_df, width='stretch', hide_index=True)

        st.divider()

        # ---- Tambah Akun ----
        with st.expander("➕ Tambah Akun Baru"):
            with st.form("form_create_user"):
                c1, c2 = st.columns(2)
                with c1:
                    new_username  = st.text_input("Username")
                    new_fullname  = st.text_input("Nama Lengkap")
                with c2:
                    new_password  = st.text_input("Password", type="password")
                    new_role      = st.selectbox("Role", ["Supervisor", "Admin"])

                new_perms = "full_access" if new_role == "Admin" else "view_only"
                st.caption(f"Akses otomatis: **{new_perms}**")

                if st.form_submit_button("Buat Akun", width='stretch'):
                    if not all([new_username, new_password, new_fullname]):
                        st.error("Semua field wajib diisi.")
                    else:
                        ok, msg = create_user_api({
                            "username"   : new_username,
                            "password"   : new_password,
                            "full_name"  : new_fullname,
                            "role"       : new_role,
                            "permissions": new_perms,
                        })
                        (st.success if ok else st.error)(msg)
                        if ok:
                            st.rerun()

        # ---- Edit Akun ----
        if not users_df.empty:
            with st.expander("✏️ Edit Akun"):
                edit_options = {
                    f"{r['username']} ({r['full_name']})": r["id"]
                    for r in users_data
                }
                edit_label = st.selectbox("Pilih akun:", list(edit_options.keys()))
                edit_id    = edit_options[edit_label]
                edit_user  = next(u for u in users_data if u["id"] == edit_id)

                with st.form("form_edit_user"):
                    e1, e2 = st.columns(2)
                    with e1:
                        e_fullname = st.text_input("Nama Lengkap", value=edit_user["full_name"])
                        e_role     = st.selectbox(
                            "Role", ["Supervisor", "Admin"],
                            index=0 if edit_user["role"] == "Supervisor" else 1,
                        )
                    with e2:
                        e_password = st.text_input(
                            "Password Baru (kosongkan jika tidak diubah)", type="password"
                        )
                    e_perms = "full_access" if e_role == "Admin" else "view_only"
                    st.caption(f"Akses otomatis: **{e_perms}**")

                    if st.form_submit_button("Simpan Perubahan", width='stretch'):
                        payload = {
                            "full_name"  : e_fullname,
                            "role"       : e_role,
                            "permissions": e_perms,
                        }
                        if e_password:
                            payload["password"] = e_password
                        ok, msg = update_user_api(edit_id, payload)
                        (st.success if ok else st.error)(msg)
                        if ok:
                            st.rerun()

            # ---- Hapus Akun ----
            with st.expander("🗑️ Hapus Akun"):
                del_options = {
                    f"{r['username']} ({r['full_name']})": r["id"]
                    for r in users_data
                }
                del_label = st.selectbox(
                    "Pilih akun yang akan dihapus:", list(del_options.keys()), key="del_select"
                )
                del_id = del_options[del_label]
                st.warning(f"Tindakan ini tidak dapat dibatalkan. Akun **{del_label}** akan dihapus permanen.")
                if st.button("🗑️ Hapus Akun Ini", type="primary", width='stretch'):
                    ok, msg = delete_user_api(del_id)
                    (st.success if ok else st.error)(msg)
                    if ok:
                        st.rerun()

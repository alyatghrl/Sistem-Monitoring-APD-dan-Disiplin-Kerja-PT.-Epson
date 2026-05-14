# Add this at the VERY top of your script
import logging
# Suppress the __about__ attribute error warning
logging.getLogger('passlib').setLevel(logging.ERROR)


import sqlite3
from passlib.context import CryptContext

import bcrypt
# Monkeypatch bcrypt to fix passlib compatibility
if not hasattr(bcrypt, "__about__"):
    bcrypt.__about__ = type('About', (object,), {'__version__': bcrypt.__version__})

# Inisialisasi hashing (sama dengan yang digunakan di main.py)
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def get_password_hash(password):
    return pwd_context.hash(password)

def init_user_db():
    # Menghubungkan ke database yang sama dengan violations (atau buat baru)
    conn = sqlite3.connect('violations.db')
    cursor = conn.cursor()

    # 1. Buat tabel users
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            hashed_password TEXT NOT NULL,
            full_name TEXT NOT NULL,
            role TEXT NOT NULL,
            permissions TEXT NOT NULL
        )
    ''')

    # 2. Data dummy untuk seeding
    users_to_create = [
        ("manager1", "password123", "Fayza Avieninda", "Manager", "full_access"),
        ("supervisor1", "password456", "Staff K3 Lapangan", "Supervisor", "view_only")
    ]

    # 3. Masukkan data ke tabel (dengan proteksi terhadap duplikasi)
    for username, password, full_name, role, perms in users_to_create:
        hashed = get_password_hash(password)
        try:
            cursor.execute('''
                INSERT INTO users (username, hashed_password, full_name, role, permissions)
                VALUES (?, ?, ?, ?, ?)
            ''', (username, hashed, full_name, role, perms))
            print(f"✅ User {username} berhasil dibuat.")
        except sqlite3.IntegrityError:
            print(f"⚠️ User {username} sudah ada, melewati proses pembuatan.")

    conn.commit()
    conn.close()
    print("\n🚀 Database User siap digunakan.")

if __name__ == "__main__":
    init_user_db()
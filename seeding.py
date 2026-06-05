import bcrypt
from sqlalchemy.orm import Session

# Import dari database.py yang sudah ada
from database import SessionLocal, DBUser

def get_password_hash(password: str) -> str:
    # Menggunakan bcrypt murni tanpa passlib (Sangat Stabil!)
    salt = bcrypt.gensalt()
    hashed = bcrypt.hashpw(password.encode('utf-8'), salt)
    return hashed.decode('utf-8')

def seed_users():
    """Menginjeksi user awal hanya jika barisnya belum ada di tabel"""
    db: Session = SessionLocal()
    try:
        users_to_create = [
            {
                "username": "admin1", 
                "password": "password123", 
                "full_name": "Admin Sistem Utama", 
                "role": "Admin", 
                "permissions": "full_access"
            },
            {
                "username": "supervisor1", 
                "password": "password456", 
                "full_name": "Staff K3 Lapangan", 
                "role": "Supervisor", 
                "permissions": "view_only"
            }
        ]

        for user_data in users_to_create:
            existing_user = db.query(DBUser).filter(DBUser.username == user_data["username"]).first()
            
            if not existing_user:
                hashed = get_password_hash(user_data["password"])
                new_user = DBUser(
                    username=user_data["username"],
                    hashed_password=hashed,
                    full_name=user_data["full_name"],
                    role=user_data["role"],
                    permissions=user_data["permissions"]
                )
                db.add(new_user)
                db.commit()
                print(f"✅ User '{user_data['username']}' berhasil dibuat.")
            else:
                print(f"⏩ Melewati pembuatan '{user_data['username']}' (Sudah ada di database).")
                
    except Exception as e:
        db.rollback()
        print(f"⚠️ Error saat melakukan seeding: {e}")
    finally:
        db.close()
        print("🚀 Proses pengecekan/seeding selesai.")

if __name__ == "__main__":
    print("Memulai proses inisialisasi database user...")
    seed_users()
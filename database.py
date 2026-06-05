from sqlalchemy import create_engine, Column, Integer, String, Float
from sqlalchemy.orm import declarative_base, sessionmaker

SQLALCHEMY_DATABASE_URL = "sqlite:///./violations.db"

engine       = create_engine(
    SQLALCHEMY_DATABASE_URL,
    connect_args={"check_same_thread": False}
)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base         = declarative_base()

class DBViolation(Base):
    __tablename__ = "violations"

    id               = Column(Integer, primary_key=True, index=True)
    timestamp        = Column(String)
    violation_type   = Column(Integer)
    confidence_score = Column(Float)
    video_directory  = Column(String)
    camera_id        = Column(String)
    status           = Column(Integer, default=0)   # 0: belum ditangani, 1: sudah
    notes            = Column(String,  default="")


class DBUser(Base):
    __tablename__ = "users"

    id              = Column(Integer, primary_key=True, index=True)
    username        = Column(String, unique=True, index=True)
    hashed_password = Column(String)
    full_name       = Column(String)
    role            = Column(String)
    permissions     = Column(String)


# Buat tabel jika belum ada
Base.metadata.create_all(bind=engine)

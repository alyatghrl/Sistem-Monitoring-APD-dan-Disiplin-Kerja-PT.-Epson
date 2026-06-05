from pydantic import BaseModel
from typing import List, Optional

# ==========================================
# VIOLATION SCHEMAS
# ==========================================

class ViolationCreate(BaseModel):
    timestamp       : Optional[str]       = None
    violation_type  : Optional[int]       = None
    confidence_score: Optional[float]     = 0.0
    video_directory : Optional[str]       = None
    camera_id       : Optional[str]       = None
    violations      : Optional[List[str]] = None   # format alternatif dari script AI
    evidence_image  : Optional[str]       = None

class ViolationUpdate(BaseModel):
    status: Optional[int] = None
    notes : Optional[str] = None

class ViolationLog(BaseModel):
    id              : int
    timestamp       : str
    violation_name  : str
    camera_id       : str
    confidence_score: float
    status          : bool
    notes           : str
    video_url       : str

    class Config:
        from_attributes = True

class ViolationResponse(BaseModel):
    status     : str
    data_count : int
    logs       : List[ViolationLog]


# ==========================================
# AUTH SCHEMAS
# ==========================================

class LoginRequest(BaseModel):
    username: str
    password: str


# ==========================================
# USER MANAGEMENT SCHEMAS (Admin CRUD)
# ==========================================

class UserCreate(BaseModel):
    username  : str
    password  : str
    full_name : str
    role      : str         # "Admin" | "Supervisor"
    permissions: str        # "full_access" | "view_only"

class UserUpdate(BaseModel):
    """Semua field opsional — hanya kirim yang ingin diubah."""
    full_name  : Optional[str] = None
    role       : Optional[str] = None
    permissions: Optional[str] = None
    password   : Optional[str] = None   # jika diisi, password akan di-hash ulang

class UserResponse(BaseModel):
    id         : int
    username   : str
    full_name  : str
    role       : str
    permissions: str

    class Config:
        from_attributes = True
from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel, EmailStr, constr


class UserCreate(BaseModel):
    email: EmailStr
    password: str


class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"


class UserOut(BaseModel):
    id: int
    email: EmailStr
    role: str

    class Config:
        orm_mode = True


class AppProjectBase(BaseModel):
    name: str
    package_name: constr(regex=r"^[a-zA-Z]+[\w\.]+$")
    url: str
    min_sdk: int
    target_sdk: int
    version_code: int
    version_name: str


class AppProjectCreate(AppProjectBase):
    pass


class AppProjectUpdate(BaseModel):
    name: Optional[str]
    url: Optional[str]
    min_sdk: Optional[int]
    target_sdk: Optional[int]
    version_code: Optional[int]
    version_name: Optional[str]


class KeystoreMeta(BaseModel):
    id: int
    alias: str
    download_allowed: bool
    created_at: datetime

    class Config:
        orm_mode = True


class BuildJobOut(BaseModel):
    id: int
    status: str
    created_at: datetime
    updated_at: datetime
    finished_at: Optional[datetime]
    apk_path: Optional[str]
    aab_path: Optional[str]
    log: Optional[str]

    class Config:
        orm_mode = True


class AppProjectDetail(AppProjectBase):
    id: int
    owner_user_id: int
    icon_path: Optional[str]
    created_at: datetime
    updated_at: datetime
    keystore: Optional[KeystoreMeta]
    build_jobs: List[BuildJobOut] = []

    class Config:
        orm_mode = True


class KeystoreRequestOut(BaseModel):
    id: int
    keystore_id: int
    user_id: int
    status: str
    admin_id: Optional[int]
    created_at: datetime
    decision_at: Optional[datetime]

    class Config:
        orm_mode = True

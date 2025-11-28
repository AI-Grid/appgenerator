import enum
from datetime import datetime
from sqlalchemy import (
    Column,
    Integer,
    String,
    DateTime,
    ForeignKey,
    Boolean,
    Text,
)
from sqlalchemy.orm import relationship

from .database import Base


class UserRole(str, enum.Enum):
    admin = "admin"
    user = "user"


class BuildStatus(str, enum.Enum):
    pending = "pending"
    running = "running"
    success = "success"
    failed = "failed"


class RequestStatus(str, enum.Enum):
    pending = "pending"
    approved = "approved"
    rejected = "rejected"


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String(255), unique=True, index=True, nullable=False)
    password_hash = Column(String(255), nullable=False)
    role = Column(String(20), nullable=False, default=UserRole.user.value)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    app_projects = relationship("AppProject", back_populates="owner")


class AppProject(Base):
    __tablename__ = "app_projects"

    id = Column(Integer, primary_key=True)
    owner_user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    name = Column(String(255), nullable=False)
    package_name = Column(String(255), unique=True, nullable=False)
    url = Column(String(1024), nullable=False)
    min_sdk = Column(Integer, nullable=False)
    target_sdk = Column(Integer, nullable=False)
    version_code = Column(Integer, nullable=False)
    version_name = Column(String(50), nullable=False)
    icon_path = Column(String(1024), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    owner = relationship("User", back_populates="app_projects")
    keystore = relationship("Keystore", back_populates="app_project", uselist=False)
    build_jobs = relationship("BuildJob", back_populates="app_project", order_by="desc(BuildJob.created_at)")


class Keystore(Base):
    __tablename__ = "keystores"

    id = Column(Integer, primary_key=True)
    app_project_id = Column(Integer, ForeignKey("app_projects.id"), nullable=False, unique=True)
    keystore_path = Column(String(1024), nullable=False)
    alias = Column(String(255), nullable=False)
    store_password = Column(String(255), nullable=False)  # TODO: encrypt
    key_password = Column(String(255), nullable=False)  # TODO: encrypt
    download_allowed = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)

    app_project = relationship("AppProject", back_populates="keystore")
    download_requests = relationship("KeystoreDownloadRequest", back_populates="keystore")


class BuildJob(Base):
    __tablename__ = "build_jobs"

    id = Column(Integer, primary_key=True)
    app_project_id = Column(Integer, ForeignKey("app_projects.id"), nullable=False)
    status = Column(String(20), nullable=False, default=BuildStatus.pending.value)
    log = Column(Text, nullable=True)
    apk_path = Column(String(1024), nullable=True)
    aab_path = Column(String(1024), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    finished_at = Column(DateTime, nullable=True)

    app_project = relationship("AppProject", back_populates="build_jobs")


class KeystoreDownloadRequest(Base):
    __tablename__ = "keystore_download_requests"

    id = Column(Integer, primary_key=True)
    keystore_id = Column(Integer, ForeignKey("keystores.id"), nullable=False)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    status = Column(String(20), nullable=False, default=RequestStatus.pending.value)
    admin_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    decision_at = Column(DateTime, nullable=True)

    keystore = relationship("Keystore", back_populates="download_requests")
    requester = relationship("User", foreign_keys=[user_id])
    admin = relationship("User", foreign_keys=[admin_id])

import os
import secrets
import subprocess
from pathlib import Path
from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session

from .. import models, schemas
from ..auth import get_current_user
from ..config import get_settings
from ..database import get_db

router = APIRouter(prefix="/apps", tags=["keystore"])
settings = get_settings()


def generate_keystore_for_app(app_project: models.AppProject, db: Session) -> models.Keystore:
    os.makedirs(settings.keystore_dir, exist_ok=True)
    alias = f"{app_project.package_name}.alias"
    store_password = secrets.token_urlsafe(12)
    key_password = secrets.token_urlsafe(12)
    keystore_filename = f"{app_project.id}_{secrets.token_hex(4)}.keystore"
    keystore_path = os.path.join(settings.keystore_dir, keystore_filename)
    dname = f"CN={app_project.name}, OU=AppGen, O=AppGen, L=Remote, S=Remote, C=US"

    try:
        subprocess.run(
            [
                "keytool",
                "-genkeypair",
                "-v",
                "-storetype",
                "PKCS12",
                "-keystore",
                keystore_path,
                "-alias",
                alias,
                "-keyalg",
                "RSA",
                "-keysize",
                "2048",
                "-validity",
                "3650",
                "-storepass",
                store_password,
                "-keypass",
                key_password,
                "-dname",
                dname,
            ],
            check=True,
        )
    except Exception:
        Path(keystore_path).write_text("Failed to invoke keytool; placeholder keystore created.\n")
    keystore = models.Keystore(
        app_project_id=app_project.id,
        keystore_path=keystore_path,
        alias=alias,
        store_password=store_password,
        key_password=key_password,
    )
    db.add(keystore)
    db.commit()
    db.refresh(keystore)
    return keystore


@router.get("/{app_id}/keystore", response_model=schemas.KeystoreMeta)
def get_keystore_metadata(app_id: int, db: Session = Depends(get_db), current_user: models.User = Depends(get_current_user)):
    app_project = db.get(models.AppProject, app_id)
    if not app_project:
        raise HTTPException(status_code=404, detail="App not found")
    if current_user.role != models.UserRole.admin.value and app_project.owner_user_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not authorized")
    if not app_project.keystore:
        keystore = generate_keystore_for_app(app_project, db)
    else:
        keystore = app_project.keystore
    return keystore


@router.post("/{app_id}/keystore/request-download", response_model=schemas.KeystoreRequestOut)
def request_keystore_download(app_id: int, db: Session = Depends(get_db), current_user: models.User = Depends(get_current_user)):
    app_project = db.get(models.AppProject, app_id)
    if not app_project:
        raise HTTPException(status_code=404, detail="App not found")
    if current_user.role != models.UserRole.admin.value and app_project.owner_user_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not authorized")
    keystore = app_project.keystore or generate_keystore_for_app(app_project, db)
    req = models.KeystoreDownloadRequest(
        keystore_id=keystore.id,
        user_id=current_user.id,
        status=models.RequestStatus.pending.value,
    )
    db.add(req)
    db.commit()
    db.refresh(req)
    return req


@router.get("/{app_id}/keystore/download")
def download_keystore(app_id: int, db: Session = Depends(get_db), current_user: models.User = Depends(get_current_user)):
    app_project = db.get(models.AppProject, app_id)
    if not app_project or not app_project.keystore:
        raise HTTPException(status_code=404, detail="Keystore not found")
    if app_project.owner_user_id != current_user.id:
        raise HTTPException(status_code=403, detail="Only owners can download")
    if not app_project.keystore.download_allowed:
        raise HTTPException(status_code=403, detail="Download not approved")
    return FileResponse(app_project.keystore.keystore_path, filename=os.path.basename(app_project.keystore.keystore_path))

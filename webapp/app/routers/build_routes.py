import os
from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session

from .. import models, schemas
from ..auth import get_current_user
from ..config import get_settings
from ..database import get_db

router = APIRouter(tags=["builds"])
settings = get_settings()


@router.post("/apps/{app_id}/build", response_model=schemas.BuildJobOut)
def create_build(app_id: int, db: Session = Depends(get_db), current_user: models.User = Depends(get_current_user)):
    app_project = db.get(models.AppProject, app_id)
    if not app_project:
        raise HTTPException(status_code=404, detail="App not found")
    if current_user.role != models.UserRole.admin.value and app_project.owner_user_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not authorized")
    job = models.BuildJob(app_project_id=app_project.id, status=models.BuildStatus.pending.value)
    db.add(job)
    db.commit()
    db.refresh(job)
    return job


@router.get("/apps/{app_id}/builds", response_model=list[schemas.BuildJobOut])
def list_builds(app_id: int, db: Session = Depends(get_db), current_user: models.User = Depends(get_current_user)):
    app_project = db.get(models.AppProject, app_id)
    if not app_project:
        raise HTTPException(status_code=404, detail="App not found")
    if current_user.role != models.UserRole.admin.value and app_project.owner_user_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not authorized")
    return app_project.build_jobs


@router.get("/builds/{build_id}", response_model=schemas.BuildJobOut)
def get_build(build_id: int, db: Session = Depends(get_db), current_user: models.User = Depends(get_current_user)):
    build = db.get(models.BuildJob, build_id)
    if not build:
        raise HTTPException(status_code=404, detail="Build not found")
    app_project = db.get(models.AppProject, build.app_project_id)
    if current_user.role != models.UserRole.admin.value and app_project.owner_user_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not authorized")
    return build


@router.get("/builds/{build_id}/download/apk")
def download_apk(build_id: int, db: Session = Depends(get_db), current_user: models.User = Depends(get_current_user)):
    build = db.get(models.BuildJob, build_id)
    if not build or not build.apk_path:
        raise HTTPException(status_code=404, detail="APK not found")
    app_project = db.get(models.AppProject, build.app_project_id)
    if current_user.role != models.UserRole.admin.value and app_project.owner_user_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not authorized")
    if build.status != models.BuildStatus.success.value:
        raise HTTPException(status_code=400, detail="Build not successful")
    return FileResponse(build.apk_path, filename=os.path.basename(build.apk_path))


@router.get("/builds/{build_id}/download/aab")
def download_aab(build_id: int, db: Session = Depends(get_db), current_user: models.User = Depends(get_current_user)):
    build = db.get(models.BuildJob, build_id)
    if not build or not build.aab_path:
        raise HTTPException(status_code=404, detail="AAB not found")
    app_project = db.get(models.AppProject, build.app_project_id)
    if current_user.role != models.UserRole.admin.value and app_project.owner_user_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not authorized")
    if build.status != models.BuildStatus.success.value:
        raise HTTPException(status_code=400, detail="Build not successful")
    return FileResponse(build.aab_path, filename=os.path.basename(build.aab_path))

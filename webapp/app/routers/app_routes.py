import os
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File
from fastapi.templating import Jinja2Templates
from fastapi import Request
from sqlalchemy.orm import Session

from .. import models, schemas
from ..auth import get_current_user
from ..config import get_settings
from ..database import get_db
from .keystore_routes import generate_keystore_for_app

router = APIRouter(prefix="/apps", tags=["apps"])
templates = Jinja2Templates(directory="app/templates")
settings = get_settings()


@router.post("", response_model=schemas.AppProjectDetail)
def create_app_project(app: schemas.AppProjectCreate, db: Session = Depends(get_db), current_user: models.User = Depends(get_current_user)):
    existing = db.query(models.AppProject).filter(models.AppProject.package_name == app.package_name).first()
    if existing:
        raise HTTPException(status_code=400, detail="Package name already exists")
    db_app = models.AppProject(owner_user_id=current_user.id, **app.dict())
    db.add(db_app)
    db.commit()
    db.refresh(db_app)
    generate_keystore_for_app(db_app, db)
    return db_app


@router.get("", response_model=list[schemas.AppProjectDetail])
def list_apps(db: Session = Depends(get_db), current_user: models.User = Depends(get_current_user)):
    query = db.query(models.AppProject)
    if current_user.role != models.UserRole.admin.value:
        query = query.filter(models.AppProject.owner_user_id == current_user.id)
    return query.all()


@router.get("/{app_id}", response_model=schemas.AppProjectDetail)
def get_app_detail(app_id: int, db: Session = Depends(get_db), current_user: models.User = Depends(get_current_user)):
    app_project = db.get(models.AppProject, app_id)
    if not app_project:
        raise HTTPException(status_code=404, detail="Not found")
    if current_user.role != models.UserRole.admin.value and app_project.owner_user_id != current_user.id:
        raise HTTPException(status_code=403, detail="Forbidden")
    return app_project


@router.put("/{app_id}", response_model=schemas.AppProjectDetail)
def update_app(app_id: int, update: schemas.AppProjectUpdate, db: Session = Depends(get_db), current_user: models.User = Depends(get_current_user)):
    app_project = db.get(models.AppProject, app_id)
    if not app_project:
        raise HTTPException(status_code=404, detail="Not found")
    if current_user.role != models.UserRole.admin.value and app_project.owner_user_id != current_user.id:
        raise HTTPException(status_code=403, detail="Forbidden")
    for field, value in update.dict(exclude_unset=True).items():
        setattr(app_project, field, value)
    db.commit()
    db.refresh(app_project)
    return app_project


@router.post("/{app_id}/icon")
def upload_icon(app_id: int, file: UploadFile = File(...), db: Session = Depends(get_db), current_user: models.User = Depends(get_current_user)):
    app_project = db.get(models.AppProject, app_id)
    if not app_project:
        raise HTTPException(status_code=404, detail="Not found")
    if current_user.role != models.UserRole.admin.value and app_project.owner_user_id != current_user.id:
        raise HTTPException(status_code=403, detail="Forbidden")
    os.makedirs(settings.icon_dir, exist_ok=True)
    filename = f"{app_id}_{file.filename}"
    path = os.path.join(settings.icon_dir, filename)
    with open(path, "wb") as f:
        f.write(file.file.read())
    app_project.icon_path = path
    db.commit()
    return {"icon_path": path}


@router.get("/{app_id}/view")
def view_app(app_id: int, request: Request, db: Session = Depends(get_db), current_user: models.User = Depends(get_current_user)):
    app_project = db.get(models.AppProject, app_id)
    if not app_project:
        raise HTTPException(status_code=404, detail="Not found")
    if current_user.role != models.UserRole.admin.value and app_project.owner_user_id != current_user.id:
        raise HTTPException(status_code=403, detail="Forbidden")
    return templates.TemplateResponse(
        "app_detail.html",
        {
            "request": request,
            "app": app_project,
            "keystore": app_project.keystore,
            "builds": app_project.build_jobs,
            "user": current_user,
        },
    )

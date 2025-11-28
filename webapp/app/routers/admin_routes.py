from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException
from fastapi.templating import Jinja2Templates
from fastapi import Request
from sqlalchemy.orm import Session

from .. import models, schemas
from ..auth import get_current_admin
from ..database import get_db

router = APIRouter(prefix="/admin", tags=["admin"])
templates = Jinja2Templates(directory="app/templates")


@router.get("/keystore-requests", response_model=list[schemas.KeystoreRequestOut])
def list_requests(db: Session = Depends(get_db), admin: models.User = Depends(get_current_admin)):
    return db.query(models.KeystoreDownloadRequest).filter(models.KeystoreDownloadRequest.status == models.RequestStatus.pending.value).all()


@router.get("/keystore-requests/view")
def view_requests(request: Request, db: Session = Depends(get_db), admin: models.User = Depends(get_current_admin)):
    reqs = db.query(models.KeystoreDownloadRequest).filter(models.KeystoreDownloadRequest.status == models.RequestStatus.pending.value).all()
    return templates.TemplateResponse("admin_keystore_requests.html", {"request": request, "requests": reqs})


@router.post("/keystore-requests/{request_id}/approve")
def approve_request(request_id: int, db: Session = Depends(get_db), admin: models.User = Depends(get_current_admin)):
    req = db.get(models.KeystoreDownloadRequest, request_id)
    if not req:
        raise HTTPException(status_code=404, detail="Request not found")
    req.status = models.RequestStatus.approved.value
    req.admin_id = admin.id
    req.decision_at = datetime.utcnow()
    keystore = db.get(models.Keystore, req.keystore_id)
    if keystore:
        keystore.download_allowed = True
    db.commit()
    return {"status": "approved"}


@router.post("/keystore-requests/{request_id}/reject")
def reject_request(request_id: int, db: Session = Depends(get_db), admin: models.User = Depends(get_current_admin)):
    req = db.get(models.KeystoreDownloadRequest, request_id)
    if not req:
        raise HTTPException(status_code=404, detail="Request not found")
    req.status = models.RequestStatus.rejected.value
    req.admin_id = admin.id
    req.decision_at = datetime.utcnow()
    db.commit()
    return {"status": "rejected"}

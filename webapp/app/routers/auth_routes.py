from datetime import timedelta
from fastapi import APIRouter, Depends, HTTPException, status, Form
from fastapi.responses import JSONResponse, RedirectResponse
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from fastapi.templating import Jinja2Templates
from fastapi import Request

from .. import models, schemas
from ..auth import create_access_token, get_password_hash, verify_password
from ..database import get_db

router = APIRouter(prefix="/auth", tags=["auth"])

templates = Jinja2Templates(directory="app/templates")


@router.get("/login")
def login_page(request: Request):
    return templates.TemplateResponse("login.html", {"request": request})


@router.get("/register")
def register_page(request: Request):
    return templates.TemplateResponse("register.html", {"request": request})


@router.post("/register", response_model=schemas.UserOut)
def register_user(user: schemas.UserCreate, db: Session = Depends(get_db)):
    existing = db.query(models.User).filter(models.User.email == user.email).first()
    if existing:
        raise HTTPException(status_code=400, detail="Email already registered")
    hashed = get_password_hash(user.password)
    db_user = models.User(email=user.email, password_hash=hashed, role=models.UserRole.user.value)
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    return db_user


@router.post("/login", response_model=schemas.Token)
def login_for_access_token(form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    user = db.query(models.User).filter(models.User.email == form_data.username).first()
    if not user or not verify_password(form_data.password, user.password_hash):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Incorrect email or password")
    access_token_expires = timedelta(minutes=60)
    access_token = create_access_token(data={"sub": user.id, "role": user.role}, expires_delta=access_token_expires)
    return schemas.Token(access_token=access_token)


@router.post("/login/form")
def login_form(email: str = Form(...), password: str = Form(...), db: Session = Depends(get_db)):
    user = db.query(models.User).filter(models.User.email == email).first()
    if not user or not verify_password(password, user.password_hash):
        return JSONResponse(status_code=401, content={"detail": "Invalid credentials"})
    token = create_access_token(data={"sub": user.id, "role": user.role})
    response = RedirectResponse(url="/dashboard", status_code=302)
    response.set_cookie("token", token, httponly=True)
    return response


@router.post("/register/form")
def register_form(email: str = Form(...), password: str = Form(...), db: Session = Depends(get_db)):
    existing = db.query(models.User).filter(models.User.email == email).first()
    if existing:
        return JSONResponse(status_code=400, content={"detail": "Email already exists"})
    hashed = get_password_hash(password)
    user = models.User(email=email, password_hash=hashed, role=models.UserRole.user.value)
    db.add(user)
    db.commit()
    return RedirectResponse(url="/auth/login", status_code=302)

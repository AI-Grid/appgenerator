import os
from fastapi import FastAPI, Depends, Request
from fastapi.responses import RedirectResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

from .database import engine, Base
from .auth import get_current_user
from .routers import auth_routes, app_routes, keystore_routes, admin_routes, build_routes

Base.metadata.create_all(bind=engine)

app = FastAPI(title="WebView App Generator")

app.include_router(auth_routes.router)
app.include_router(app_routes.router)
app.include_router(keystore_routes.router)
app.include_router(admin_routes.router)
app.include_router(build_routes.router)

app.mount("/static", StaticFiles(directory="app/static"), name="static")
templates = Jinja2Templates(directory="app/templates")


@app.get("/")
def root():
    return RedirectResponse(url="/dashboard")


@app.get("/dashboard")
def dashboard(request: Request, current_user=Depends(get_current_user)):
    return templates.TemplateResponse("dashboard.html", {"request": request, "user": current_user})

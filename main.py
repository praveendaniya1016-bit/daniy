import os
import re
import time
from pathlib import Path

from fastapi import Depends, FastAPI, File, Form, HTTPException, Request, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

import database
from gemini_utils import generate_recommendations
from security import SESSION_TTL, decode_token, hash_password, issue_token, verify_password
(BASE_DIR / "static").mkdir(parents=True, exist_ok=True)
(BASE_DIR / "templates").mkdir(parents=True, exist_ok=True)

BASE_DIR = Path(__file__).resolve().parent
COOKIE_NAME = "pocketsmart_session"
MAX_IMAGE_BYTES = 5 * 1024 * 1024
CATEGORIES = {"home": "Home", "party": "Party", "jewelry": "Jewelry"}

app = FastAPI(title="PocketSmart AI", description="Budget-aware plans for home, parties, and jewelry.")
app.add_middleware(
    CORSMiddleware,
    allow_origins=[origin.strip() for origin in os.getenv("CORS_ORIGINS", "").split(",") if origin.strip()],
    allow_credentials=True,
    allow_methods=["GET", "POST"],
    allow_headers=["Authorization", "Content-Type"],
)
app.mount("/static", StaticFiles(directory=BASE_DIR / "static"), name="static")
templates = Jinja2Templates(directory=BASE_DIR / "templates")
database.initialize_database()


def current_user(request: Request):
    token = request.cookies.get(COOKIE_NAME)
    authorization = request.headers.get("authorization", "")
    if not token and authorization.lower().startswith("bearer "):
        token = authorization[7:].strip()
    claims = decode_token(token) if token else None
    if not claims:
        return None
    user_id = database.get_session(claims["jti"], int(time.time()))
    return database.get_user_by_id(user_id) if user_id else None


def require_user(user=Depends(current_user)):
    if not user:
        raise HTTPException(status_code=401, detail="Sign in to access this page.")
    return user


def page_context(request, user=None, **extra):
    return {"request": request, "user": user, "categories": CATEGORIES, **extra}


def set_session(response, user_id):
    token, claims = issue_token(user_id)
    database.create_session(claims["jti"], user_id, claims["exp"])
    response.set_cookie(
        COOKIE_NAME,
        token,
        max_age=SESSION_TTL,
        httponly=True,
        secure=os.getenv("COOKIE_SECURE", "false").lower() == "true",
        samesite="lax",
        path="/",
    )
    return token


def clean_text(value, label, maximum=120):
    value = " ".join((value or "").split())
    if not value or len(value) > maximum:
        raise HTTPException(status_code=422, detail=f"Enter {label} (up to {maximum} characters).")
    return value


def clean_budget(budget):
    if budget < 500 or budget > 10_000_000:
        raise HTTPException(status_code=422, detail="Budget must be between ₹500 and ₹1,00,00,000.")
    return round(budget, 2)


def planner_result(category, payload, user, image=None, image_mime=None):
    payload["budget"] = clean_budget(float(payload["budget"]))
    result = generate_recommendations(category, payload, image, image_mime)
    saved_id = database.save_recommendation(user["id"], category, payload, result) if user else None
    return {"category": CATEGORIES[category], "budget": payload["budget"], "recommendation": result, "id": saved_id}


@app.get("/", response_class=HTMLResponse)
def home(request: Request):
    user = current_user(request)
    recent = database.get_history(user["id"], 4) if user else []
    return templates.TemplateResponse(request,"index.html", page_context(request, user, recent=recent))


@app.get("/planner/{category}", response_class=HTMLResponse)
def planner_page(category: str, request: Request):
    if category not in CATEGORIES:
        raise HTTPException(status_code=404, detail="Planner not found.")
    return templates.TemplateResponse(request,"planner.html", page_context(request, current_user(request), category=category))


@app.get("/register", response_class=HTMLResponse)
def register_page(request: Request):
    return templates.TemplateResponse("auth.html", page_context(request, current_user(request), mode="register"))


@app.post("/register")
def register(request: Request, name: str = Form(...), email: str = Form(...), password: str = Form(...)):
    name = clean_text(name, "your name", 80)
    email = email.strip().lower()
    if not re.fullmatch(r"[^\s@]+@[^\s@]+\.[^\s@]+", email) or len(email) > 254:
        return templates.TemplateResponse("auth.html", page_context(request, mode="register", error="Enter a valid email address."), status_code=422)
    if len(password) < 8 or len(password) > 128:
        return templates.TemplateResponse("auth.html", page_context(request, mode="register", error="Use a password between 8 and 128 characters."), status_code=422)
    try:
        user = database.create_user(name, email, hash_password(password))
    except Exception as error:
        if "UNIQUE constraint failed" in str(error):
            return templates.TemplateResponse("auth.html", page_context(request, mode="register", error="That email already has an account."), status_code=409)
        raise
    response = RedirectResponse("/dashboard", status_code=303)
    set_session(response, user["id"])
    return response


@app.get("/login", response_class=HTMLResponse)
def login_page(request: Request):
    return templates.TemplateResponse("auth.html", page_context(request, current_user(request), mode="login"))


@app.post("/login")
def login(request: Request, email: str = Form(...), password: str = Form(...)):
    user = database.get_user_by_email(email.strip().lower())
    if not user or not verify_password(password, user["password_hash"]):
        return templates.TemplateResponse("auth.html", page_context(request, mode="login", error="Email or password didn’t match."), status_code=401)
    response = RedirectResponse("/dashboard", status_code=303)
    set_session(response, user["id"])
    return response


@app.post("/logout")
def logout(request: Request):
    token = request.cookies.get(COOKIE_NAME)
    claims = decode_token(token) if token else None
    if claims:
        database.delete_session(claims["jti"])
    response = RedirectResponse("/", status_code=303)
    response.delete_cookie(COOKIE_NAME, path="/")
    return response


@app.get("/dashboard", response_class=HTMLResponse)
def dashboard(request: Request, user=Depends(require_user)):
    history = database.get_history(user["id"], 8)
    stats = database.get_user_stats(user["id"])
    return templates.TemplateResponse("dashboard.html", page_context(request, user, history=history, stats=stats))


@app.get("/activity", response_class=HTMLResponse)
def activity_page(request: Request, user=Depends(require_user)):
    history = database.get_history(user["id"])
    return templates.TemplateResponse("history.html", page_context(request, user, history=history))


@app.get("/plan/{recommendation_id}", response_class=HTMLResponse)
def recommendation_page(recommendation_id: int, request: Request, user=Depends(require_user)):
    plan = database.get_recommendation(user["id"], recommendation_id)
    if not plan:
        raise HTTPException(status_code=404, detail="Recommendation not found.")
    return templates.TemplateResponse("recommendation.html", page_context(request, user, plan=plan))


@app.get("/testimonials", response_class=HTMLResponse)
def testimonials_page(request: Request):
    return templates.TemplateResponse("testimonials.html", page_context(request, current_user(request)))


@app.post("/generate-home")
def generate_home(
    budget: float = Form(...), room: str = Form(...), style: str = Form(...),
    priority: str = Form(...), user=Depends(current_user),
):
    payload = {"budget": budget, "room": clean_text(room, "a room", 80), "style": clean_text(style, "a style", 80), "priority": clean_text(priority, "a priority", 100)}
    return planner_result("home", payload, user)


@app.post("/generate-party")
def generate_party(
    budget: float = Form(...), guests: int = Form(...), occasion: str = Form(...),
    locality: str = Form(...), date: str = Form(""), user=Depends(current_user),
):
    if guests < 1 or guests > 1000:
        raise HTTPException(status_code=422, detail="Guest count must be between 1 and 1,000.")
    payload = {"budget": budget, "guests": guests, "occasion": clean_text(occasion, "an occasion", 80), "locality": clean_text(locality, "a location", 100), "date": date[:30]}
    return planner_result("party", payload, user)


@app.post("/generate-jewelry")
async def generate_jewelry(
    budget: float = Form(...), occasion: str = Form(...), outfit: str = Form(...),
    style: str = Form(...), image: UploadFile | None = File(None), user=Depends(current_user),
):
    image_data = None
    image_mime = None
    if image and image.filename:
        image_mime = image.content_type or ""
        if image_mime not in {"image/jpeg", "image/png", "image/webp"}:
            raise HTTPException(status_code=422, detail="Upload a JPG, PNG, or WebP image.")
        image_data = await image.read(MAX_IMAGE_BYTES + 1)
        if len(image_data) > MAX_IMAGE_BYTES:
            raise HTTPException(status_code=413, detail="Keep the outfit image under 5 MB.")
    payload = {"budget": budget, "occasion": clean_text(occasion, "an occasion", 80), "outfit": clean_text(outfit, "an outfit description", 180), "style": clean_text(style, "a jewelry style", 80), "image_attached": bool(image_data)}
    return planner_result("jewelry", payload, user, image_data, image_mime)


@app.post("/token")
def token(email: str = Form(...), password: str = Form(...)):
    user = database.get_user_by_email(email.strip().lower())
    if not user or not verify_password(password, user["password_hash"]):
        raise HTTPException(status_code=401, detail="Incorrect email or password.")
    access_token, claims = issue_token(user["id"])
    database.create_session(claims["jti"], user["id"], claims["exp"])
    return {"access_token": access_token, "token_type": "bearer"}


@app.get("/session-info")
def session_info(user=Depends(require_user)):
    return {"authenticated": True, "user_id": user["id"], "name": user["name"], "email": user["email"]}


@app.get("/session-data")
def session_data(user=Depends(require_user)):
    return {"user": user, "recent_recommendations": database.get_history(user["id"], 10)}


@app.get("/history")
def history(user=Depends(require_user)):
    return {"items": database.get_history(user["id"])}


@app.get("/recommendations-details")
def recommendation_details(id: int, user=Depends(require_user)):
    recommendation = database.get_recommendation(user["id"], id)
    if not recommendation:
        raise HTTPException(status_code=404, detail="Recommendation not found.")
    return recommendation


@app.get("/startup")
def startup():
    return {"status": "ready", "gemini_configured": bool(os.getenv("GEMINI_API_KEY")), "database": str(database.DATABASE_PATH.name)}


@app.get("/health")
def health():
    return {"status": "ok"}

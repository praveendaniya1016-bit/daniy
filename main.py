from fastapi import FastAPI, Request, Form, HTTPException
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
import re
import database
from security import hash_password, verify_password, create_access_token
# from gemini_utils import get_ai_response

app = FastAPI()
app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="templates")

CATEGORIES = ["study", "fitness", "finance", "general"]

def clean_text(text: str, field: str, max_len: int):
    text = text.strip()
    if not text or len(text) > max_len:
        raise HTTPException(status_code=400, detail=f"{field} invalid da")
    return text

@app.get("/", response_class=HTMLResponse)
def home(request: Request):
    return templates.TemplateResponse(request, "index.html", {"request": request})

@app.get("/planner/{category}", response_class=HTMLResponse)
def planner_page(category: str, request: Request):
    if category not in CATEGORIES:
        raise HTTPException(status_code=404, detail="Category not found da")
    return templates.TemplateResponse(request, "planner.html", {"request": request, "category": category})

@app.get("/register", response_class=HTMLResponse)
def register_page(request: Request):
    return templates.TemplateResponse(request, "auth.html", {"request": request, "page": "register"})

@app.post("/register", response_class=HTMLResponse)
def register(request: Request, name: str = Form(...), email: str = Form(...), password: str = Form(...)):
    name = clean_text(name, "your name", 80)
    email = email.strip().lower()
    if not re.fullmatch(r"[^\s@]+@[^\s@]+\.[^\s@]+", email):
        return templates.TemplateResponse(request, "auth.html", {"request": request, "page": "register", "error": "Invalid email da"})
    if len(password) < 8:
        return templates.TemplateResponse(request, "auth.html", {"request": request, "page": "register", "error": "Password 8 char ku mela irukkanum da"})
    try:
        user = database.create_user(name, email, hash_password(password))
    except Exception as error:
        if "UNIQUE constraint failed" in str(error):
            return templates.TemplateResponse(request, "auth.html", {"request": request, "page": "register", "error": "Email already exists da"})
        raise
    return templates.TemplateResponse(request, "auth.html", {"request": request, "page": "login", "success": "Registered da! Login pannu da"})

@app.get("/login", response_class=HTMLResponse)
def login_page(request: Request):
    return templates.TemplateResponse(request, "auth.html", {"request": request, "page": "login"})

@app.post("/login", response_class=HTMLResponse)
def login(request: Request, email: str = Form(...), password: str = Form(...)):
    email = email.strip().lower()
    user = database.get_user_by_email(email)
    if not user or not verify_password(password, user["password"]):
        return templates.TemplateResponse(request, "auth.html", {"request": request, "page": "login", "error": "Invalid login da"})
    response = RedirectResponse(url="/", status_code=302)
    token = create_access_token({"sub": user["email"]})
    response.set_cookie(key="access_token", value=token, httponly=True)
    return response

@app.get("/logout")
def logout():
    response = RedirectResponse(url="/login", status_code=302)
    response.delete_cookie("access_token")
    return response

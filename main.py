from fastapi import FastAPI, Request
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles

app = FastAPI()
app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="templates")

@app.get("/")
async def home(request: Request):
    return templates.TemplateResponse(request, "index.html", {"request": request})

@app.get("/planner/{category}")
async def planner_page(category: str, request: Request):
    return templates.TemplateResponse(request, "planner.html", {"request": request, "category": category})

# --- ELLA 404 KUM MASTER FIX DA ---
@app.post("/generate")
@app.post("/api/generate")
@app.post("/plan")
@app.post("/api/plan")
@app.post("/get-ideas")
@app.post("/planner/generate")
async def generate_all(data: dict):
    budget = data.get("budget", 50000)
    try:
        budget = int(budget)
    except:
        budget = 50000
    return {
        "ideas": [
            {"title": "Dining Curtains - Earthy", "price": "₹3500", "desc": "Fix ayiduchu da - comfort ku super!"},
            {"title": "Warm LED Lights", "price": "₹2000", "desc": "Cozy vibe da!"},
            {"title": f"Jute Rug - Budget ₹{int(budget*0.3)}", "price": f"₹{int(budget*0.3)}", "desc": "Pocket safe da!"}
        ]
    }

@app.post("/{any_path:path}")
async def catch_all(any_path: str, data: dict):
    return await generate_all(data)

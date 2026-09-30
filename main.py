from fastapi import FastAPI, Request
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
from fastapi.responses import JSONResponse

app = FastAPI()
app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="templates")

@app.get("/")
async def home(request: Request):
    return templates.TemplateResponse(request, "index.html", {"request": request})

@app.get("/planner/{category}")
async def planner_page(category: str, request: Request):
    return templates.TemplateResponse(request, "planner.html", {"request": request, "category": category})

# --- ENA 404 VARUTHUNU PAATHA FIX DA - ELLA ROUTE UM ---
@app.post("/generate")
@app.post("/api/generate")
@app.post("/plan")
@app.post("/api/plan")
@app.post("/get-ideas")
async def generate_all(data: dict):
    budget = data.get("budget", 25000)
    return {
        "ideas": [
            {"title": "Earthy Curtains - Dining", "price": "₹3500", "desc": "Comfort & soft furnishings ku sema da"},
            {"title": "Warm LED Lights", "price": "₹2000", "desc": "Cozy vibe varum da"},
            {"title": f"Budget Rug under ₹{int(int(budget)*0.3)}", "price": f"₹{int(int(budget)*0.3)}", "desc": "Pocket smart ah irukkum da"}
        ]
    }

@app.get("/health")
async def health():
    return {"status": "ok"}

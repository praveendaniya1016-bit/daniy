from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI()
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])

users = {}

@app.get("/", response_class=HTMLResponse)
async def home():
    return HTMLResponse('<html><head><meta http-equiv="refresh" content="0; url=/login"></head></html>')

@app.get("/login", response_class=HTMLResponse)
async def login_page():
    return HTMLResponse("""
    <html><body style="font-family:sans-serif; padding:40px; background:#f0f0ff">
    <h2>PocketSmart AI - Login Da! 🚀</h2>
    <form method="post" action="/login" style="display:flex; flex-direction:column; gap:10px; max-width:300px">
    <input name="email" placeholder="demo@gmail.com" value="demo@gmail.com" style="padding:10px">
    <input name="password" type="password" placeholder="123456" value="123456" style="padding:10px">
    <button type="submit" style="padding:12px; background:#6c5ce7; color:white; border:none; border-radius:8px; font-weight:bold">Login Da!</button>
    </form>
    <br><a href="/register">New user? Register Da</a>
    <br><br><a href="/dashboard" style="color:green; font-weight:bold">Direct Dashboard ku Poo Da (Skip Login)</a>
    </body></html>
    """)

@app.get("/register", response_class=HTMLResponse)
async def register_page():
    return HTMLResponse("""
    <html><body style="font-family:sans-serif; padding:40px; background:#f0f0ff">
    <h2>PocketSmart AI - Register Da! 🎉</h2>
    <form method="post" action="/register" style="display:flex; flex-direction:column; gap:10px; max-width:300px">
    <input name="name" placeholder="Name" required style="padding:10px">
    <input name="email" placeholder="Email" required style="padding:10px">
    <input name="password" type="password" placeholder="Password" required style="padding:10px">
    <button type="submit" style="padding:12px; background:#6c5ce7; color:white; border:none; border-radius:8px">Register Da!</button>
    </form><br><a href="/login">Already have account? Login Da</a>
    </body></html>
    """)

@app.post("/login")
@app.post("/register")
async def auth_post(request: Request):
    return HTMLResponse('<html><head><meta http-equiv="refresh" content="0; url=/dashboard"></head><body>Success Da!</body></html>')

@app.get("/dashboard", response_class=HTMLResponse)
async def dashboard():
    return HTMLResponse("""
    <html><body style="font-family:sans-serif; padding:20px; background:#6c5ce7; min-height:100vh">
    <div style="background:white; padding:20px; border-radius:15px">
    <h2>Welcome Demo Da! 🎉</h2>
    <h1 style="text-align:center; color:#6c5ce7">Your Pocket AI Assistant Da! 🚀</h1>
    <div style="display:flex; gap:15px; justify-content:center; margin-top:30px; flex-wrap:wrap">
        <a href="/planner/home" style="padding:30px; background:#ffeaa7; text-decoration:none; border-radius:15px; color:black; text-align:center; width:140px"><div style="font-size:30px">🏠</div><b>Home Plan</b></a>
        <a href="/planner/jewellery" style="padding:30px; background:#fab1a0; text-decoration:none; border-radius:15px; color:black; text-align:center; width:140px"><div style="font-size:30px">💍</div><b>Jewellery Plan</b></a>
        <a href="/planner/party" style="padding:30px; background:#a29bfe; text-decoration:none; border-radius:15px; color:black; text-align:center; width:140px"><div style="font-size:30px">🎉</div><b>Party Plan</b></a>
    </div>
    </div></body></html>
    """)

@app.get("/planner/{category}", response_class=HTMLResponse)
async def planner_page(category: str):
    return HTMLResponse(f"""
    <html><body style="padding:30px; font-family:sans-serif; background:#f8f9ff">
    <h2>{category.title()} Planner Da! 💡</h2>
    <label>Budget: <input id="budget" type="number" value="50000" style="padding:10px; border-radius:8px"></label>
    <button onclick="gen()" style="padding:12px 20px; background:#6c5ce7; color:white; border:none; border-radius:8px; margin-left:10px; font-weight:bold">Find my ideas Da!</button>
    <div id="result" style="margin-top:25px"></div>
    <br><br><a href="/dashboard">⬅️ Back to Dashboard Da</a>
    <script>
    function gen(){{
        let b = document.getElementById('budget').value || 50000;
        document.getElementById('result').innerHTML = `
            <div style='background:white; padding:15px; margin:10px 0; border-radius:12px; border-left:5px solid #6c5ce7; box-shadow:0 2px 5px #ccc'>
                <b>1. Earthy Curtains for {category}</b> - <span style='color:green; font-weight:bold'>₹${{Math.floor(b*0.15)}}</span><br>
                <small>Cozy look varum da, budget ku perfect da! 🌟</small>
            </div>
            <div style='background:white; padding:15px; margin:10px 0; border-radius:12px; border-left:5px solid #6c5ce7; box-shadow:0 2px 5px #ccc'>
                <b>2. Warm LED Lights</b> - <span style='color:green; font-weight:bold'>₹${{Math.floor(b*0.1)}}</span><br>
                <small>Veede glow aagum da, super ambience da! ✨</small>
            </div>
            <div style='background:white; padding:15px; margin:10px 0; border-radius:12px; border-left:5px solid #6c5ce7; box-shadow:0 2px 5px #ccc'>
                <b>3. Jute Rug & Planters</b> - <span style='color:green; font-weight:bold'>₹${{Math.floor(b*0.2)}}</span><br>
                <small>Natural vibe, Instagram worthy da! 🪴</small>
            </div>
        `;
    }}
    gen();
    </script>
    </body></html>
    """)

@app.post("/generate")
@app.post("/api/generate")
async def generate_api(request: Request):
    return JSONResponse({"ideas": [{"title": "Demo", "price": "₹100"}]})

@app.get("/logout")
async def logout():
    return HTMLResponse('<html><head><meta http-equiv="refresh" content="0; url=/login"></head></html>')

# PocketSmart AI

A small FastAPI + Jinja budget-planning app for home refreshes, party plans, and jewelry ideas. It includes signed login sessions, JWT authentication, a SQLite plan history, and optional Gemini recommendations with a useful no-key fallback.

## Run locally

```powershell
python -m pip install -r requirements.txt
$env:APP_SECRET = "use-a-long-random-secret-here"
python -m uvicorn main:app --reload
```

Open http://127.0.0.1:8000. The SQLite database is created automatically as `pocketsmart.db` in the project folder. Set `GEMINI_API_KEY` to enable Gemini; without it, the planners return clearly labelled planning estimates. Set `GEMINI_MODEL` to choose a model (default: `gemini-2.5-flash`). For HTTPS deployments, set `COOKIE_SECURE=true` and use a unique `APP_SECRET`.

For a separate frontend origin, set `CORS_ORIGINS` to a comma-separated allowlist (for example, `https://app.example.com`).

## Included routes

- `/` and `/planner/{home|party|jewelry}`: responsive planner forms; jewelry accepts JPG, PNG, and WebP outfit photos up to 5 MB.
- `POST /generate-home`, `POST /generate-party`, `POST /generate-jewelry`: form-data recommendation endpoints.
- `/register`, `/login`, `POST /logout`: account and signed, revocable browser session.
- `POST /token`: email/password form that returns an HS256 bearer token.
- `/dashboard`, `/activity`, `/plan/{id}`, `/testimonials`: saved-plan dashboard, history, readable plan details, and community page.
- `/session-info`, `/session-data`, `/history`, `/recommendations-details?id=...`: authenticated session and recommendation APIs.
- `/startup`, `/health`: service status.

Planning prices are estimates, not live product listings. Retailer links open search pages; confirm availability and final prices with each provider.
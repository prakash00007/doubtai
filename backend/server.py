"""
DoubtAI — FastAPI Server v6
New: Smart Analytics + Weak Topic Detector
"""
import hashlib, time, os, base64
from pathlib import Path
from fastapi import FastAPI, UploadFile, File, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
from typing import Optional
from dotenv import load_dotenv
from solver import solve
from streak import checkin, get_streak
from analytics import log_question, get_analytics, get_global_topics, get_suggestions

load_dotenv()

app = FastAPI(title="DoubtAI API", version="6.0.0")
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])

# If a built frontend exists, serve the React app from FastAPI.
# - Docker deploy copies `frontend/dist` -> `backend/static`
# - Local dev can also run `npm run build` in `frontend/` (creates `frontend/dist`)
_BACKEND_DIR = Path(__file__).resolve().parent
_REPO_DIR = _BACKEND_DIR.parent
_STATIC_DIR = (_BACKEND_DIR / "static") if (_BACKEND_DIR / "static").exists() else (_REPO_DIR / "frontend" / "dist")
_ASSETS_DIR = _STATIC_DIR / "assets"
if _ASSETS_DIR.exists():
    app.mount("/assets", StaticFiles(directory=str(_ASSETS_DIR)), name="assets")

# ── Cache ─────────────────────────────────────────────────────────────────────
_cache = {}

def _cache_key(q, s):
    return hashlib.md5(f"{q.lower().strip()}_{s}".encode()).hexdigest()

# ── Rate limiter ──────────────────────────────────────────────────────────────
_usage = {}
LIMIT = int(os.getenv("FREE_DAILY_LIMIT", 10))

def _ip(req):
    fwd = req.headers.get("x-forwarded-for")
    return fwd.split(",")[0] if fwd else req.client.host

def _check(ip, premium):
    if premium: return
    now = time.time()
    if ip not in _usage:
        _usage[ip] = {"count": 0, "reset": now + 86400}
    u = _usage[ip]
    if now > u["reset"]:
        u["count"] = 0; u["reset"] = now + 86400
    if u["count"] >= LIMIT:
        raise HTTPException(429, f"Free limit of {LIMIT} doubts/day reached.")
    u["count"] += 1

def _left(ip):
    return max(0, LIMIT - _usage.get(ip, {}).get("count", 0))

def _similar(question, subject):
    from groq import Groq
    client = Groq(api_key=os.getenv("GROQ_API_KEY"))
    try:
        r = client.chat.completions.create(
            model="llama-3.1-8b-instant", max_tokens=150,
            messages=[{"role":"user","content":
                f'Based on this {subject} question: "{question}"\n'
                f'Generate exactly 3 related follow-up questions a JEE/NEET student might ask.\n'
                f'Return ONLY the 3 questions, one per line, no numbering.'}]
        )
        lines = r.choices[0].message.content.strip().split('\n')
        return [l.strip() for l in lines if l.strip()][:3]
    except:
        return []

# ── Models ────────────────────────────────────────────────────────────────────
class AskRequest(BaseModel):
    question:   str
    subject:    Optional[str] = "Physics"
    is_premium: Optional[bool] = False
    history:    Optional[list] = []

class AskResponse(BaseModel):
    answer:     str
    sources:    list
    model:      str
    question:   str
    remaining:  Optional[int] = None
    from_cache: Optional[bool] = False
    similar:    Optional[list] = []
    streak:     Optional[dict] = None
    topic:      Optional[str]  = None   # ← detected topic


# ── Core routes ───────────────────────────────────────────────────────────────
@app.get("/api/health")
def health():
    return {"status": "DoubtAI v6.0 🚀", "docs": "/docs"}

@app.get("/stats")
def stats():
    from utils.vector_store import get_stats
    global_data = get_global_topics(5)
    return {**get_stats(), "cached": len(_cache), **global_data}

@app.get("/api/usage")
def usage(request: Request):
    ip = _ip(request)
    used = _usage.get(ip, {}).get("count", 0)
    return {"used": used, "remaining": _left(ip), "limit": LIMIT}


# ── Streak routes ─────────────────────────────────────────────────────────────
@app.get("/api/streak")
def streak_info(request: Request):
    return get_streak(_ip(request))

@app.post("/api/streak/checkin")
def streak_checkin(request: Request):
    ip = _ip(request)
    checkin(ip)
    return get_streak(ip)


# ── Analytics routes ──────────────────────────────────────────────────────────
@app.get("/api/analytics")
def analytics(request: Request):
    """Personal study analytics — weak topics, subject breakdown, suggestions."""
    return get_analytics(_ip(request))

@app.get("/api/analytics/global")
def global_analytics():
    """Most asked topics across all students."""
    return get_global_topics(10)

@app.get("/api/analytics/suggest")
def suggest(request: Request, subject: str = "Physics"):
    """Smart study suggestions based on what student hasn't covered."""
    ip = _ip(request)
    suggestions = get_suggestions(ip, subject)
    return {
        "subject":     subject,
        "suggestions": suggestions
    }


# ── Solve routes ──────────────────────────────────────────────────────────────
@app.post("/api/solve", response_model=AskResponse)
async def solve_text(req: AskRequest, request: Request):
    if not req.question or len(req.question.strip()) < 5:
        raise HTTPException(400, "Question too short.")
    if len(req.question) > 2000:
        raise HTTPException(400, "Question too long.")

    ip = _ip(request)
    _check(ip, req.is_premium or False)

    # Auto-track streak + analytics
    checkin(ip)
    streak_data = get_streak(ip)

    # Cache check
    use_cache = len(req.history or []) == 0
    key = _cache_key(req.question, req.subject or "Physics")
    if use_cache and key in _cache:
        cached = _cache[key]
        # Still log for analytics even on cache hit
        log_question(ip, req.question, req.subject or "Physics",
                     cached.get("q_type", "theoretical"))
        return AskResponse(**cached, remaining=_left(ip),
                           from_cache=True, streak=streak_data)

    result = solve(req.question.strip(), req.subject or "Physics",
                   history=req.history or [])
    similar = _similar(req.question, req.subject or "Physics")

    # Log for analytics
    log_question(ip, req.question, req.subject or "Physics",
                 result.get("q_type", "theoretical"))

    cache_data = {
        "answer":   result["answer"],
        "sources":  result["sources"],
        "model":    result["model"],
        "question": result["question"],
        "similar":  similar,
        "q_type":   result.get("q_type", "theoretical")
    }
    if use_cache:
        _cache[key] = cache_data

    return AskResponse(
        answer=result["answer"], sources=result["sources"],
        model=result["model"],  question=result["question"],
        similar=similar, remaining=_left(ip),
        from_cache=False, streak=streak_data,
        topic=result.get("q_type")
    )


@app.post("/api/image", response_model=AskResponse)
async def solve_image(
    request: Request,
    file: UploadFile = File(...),
    subject: str = "Physics",
    is_premium: bool = False
):
    if not file.content_type.startswith("image/"):
        raise HTTPException(400, "Upload a JPG or PNG.")
    data = await file.read()
    if len(data) > 5 * 1024 * 1024:
        raise HTTPException(400, "Image too large. Max 5MB.")

    ip = _ip(request)
    _check(ip, is_premium)
    checkin(ip)
    streak_data = get_streak(ip)

    result = solve("", subject, base64.b64encode(data).decode(), file.content_type)
    log_question(ip, result["question"], subject,
                 result.get("q_type", "numerical"))
    similar = _similar(result["question"], subject)

    return AskResponse(
        **{k: result[k] for k in ["answer","sources","model","question"]},
        similar=similar, remaining=_left(ip),
        from_cache=False, streak=streak_data
    )

@app.delete("/api/cache")
def clear_cache():
    count = len(_cache)
    _cache.clear()
    return {"message": "Cache cleared", "removed": count}

@app.get("/{full_path:path}", include_in_schema=False)
def frontend(full_path: str):
    """Single-service deploy: serve the built React app, with SPA fallback."""
    if not _STATIC_DIR.exists():
        raise HTTPException(404, "Frontend not built. Run `npm run build` in frontend/ or deploy with Docker.")
    candidate = (_STATIC_DIR / full_path).resolve()
    # Prevent path traversal outside the static directory.
    if _STATIC_DIR not in candidate.parents and candidate != _STATIC_DIR:
        raise HTTPException(404)
    if candidate.is_file():
        return FileResponse(str(candidate))
    return FileResponse(str(_STATIC_DIR / "index.html"))


# ── Start ─────────────────────────────────────────────────────────────────────
if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("PORT", 8000))
    print(f"\n🚀 DoubtAI v6.0 → http://localhost:{port}")
    print(f"📖 Docs         → http://localhost:{port}/docs\n")
    uvicorn.run("server:app", host="0.0.0.0", port=port, reload=True)

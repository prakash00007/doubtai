"""
DoubtAI — FastAPI Server
==========================
Run: python server.py
Docs: http://localhost:8000/docs
"""
from fastapi import FastAPI, UploadFile, File, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional
import base64, time, os
from dotenv import load_dotenv
from solver import solve

load_dotenv()

app = FastAPI(title="DoubtAI API", version="1.0.0")

app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])

# ── Rate limiter ──────────────────────────────────────────────────────────────
_usage = {}
LIMIT = int(os.getenv("FREE_DAILY_LIMIT", 10))

def _ip(req: Request) -> str:
    fwd = req.headers.get("x-forwarded-for")
    return fwd.split(",")[0] if fwd else req.client.host

def _check(ip: str, premium: bool):
    if premium: return
    now = time.time()
    if ip not in _usage:
        _usage[ip] = {"count": 0, "reset": now + 86400}
    u = _usage[ip]
    if now > u["reset"]:
        u["count"] = 0; u["reset"] = now + 86400
    if u["count"] >= LIMIT:
        raise HTTPException(429, f"Free limit of {LIMIT} doubts/day reached. Upgrade to Pro.")
    u["count"] += 1

def _left(ip: str) -> int:
    return max(0, LIMIT - _usage.get(ip, {}).get("count", 0))


# ── Models ────────────────────────────────────────────────────────────────────
class AskRequest(BaseModel):
    question:   str
    subject:    Optional[str] = "Physics"
    is_premium: Optional[bool] = False

class AskResponse(BaseModel):
    answer:    str
    sources:   list
    model:     str
    question:  str
    remaining: Optional[int] = None


# ── Routes ────────────────────────────────────────────────────────────────────
@app.get("/")
def root():
    return {"status": "DoubtAI running 🚀", "docs": "/docs"}

@app.get("/stats")
def stats():
    from utils.vector_store import get_stats
    return get_stats()

@app.get("/api/usage")
def usage(request: Request):
    ip = _ip(request)
    used = _usage.get(ip, {}).get("count", 0)
    return {"used": used, "remaining": _left(ip), "limit": LIMIT}

@app.post("/api/solve", response_model=AskResponse)
async def solve_text(req: AskRequest, request: Request):
    if not req.question or len(req.question.strip()) < 5:
        raise HTTPException(400, "Question too short.")
    if len(req.question) > 2000:
        raise HTTPException(400, "Question too long (max 2000 chars).")
    ip = _ip(request)
    _check(ip, req.is_premium or False)
    result = solve(req.question.strip(), req.subject or "Physics")
    return AskResponse(**result, remaining=_left(ip))

@app.post("/api/image", response_model=AskResponse)
async def solve_image(
    request: Request,
    file: UploadFile = File(...),
    subject: str = "Physics",
    is_premium: bool = False
):
    if not file.content_type.startswith("image/"):
        raise HTTPException(400, "Upload a JPG or PNG image.")
    data = await file.read()
    if len(data) > 5 * 1024 * 1024:
        raise HTTPException(400, "Image too large. Max 5MB.")
    ip = _ip(request)
    _check(ip, is_premium)
    result = solve("", subject, base64.b64encode(data).decode(), file.content_type)
    return AskResponse(**result, remaining=_left(ip))


# ── Start ─────────────────────────────────────────────────────────────────────
if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("PORT", 8000))
    print(f"\n🚀 DoubtAI → http://localhost:{port}")
    print(f"📖 Docs    → http://localhost:{port}/docs\n")
    uvicorn.run("server:app", host="0.0.0.0", port=port, reload=True)
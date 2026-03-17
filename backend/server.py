"""
DoubtAI — FastAPI Server v4
Features: conversation history, caching, rate limiting, image scan, similar questions
"""
import hashlib, time, os, base64
from fastapi import FastAPI, UploadFile, File, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional
from dotenv import load_dotenv
from solver import solve

load_dotenv()

app = FastAPI(title="DoubtAI API", version="4.0.0")
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])

# ── Cache ─────────────────────────────────────────────────────────────────────
_cache = {}

def _cache_key(q: str, s: str) -> str:
    return hashlib.md5(f"{q.lower().strip()}_{s}".encode()).hexdigest()

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


# ── Similar questions generator ───────────────────────────────────────────────
def _generate_similar(question: str, subject: str) -> list:
    from groq import Groq
    client = Groq(api_key=os.getenv("GROQ_API_KEY"))
    try:
        r = client.chat.completions.create(
            model="llama-3.1-8b-instant",
            max_tokens=150,
            messages=[{
                "role": "user",
                "content": f"""Based on this {subject} question: "{question}"
Generate exactly 3 related follow-up questions a JEE/NEET student might ask next.
Return ONLY the 3 questions, one per line, no numbering, no explanation."""
            }]
        )
        lines = r.choices[0].message.content.strip().split('\n')
        return [l.strip() for l in lines if l.strip()][:3]
    except:
        return []


# ── Models ────────────────────────────────────────────────────────────────────
class HistoryMessage(BaseModel):
    role:    str   # "user" or "assistant"
    content: str

class AskRequest(BaseModel):
    question:   str
    subject:    Optional[str] = "Physics"
    is_premium: Optional[bool] = False
    history:    Optional[list] = []    # conversation history

class AskResponse(BaseModel):
    answer:     str
    sources:    list
    model:      str
    question:   str
    remaining:  Optional[int] = None
    from_cache: Optional[bool] = False
    similar:    Optional[list] = []


# ── Routes ────────────────────────────────────────────────────────────────────
@app.get("/")
def root():
    return {"status": "DoubtAI v4.0 running 🚀", "docs": "/docs"}

@app.get("/stats")
def stats():
    from utils.vector_store import get_stats
    return {**get_stats(), "cached_answers": len(_cache)}

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

    # Only use cache if no conversation history
    # (follow-up questions need fresh answers)
    use_cache = len(req.history or []) == 0
    key = _cache_key(req.question, req.subject or "Physics")

    if use_cache and key in _cache:
        print(f"⚡ Cache hit: {req.question[:50]}...")
        cached = _cache[key]
        return AskResponse(**cached, remaining=_left(ip), from_cache=True)

    # Solve with conversation history
    result = solve(
        question=req.question.strip(),
        subject=req.subject or "Physics",
        history=req.history or []
    )

    # Generate similar questions
    similar = _generate_similar(req.question, req.subject or "Physics")

    cache_data = {
        "answer":   result["answer"],
        "sources":  result["sources"],
        "model":    result["model"],
        "question": result["question"],
        "similar":  similar
    }

    # Only cache if no history (standalone questions)
    if use_cache:
        _cache[key] = cache_data

    return AskResponse(**cache_data, remaining=_left(ip), from_cache=False)


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

    result = solve(
        question="",
        subject=subject,
        image_b64=base64.b64encode(data).decode(),
        media_type=file.content_type
    )
    similar = _generate_similar(result["question"], subject)

    return AskResponse(
        **result,
        similar=similar,
        remaining=_left(ip),
        from_cache=False
    )

@app.delete("/api/cache")
def clear_cache():
    count = len(_cache)
    _cache.clear()
    return {"message": "Cache cleared", "entries_removed": count}


# ── Start ─────────────────────────────────────────────────────────────────────
if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("PORT", 8000))
    print(f"\n🚀 DoubtAI v4.0 → http://localhost:{port}")
    print(f"📖 Docs         → http://localhost:{port}/docs\n")
    uvicorn.run("server:app", host="0.0.0.0", port=port, reload=True)
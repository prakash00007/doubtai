
"""
DoubtAI — Tests
Run: python tests/test_all.py
"""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

P = "✅"; F = "❌"; S = "⏭️"

def test_embedder():
    print("\n── Embedder ──────────────────────────────")
    try:
        from utils.embedder import embed_text, EMBEDDING_DIM
        v = embed_text("Newton's second law")
        assert len(v) == EMBEDDING_DIM
        print(f"{P} Embedder OK — dim={EMBEDDING_DIM}")
        return True
    except Exception as e:
        print(f"{F} Embedder FAILED: {e}"); return False

def test_claude():
    print("\n── Groq API ──────────────────────────────")
    from dotenv import load_dotenv; load_dotenv()
    key = os.getenv("GROQ_API_KEY","")
    if not key or "your" in key:
        print(f"{S} Skipped — add GROQ_API_KEY to .env"); return None
    try:
        from groq import Groq
        client = Groq(api_key=key)
        r = client.chat.completions.create(
            model="llama-3.1-8b-instant",
            messages=[{"role":"user","content":"Say OK"}],
            max_tokens=5
        )
        print(f"{P} Groq OK — '{r.choices[0].message.content.strip()}'")
        return True
    except Exception as e:
        print(f"{F} Groq FAILED: {e}"); return False
def test_pinecone():
    print("\n── Pinecone ──────────────────────────────")
    from dotenv import load_dotenv; load_dotenv()
    key = os.getenv("PINECONE_API_KEY","")
    if not key or "your" in key:
        print(f"{S} Skipped — add PINECONE_API_KEY to .env"); return None
    try:
        from utils.vector_store import get_stats
        s = get_stats()
        print(f"{P} Pinecone OK — {s['total_vectors']:,} vectors"); return True
    except Exception as e:
        print(f"{F} Pinecone FAILED: {e}"); return False

def test_rag():
    print("\n── RAG Search ────────────────────────────")
    from dotenv import load_dotenv; load_dotenv()
    if not os.getenv("PINECONE_API_KEY","") or "your" in os.getenv("PINECONE_API_KEY",""):
        print(f"{S} Skipped — Pinecone not configured"); return None
    try:
        from rag import find_context
        r = find_context("Newton's second law", "Physics", 3)
        if not r:
            print(f"⚠️  RAG: 0 results — run ingest.py first"); return None
        print(f"{P} RAG OK — {len(r)} results, top: {r[0]['book']} ({r[0]['score']})")
        return True
    except Exception as e:
        print(f"{F} RAG FAILED: {e}"); return False

def test_solver():
    print("\n── Full Solver ───────────────────────────")
    from dotenv import load_dotenv; load_dotenv()
    if not os.getenv("ANTHROPIC_API_KEY","") or "your" in os.getenv("ANTHROPIC_API_KEY",""):
        print(f"{S} Skipped — Claude API key not set"); return None
    try:
        from solver import solve
        r = solve("What is Newton's first law?", "Physics")
        assert len(r["answer"]) > 50
        print(f"{P} Solver OK — {len(r['answer'])} chars, model: {r['model']}")
        print(f"   Preview: {r['answer'][:120]}...")
        return True
    except Exception as e:
        print(f"{F} Solver FAILED: {e}"); return False

if __name__ == "__main__":
    target = sys.argv[1] if len(sys.argv) > 1 else None
    tests = {"embedder": test_embedder, "claude": test_claude,
             "pinecone": test_pinecone, "rag": test_rag, "solver": test_solver}

    print("="*50)
    print("  DoubtAI Tests")
    print("="*50)

    if target:
        results = {target: tests[target]()}
    else:
        results = {n: fn() for n, fn in tests.items()}

    print("\n" + "="*50)
    passed = sum(1 for v in results.values() if v is True)
    skipped = sum(1 for v in results.values() if v is None)
    failed = sum(1 for v in results.values() if v is False)

    for name, r in results.items():
        icon = P if r is True else (S if r is None else F)
        print(f"  {icon} {name}")

    print(f"\n  {passed} passed · {skipped} skipped · {failed} failed")
    if failed == 0:
        print("\n🎉 All good! Run: python server.py")
    print()

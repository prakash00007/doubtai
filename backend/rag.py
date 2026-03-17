"""
DoubtAI — RAG Search
======================
Takes a student question → returns relevant book passages.
"""
from utils.embedder import embed_text
from utils.vector_store import search


def find_context(question: str, subject: str = None, top_k: int = 5) -> list:
    q_vector = embed_text(question)
    results = search(q_vector, subject=subject, top_k=top_k)
    # Drop low-relevance results
    return [r for r in results if r["score"] >= 0.3]


def build_context(results: list) -> tuple:
    """Returns (context_string, list_of_books_used)"""
    if not results:
        return "No specific book content found.", []

    parts = []
    books = []
    for r in results:
        parts.append(f"[From {r['book']} — score {r['score']}]\n{r['text']}")
        if r["book"] not in books:
            books.append(r["book"])

    return "\n\n---\n\n".join(parts), books


# Quick test
if __name__ == "__main__":
    import sys
    q = sys.argv[1] if len(sys.argv) > 1 else "What is Newton's second law?"
    print(f"\nSearching: '{q}'\n")
    results = find_context(q, subject="Physics")
    if not results:
        print("No results. Run ingest.py first.")
    else:
        for i, r in enumerate(results, 1):
            print(f"Result {i} — {r['book']} (score: {r['score']})")
            print(f"  {r['text'][:200]}...\n")
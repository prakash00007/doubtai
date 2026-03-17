"""
DoubtAI — AI Solver (Groq — 100% FREE)
Models: Llama 3.3 70B (hard) + Llama 3.1 8B (simple)
Free limit: 14,400 requests/day
"""
import os
from groq import Groq
from dotenv import load_dotenv
from rag import find_context, build_context

load_dotenv()
client = Groq(api_key=os.getenv("GROQ_API_KEY"))

PROMPTS = {
    "Physics": """You are an expert JEE/NEET Physics teacher who teaches like HC Verma and NCERT.
Always:
- Break solution into clear numbered steps
- Explain the physical intuition (WHY not just HOW)
- Show formulas before substituting values
- Write equations like: F = ma, E = mc²
- End with: KEY CONCEPT: [one powerful takeaway]
- Language suitable for Class 11/12 student""",

    "Chemistry": """You are an expert JEE/NEET Chemistry teacher who teaches like NCERT and OP Tandon.
Always:
- Use NCERT systematic approach
- Show balanced chemical equations
- Explain reactions using electron movement
- Show mole concept step by step for numerics
- End with: KEY CONCEPT: [one powerful takeaway]
- Language suitable for Class 11/12 student""",

    "Maths": """You are an expert JEE Maths teacher who teaches like Cengage and RD Sharma.
Always:
- State the theorem/formula first
- Show every substitution and simplification step
- Mention common mistakes students make
- End with: KEY CONCEPT: [one powerful takeaway]
- Language suitable for Class 11/12 student""",

    "Biology": """You are an expert NEET Biology teacher who teaches like NCERT and Trueman's.
Always:
- Use proper scientific terminology
- Explain processes in sequential steps
- Connect to real biological significance
- Give mnemonics where helpful
- End with: KEY CONCEPT: [one powerful takeaway]
- Language suitable for Class 11/12 student"""
}

SIMPLE = ["what is", "define", "meaning of", "what are", "who is",
          "state the", "list the", "name the", "what do you mean"]

def _is_simple(q: str) -> bool:
    if any(c.isdigit() for c in q): return False
    return len(q.split()) < 15 and any(q.lower().startswith(k) for k in SIMPLE)

def _model(q: str) -> str:
    if _is_simple(q):
        return "llama-3.1-8b-instant"    # fast, free, simple questions
    return "llama-3.3-70b-versatile"     # smarter, complex problems


def solve(question: str, subject: str = "Physics", image_b64: str = None, media_type: str = "image/jpeg") -> dict:

    print(f"\n❓ {question[:70]}...")
    print(f"   Subject: {subject}")

    # Step 1 — RAG
    print("\n[1/2] Searching books...")
    results = find_context(question, subject=subject, top_k=5)
    context, books = build_context(results)
    print(f"   Sources: {', '.join(books) if books else 'none matched'}")

    # Step 2 — Groq
    model = _model(question)
    print(f"\n[2/2] {model} answering...")

    system = PROMPTS.get(subject, PROMPTS["Physics"])
    full_prompt = f"""Here is content from the student's textbooks:

{context}

---
Answer this {subject} doubt using the book content above as your guide.
Mirror the style and terminology of those books.

Question: {question}"""

    response = client.chat.completions.create(
        model=model,
        messages=[
            {"role": "system", "content": system},
            {"role": "user",   "content": full_prompt}
        ],
        max_tokens=1000
    )

    print("   ✅ Done\n")
    return {
        "answer":   response.choices[0].message.content,
        "sources":  books,
        "model":    model,
        "question": question
    }


if __name__ == "__main__":
    import sys
    q = sys.argv[1] if len(sys.argv) > 1 else "What is Newton's first law?"
    result = solve(q, "Physics")
    print("="*60)
    print(result["answer"])
    print(f"\nModel: {result['model']}")
    print(f"Sources: {result['sources']}")
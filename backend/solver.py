"""
DoubtAI — AI Solver v7 (Final)
- Smart format: numerical / theoretical / mcq
- STRICT subject filtering in RAG
- Conversation history
- LaTeX cleaning
- Image scan
- Hinglish support
"""
import os, re, base64
from groq import Groq
from dotenv import load_dotenv
from rag import find_context, build_context

load_dotenv()
client = Groq(api_key=os.getenv("GROQ_API_KEY"))


# ── LaTeX cleaner ─────────────────────────────────────────────────────────────
def _clean_latex(text):
    text = re.sub(r'\\frac\{([^}]*)\}\{([^}]*)\}', r'(\1/\2)', text)
    text = re.sub(r'\\sqrt\{([^}]*)\}', r'√(\1)', text)
    text = re.sub(r'\\sqrt\s+(\w+)', r'√\1', text)
    for src, dst in [('\\times','×'),('\\cdot','·'),('\\div','÷'),('\\circ','°'),
                     ('\\pm','±'),('\\approx','≈'),('\\neq','≠'),('\\leq','≤'),
                     ('\\geq','≥'),('\\infty','∞'),('\\pi','π')]:
        text = text.replace(src, dst)
    for name, sym in {'alpha':'α','beta':'β','gamma':'γ','delta':'δ','theta':'θ',
                      'phi':'φ','omega':'ω','lambda':'λ','mu':'μ','sigma':'σ',
                      'tau':'τ','epsilon':'ε','rho':'ρ','eta':'η','nu':'ν'}.items():
        text = text.replace(f'\\{name}', sym)
    text = re.sub(r'\\(sin|cos|tan|sec|cosec|cot|log|ln|exp|lim|max|min)', r'\1', text)
    text = re.sub(r'\^\{2\}','²',text)
    text = re.sub(r'\^\{3\}','³',text)
    text = re.sub(r'\^\{n\}','ⁿ',text)
    text = re.sub(r'\^\{([^}]+)\}',r'^(\1)',text)
    text = re.sub(r'_\{([^}]+)\}',r'_\1',text)
    text = re.sub(r'\\(left|right|big|Big|bigg|Bigg)','',text)
    text = re.sub(r'\\\[','\n',text); text = re.sub(r'\\\]','\n',text)
    text = re.sub(r'\\\(','',text); text = re.sub(r'\\\)','',text)
    text = re.sub(r'\$\$?(.*?)\$\$?',r'\1',text,flags=re.DOTALL)
    text = text.replace('{','').replace('}','').replace('\\\\','\n')
    text = re.sub(r'\\[a-zA-Z]+','',text)
    text = re.sub(r' +',' ',text)
    text = re.sub(r'\n{3,}','\n\n',text)
    return text.strip()


# ── Strict subject relevance checker ─────────────────────────────────────────
def _is_relevant(context, subject):
    """
    Strictly check if RAG content matches the subject.
    If Physics content comes for a Chemistry question → reject it.
    """
    if not context or "No specific" in context:
        return False

    ctx = context.lower()

    # Subject-specific strong keywords
    must_have = {
        "Physics":   ["newton","force","velocity","acceleration","momentum",
                      "energy","electric","magnetic","optic","wave","gravity",
                      "motion","kinetic","potential","thermodynamic"],
        "Chemistry": ["atom","molecule","bond","electron","orbital","mole",
                      "reaction","element","compound","acid","base","periodic",
                      "oxidation","reduction","stoichiometry","ionic","covalent",
                      "valence","enthalpy","equilibrium","concentration"],
        "Maths":     ["theorem","derivative","integral","function","polynomial",
                      "trigonometry","matrix","determinant","vector","probability",
                      "calculus","equation","sequence","series","limit"],
        "Biology":   ["cell","dna","rna","protein","gene","chromosome","enzyme",
                      "photosynthesis","respiration","mitosis","meiosis","tissue",
                      "organ","evolution","ecology","bacteria","virus"]
    }

    # Anti-keywords: if these dominate, content is from wrong subject
    anti_keywords = {
        "Chemistry": ["newton","velocity","acceleration","optic","magnetic",
                      "electromagnetic","wave","gravitational","kinetic theory"],
        "Physics":   ["stoichiometry","molar mass","valence electron","ionic bond",
                      "covalent bond","oxidation state","electrode","electrolysis"],
        "Biology":   ["newton","velocity","stoichiometry","polynomial","matrix"],
        "Maths":     ["newton","atom","molecule","cell","dna","protein"]
    }

    # Check must-have keywords
    subject_kw = must_have.get(subject, [])
    match_count = sum(1 for k in subject_kw if k in ctx)

    # Check anti-keywords (wrong subject content)
    anti_kw = anti_keywords.get(subject, [])
    anti_count = sum(1 for k in anti_kw if k in ctx)

    # Relevant only if: enough subject keywords AND not dominated by wrong subject
    return match_count >= 2 and anti_count <= 1


# ── Question type detector ────────────────────────────────────────────────────
def _question_type(q):
    ql = q.lower()
    if re.search(r'\([abcd]\)|\boption [abcd]\b', ql):
        return 'mcq'
    has_units = bool(re.search(
        r'\d+\.?\d*\s*(kg|m|s|n|j|w|k|mol|l|v|a|°|hz|m/s|km|cm|g|nm|pa|atm|k|cal)',
        ql
    ))
    num_words = ['find','calculate','determine','compute','evaluate','solve',
                 'how much','how many','prove that','show that','verify','derive',
                 'what is the value of','what will be']
    if has_units or any(w in ql for w in num_words):
        return 'numerical'
    return 'theoretical'


# ── Format templates ──────────────────────────────────────────────────────────
FORMATS = {
    'numerical': """
FORMAT FOR NUMERICAL PROBLEMS — USE EXACTLY:

GIVEN:
• [value with unit]
• [value with unit]

FIND:
• [what to calculate]

SOLUTION:
Step 1: [Step name]
Formula: [formula in plain text]
Calculation: [substitute values]
Result: [answer with unit]

Step 2: [next step if needed]

ANSWER: [final answer with unit]

KEY CONCEPT: [one line takeaway]""",

    'theoretical': """
FORMAT FOR THEORY QUESTIONS — USE EXACTLY:

CONCEPT:
[Clear 2-3 line explanation of the core idea in flowing text — no bullets here]

EXPLANATION:
• [First key point with proper detail]
• [Second key point with proper detail]
• [Third key point if needed]
[Use → to show cause and effect relationships]

EXAMPLE:
[One concrete real-world or textbook example that makes it crystal clear]

KEY CONCEPT: [One powerful one-line takeaway students must remember]""",

    'mcq': """
FORMAT FOR MCQ — USE EXACTLY:

ANALYSIS:
[What concept or formula this question is testing]

SOLUTION:
[Work through step by step — show the math clearly]

ANSWER: [Option letter] — [the value or reason]

WHY OTHERS ARE WRONG:
• Option [X]: [brief reason]
• Option [Y]: [brief reason]

KEY CONCEPT: [What this question is really testing]"""
}

SUBJECT_EXTRA = {
    "Physics":   "You teach exactly like HC Verma — build physical intuition first, then show the math.",
    "Chemistry": "You teach like NCERT Chemistry. For reactions always use format: 2H₂ + O₂ → 2H₂O with subscripts H₂O, CO₂, H₂SO₄, CaCO₃.",
    "Maths":     "You teach like Cengage and RD Sharma. Always add COMMON MISTAKE: section at the end.",
    "Biology":   "You teach like NCERT Biology. Add MNEMONIC: section wherever it helps memory."
}

RULES = """
ABSOLUTE RULES — NEVER BREAK:
• Plain text equations ONLY: F = m × a, E = m × c²
• Allowed math symbols: × ÷ √ ² ³ ° → ∴ ∵ ≈ ≠ ≤ ≥ α β γ θ φ ω λ μ π ∫ Σ ∞ ⇌
• COMPLETELY BANNED: $ signs, \\frac, \\sqrt, \\[ \\], \\( \\), ANY LaTeX
• Fractions: write as (a+b)/(c+d) — NEVER \\frac{a+b}{c+d}
• Roots: write as √(2gh) — NEVER \\sqrt{2gh}
• Student writes in Hindi/Hinglish → you reply in Hinglish
• You remember previous conversation — use it for follow-up questions
• ONLY answer from the subject asked — do NOT mix subjects"""

def _system(subject, q_type):
    return (
        f"You are an expert JEE/NEET {subject} teacher. "
        f"{SUBJECT_EXTRA.get(subject, '')}\n"
        f"{FORMATS[q_type]}\n{RULES}"
    )


# ── Model routing ─────────────────────────────────────────────────────────────
SIMPLE_STARTS = [
    "what is","define","meaning of","what are","who is","state the",
    "list the","name the","full form","expand","what was","when was"
]

def _model(q):
    ql = q.lower().strip()
    if (len(q.split()) < 12
        and any(ql.startswith(k) for k in SIMPLE_STARTS)
        and not any(c.isdigit() for c in q)):
        return "llama-3.1-8b-instant"
    return "llama-3.3-70b-versatile"


# ── Image reader ──────────────────────────────────────────────────────────────
def extract_from_image(image_bytes):
    print("   🔍 Llama 4 Scout reading image...")
    image_b64 = base64.b64encode(image_bytes).decode()
    r = client.chat.completions.create(
        model="meta-llama/llama-4-scout-17b-16e-instruct",
        messages=[{"role": "user", "content": [
            {"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{image_b64}"}},
            {"type": "text", "text": (
                "Extract the question from this image exactly. "
                "Convert ALL math to plain text: H not $H$, "
                "30 degrees not $30^\\circ$, (1/2)mv² not $\\frac{1}{2}mv^2$. "
                "Remove ALL $ signs and LaTeX. "
                "Return ONLY the clean question text."
            )}
        ]}],
        max_tokens=600
    )
    extracted = r.choices[0].message.content.strip()
    print(f"   📝 {extracted[:100]}...")
    return extracted


# ── Main solver ───────────────────────────────────────────────────────────────
def solve(question="", subject="Physics", image_b64=None,
          media_type="image/jpeg", history=[]):

    # Step 0 — image
    if image_b64:
        print("📷 Reading image...")
        question = _clean_latex(
            extract_from_image(base64.b64decode(image_b64))
        )

    q_type = _question_type(question)
    print(f"\n❓ {question[:70]}...")
    print(f"   Subject: {subject} | Type: {q_type} | History: {len(history)}")

    # Step 1 — RAG with strict subject filter
    print("\n[1/2] Searching books...")
    is_followup = len(history) > 0 and len(question.split()) < 10

    if is_followup:
        context, books = "Refer to the previous question.", []
        print("   Follow-up → conversation context")
    else:
        results = find_context(question, subject=subject, top_k=6)
        context, books = build_context(results)

        if not _is_relevant(context, subject):
            print(f"   ⚠️  No relevant {subject} books loaded → AI knowledge")
            context = ""
            books = []
        else:
            print(f"   ✅ {', '.join(books)}")

    # Step 2 — Groq
    model = _model(question)
    system = _system(subject, q_type)
    print(f"\n[2/2] {model} answering ({q_type})...")

    if books:
        prompt = (
            f"Reference from student's {subject} textbooks:\n{context}\n\n"
            f"---\n{subject} Question: {question}\n\n"
            f"Follow the exact format. Use the textbook content."
        )
    else:
        prompt = (
            f"{subject} Question: {question}\n\n"
            f"Answer from your expert knowledge of JEE/NEET {subject} Class 11/12. "
            f"Follow the exact format."
        )

    msgs = [{"role": "system", "content": system}]
    for h in history[-8:]:
        if isinstance(h, dict) and 'role' in h and 'content' in h:
            msgs.append({"role": h["role"], "content": str(h["content"])[:500]})
    msgs.append({"role": "user", "content": prompt})

    r = client.chat.completions.create(
        model=model, messages=msgs, max_tokens=1200
    )
    answer = _clean_latex(r.choices[0].message.content)
    print("   ✅ Done\n")

    return {
        "answer":   answer,
        "sources":  books,
        "model":    model,
        "question": question,
        "q_type":   q_type
    }


# ── Test ──────────────────────────────────────────────────────────────────────
if __name__ == "__main__":
    import sys
    tests = [
        ("Explain Newton's first law", "Physics"),
        ("A 5kg block pushed with 20N, mu=0.3. Find acceleration.", "Physics"),
        ("What is osmosis?", "Biology"),
        ("chemistry chapter 2 crux class 11 structure of atom", "Chemistry"),
        ("Explain mole concept", "Chemistry"),
    ]
    q = sys.argv[1] if len(sys.argv) > 1 else None
    s = sys.argv[2] if len(sys.argv) > 2 else "Physics"
    if q:
        tests = [(q, s)]
    for question, subject in tests:
        print(f"\n{'='*60}")
        print(f"Q ({_question_type(question)}): {question}")
        result = solve(question, subject)
        print(result["answer"])
        print(f"Sources: {result['sources']} | Model: {result['model']}")
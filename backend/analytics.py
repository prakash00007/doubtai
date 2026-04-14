"""
DoubtAI — Smart Analytics & Weak Topic Detector
=================================================
Tracks what topics students ask about most,
detects weak areas, and suggests what to study next.

Endpoints:
    GET  /api/analytics/{ip}        → personal study analytics
    GET  /api/analytics/topics      → most asked topics today
    POST /api/analytics/log         → log a question (auto-called on solve)
    GET  /api/analytics/suggest     → smart study suggestions
"""
from datetime import datetime, date
from collections import Counter
import re

# In-memory store
# { ip: { "questions": [...], "subjects": Counter, "topics": Counter } }
_analytics = {}

# Global topic counter
_global_topics = Counter()
_global_subjects = Counter()


# ── Topic extractor ───────────────────────────────────────────────────────────
TOPIC_KEYWORDS = {
    # Physics
    "Newton's Laws":       ["newton", "force", "inertia", "action reaction"],
    "Kinematics":          ["velocity", "acceleration", "displacement", "projectile", "motion"],
    "Work & Energy":       ["work", "energy", "power", "kinetic", "potential"],
    "Gravitation":         ["gravity", "gravitational", "satellite", "orbital", "kepler"],
    "Waves":               ["wave", "frequency", "wavelength", "amplitude", "sound"],
    "Thermodynamics":      ["heat", "temperature", "entropy", "carnot", "thermodynamic"],
    "Electrostatics":      ["charge", "electric field", "coulomb", "capacitor", "potential"],
    "Current Electricity": ["current", "resistance", "ohm", "circuit", "voltage"],
    "Optics":              ["light", "lens", "mirror", "refraction", "reflection"],
    "Modern Physics":      ["photoelectric", "quantum", "nuclear", "radioactive", "photon"],
    "SHM":                 ["shm", "simple harmonic", "oscillation", "pendulum"],
    "Rotational Motion":   ["torque", "angular", "moment of inertia", "rotation"],

    # Chemistry
    "Atomic Structure":    ["atom", "electron", "orbital", "quantum number", "bohr"],
    "Chemical Bonding":    ["bond", "ionic", "covalent", "hybridization", "vsepr"],
    "Thermochemistry":     ["enthalpy", "entropy", "gibbs", "hess", "calorimeter"],
    "Equilibrium":         ["equilibrium", "le chatelier", "kc", "kp", "ksp"],
    "Electrochemistry":    ["electrode", "electrolysis", "cell", "faraday", "emf"],
    "Organic Chemistry":   ["organic", "alkane", "alkene", "benzene", "functional group"],
    "Mole Concept":        ["mole", "molarity", "stoichiometry", "avogadro", "limiting"],
    "Periodic Table":      ["periodic", "ionization", "electronegativity", "atomic radius"],

    # Maths
    "Calculus":            ["derivative", "integral", "differentiation", "limit", "continuity"],
    "Algebra":             ["quadratic", "polynomial", "equation", "matrix", "determinant"],
    "Trigonometry":        ["sin", "cos", "tan", "trigonometric", "angle"],
    "Coordinate Geometry": ["circle", "parabola", "ellipse", "hyperbola", "conic"],
    "Probability":         ["probability", "permutation", "combination", "random"],
    "Vectors":             ["vector", "dot product", "cross product", "magnitude"],
    "Sequences":           ["sequence", "series", "ap", "gp", "arithmetic", "geometric"],

    # Biology
    "Cell Biology":        ["cell", "mitosis", "meiosis", "organelle", "membrane"],
    "Genetics":            ["gene", "dna", "rna", "chromosome", "heredity", "mutation"],
    "Photosynthesis":      ["photosynthesis", "chlorophyll", "calvin", "light reaction"],
    "Respiration":         ["respiration", "atp", "glycolysis", "krebs", "mitochondria"],
    "Human Physiology":    ["digestion", "circulation", "nervous", "hormone", "kidney"],
    "Ecology":             ["ecosystem", "food chain", "biodiversity", "population"],
    "Evolution":           ["evolution", "natural selection", "darwin", "adaptation"],
    "Plant Biology":       ["plant", "root", "stem", "leaf", "flower", "transpiration"],
}


def _extract_topic(question: str) -> str:
    """Find which topic a question belongs to."""
    q = question.lower()
    best_topic = "General"
    best_score = 0

    for topic, keywords in TOPIC_KEYWORDS.items():
        score = sum(1 for kw in keywords if kw in q)
        if score > best_score:
            best_score = score
            best_topic = topic

    return best_topic


def log_question(ip: str, question: str, subject: str, q_type: str):
    """Log a question for analytics. Called automatically on every solve."""
    if ip not in _analytics:
        _analytics[ip] = {
            "questions": [],
            "subjects":  Counter(),
            "topics":    Counter(),
            "types":     Counter()
        }

    topic = _extract_topic(question)
    today = date.today().isoformat()

    # Save question record
    _analytics[ip]["questions"].append({
        "question": question[:100],
        "subject":  subject,
        "topic":    topic,
        "type":     q_type,
        "date":     today
    })

    # Keep last 500 questions per user
    _analytics[ip]["questions"] = _analytics[ip]["questions"][-500:]

    # Update counters
    _analytics[ip]["subjects"][subject] += 1
    _analytics[ip]["topics"][topic] += 1
    _analytics[ip]["types"][q_type] += 1

    # Update global counters
    _global_topics[topic] += 1
    _global_subjects[subject] += 1


def get_analytics(ip: str) -> dict:
    """Get personal study analytics for a user."""
    if ip not in _analytics or not _analytics[ip]["questions"]:
        return {
            "total_questions": 0,
            "message": "No questions asked yet. Start solving doubts!",
            "subjects": {},
            "top_topics": [],
            "weak_topics": [],
            "strong_topics": [],
            "today_count": 0,
            "suggestion": "Ask your first doubt to get personalized analytics!"
        }

    user = _analytics[ip]
    today = date.today().isoformat()

    total = len(user["questions"])
    today_qs = sum(1 for q in user["questions"] if q["date"] == today)

    # Most asked topics = potential weak areas (asked more = struggling more)
    top_topics = user["topics"].most_common(5)
    weak_topics = [t for t, c in top_topics if c >= 3]

    # Subjects breakdown
    subjects = dict(user["subjects"])
    total_subj = sum(subjects.values()) or 1
    subjects_pct = {k: round(v/total_subj*100) for k, v in subjects.items()}

    # Question type breakdown
    types = dict(user["types"])

    # Strongest subject (most questions)
    strongest = max(subjects, key=subjects.get) if subjects else None

    # Weakest subject (least questions — possibly avoided)
    all_subjects = ["Physics", "Chemistry", "Maths", "Biology"]
    weakest = min(all_subjects, key=lambda s: subjects.get(s, 0))

    # Generate smart suggestion
    if weak_topics:
        suggestion = f"You ask a lot about {weak_topics[0]} — consider revising it thoroughly!"
    elif weakest and subjects.get(weakest, 0) == 0:
        suggestion = f"You haven't asked any {weakest} doubts yet. Don't ignore it for JEE/NEET!"
    else:
        suggestion = f"Great balance! Keep solving doubts consistently."

    return {
        "total_questions": total,
        "today_count":     today_qs,
        "subjects":        subjects_pct,
        "top_topics":      [{"topic": t, "count": c} for t, c in top_topics],
        "weak_topics":     weak_topics,
        "strongest_subject": strongest,
        "weakest_subject":   weakest,
        "question_types":  types,
        "suggestion":      suggestion,
        "recent": [q["question"] for q in user["questions"][-5:]][::-1]
    }


def get_global_topics(top_n: int = 10) -> dict:
    """Most asked topics across all students today."""
    return {
        "top_topics":   [{"topic": t, "count": c}
                         for t, c in _global_topics.most_common(top_n)],
        "top_subjects": [{"subject": s, "count": c}
                         for s, c in _global_subjects.most_common(4)],
        "total_questions": sum(_global_topics.values())
    }


def get_suggestions(ip: str, subject: str) -> list:
    """Smart topic suggestions based on what student hasn't studied."""
    if ip not in _analytics:
        return [
            f"Start with NCERT {subject} basics",
            "Try solving previous year JEE questions",
            "Focus on high-weightage chapters first"
        ]

    user = _analytics[ip]
    studied = set(user["topics"].keys())

    # Find unstudied topics in this subject
    subject_topics = {
        "Physics":   ["Newton's Laws","Kinematics","Work & Energy","Gravitation",
                      "Waves","Thermodynamics","Electrostatics","Current Electricity",
                      "Optics","Modern Physics","SHM","Rotational Motion"],
        "Chemistry": ["Atomic Structure","Chemical Bonding","Thermochemistry",
                      "Equilibrium","Electrochemistry","Organic Chemistry",
                      "Mole Concept","Periodic Table"],
        "Maths":     ["Calculus","Algebra","Trigonometry","Coordinate Geometry",
                      "Probability","Vectors","Sequences"],
        "Biology":   ["Cell Biology","Genetics","Photosynthesis","Respiration",
                      "Human Physiology","Ecology","Evolution","Plant Biology"]
    }

    all_topics = subject_topics.get(subject, [])
    unstudied  = [t for t in all_topics if t not in studied]
    weak       = [t for t, c in user["topics"].most_common() if c >= 3]

    suggestions = []

    if weak:
        suggestions.append(f"Revise {weak[0]} — you've asked {user['topics'][weak[0]]} questions on it")
    if unstudied:
        suggestions.append(f"You haven't studied {unstudied[0]} yet — important for JEE/NEET!")
    if len(unstudied) > 1:
        suggestions.append(f"Also cover {unstudied[1]} before your exam")

    if not suggestions:
        suggestions = [f"Great {subject} coverage! Try harder JEE Advanced problems now."]

    return suggestions

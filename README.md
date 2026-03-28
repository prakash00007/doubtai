# 📚 DoubtAI — AI Doubt Solver for JEE & NEET

> **Your personal IIT topper, available 24/7 at ₹0.**  
> Step-by-step answers in the exact style of NCERT, HC Verma, and Cengage..

<div align="center">

![Python](https://img.shields.io/badge/Python-3.10+-blue?style=for-the-badge&logo=python)
![FastAPI](https://img.shields.io/badge/FastAPI-0.104-009688?style=for-the-badge&logo=fastapi)
![React](https://img.shields.io/badge/React-18-61DAFB?style=for-the-badge&logo=react)
![Groq](https://img.shields.io/badge/Groq-Llama_3.3_70B-FF6B35?style=for-the-badge)
![Pinecone](https://img.shields.io/badge/Pinecone-Vector_DB-6C3483?style=for-the-badge)
![License](https://img.shields.io/badge/License-MIT-27AE60?style=for-the-badge)

**[🚀 Demo](#) · [📖 Docs](#-api-endpoints) · [🐛 Report Bug](https://github.com/prakash00007/doubtai/issues) · [✨ Request Feature](https://github.com/prakash00007/doubtai/issues)***

</div>

---

## 🎯 What is DoubtAI?

DoubtAI is a full-stack AI-powered doubt-solving platform built for **25 lakh+ JEE and NEET aspirants** in India. Students can ask any Physics, Chemistry, Maths, or Biology doubt — by typing or photographing a question — and get a structured, book-accurate answer instantly.

Unlike generic AI (ChatGPT, Gemini), DoubtAI answers **from the actual books students study** — NCERT, HC Verma, Cengage, Black Book — using a custom **RAG (Retrieval Augmented Generation)** pipeline.

---

## ✨ Features

| Feature | Description |
|---|---|
| 📖 **Book-Accurate RAG** | Answers sourced from 10 indexed JEE/NEET textbooks |
| 📷 **Image Scan** | Photograph any textbook question — Llama 4 Scout reads it |
| 🧠 **Smart Format** | Numerical → `GIVEN/STEPS/ANSWER`, Theory → `CONCEPT/EXPLANATION` |
| ⚡ **Answer Caching** | Same question answered instantly from MD5-hash cache |
| 💬 **Conversation Memory** | Follow-up questions use previous context (last 4 exchanges) |
| 🔀 **Multi-LLM Routing** | Simple → Llama 8B (fast), Hard → Llama 70B (accurate) |
| 🌐 **Hinglish Support** | Ask in Hindi/Hinglish, get answer in Hinglish |
| 📊 **Solution Flow Viz** | Visual step-by-step breakdown of solutions |
| 🚫 **Zero LaTeX** | All equations in clean plain text with unicode symbols |
| 🔒 **Rate Limiting** | IP-based 10 free doubts/day system |

---

## 🏗️ Architecture

```
Student Question (text or photo)
           ↓
  ┌─────────────────────┐
  │  Question Classifier │  → numerical / theoretical / mcq
  └────────┬────────────┘
           ↓
  ┌─────────────────────┐
  │    RAG Pipeline      │
  │  • Embed (MiniLM)   │  → 384-dim vector
  │  • Search Pinecone  │  → cosine similarity
  │  • Subject Filter   │  → reject wrong-subject content
  │  • Return top 5     │  → book chunks
  └────────┬────────────┘
           ↓
  ┌─────────────────────┐
  │   Groq LLM Router   │
  │  Simple → Llama 8B  │
  │  Hard   → Llama 70B │
  │  Image  → Llama 4   │
  └────────┬────────────┘
           ↓
  ┌─────────────────────┐
  │   LaTeX Cleaner     │  → 30+ regex rules
  │   Answer Formatter  │  → structured sections
  └────────┬────────────┘
           ↓
     Perfect Answer ✅
```

---

## 📚 Books Indexed (3,032 vectors)

| Book | Subject | Chunks |
|---|---|---|
| NCERT Physics Class 11 | Physics | ~186 |
| NCERT Physics Class 12 | Physics | ~200 |
| NCERT Chemistry Class 11 | Chemistry | ~180 |
| NCERT Biology Class 11 | Biology | ~200 |
| NCERT Biology Class 12 | Biology | ~200 |
| HC Verma Vol 1 | Physics | ~400 |
| HC Verma Vol 2 | Physics | ~684 |
| HC Verma Solutions | Physics | ~500 |
| Black Book Maths (Vikas Gupta) | Maths | ~300 |
| NCERT Exemplar Chemistry 12 | Chemistry | ~180 |

---

## 🛠️ Tech Stack

### Backend
- **Python 3.10+** · **FastAPI** · **Uvicorn**
- **Groq API** — Llama 3.1 8B, Llama 3.3 70B, Llama 4 Scout (vision)
- **Pinecone** — Serverless vector database
- **sentence-transformers** — Local MiniLM embeddings (FREE, no API cost)
- **PyMuPDF** — PDF text extraction

### Frontend
- **React 18** · **Vite** · **Axios**
- Custom CSS with CSS variables for theming

### AI Pipeline
- Custom **RAG** implementation from scratch
- **MD5 hash-based** answer caching
- **Conversation history** (last 4 exchanges)
- **Multi-model routing** based on question complexity

---

## 🚀 Getting Started

### Prerequisites
- Python 3.10+
- Node.js 18+
- Groq API key — [console.groq.com](https://console.groq.com) *(free)*
- Pinecone API key — [app.pinecone.io](https://app.pinecone.io) *(free)*

### 1. Clone the repo
```bash
git clone https://github.com/prakash00007/doubtai.git
cd doubtai
```

### 2. Backend setup
```bash
cd backend
pip install -r requirements.txt
cp .env.example .env
# Add your GROQ_API_KEY and PINECONE_API_KEY in .env
```

### 3. Ingest books into Pinecone
```bash
# Download NCERT PDFs from ncert.nic.in and place in backend/books/
python3 ingest.py --book physics11
python3 ingest.py --book chemistry11
# Repeat for each book
```

### 4. Start the backend
```bash
python3 server.py
# API running at  → http://localhost:8000
# Swagger docs at → http://localhost:8000/docs
```

### 5. Start the frontend
```bash
cd ../frontend
npm install
npm run dev
# App running at → http://localhost:5173
```

---

## 📁 Project Structure

```
doubtai/
├── backend/
│   ├── books/                  ← NCERT + HCV PDFs (gitignored)
│   ├── utils/
│   │   ├── embedder.py         ← FREE local MiniLM embeddings
│   │   ├── pdf_parser.py       ← PDF text extraction + chunking
│   │   └── vector_store.py     ← Pinecone read/write
│   ├── .env.example            ← API keys template
│   ├── requirements.txt
│   ├── ingest.py               ← Load books into Pinecone (run once)
│   ├── rag.py                  ← Semantic search pipeline
│   ├── solver.py               ← Core AI solver with routing
│   └── server.py               ← FastAPI REST API
└── frontend/
    ├── src/
    │   ├── components/
    │   │   ├── Sidebar.jsx     ← Subject selector + history
    │   │   ├── ChatArea.jsx    ← Answer display + visualization
    │   │   └── InputBar.jsx    ← Text input + image upload
    │   └── App.jsx             ← Main app with state management
    ├── index.html
    └── vite.config.js
```

---

## 🔌 API Endpoints

| Method | Endpoint | Description |
|---|---|---|
| `GET` | `/` | Health check |
| `GET` | `/stats` | Vector count + cache stats |
| `GET` | `/api/usage` | Daily quota remaining |
| `POST` | `/api/solve` | Solve a text question |
| `POST` | `/api/image` | Solve from a photo |
| `DELETE` | `/api/cache` | Clear answer cache |

### Example
```bash
curl -X POST http://localhost:8000/api/solve \
  -H "Content-Type: application/json" \
  -d '{"question": "Explain Newton third law", "subject": "Physics"}'
```

---

## 💰 Cost Breakdown

| Component | Cost |
|---|---|
| Groq API (Llama 8B / 70B / 4 Scout) | **FREE** (14,400 req/day) |
| Pinecone vector DB | **FREE** (starter tier) |
| Local MiniLM embeddings | **FREE** (runs on your machine) |
| **Total per doubt** | **~₹0** |

---

## 🗺️ Roadmap

- [ ] Deploy on Railway + Vercel
- [ ] Razorpay payments (₹199/month Pro plan)
- [ ] LaTeX math rendering (KaTeX)
- [ ] Mobile app (React Native)
- [ ] More books: Arihant PYQs, DC Pandey, N Awasthi
- [ ] Institute dashboard with analytics
- [ ] WhatsApp bot integration

---

## 🤝 Contributing

Contributions are welcome! Here's how:

1. Fork the repo
2. Create your branch: `git checkout -b feature/amazing-feature`
3. Commit your changes: `git commit -m 'Add amazing feature'`
4. Push to the branch: `git push origin feature/amazing-feature`
5. Open a Pull Request

---

## 📄 License

Distributed under the **MIT License** — see [LICENSE](LICENSE) for details.

---

## 👨‍💻 Built By

**Prakash** — Student developer from Bhopal, India 🇮🇳  
Building tools that make quality education accessible to every JEE/NEET aspirant.

---

<div align="center">

*If this helped you, please give it a ⭐ on GitHub!*

</div>

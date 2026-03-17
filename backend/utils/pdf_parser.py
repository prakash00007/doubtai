"""
Reads NCERT PDFs and splits them into chunks for the vector DB.
"""
import fitz  # PyMuPDF
import re
import os


def extract_text(pdf_path: str) -> str:
    if not os.path.exists(pdf_path):
        raise FileNotFoundError(
            f"\n❌ File not found: {pdf_path}"
            f"\n   Download from: https://ncert.nic.in/textbook.php"
            f"\n   Save into backend/books/ folder\n"
        )

    print(f"   📄 Reading {os.path.basename(pdf_path)}...")
    doc = fitz.open(pdf_path)
    pages = []

    for i, page in enumerate(doc):
        text = page.get_text("text")
        text = _clean(text)
        if text.strip():
            pages.append(text)
        if (i + 1) % 50 == 0:
            print(f"   {i+1}/{len(doc)} pages read...")

    full = "\n\n".join(pages)
    print(f"   ✅ {len(doc)} pages → {len(full):,} characters")
    return full


def _clean(text: str) -> str:
    lines = []
    for line in text.split('\n'):
        line = line.strip()
        if not line: continue
        if re.fullmatch(r'\d{1,3}', line): continue   # page numbers
        if len(line) <= 2: continue
        lines.append(line)
    return '\n'.join(lines)


def chunk_text(text: str, chunk_size: int = 500, overlap: int = 50) -> list:
    words = text.split()
    chunks = []
    start = 0
    idx = 0

    while start < len(words):
        end = min(start + chunk_size, len(words))
        chunk = ' '.join(words[start:end])
        if len(words[start:end]) >= 50:
            chunks.append({"text": chunk, "index": idx, "word_count": len(words[start:end])})
            idx += 1
        start += (chunk_size - overlap)

    return chunks


if __name__ == "__main__":
    import sys
    path = sys.argv[1] if len(sys.argv) > 1 else "books/ncert_physics_11.pdf"
    try:
        text = extract_text(path)
        chunks = chunk_text(text)
        print(f"Total chunks: {len(chunks)}")
        print(f"Sample:\n{chunks[0]['text'][:300]}")
    except FileNotFoundError as e:
        print(e)
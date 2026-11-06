
import os
from pathlib import Path

from dotenv import load_dotenv
from docx import Document
from groq import Groq
from pypdf import PdfReader
from sklearn.feature_extraction.text import TfidfVectorizer

load_dotenv()

PROJECT_ROOT = Path(__file__).resolve().parents[2]
KNOWLEDGE_BASE = PROJECT_ROOT / "knowledge_base"

GROQ_MODEL = os.getenv("GROQ_MODEL", "openai/gpt-oss-20b")


def extract_text(file_path: Path) -> str:
    """Extract text from PDF, DOCX, or TXT documents."""

    extension = file_path.suffix.lower()

    if extension == ".pdf":
        reader = PdfReader(str(file_path))
        return "\n".join(
            page.extract_text() or "" for page in reader.pages
        )

    if extension == ".docx":
        document = Document(str(file_path))
        return "\n".join(
            paragraph.text for paragraph in document.paragraphs
        )

    if extension == ".txt":
        return file_path.read_text(encoding="utf-8", errors="ignore")

    return ""


def split_into_chunks(
    text: str,
    chunk_size: int = 1000,
    overlap: int = 150,
) -> list[str]:
    """Split document text into overlapping chunks."""

    text = " ".join(text.split())

    if not text:
        return []

    chunks = []
    start = 0

    while start < len(text):
        end = start + chunk_size
        chunks.append(text[start:end])

        if end >= len(text):
            break

        start = end - overlap

    return chunks


def retrieve_documents(
    question: str,
    top_k: int = 4,
) -> list[dict]:
    """Retrieve the most relevant document chunks using TF-IDF."""

    documents = []

    for file_path in KNOWLEDGE_BASE.iterdir():
        if file_path.suffix.lower() not in {".pdf", ".docx", ".txt"}:
            continue

        extracted_text = extract_text(file_path)

        for chunk in split_into_chunks(extracted_text):
            documents.append({
                "source": file_path.name,
                "text": chunk,
            })

    if not documents:
        return []

    texts = [item["text"] for item in documents]

    vectorizer = TfidfVectorizer(ngram_range=(1, 2))

    try:
        document_vectors = vectorizer.fit_transform(texts)
        question_vector = vectorizer.transform([question])
    except ValueError:
        return []

    scores = (
        document_vectors @ question_vector.T
    ).toarray().ravel()

    best_indices = scores.argsort()[::-1][:top_k]

    results = []

    for index in best_indices:
        if scores[index] <= 0:
            continue

        results.append({
            **documents[index],
            "score": round(float(scores[index]), 4),
        })

    return results


def generate_answer(question: str) -> dict:
    """Retrieve context and generate a grounded answer using Groq."""

    api_key = os.getenv("GROQ_API_KEY")

    if not api_key:
        raise ValueError("GROQ_API_KEY is not configured.")

    retrieved_chunks = retrieve_documents(question)

    if not retrieved_chunks:
        return {
            "answer": "I could not find relevant information in the uploaded documents.",
            "sources": [],
        }

    context = "\n\n".join(
        f"Source: {item['source']}\n{item['text']}"
        for item in retrieved_chunks
    )

    client = Groq(api_key=api_key)

    response = client.chat.completions.create(
        model=GROQ_MODEL,
        messages=[
            {
                "role": "system",
                "content": (
                    "You are the ChargePilot EV Charging Information Agent. "
                    "Answer using only the supplied document context. "
                    "If the context does not contain the answer, say so. "
                    "Do not invent station information, prices, or policies. "
                    "Mention the source document names where appropriate."
                ),
            },
            {
                "role": "user",
                "content": (
                    f"Question: {question}\n\n"
                    f"Retrieved document context:\n{context}"
                ),
            },
        ],
        max_completion_tokens=700,
    )

    answer = response.choices[0].message.content

    return {
        "answer": answer or "No answer was generated.",
        "sources": list({
            item["source"] for item in retrieved_chunks
        }),
    }

import os, uuid, json, requests
from datetime import datetime
from langchain_chroma import Chroma
from langchain_huggingface import HuggingFaceEmbeddings
from django.conf import settings

API_URL = "http://localhost:7000/v1/completions"
embeddings = HuggingFaceEmbeddings(model_name="sentence-transformers/all-MiniLM-L6-v2")

DB_ROOT = os.path.join(settings.BASE_DIR, "rag", "company_dbs")
LOG_ROOT = os.path.join(settings.BASE_DIR, "rag", "chat_logs")
os.makedirs(LOG_ROOT, exist_ok=True)

company_dbs = {}

def get_db(company_id: str):
    if company_id not in company_dbs:
        db_path = os.path.join(DB_ROOT, company_id)
        if not os.path.exists(db_path):
            raise ValueError(f"No database found for company ID: {company_id}")
        company_dbs[company_id] = Chroma(persist_directory=db_path, embedding_function=embeddings)
    return company_dbs[company_id]

def get_context(query: str, db: Chroma, k: int = 3) -> str:
    docs = db.similarity_search(query, k=k)
    return "\n\n".join([d.page_content for d in docs])

def stream_model(prompt: str, max_tokens: int = 300):
    payload = {"model": "gemma-2b-it", "prompt": prompt, "max_tokens": max_tokens, "stream": True}
    with requests.post(API_URL, json=payload, stream=True) as r:
        r.raise_for_status()
        for line in r.iter_lines(decode_unicode=True):
            if line and line.startswith("data: "):
                data = line[len("data: "):]
                if data.strip() == "[DONE]":
                    break
                try:
                    chunk = json.loads(data)
                    token = chunk["choices"][0].get("text", "")
                    if token:
                        yield token
                except Exception:
                    continue

def build_prompt(user_query: str, db: Chroma):
    context = get_context(user_query, db, k=3)
    return f"""Use the following context to answer the question.

Context:
{context}

Question: {user_query}

Answer:"""

def save_qa(company_id: str, question=None, answer=None, feedback=None, qid=None):
    file_path = os.path.join(LOG_ROOT, f"{company_id}.md")
    content = ""
    if os.path.exists(file_path):
        with open(file_path, "r", encoding="utf-8") as f:
            content = f.read()

    timestamp = datetime.now().isoformat()

    if answer:  # Save Q&A
        if not qid:
            qid = str(uuid.uuid4())
        entry = (
            "---\n"
            f"QID: {qid}\n"
            f"Question: {question}\n"
            f"Answer: {answer}\n"
            f"Feedback: \n"
            f"Timestamp: {timestamp}\n"
            "---\n\n"
        )
        content += entry
    elif feedback and qid:  # Save Feedback
        sections = content.split("---\n")
        for i in range(len(sections) - 1, -1, -1):
            if f"QID: {qid}\n" in sections[i]:
                lines = sections[i].splitlines()
                for idx, line in enumerate(lines):
                    if line.startswith("Feedback:"):
                        lines[idx] = f"Feedback: {feedback}"
                        break
                sections[i] = "\n".join(lines)
                break
        content = "---\n".join(sections)

    with open(file_path, "w", encoding="utf-8") as f:
        f.write(content)

    return qid

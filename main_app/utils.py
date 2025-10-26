import os, uuid, json, requests
from datetime import datetime
from langchain_chroma import Chroma
from langchain_huggingface import HuggingFaceEmbeddings
from django.conf import settings

# API_URL = "http://localhost:7000/v1/completions"

API_URL = "http://103.182.141.254:7000/v1/completions"
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
    context = get_context(user_query, db, k=1)
    return f"""
You are the official AI Assistant for LegalTech India. Your single most important task is to answer the user's query using ONLY the provided context.

<context>
{context}
</context>

<query>
{user_query}
</query>

**Instructions:**

1.  **Primary Goal (Success Path):** Read the query. If the provided context contains the information needed to answer the query, you MUST provide a clear and helpful answer synthesized from that context. After answering, add a relevant call to action (e.g., "For help with LLP registration, our experts are ready to assist.").

2.  **Fallback (Failure Path):** If the context does **not** contain the information to answer the query, **OR** if the query is **completely unrelated** to legal and business services in India, you **MUST** respond with the following message and nothing else:
    *"I apologize, my knowledge is limited to the information I have been provided about LegalTech India's services. I am unable to answer that question. Is there anything I can help you with regarding business registration, compliance, or our other services?"*

3.  **Greetings:** If the user provides a simple greeting like "hello," respond politely and ask how you can help.

4.  **Final Check:** Do not provide legal advice.

Answer:
"""

from .models import ChatLog, Student

def save_qa(company_id: str, question=None, answer=None, feedback=None, qid=None):
    if not qid:
        qid = str(uuid.uuid4())

    try:
        student = Student.objects.get(student_id=company_id)
    except Student.DoesNotExist:
        raise ValueError(f"No student found with ID: {company_id}")

    if answer:  # Save new Q&A
        ChatLog.objects.create(
            qid=qid,
            student=student,
            question=question,
            answer=answer,
        )
    elif feedback and qid:  # Update feedback
        try:
            log = ChatLog.objects.get(qid=qid, student=student)
            log.feedback = feedback
            log.save()
        except ChatLog.DoesNotExist:
            raise ValueError(f"No chat log found with QID: {qid}")

    return qid

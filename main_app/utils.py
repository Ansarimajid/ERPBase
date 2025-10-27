import os, uuid, json, time, itertools
from datetime import datetime
from google import genai
from google.genai import types
import chromadb
from chromadb import Documents, EmbeddingFunction, Embeddings
# from langchain_chroma import Chroma
# from langchain_huggingface import HuggingFaceEmbeddings
from django.conf import settings
from .models import ChatLog, Student

# ==== GEMINI API KEYS ====
API_KEYS = [
    "AIzaSyDjjbiQh5ojq0MLKhI47snoi8b2HtwXhgw",
    "AIzaSyBLc81jGeNSmglfbohw74VxZ8p29QKlOR8",
    "AIzaSyB2lnnLnyK3AWqswwkq6-FT3IorE0wLXOc",
]

MODEL = "gemma-3-27b-it"   # fast, cheap, supports streaming
HIT_LIMIT = 20               # max hits per minute per key
TIME_WINDOW = 60             # seconds
KEY_MAX_AGE = 3600           # force rotate every hour

key_usage = {key: [] for key in API_KEYS}
key_last_used = {key: 0 for key in API_KEYS}
key_cycle = itertools.cycle(API_KEYS)
current_key = next(key_cycle)
key_last_used[current_key] = time.time()

def _get_available_key():
    """Rotate Gemini API key automatically if usage limits are hit."""
    global current_key
    while True:
        now = time.time()
        timestamps = key_usage[current_key]
        key_usage[current_key] = [t for t in timestamps if now - t < TIME_WINDOW]
        hits = len(key_usage[current_key])
        age = now - key_last_used[current_key]

        if age > KEY_MAX_AGE:
            print(f"🔁 Rotating expired key: {current_key}")
            current_key = next(key_cycle)
            key_last_used[current_key] = time.time()
            continue

        if hits < HIT_LIMIT:
            return current_key

        print(f"⚠️ Rate limit hit for {current_key}, rotating...")
        current_key = next(key_cycle)
        key_last_used[current_key] = time.time()

        if all(len(key_usage[k]) >= HIT_LIMIT for k in API_KEYS):
            print("⏳ All keys over limit, sleeping 10s...")
            time.sleep(10)

# ==== EMBEDDING + DB (Gemini + Chroma) ====
DB_ROOT = os.path.join(settings.BASE_DIR, "rag", "company_dbs")
LOG_ROOT = os.path.join(settings.BASE_DIR, "rag", "chat_logs")
os.makedirs(LOG_ROOT, exist_ok=True)
company_dbs = {}

# --- Gemini embedding function ---
class GeminiEmbeddingFunction(EmbeddingFunction):
    def __init__(self):
        super().__init__()
        self.client = genai.Client(api_key=_get_available_key())  # use rotating key system

    def __call__(self, input: Documents) -> Embeddings:
        EMBEDDING_MODEL_ID = "gemini-embedding-001"
        response = self.client.models.embed_content(
            model=EMBEDDING_MODEL_ID,
            contents=input,
            config=types.EmbedContentConfig(task_type="retrieval_query")
        )
        return response.embeddings[0].values


# --- Load per-company Chroma DB ---
def get_db(company_id: str):
    """Load a persistent Chroma DB for a given company."""
    if company_id not in company_dbs:
        db_path = os.path.join(DB_ROOT, company_id)
        if not os.path.exists(db_path):
            raise ValueError(f"No database found for company ID: {company_id}")

        chroma_client = chromadb.PersistentClient(path=db_path)
        db = chroma_client.get_collection(
            name="try1",  # or use company_id as name if unique per org
            embedding_function=GeminiEmbeddingFunction()
        )
        company_dbs[company_id] = db

    return company_dbs[company_id]


# --- Retrieve top documents ---
def get_context(query: str, db, k: int = 3) -> str:
    """Query a Gemini-embedded Chroma DB and return concatenated results."""
    results = db.query(query_texts=[query], n_results=k)
    docs = results["documents"][0]
    return "\n\n".join(docs)


# ==== GEMINI STREAMING ====
def stream_model(prompt: str, max_tokens: int = 300):
    """
    Stream response from Gemini model with API key rotation.
    """
    global current_key
    while True:
        key = _get_available_key()
        client = genai.Client(api_key=key)
        contents = [types.Content(role="user", parts=[types.Part.from_text(text=prompt)])]
        config = types.GenerateContentConfig(max_output_tokens=max_tokens)

        try:
            key_usage[key].append(time.time())
            print(f"🚀 Using Gemini key: {key}")

            for chunk in client.models.generate_content_stream(
                model=MODEL, contents=contents, config=config
            ):
                if chunk.text:
                    yield chunk.text

            break

        except Exception as e:
            print(f"❌ Error with key {key}: {e}")
            current_key = next(key_cycle)
            key_last_used[current_key] = time.time()
            continue

# ==== PROMPT BUILD ====
def build_prompt(user_query: str, db):
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

2.  **Greetings:** If the user provides a simple greeting, respond politely and **only** ask how you can help and **nothing else**.

3.  **Fallback (Failure Path):** If the context does **not** contain the information to answer the query, **OR** if the query is **completely unrelated** to legal and business services in India, you **MUST** respond with the following message and nothing else:
    *"I apologize, my knowledge is limited to the information I have been provided about LegalTech India's services. I am unable to answer that question. Is there anything I can help you with regarding business registration, compliance, or our other services?"*

4.  **Final Check:** Do not provide legal advice.

Answer:
"""


def save_qa(company_id: str, question=None, answer=None, feedback=None, qid=None):
    if not qid:
        qid = str(uuid.uuid4())

    try:
        student = Student.objects.get(student_id=company_id)
    except Student.DoesNotExist:
        raise ValueError(f"No student found with ID: {company_id}")

    if answer:
        ChatLog.objects.create(qid=qid, student=student, question=question, answer=answer)
    elif feedback and qid:
        try:
            log = ChatLog.objects.get(qid=qid, student=student)
            log.feedback = feedback
            log.save()
        except ChatLog.DoesNotExist:
            raise ValueError(f"No chat log found with QID: {qid}")

    return qid
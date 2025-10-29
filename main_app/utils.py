import uuid, time, itertools
from google import genai
from google.genai import types
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
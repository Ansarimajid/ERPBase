import json
import requests
from django.contrib import messages
from django.contrib.auth import login, logout
from django.http import HttpResponse, JsonResponse
from django.shortcuts import redirect, render, reverse
from django.views.decorators.csrf import csrf_exempt

from .EmailBackend import EmailBackend

from django.http import JsonResponse, StreamingHttpResponse, FileResponse
from django.views.decorators.http import require_POST
from django.conf import settings
import json, uuid, os
from .utils import stream_model, save_qa


def login_page(request):
    if request.user.is_authenticated:
        if request.user.user_type == '1':
            return redirect(reverse("admin_home"))
        elif request.user.user_type == '2':
            return redirect(reverse("staff_home"))
        else:
            return redirect(reverse("student_home"))
    return render(request, 'main_app/login.html')


def doLogin(request, **kwargs):
    if request.method != 'POST':
        return HttpResponse("<h4>Denied</h4>")
    else:      
        #Authenticate
        user = EmailBackend.authenticate(request, username=request.POST.get('email'), password=request.POST.get('password'))
        if user != None:
            login(request, user)
            
            # Handle "Remember Me" functionality
            remember_me = request.POST.get('remember')
            if remember_me:
                # Set session to expire when browser closes = False
                # Session will last for 30 days
                request.session.set_expiry(30 * 24 * 60 * 60)  # 30 days in seconds
            else:
                # Set session to expire when browser closes
                request.session.set_expiry(0)
            
            if user.user_type == '1':
                return redirect(reverse("admin_home"))
            elif user.user_type == '2':
                return redirect(reverse("staff_home"))
            else:
                return redirect(reverse("student_home"))
        else:
            messages.error(request, "Invalid details")
            return redirect("/")

def logout_user(request):
    if request.user != None:
        logout(request)
    return redirect("/")

@csrf_exempt
@require_POST
def company_chat(request, company_id):
    data = json.loads(request.body.decode("utf-8"))
    question = data.get("question")
    history = data.get("history", [])

    if not question:
        return JsonResponse({"error": "No question provided"}, status=400)

    # 🔹 Call your Flask API for prompt generation instead of local build_prompt
    try:
        flask_response = requests.post(
            "http://103.182.141.254:7000/generate_prompt",
            headers={"Content-Type": "application/json"},
            json={"company_id": company_id, "user_query": question},
            timeout=10
        )
        if flask_response.status_code != 200:
            return JsonResponse({"error": "Flask API failed", "details": flask_response.text}, status=500)
        prompt_data = flask_response.json()
        prompt = prompt_data.get("prompt", "")
    except Exception as e:
        return JsonResponse({"error": f"Failed to connect Flask API: {e}"}, status=500)

    print(f"📝 Prompt fetched from Flask for company {company_id}:\n{prompt}")

    qid = str(uuid.uuid4())

    def event_stream():
        answer = ""
        for token in stream_model(prompt):  # ✅ Still using Gemini streaming
            answer += token
            safe_token = token.replace("\n", " ")
            yield f"data: {safe_token}\n\n"

        try:
            from .utils import save_qa
            save_qa(company_id, question, answer, qid=qid)
        except Exception as e:
            print(f"⚠️ Failed to save Q&A: {e}")

    response = StreamingHttpResponse(event_stream(), content_type="text/event-stream")
    response["X-QID"] = qid
    return response


@csrf_exempt
@require_POST
def submit_feedback(request, company_id):
    data = json.loads(request.body.decode("utf-8"))
    qid = data.get("qid")
    feedback = data.get("feedback")

    if not qid or not feedback:
        return JsonResponse({"error": "Both qid and feedback are required"}, status=400)

    try:
        save_qa(company_id, feedback=feedback, qid=qid)
    except Exception as e:
        print(f"⚠️ Failed to save feedback: {e}")

    return JsonResponse({"status": "success", "message": "Feedback saved"})


from django.shortcuts import render
from .models import Student, StudentBot

def home(request):
    base_url = request.build_absolute_uri('/')  # Gets full domain + port

    # Try to get student for this user
    try:
        student = Student.objects.get(admin=request.user)
        student_bot, _ = StudentBot.objects.get_or_create(student=student)

        bot_name = student_bot.bot_name
        color = student_bot.color
        student_id = student.student_id
    except Student.DoesNotExist:
        # Fallback defaults if no student exists
        bot_name = "NuroBot"
        color = "#b72615"
        student_id = "BX100DCA"

    context = {
        "base_url": base_url,
        "bot_name": bot_name,
        "color": color,
        "student_id": student_id,
    }

    return render(request, "Rag/index.html", context)



def widget(request):
    widget_path = os.path.join(settings.BASE_DIR, "main_app/templates/Rag/", "widget.js")
    return FileResponse(open(widget_path, "rb"), content_type="application/javascript")
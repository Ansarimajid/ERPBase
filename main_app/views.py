import json
import requests
from django.contrib import messages
from django.contrib.auth import authenticate, login, logout
from django.http import HttpResponse, JsonResponse
from django.shortcuts import get_object_or_404, redirect, render, reverse
from django.views.decorators.csrf import csrf_exempt

from .EmailBackend import EmailBackend

# Create your views here.

from django.http import JsonResponse, StreamingHttpResponse, FileResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST
from django.conf import settings
import json, uuid, os
from .utils import get_db, build_prompt, stream_model, save_qa


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
        # #Google recaptcha
        # captcha_token = request.POST.get('g-recaptcha-response')
        # captcha_url = "https://www.google.com/recaptcha/api/siteverify"
        # captcha_key = "6LfTGD4qAAAAALtlli02bIM2MGi_V0cUYrmzGEGd"
        # data = {
        #     'secret': captcha_key,
        #     'response': captcha_token
        # }
        # # Make request
        # try:
        #     captcha_server = requests.post(url=captcha_url, data=data)
        #     response = json.loads(captcha_server.text)
        #     if response['success'] == False:
        #         messages.error(request, 'Invalid Captcha. Try Again')
        #         return redirect('/')
        # except:
        #     messages.error(request, 'Captcha could not be verified. Try Again')
        #     return redirect('/')
        
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


from django.http import StreamingHttpResponse, JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST
import uuid

@csrf_exempt
@require_POST
def company_chat(request, company_id):
    try:
        db = get_db(company_id)
    except ValueError as e:
        return JsonResponse({"error": str(e)}, status=404)

    data = json.loads(request.body.decode("utf-8"))
    question = data.get("question")
    history = data.get("history", [])

    if not question:
        return JsonResponse({"error": "No question provided"}, status=400)

    prompt = build_prompt(question, db)
    print(f"📝 Built prompt for company {company_id}:\n{prompt}")
    qid = str(uuid.uuid4())  # ✅ generate QID upfront

    def event_stream():
        answer = ""
        for token in stream_model(prompt):
            answer += token
            safe_token = token.replace("\n", " ")
            yield f"data: {safe_token}\n\n"
        try:
            save_qa(company_id, question, answer, qid=qid)
        except Exception as e:
            # Don’t block widget if saving fails
            print(f"⚠️ Failed to save Q&A: {e}")

    response = StreamingHttpResponse(event_stream(), content_type="text/event-stream")
    response["X-QID"] = qid  # ✅ always send QID
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


def home(request):
    return render(request, "Rag/index.html")

def widget(request):
    widget_path = os.path.join(settings.BASE_DIR, "rag", "widget.js")
    return FileResponse(open(widget_path, "rb"), content_type="application/javascript")
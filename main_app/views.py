import json
import requests
from django.contrib import messages
from django.contrib.auth import authenticate, login, logout
from django.http import HttpResponse, JsonResponse
from django.shortcuts import get_object_or_404, redirect, render, reverse
from django.views.decorators.csrf import csrf_exempt

from .EmailBackend import EmailBackend

# Create your views here.


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


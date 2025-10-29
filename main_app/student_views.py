from django.contrib import messages
from django.core.files.storage import FileSystemStorage
from django.shortcuts import (get_object_or_404,
                              redirect, render)
from django.urls import reverse
from django.views.decorators.csrf import csrf_exempt

from .forms import *
from .models import *

def student_home(request):
    student = get_object_or_404(Student, admin=request.user)

    total_questions = ChatLog.objects.filter(student=student).count()
    satisfied_count = ChatLog.objects.filter(student=student, feedback__iexact="satisfied").count()
    not_satisfied_count = ChatLog.objects.filter(student=student, feedback__iexact="not satisfied").count()

    recent_questions = ChatLog.objects.filter(student=student).order_by("-timestamp")[:5]
    all_logs = ChatLog.objects.filter(student=student).order_by("-timestamp")

    context = {
        'page_title': 'NuroBot Dashboard',
        'total_questions': total_questions,
        'satisfied_count': satisfied_count,
        'not_satisfied_count': not_satisfied_count,
        'recent_questions': recent_questions,
    }
    return render(request, 'student_template/erpnext_student_home.html', context)



def student_view_profile(request):
    student = get_object_or_404(Student, admin=request.user)
    form = StudentEditForm(request.POST or None, request.FILES or None,
                           instance=student)
    context = {'form': form,
               'page_title': 'View/Edit Profile'
               }
    if request.method == 'POST':
        try:
            if form.is_valid():
                first_name = form.cleaned_data.get('first_name')
                last_name = form.cleaned_data.get('last_name')
                password = form.cleaned_data.get('password') or None
                address = form.cleaned_data.get('address')
                gender = form.cleaned_data.get('gender')
                passport = request.FILES.get('profile_pic') or None
                admin = student.admin
                if password != None:
                    admin.set_password(password)
                if passport != None:
                    fs = FileSystemStorage()
                    filename = fs.save(passport.name, passport)
                    passport_url = fs.url(filename)
                    admin.profile_pic = passport_url
                admin.first_name = first_name
                admin.last_name = last_name
                admin.address = address
                admin.gender = gender
                admin.save()
                student.save()
                messages.success(request, "Profile Updated!")
                return redirect(reverse('student_view_profile'))
            else:
                messages.error(request, "Invalid Data Provided")
        except Exception as e:
            messages.error(request, "Error Occured While Updating Profile " + str(e))

    return render(request, "student_template/student_view_profile.html", context)

def student_chatlog(request):
    student = get_object_or_404(Student, admin=request.user)
    logs = ChatLog.objects.filter(student=student).order_by("-timestamp")

    context = {
        "page_title": "My Chat History",
        "logs": logs,
    }
    return render(request, "student_template/student_chatlog.html", context)

def student_chatlog_satisfied(request):
    student = get_object_or_404(Student, admin=request.user)
    satisfied_logs = ChatLog.objects.filter(student=student, feedback__iexact="satisfied").order_by("-timestamp")

    context = {
        "page_title": "My Chat History - Satisfied",
        "logs": satisfied_logs,
    }
    return render(request, "student_template/student_chatlog.html", context)

def student_chatlog_notsatisfied(request):
    student = get_object_or_404(Student, admin=request.user)
    notsatisfied_logs = ChatLog.objects.filter(student=student, feedback__iexact="not satisfied").order_by("-timestamp")

    context = {
        "page_title": "My Chat History - Not Satisfied",
        "logs": notsatisfied_logs,
    }
    return render(request, "student_template/student_chatlog.html", context)

from django.shortcuts import render, get_object_or_404
from .models import Student, StudentBot

def snippet(request):
    student = get_object_or_404(Student, admin=request.user)
    student_id = student.student_id
    student_bot, _ = StudentBot.objects.get_or_create(student=student)

    base_url = request.build_absolute_uri('/')

    context = {
        "page_title": "Snippet to Connect",
        "student_id": student_id,
        "bot_name": student_bot.bot_name,
        "color": student_bot.color,
        "base_url": base_url,
    }
    return render(request, "student_template/snippet.html", context)


from django.http import JsonResponse
import json

@csrf_exempt
def save_bot_customization(request):
    if request.method == "POST":
        data = json.loads(request.body.decode("utf-8"))
        bot_name = data.get("bot_name")
        color = data.get("color")

        student = get_object_or_404(Student, admin=request.user)

        student_bot, created = StudentBot.objects.get_or_create(student=student)
        student_bot.bot_name = bot_name
        student_bot.color = color
        student_bot.save()

        return JsonResponse({"success": True, "message": "Bot customization saved!"})
    
    return JsonResponse({"success": False, "error": "Invalid request method."})
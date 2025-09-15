import json
import math
from datetime import datetime

from django.contrib import messages
from django.core.files.storage import FileSystemStorage
from django.http import HttpResponse, JsonResponse
from django.shortcuts import (HttpResponseRedirect, get_object_or_404,
                              redirect, render)
from django.urls import reverse
from django.views.decorators.csrf import csrf_exempt

from .forms import *
from .models import *

import numpy as np
from sklearn.metrics.pairwise import cosine_similarity
from .utils import embeddings   # ✅ import from utils.py

def group_similar_questions(questions, threshold=0.9):
    """
    Group similar questions by cosine similarity on embeddings.
    Returns a list of dicts:
    {
        "representative": str,
        "count": int,
        "questions": [..]
    }
    """
    if not questions:
        return []

    # Extract texts
    texts = [q.question for q in questions]

    # Generate embeddings
    embeddings_matrix = embeddings.embed_documents(texts)
    embeddings_matrix = np.array(embeddings_matrix)

    groups = []
    used = set()

    for i, q in enumerate(questions):
        if i in used:
            continue
        group = {
            "representative": q.question,  # 👈 first version of the question as representative
            "count": 1,
            "questions": [q.question],
        }
        used.add(i)

        for j in range(i + 1, len(questions)):
            if j in used:
                continue
            sim = cosine_similarity(
                [embeddings_matrix[i]], [embeddings_matrix[j]]
            )[0][0]
            if sim >= threshold:
                group["count"] += 1
                group["questions"].append(questions[j].question)
                used.add(j)

        groups.append(group)

    # Sort by frequency
    groups.sort(key=lambda g: g["count"], reverse=True)
    return groups



def student_home(request):
    student = get_object_or_404(Student, admin=request.user)

    total_questions = ChatLog.objects.filter(student=student).count()
    satisfied_count = ChatLog.objects.filter(student=student, feedback__iexact="satisfied").count()
    not_satisfied_count = ChatLog.objects.filter(student=student, feedback__iexact="not satisfied").count()

    recent_questions = ChatLog.objects.filter(student=student).order_by("-timestamp")[:5]
    all_logs = ChatLog.objects.filter(student=student).order_by("-timestamp")
    most_asked = group_similar_questions(all_logs, threshold=0.9)[:5]



    context = {
        'page_title': 'Student Homepage',
        'total_questions': total_questions,
        'satisfied_count': satisfied_count,
        'not_satisfied_count': not_satisfied_count,
        'recent_questions': recent_questions,
        'most_asked': most_asked,
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

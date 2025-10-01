# resumes/views.py
from django.shortcuts import render
from django.contrib.auth.decorators import login_required

@login_required
def upload_resume(request):
    return render(request, 'resumes/upload.html')

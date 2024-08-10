from django.shortcuts import render, redirect
from django.http import JsonResponse
from django.contrib.auth.models import User

def chatPage(request, *args, **kwargs):
    context = {}
    return render(request, "chatPage.html", context)

def get_all_usernames(request):
    usernames = User.objects.values_list('username', flat=True)
    return JsonResponse(list(usernames), safe=False)
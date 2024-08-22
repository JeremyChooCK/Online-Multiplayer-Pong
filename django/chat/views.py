from django.shortcuts import render, redirect
from django.http import JsonResponse
from django.contrib.auth.models import User
from rest_framework import generics, permissions
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated

def chatPage(request, *args, **kwargs):
    context = {}
    return render(request, "chatPage.html", context)

# @api_view(['GET'])
# @permission_classes([IsAuthenticated])
def get_all_usernames(request):
    usernames = User.objects.values_list('username', flat=True)
    return JsonResponse(list(usernames), safe=False)
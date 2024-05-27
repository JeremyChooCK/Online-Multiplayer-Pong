from django.shortcuts import render

# Create your views here.

def index(request):
    return render(request, 'index.html')

def oauth_token(request):
    return render(request, 'oauth_token.html')
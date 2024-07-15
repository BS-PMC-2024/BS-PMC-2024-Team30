from django.shortcuts import render, redirect
from django.http import HttpResponse
#from .forms import ManagerUserCreationForm, RegularUserCreationForm

def home(request):
    return render(request, 'noss/home.html')

def login(request):
    return render(request, 'noss/login.html')

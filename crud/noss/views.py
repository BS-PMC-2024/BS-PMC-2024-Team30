from django.shortcuts import render

def home(request):
    return render(request, 'noss/home.html')
#test1234
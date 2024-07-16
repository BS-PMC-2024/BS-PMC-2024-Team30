from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required

@login_required
def home(request):
    if request.user.persona == 'manager':
        return redirect('manager_home')
    else:
        return redirect('developer_home')

@login_required
def manager_home(request):
    return render(request, 'noss/manager_home.html')

@login_required
def developer_home(request):
    return render(request, 'noss/developer_home.html')

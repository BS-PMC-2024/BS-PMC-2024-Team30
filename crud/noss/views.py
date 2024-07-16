from django.shortcuts import render

def home(request):
<<<<<<< Updated upstream
    return render(request, 'noss/home.html')
#test
=======
<<<<<<< HEAD
<<<<<<< HEAD
    return HttpResponse('<h1>Home</h1>')
=======
=======
>>>>>>> 42c11bd (commit)
    return render(request, 'noss/home.html')

def login(request):
    return render(request, 'noss/login.html')
<<<<<<< HEAD
>>>>>>> 2844f25 (basic website - BSPMS2430-2 , BSPMS2430-3)
=======
=======
    return HttpResponse('<h1>Home</h1>')
#set
>>>>>>> 6e16e92 (commit)
>>>>>>> 42c11bd (commit)
>>>>>>> Stashed changes

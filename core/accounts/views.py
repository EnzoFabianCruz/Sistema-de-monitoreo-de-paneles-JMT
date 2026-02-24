from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login, logout

def login_view(request):
    if request.method =="POST":
        username = request.POST.get("username")
        password = request.POST.get("password")

        user = authenticate(
            request,
            username=username,
            password=password
        )
        if user is not None:
            login(request, user)
            if user.groups.filter(name="Administrador").exists():
                return redirect("admin")
            else:
                return redirect("home")
        
        else:
            return render(request, "accounts/login.html",{
                "error": "Usuario o contraseña incorrectos"
            })

    return render(request, "accounts/login.html")

def logout_view(request):
    logout(request)
    return redirect('login')

from django.shortcuts import render, redirect
from django.contrib import auth
from django.contrib.auth.models import User

from ejudge.database import EjudgeDatabase
from . import forms


def is_login_and_password_correct(login, password):
    ejudge_database = EjudgeDatabase()
    is_correct = ejudge_database.is_login_and_password_correct(login, password)
    if not is_correct:
        return False, 0
    return True, ejudge_database.get_user_by_login(login)['user_id']


def get_user_or_create(login, password, ejudge_user_id):
    qs = User.objects.filter(username=login)
    if qs.exists():
        user = qs.first()
    else:
        user = User.objects.create_user(login, password=password, first_name=login)

    user.info.ejudge_user_id = ejudge_user_id
    return user


def login(request):
    if request.method == 'POST':
        form = forms.LoginForm(data=request.POST)
        if form.is_valid():
            login = form.cleaned_data['login']
            password = form.cleaned_data['password']
            is_correct, ejudge_user_id = is_login_and_password_correct(login, password)
            if is_correct:
                user = get_user_or_create(login, password, ejudge_user_id)
                auth.login(request, user)
                return redirect('map:index')
            form.add_error('password', 'Неверный пароль')
    else:
        form = forms.LoginForm()
    return render(request, 'users/login.html', {'form': form})


# TODO: only POST
def logout(request):
    auth.logout(request)
    return redirect('map:index')

from django import forms


class LoginForm(forms.Form):
    login = forms.CharField(max_length=255, strip=True, label='Логин', label_suffix='')

    password = forms.CharField(max_length=255, widget=forms.PasswordInput(), label='Пароль', label_suffix='')

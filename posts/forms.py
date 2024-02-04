from django import forms

from .models import User


class ResetForm(forms.Form):
    username = forms.CharField(min_length=4, max_length=255, label='Имя пользователя')
    email = forms.EmailField(max_length=255)
    password1 = forms.CharField(widget=forms.PasswordInput, label='Пароль')
    password2 = forms.CharField(widget=forms.PasswordInput, label='Подтвердите пароль')

    def clean_username(self):
        username = self.cleaned_data.get('username')
        if User.objects.filter(username=username).exists():
            return username
        raise forms.ValidationError('Пользователь с таким именем уже существует')

    def clean_email(self):
        email = self.cleaned_data.get("email")
        if User.objects.filter(email=email).exists():
            return email
        raise forms.ValidationError("Пользователь с таким email уже существует")

    def clean(self):
        data = self.cleaned_data
        if data['password1'] != data['password2']:
            raise forms.ValidationError("Пароли не совподают")
        return data


class RegisterForm(forms.Form):
    username = forms.CharField(min_length=3, max_length=150, label='Имя пользователя')
    email = forms.EmailField(max_length=256)
    password1 = forms.CharField(widget=forms.PasswordInput, label="Пароль")
    password2 = forms.CharField(widget=forms.PasswordInput, label="Повторите пароль")

    def clean_username(self):
        username = self.cleaned_data.get('username')
        if username and User.objects.filter(username=username).exists():
            raise forms.ValidationError('Пользователь с таким именем уже существует')
        return username

    def clean_email(self):
        email = self.cleaned_data.get('email')
        if email and User.objects.filter(email=email).exists():
            raise forms.ValidationError('Пользователь с таким email уже существует')
        return email

    def clean(self):
        data = self.cleaned_data
        if data["password1"] != data["password2"]:
            raise forms.ValidationError("Пароли не совпадают")
        return data

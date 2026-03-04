from django.contrib.auth.forms import UserCreationForm
from .models import User
from django import forms


class UserSignupForm(UserCreationForm):

    class Meta:
        model=User
        fields=["name","gender","role","email","phone","address","password1","password2"]
        widgets={
            'password1':forms.PasswordInput(),
            'password2':forms.PasswordInput(),
            'name':forms.TextInput(attrs={'class':'form-control'}),
            'gender':forms.RadioSelect(attrs={'class':'form-control'}),
            'phone':forms.TextInput(attrs={'class':'form-control'}),
            'address':forms.TextInput(attrs={'class':'form-control'}),
            'role':forms.Select(attrs={'class':'form-control'}),
        }

class UserLoginForm(forms.Form):
    email=forms.EmailField()
    password=forms.CharField(widget=forms.PasswordInput())


from django.forms import ModelForm
from .models import Todo
from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User

class SignUpForm(UserCreationForm):
    
    email = forms.EmailField(max_length=150, help_text='Email')


    class Meta:
        model = User
        fields = ('username', 'email', 'password1', 'password2', )

class TodoForm(ModelForm):
    
    class Meta:
        model = Todo
        fields = ['title', 'memo', 'important']

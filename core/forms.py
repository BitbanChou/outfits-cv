from django import forms
from .models import SkinTone, ClothingItem


class LoginForm(forms.Form):
    username = forms.CharField()
    password = forms.CharField(widget=forms.PasswordInput)


class SkinToneForm(forms.ModelForm):
    class Meta:
        model  = SkinTone
        fields = ['image']


class ClothingItemForm(forms.ModelForm):
    class Meta:
        model  = ClothingItem
        fields = ['image', 'category']

from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User

class RegisterForm(UserCreationForm):
    email = forms.EmailField(required=True)
    
    class Meta:
        model = User
        fields = ("username", "email", "password1", "password2")
    
    def save(self, commit=True):
        user = super(RegisterForm, self).save(commit=False)
        user.email = self.cleaned_data['email']
        if commit:
            user.save()
        return user
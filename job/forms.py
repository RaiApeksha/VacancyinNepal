from django import forms
from django.contrib.auth.models import User
from .models import Student, Recruiter

class StudentUpdateForm(forms.ModelForm):
    class Meta:
        model = Student
        fields = ['mobile', 'image', 'gender']

class UserUpdateForm(forms.ModelForm):
    class Meta:
        model = User
        fields = ['first_name', 'last_name']

class RecruiterUpdateForm(forms.ModelForm):
    class Meta:
        model = Recruiter
        fields = ['mobile', 'company', 'contact', 'image']
        labels = {
            'company': 'Company Name',
        }

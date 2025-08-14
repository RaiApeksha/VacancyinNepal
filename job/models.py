from django.db import models
from django.contrib.auth.models import User
from django.contrib.auth.models import AbstractUser

class Student(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    mobile = models.CharField(max_length=15, null=True)
    image = models.FileField(null=True)
    gender = models.CharField(max_length=10, null=True)
    type = models.CharField(max_length=15, null=True)


    def __str__(self):
        return self.user.username

from django.db import models
from django.contrib.auth.models import User

from django.db import models
from django.contrib.auth.models import User

class Recruiter(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    mobile = models.CharField(max_length=15, blank=True, null=True)
    company = models.CharField(max_length=100, blank=True, null=True)
    contact = models.CharField(max_length=100, blank=True, null=True)
    gender = models.CharField(max_length=10, null=True)
    image = models.ImageField(upload_to='recruiter_images/', blank=True, null=True)
    status = models.CharField(
        max_length=20,
        choices=(("Pending", "Pending"), ("Approved", "Approved")),
        default="Pending",
    )
    created_date = models.DateTimeField(auto_now_add=True)
    def __str__(self):
        return self.user.username



class Job(models.Model):
    recruiter = models.ForeignKey(Recruiter, on_delete=models.CASCADE)
    title = models.CharField(max_length=100)
    description = models.TextField()
    category = models.CharField(max_length=100)
    location = models.CharField(max_length=100)
    experience = models.CharField(max_length=100)
    salary = models.CharField(max_length=50)
    created = models.DateTimeField(auto_now_add=True)
    def __str__(self):
        return self.title

class Application(models.Model):
    job = models.ForeignKey(Job, on_delete=models.CASCADE)
    student = models.ForeignKey(Student, on_delete=models.CASCADE)
    resume = models.FileField()
    applied_on = models.DateTimeField(auto_now_add=True)
    def __str__(self):
        return f"{self.student.user.username} applied to {self.job.title}"





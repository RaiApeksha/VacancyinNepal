from django.contrib import admin
from .models import Student, Recruiter, Job, Application
from django.contrib.admin.sites import AlreadyRegistered

# ✅ Custom Admin for Recruiter to easily approve/deny
@admin.register(Recruiter)
class RecruiterAdmin(admin.ModelAdmin):
    list_display = ['user', 'mobile', 'company', 'status', 'created_date']
    list_filter = ['status']
    search_fields = ['user__username', 'company', 'mobile']
    list_editable = ['status']  # Editable directly in list view

# ✅ Custom Admin for Application model (To display applied job, student, and date)
class ApplicationAdmin(admin.ModelAdmin):
    list_display = ('job', 'student', 'applied_on')  # Show job title, student name, and application date
    search_fields = ('student__user__username', 'job__title')  # Allow searching by student username and job title
    list_filter = ('job', 'student')  # Filter by job or student

# ✅ Register models with the admin site
admin.site.register(Student)
admin.site.register(Job)

# Register the Application model with the custom admin view (only once)
try:
    admin.site.register(Application, ApplicationAdmin)
except AlreadyRegistered:
    pass



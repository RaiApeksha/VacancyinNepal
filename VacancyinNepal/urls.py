from django.contrib import admin
from django.urls import path
from job import views
from django.conf import settings
from django.conf.urls.static import static
from job import views as job_views

urlpatterns = [
    # Admin panel
    path('admin/', admin.site.urls),

    # Homepage
    path('', views.index, name="index"),

    # Authentication routes
    path('admin_login/', views.admin_login, name="admin_login"),
    path('admin_logout/', views.admin_logout, name='admin_logout'),  # Usually keep admin logout near admin login
    path('recruiter_login/', views.recruiter_login, name="recruiter_login"),
    path('user_signup/', views.user_signup, name='user_signup'),
    path('logout/', views.custom_logout, name="logout"),
    path('signup/', views.user_signup, name='user_signup'),
    path('student_login/', views.student_login, name="student_login"),


 # Admin dashboard and actions
    path('admin_home/', views.admin_home, name='admin_home'),

    path('update_recruiter_status/<int:recruiter_id>/<str:action>/', views.update_recruiter_status, name='update_recruiter_status'),

    # Job management
    path('post_job/', views.post_job, name="post_job"),
    path('job/', views.job_list, name="job_list"),
    path('job/<int:job_id>/', views.job_detail, name="job_detail"),
    path('job/<int:job_id>/apply/', views.apply_job, name="apply_job"),
    path("accounts/login/", job_views.student_login, name="login"),

    # User dashboards
    path('user_home/', views.user_home, name="user_home"),
    path('recruiter_dashboard/', views.recruiter_dashboard, name="recruiter_dashboard"),


    # Profile updates
    path('update_student/', views.update_student_profile, name="update_student_profile"),
    path('update_recruiter/', views.update_recruiter_profile, name="update_recruiter_profile"),
]

# Static and media files in development
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

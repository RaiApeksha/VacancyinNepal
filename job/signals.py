

from django.db.models.signals import post_save
from django.dispatch import receiver
from django.core.mail import send_mail
from django.conf import settings
from django.contrib.auth.models import User
from .models import Application
import sys
import codecs
sys.stdout = codecs.getwriter("utf-8")(sys.stdout.detach())

# --- 1. Send Welcome Email on User Signup ---
def user_signup(request):
    error = ""
    if request.method == 'POST':
        f = request.POST['fname']
        l = request.POST['lname']
        p = request.POST['pwd']
        i = request.FILES.get('image')
        e = request.POST['email']
        g = request.POST['gender']
        c = request.POST['contact']
        try:
            if User.objects.filter(username=e).exists():
                error = "email_taken"
            else:
                user = User.objects.create_user(first_name=f, username=e, password=p, last_name=l, email=e)
                Student.objects.create(user=user, mobile=c, image=i, gender=g, type="student")
                error = "no"

                # send welcome email
                send_mail(
                    subject="Welcome to Vacancy in Nepal!",
                    message=f"Hi {f},\n\nThank you for signing up on Vacancy in Nepal!",
                    from_email=settings.EMAIL_HOST_USER,
                    recipient_list=[e],
                    fail_silently=False,
                )

                # notify admin of new signup
                send_mail(
                    subject="New User Registered",
                    message=f"New student registered with email: {e}",
                    from_email=settings.EMAIL_HOST_USER,
                    recipient_list=["infovin6@gmail.com"],
                    fail_silently=False,
                )
                print("emails sent after signup!")

        except Exception as e:
            print("Signup Error:", e)
            traceback.print_exc()
            error = "yes"

    return render(request, 'user_signup.html', {'error': error})
# --- 2. Send Job Application Confirmation ---
@receiver(post_save, sender=Application)
def send_application_confirmation(sender, instance, created, **kwargs):
    if created:
        job = instance.job
        student = instance.student
        recruiter = job.recruiter

        try:
            # --- Email to Student ---
            subject = "Job Application Submitted"
            message = (
                f"Hi {student.user.first_name},\n\n"
                f"You have successfully applied for the job '{job.title}' at {recruiter.company}. Best of luck!"
            )
            from_email = settings.EMAIL_HOST_USER
            recipient_list = [student.user.email]

            send_mail(subject, message, from_email, recipient_list)

            # --- Email to Recruiter ---
            subject = "New Job Application"
            message = (
                f"Hi {recruiter.user.first_name},\n\n"
                f"You have received a new application for the job '{job.title}' from "
                f"{student.user.first_name} {student.user.last_name}. You can review it in your dashboard."
            )
            recipient_list = [recruiter.user.email]

            send_mail(subject, message, from_email, recipient_list)

            print("Job application confirmation emails sent!")

        except Exception as e:
            print(f"Failed to send job application emails: {e}")

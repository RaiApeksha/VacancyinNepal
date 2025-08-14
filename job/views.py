from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.models import User
from .models import Student, Recruiter, Job, Application
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.views.decorators.csrf import csrf_exempt
from django.db.models import Q
from .forms import UserUpdateForm, StudentUpdateForm, RecruiterUpdateForm
from django.core.mail import send_mail
from django.conf import settings
from django.contrib.admin.views.decorators import staff_member_required
from django.utils import timezone
import traceback
from django.contrib.auth.decorators import user_passes_test
from django.core.mail import send_mail, BadHeaderError, EmailMessage
from django.http import HttpResponse
from django.template.loader import render_to_string
import logging
from django.shortcuts import redirect
logger = logging.getLogger(__name__)
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.urls import reverse


def superuser_required(user):
    return user.is_superuser

@staff_member_required
def admin_home(request):
    total_students = Student.objects.count()
    total_recruiters = Recruiter.objects.count()
    total_jobs = Job.objects.count()
    total_applications = Application.objects.count()
    pending_recruiters = Recruiter.objects.filter(status='Pending')

    context = {
        'total_students': total_students,
        'total_recruiters': total_recruiters,
        'total_jobs': total_jobs,
        'total_applications': total_applications,
        'pending_recruiters': pending_recruiters,
    }
    return render(request, 'admin_home.html', context)

@staff_member_required
def update_recruiter_status(request, recruiter_id, action):
    recruiter = get_object_or_404(Recruiter, id=recruiter_id)

    if action == "approve":
        recruiter.status = "Approved"
        recruiter.save()

        try:
            # Build an absolute URL for the recruiter login page
            login_url = request.build_absolute_uri(reverse("recruiter_login"))

            html_message = render_to_string(
                "emails/recruiter_approved.html",
                {
                    "first_name": recruiter.user.first_name,
                    "login_url": login_url,
                },
            )
            email = EmailMessage(
                "Your Recruiter Account is Approved!",
                html_message,
                settings.EMAIL_HOST_USER,
                [recruiter.user.email],
            )
            email.content_subtype = "html"
            email.send()
        except Exception as mail_error:
            logger.error("Recruiter approval email failed: %s", mail_error)

        messages.success(request, f"{recruiter.user.username} approved and notified.")

    elif action == "reject":
        recruiter.status = "Rejected"
        recruiter.save()
        messages.warning(request, f"{recruiter.user.username} rejected.")

    return redirect("admin_home")

def admin_logout(request):
    logout(request)
    return redirect('admin_login')

def index(request):
    jobs = Job.objects.all().order_by('-created')[:5]
    return render(request, 'index.html', {'jobs': jobs})

def admin_login(request):
    if request.method == "POST":
        uname = request.POST.get("uname")
        pwd = request.POST.get("pwd")
        user = authenticate(username=uname, password=pwd)
        if user is not None and user.is_superuser:
            login(request, user)
            return redirect("admin_home")
        else:
            messages.error(request, "Invalid admin credentials or not a superuser.")
    return render(request, "admin_login.html")

def recruiter_login(request):
    if request.method == "POST":
        email = request.POST.get("uname")
        pwd   = request.POST.get("pwd")
        user  = authenticate(username=email, password=pwd)

        if user is not None:
            try:
                recruiter = Recruiter.objects.get(user=user)
                if recruiter.status.lower() == "approved":
                    login(request, user)
                    return redirect("post_job")
                else:
                    messages.warning(request,
                                     "Your account is not yet approved by admin.")
            except Recruiter.DoesNotExist:
                messages.error(request, "Recruiter profile not found.")
        else:
            messages.error(request, "Invalid username or password.")

    return render(request, "recruiter_login.html", {"no_footer": True})




def user_signup(request):
    if request.method == "POST":
        first_name = request.POST.get("fname").strip()
        last_name  = request.POST.get("lname").strip()
        email      = request.POST.get("email").strip().lower()
        password   = request.POST.get("pwd")
        confirm    = request.POST.get("cpwd")
        contact    = request.POST.get("contact")
        gender     = request.POST.get("gender")
        role       = request.POST.get("role")  # "student" or "recruiter"
        photo      = request.FILES.get("image")

        # Validate the email and password
        if User.objects.filter(username=email).exists():
            messages.error(request, "Email is already registered.")
            return render(request, "user_signup.html")
        if password != confirm:
            messages.error(request, "Passwords do not match.")
            return render(request, "user_signup.html")

        # Create the user
        user = User.objects.create_user(
            username=email,
            password=password,
            first_name=first_name,
            last_name=last_name,
            email=email,
        )

        if role.lower() == "student":
            # Create the student profile
            Student.objects.create(
                user=user,
                mobile=contact,
                gender=gender,
                image=photo,
                type="student",
            )
            # Send welcome email to student
            message = render_to_string(
                "emails/student_welcome.html",
                {"first_name": first_name, "last_name": last_name},
            )
            email_message = EmailMessage(
                "Welcome to Vacancy in Nepal",
                message,
                settings.EMAIL_HOST_USER,
                [email],
            )
            email_message.content_subtype = "html"
            email_message.send()

            # Notify admin of new student signup
            admin_message = render_to_string(
                "emails/student_admin_notify.html",
                {"first_name": first_name, "last_name": last_name, "email": email},
            )
            admin_email = EmailMessage(
                "New Student Signup Alert",
                admin_message,
                settings.EMAIL_HOST_USER,
                ["infovin6@gmail.com"],
            )
            admin_email.content_subtype = "html"
            admin_email.send()

            messages.success(request, "Student account created successfully.")
            return redirect("student_login")

        elif role.lower() == "recruiter":
            # Create the recruiter profile (pending approval)
            Recruiter.objects.create(
                user=user,
                mobile=contact,
                gender=gender,
                image=photo,
                status="Pending",
            )
            # Send welcome email to recruiter (pending approval)
            message = render_to_string(
                "emails/recruiter_welcome.html",
                {"first_name": first_name, "last_name": last_name},
            )
            email_message = EmailMessage(
                "Welcome to Vacancy in Nepal",
                message,
                settings.EMAIL_HOST_USER,
                [email],
            )
            email_message.content_subtype = "html"
            email_message.send()

            # Notify admin of new recruiter signup
            admin_message = render_to_string(
                "emails/recruiter_admin_notify.html",
                {"first_name": first_name, "last_name": last_name, "email": email},
            )
            admin_email = EmailMessage(
                "New Recruiter Signup Alert",
                admin_message,
                settings.EMAIL_HOST_USER,
                ["infovin6@gmail.com"],
            )
            admin_email.content_subtype = "html"
            admin_email.send()

            messages.success(
                request,
                "Recruiter account created successfully. An admin will approve your account soon.",
            )
            return redirect("recruiter_dashboard")

    # GET request
    return render(request, "user_signup.html")

@login_required
def recruiter_dashboard(request):
    try:
        recruiter = Recruiter.objects.get(user=request.user)
    except Recruiter.DoesNotExist:
        messages.warning(request, "You are not authorized to view the recruiter dashboard.")
        return redirect('user_home')

    jobs = Job.objects.filter(recruiter=recruiter).order_by('-created')
    return render(request, 'recruiter_dashboard.html', {'jobs': jobs})


@login_required
def post_job(request):
    error = ""

    try:
        recruiter = Recruiter.objects.get(user=request.user)
    except Recruiter.DoesNotExist:
        messages.error(request, "You must be a recruiter to post a job.")
        return redirect("recruiter_login")

    if recruiter.status != "Approved":
        messages.warning(request, "Your account is still pending approval by the admin.")
        return redirect("recruiter_dashboard")

    if request.method == "POST":
        t = request.POST.get('title')
        d = request.POST.get('desc')
        c = request.POST.get('category')
        l = request.POST.get('location')
        e = request.POST.get('exp')
        s = request.POST.get('salary')

        try:
            Job.objects.create(
                recruiter=recruiter,
                title=t,
                description=d,
                category=c,
                location=l,
                experience=e,
                salary=s,
                created=timezone.now()
            )
            error = "no"
        except Exception as e:
            print("Error posting job:", e)
            error = "yes"

    return render(request, 'post_job.html', {'error': error})


def job_list(request):
    query = request.GET.get('q')
    location = request.GET.get('location')
    category = request.GET.get('category')

    jobs = Job.objects.all()

    if query:
        jobs = jobs.filter(Q(title__icontains=query) | Q(description__icontains=query))

    if location:
        jobs = jobs.filter(location__icontains=location)

    if category:
        jobs = jobs.filter(category__icontains=category)

    applied_job_ids = []
    if request.user.is_authenticated and hasattr(request.user, 'student'):
        student = Student.objects.get(user=request.user)
        applied_job_ids = list(Application.objects.filter(student=student).values_list('job_id', flat=True))

    return render(request, 'job_list.html', {
        'jobs': jobs,
        'applied_job_ids': applied_job_ids,
    })


@login_required
def job_detail(request, job_id):
    job = get_object_or_404(Job, id=job_id)

    try:
        Student.objects.get(user=request.user)
        is_student = True
    except Student.DoesNotExist:
        is_student = False

    return render(request, "job_detail.html", {
        "job": job,
        "is_student": is_student,
    })




@login_required
def apply_job(request, job_id):
    job = get_object_or_404(Job, id=job_id)

    # Get the student's profile
    try:
        student = Student.objects.get(user=request.user)
    except Student.DoesNotExist:
        messages.warning(request, "Please log in as a student to apply.")
        return redirect("student_login")

    # Get the student's profile
    student = request.user.student

    # Prevent duplicate applications for the same job
    if Application.objects.filter(job=job, student=student).exists():
        messages.warning(request, "You have already applied for this job.")
        return redirect("job_detail", job_id=job.id)

    # Process form submission
    if request.method == "POST":
        # Fetch the uploaded resume
        resume = request.FILES.get("resume")
        if not resume:
            messages.error(request, "Please upload your resume to apply for the job.")
            return redirect("job_detail", job_id=job.id)

        # Create the application entry
        application = Application.objects.create(
            job=job,
            student=student,
            resume=resume
        )

        # Notify the recruiter about the new application
        recruiter = job.recruiter
        send_mail(
            subject=f"New application for {job.title}",
            message=(
                f"Dear {recruiter.user.first_name},\n\n"
                f"{student.user.get_full_name()} has applied for your job posting:\n"
                f"{job.title}.\n\n"
                f"Student Email: {student.user.email}\n\n"
                f"Regards,\nVacancy in Nepal Team"
            ),
            from_email=settings.EMAIL_HOST_USER,
            recipient_list=[recruiter.user.email],
            fail_silently=False,
        )

        # Notify the student about their successful application
        send_mail(
            subject=f"Application submitted for {job.title}",
            message=(
                f"Dear {student.user.first_name},\n\n"
                f"Thank you for applying for '{job.title}'. Your application has been submitted successfully.\n"
                f"We will inform you once the recruiter reviews your application.\n\n"
                f"Regards,\nVacancy in Nepal Team"
            ),
            from_email=settings.EMAIL_HOST_USER,
            recipient_list=[student.user.email],
            fail_silently=False,
        )

        # Set a success message to display on the next page
        messages.success(request, "Your application was submitted successfully!")

        # Redirect wherever you want to show the success message
        # You can redirect back to the job detail page or to the user's home page
        return redirect("job_detail", job_id=job.id)

    # If it's not a POST request, redirect to the job detail page
    return redirect("job_detail", job_id=job.id)

@login_required
def update_student_profile(request):
    student = Student.objects.get(user=request.user)
    if request.method == 'POST':
        u_form = UserUpdateForm(request.POST, instance=request.user)
        s_form = StudentUpdateForm(request.POST, request.FILES, instance=student)
        if u_form.is_valid() and s_form.is_valid():
            u_form.save()
            s_form.save()
            messages.success(request, 'Profile updated successfully!')
            return redirect('user_home')
    else:
        u_form = UserUpdateForm(instance=request.user)
        s_form = StudentUpdateForm(instance=student)
    return render(request, 'update_student_profile.html', {'u_form': u_form, 's_form': s_form})


@login_required
def update_recruiter_profile(request):
    recruiter = Recruiter.objects.get(user=request.user)
    if request.method == 'POST':
        u_form = UserUpdateForm(request.POST, instance=request.user)
        r_form = RecruiterUpdateForm(request.POST, request.FILES, instance=recruiter)
        if u_form.is_valid() and r_form.is_valid():
            u_form.save()
            r_form.save()
            messages.success(request, 'Profile updated successfully!')
            return redirect('user_home')
    else:
        u_form = UserUpdateForm(instance=request.user)
        r_form = RecruiterUpdateForm(instance=recruiter)
    return render(request, 'update_recruiter_profile.html', {'u_form': u_form, 'r_form': r_form})


def custom_logout(request):
    logout(request)
    return redirect('index')


def student_login(request):
    if request.method == "POST":
        u = request.POST.get('uname')
        p = request.POST.get('pwd')

        # Authenticate the user
        user = authenticate(username=u, password=p)

        if user is not None:
            login(request, user)  # Log the user in

            # After login, check if there's a "next" parameter in the URL
            next_url = request.GET.get('next')  # This gets the URL the user originally wanted to visit

            # If no "next" parameter, redirect to the job list page (default destination)
            if next_url:
                return redirect(next_url)
            else:
                return redirect('job_list')  # Redirect to job list page if no "next" parameter

        else:
            messages.error(request, "Invalid username or password.")

    return render(request, 'user_login.html', {'no_footer': True})



@login_required
def user_home(request):
    user = request.user
    context = {
        'user': user
    }

    if hasattr(user, 'student'):
        return render(request, 'student_dashboard.html', context)
    elif hasattr(user, 'recruiter'):
        return render(request, 'recruiter_dashboard.html', context)
    else:
        return HttpResponse("Invalid user type.")


@receiver(post_save, sender=Recruiter)
def send_recruiter_approval_email(sender, instance, created, **kwargs):
    if not created:
        # Check if status changed from something else to "Approved"
        try:
            previous = Recruiter.objects.get(pk=instance.pk)
            prev_status = previous.status
        except Recruiter.DoesNotExist:
            prev_status = None

        if prev_status != "Approved" and instance.status == "Approved":
            # Build login URL (may need request object or set DOMAIN in settings)
            from django.contrib.sites.models import Site
            domain = Site.objects.get_current().domain
            login_url = f"http://{domain}{reverse('recruiter_login')}"

            html_message = render_to_string(
                "emails/recruiter_approved.html",
                {
                    "first_name": instance.user.first_name,
                    "login_url": login_url,
                },
            )
            plain_message = (
                f"Dear {instance.user.first_name},\n\n"
                "Your recruiter account has been approved!\n"
                f"You can now log in at {login_url}\n\n"
                "Regards,\nAdmin Team"
            )
            send_mail(
                subject="Your recruiter account has been approved!",
                message=plain_message,
                from_email=settings.EMAIL_HOST_USER,
                recipient_list=[instance.user.email],
                html_message=html_message,
                fail_silently=False,
            )
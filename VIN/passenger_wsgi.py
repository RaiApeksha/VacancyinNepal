import sys, os

# Correct path to your Django project
sys.path.insert(0, "/home/vacancyi/public_html")
sys.path.insert(0, "/home/vacancyi/public_html/VacancyinNepal")

# Activate virtual environment
activate_env = '/home/vacancyi/virtualenv/VIN/VacancyinNepal/3.10/bin/activate_this.py'
with open(activate_env) as f:
    exec(f.read(), {'__file__': activate_env})

# Set environment variable
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "VacancyinNepal.settings")

from django.core.wsgi import get_wsgi_application
application = get_wsgi_application()

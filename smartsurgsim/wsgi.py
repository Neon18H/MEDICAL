"""WSGI config for SmartSurgSim."""
import os

from django.core.wsgi import get_wsgi_application

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "smartsurgsim.settings")

application = get_wsgi_application()

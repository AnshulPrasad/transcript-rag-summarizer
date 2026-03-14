import os
import sys
from pathlib import Path

# Ensure app/ folder is on path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent / 'app'))

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'guru_project.settings')

from django.core.wsgi import get_wsgi_application
application = get_wsgi_application()
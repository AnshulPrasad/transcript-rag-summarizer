FROM python:3.10-slim

ENV DEBIAN_FRONTEND=noninteractive \
    PYTHONUNBUFFERED=1

RUN apt-get update && apt-get install -y \
    python3-pip \
    build-essential \
    git \
    curl \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY requirements.txt /tmp/requirements.txt
RUN python3 -m pip install --upgrade pip setuptools wheel \
 && python3 -m pip install --no-cache-dir -r /tmp/requirements.txt \
 && python3 -c "import django; print('DJANGO_VER=', django.__version__)" || true

RUN useradd -m -u 1000 appuser \
 && mkdir -p /app \
 && chown -R appuser:appuser /app

COPY --chown=appuser:appuser . /app

USER appuser
ENV HOME=/home/appuser

WORKDIR /app

# HF Spaces requires port 7860
EXPOSE 7860

CMD ["sh", "-c", "\
  python manage.py migrate --run-syncdb && \
  python manage.py shell -c \"\
import os; \
from django.contrib.auth import get_user_model; \
User = get_user_model(); \
email = os.environ.get('ADMIN_EMAIL','admin@example.com'); \
password = os.environ.get('ADMIN_PASSWORD','changeme123'); \
User.objects.filter(username='admin').exists() or User.objects.create_superuser('admin', email, password); \
print('Superuser ready') \
\" && \
  gunicorn guru_project.wsgi:application --bind 0.0.0.0:7860 --workers 2 --timeout 120 \
"]
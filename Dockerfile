FROM python:3.10-slim

ENV DEBIAN_FRONTEND=noninteractive \
    PYTHONUNBUFFERED=1

RUN apt-get update && apt-get install -y \
    curl \
    libgomp1 \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY requirements.txt /tmp/requirements.txt
RUN pip install --upgrade pip \
 && pip install --no-cache-dir -r /tmp/requirements.txt

RUN useradd -m -u 1000 appuser \
 && chown -R appuser:appuser /app

COPY --chown=appuser:appuser . /app

USER appuser
ENV HOME=/home/appuser

EXPOSE 7860

CMD ["sh", "-c", "\
  PYTHONPATH=/app/app python manage.py migrate --run-syncdb 2>&1 && \
  PYTHONPATH=/app/app python manage.py shell -c \"\
import os; \
from django.contrib.auth import get_user_model; \
User = get_user_model(); \
email = os.environ.get('ADMIN_EMAIL', 'admin@example.com'); \
password = os.environ.get('ADMIN_PASSWORD', 'changeme123'); \
User.objects.filter(username='admin').exists() or User.objects.create_superuser('admin', email, password); \
print('Superuser ready'); \
\" 2>&1 && \
  PYTHONPATH=/app/app gunicorn guru_project.wsgi:application \
    --bind 0.0.0.0:7860 \
    --workers 2 \
    --timeout 120 \
    --log-level info \
"]
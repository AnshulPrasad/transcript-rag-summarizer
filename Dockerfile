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

CMD ["gunicorn", "guru_project.wsgi:application", "--bind", "0.0.0.0:7860", "--workers", "2", "--timeout", "120"]
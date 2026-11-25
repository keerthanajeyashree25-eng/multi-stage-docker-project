FROM python:3.12-alpine AS builder

ENV PIP_DISABLE_PIP_VERSION_CHECK=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /build

COPY requirements.txt .
RUN python -m pip install --no-cache-dir --prefix=/install -r requirements.txt

FROM python:3.12-alpine AS production

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PORT=5000 \
    PROMETHEUS_MULTIPROC_DIR=/tmp/prometheus_multiproc

WORKDIR /app

RUN apk add --no-cache libpq \
    && addgroup -S -g 10001 app \
    && adduser -S -H -u 10001 -G app -s /sbin/nologin appuser \
    && mkdir -p /tmp/prometheus_multiproc \
    && chown appuser:app /tmp/prometheus_multiproc

COPY --from=builder /install /usr/local
COPY --chown=appuser:app app/ ./app/
COPY --chown=appuser:app templates/ ./templates/
COPY --chown=appuser:app static/ ./static/
COPY --chown=appuser:app app.py .
COPY --chown=appuser:app gunicorn.conf.py .

USER appuser

EXPOSE 5000

HEALTHCHECK --interval=30s --timeout=3s --start-period=10s --retries=3 \
    CMD python -c "import os; from urllib.request import urlopen; urlopen('http://127.0.0.1:' + os.environ.get('PORT', '5000') + '/health', timeout=2)"

CMD ["sh", "-c", "exec gunicorn --config gunicorn.conf.py --bind=0.0.0.0:${PORT:-5000} --workers=2 --access-logfile=- --error-logfile=- app:app"]
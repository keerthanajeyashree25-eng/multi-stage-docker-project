FROM python:3.12-slim-bookworm AS builder

ENV PIP_DISABLE_PIP_VERSION_CHECK=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /build
COPY requirements.txt .
RUN python -m pip install --no-cache-dir --prefix=/install -r requirements.txt

FROM python:3.12-slim-bookworm AS runtime

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /app

RUN groupadd --system --gid 10001 app \
    && useradd --system --uid 10001 --gid app --home-dir /home/app --create-home \
        --shell /usr/sbin/nologin app

COPY --from=builder /install /usr/local
COPY --chown=app:app app ./app
COPY --chown=app:app templates ./templates
COPY --chown=app:app static ./static
COPY --chown=app:app app.py .

USER 10001:10001
EXPOSE 5000

HEALTHCHECK --interval=30s --timeout=3s --start-period=10s --retries=3 \
    CMD python -c "from urllib.request import urlopen; urlopen('http://127.0.0.1:5000/health', timeout=2)"

CMD ["gunicorn", "--bind=0.0.0.0:5000", "--workers=2", "--access-logfile=-", "--error-logfile=-", "app:app"]
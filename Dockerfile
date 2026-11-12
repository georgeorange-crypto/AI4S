FROM python:3.12-slim@sha256:5e2bdb1b0d542d5039cffb8181c65930093949194a65c365dfb1b0fe13a4fa5b
ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1
WORKDIR /app
COPY requirements.lock /tmp/requirements.lock
RUN pip install --no-cache-dir --requirement /tmp/requirements.lock
COPY ai4s /app/ai4s
COPY migrations /app/migrations
COPY alembic.ini pyproject.toml /app/
RUN useradd --create-home --uid 10001 ai4s && chown -R ai4s:ai4s /app
USER 10001:10001
EXPOSE 8000
CMD ["sh", "-c", "alembic upgrade head && uvicorn ai4s.api:app --host 0.0.0.0 --port 8000"]

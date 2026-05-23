FROM python:3.11-slim-bookworm

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1

WORKDIR /srv

COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

COPY app ./app
COPY alembic ./alembic
COPY alembic.ini pyproject.toml ./
COPY scripts ./scripts

# Railway/most PaaS inject $PORT; default to 8000 locally.
EXPOSE 8000
RUN ls -la /srv
RUN ls -la /srv/scripts
CMD ["bash", "/srv/scripts/start.sh"]

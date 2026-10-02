FROM python:3.12-slim
COPY --from=ghcr.io/astral-sh/uv:latest /uv /usr/local/bin/uv
ENV PYTHONUNBUFFERED=1 UV_LINK_MODE=copy
WORKDIR /srv
COPY pyproject.toml README.md ./
RUN uv sync --no-dev --no-install-project
COPY app ./app
COPY evals ./evals
ENV NCI_DATA_DIR=/srv/data
EXPOSE 8030
HEALTHCHECK --interval=15s --timeout=3s CMD python -c "import urllib.request as u; u.urlopen('http://127.0.0.1:8030/health', timeout=2)"
CMD ["uv", "run", "--no-dev", "uvicorn", "app.main:create_app", "--factory", "--host", "0.0.0.0", "--port", "8030"]

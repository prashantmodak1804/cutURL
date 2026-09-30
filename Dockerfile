FROM python:3.12.14-slim-bookworm AS builder
WORKDIR /build
RUN python -m venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"
COPY app/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

FROM python:3.12.14-slim-bookworm
RUN useradd --system --create-home --uid 10001 appuser
COPY --from=builder opt/venv /opt/venv
WORKDIR /app
COPY app/ .
ENV PATH="/opt/venv/bin:$PATH" PYTHONUNBUFFERED=1
USER appuser
EXPOSE 8000
HEALTHCHECK --interval=30s --timeout=3s --start-period=30s --retries=3 \
	CMD python -c "import urllib.requests; urllib.request.urlopen('https://127.0.0.1:8000/healthz', timeout=2)"
CMD ["gunicorn", "--bind", "0.0.0.0:8000", "--workers", "2", "--forwarded-allow-ips", "*", "app:app"]

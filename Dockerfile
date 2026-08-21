# ── Base image ────────────────────────────────────────────
# python:3.13-slim = official Python, stripped of extras
# Smaller image = faster deploys, smaller attack surface
FROM python:3.13-slim

# ── System dependencies ───────────────────────────────────
# gcc needed to compile some Python packages (psycopg2)
# rm -rf cleans apt cache — keeps image size down
RUN apt-get update && apt-get install -y \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# ── Working directory ─────────────────────────────────────
# All subsequent commands run from /app inside the container
WORKDIR /app

# ── Install dependencies BEFORE copying code ─────────────
# WHY: Docker caches each layer. If requirements.txt
# hasn't changed, this layer is reused — pip install
# only runs again when dependencies actually change.
# If we copied code first, any code change would
# invalidate this layer and reinstall everything.
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# ── Copy application code ─────────────────────────────────
# Happens after pip install so code changes don't
# trigger a full reinstall
COPY . .



# ── Non-root user ─────────────────────────────────────────
# Running as root inside a container is a security risk
# If the container is compromised, attacker gets root
RUN useradd --create-home appuser \
    && chown -R appuser:appuser /app
USER appuser

# ── Port ─────────────────────────────────────────────────
# Documents what port the app listens on
# Does not actually publish it — that is docker-compose's job
EXPOSE 5000

# ── Environment ───────────────────────────────────────────
ENV FLASK_APP=app.py
ENV PYTHONUNBUFFERED=1

# ── Start command ─────────────────────────────────────────
# Gunicorn = production WSGI server
# Flask's built-in server is single-threaded — not for production
# workers=2 = handle 2 concurrent requests (adjust per server RAM)
CMD ["gunicorn", "--bind", "0.0.0.0:5000", "--workers", "2", "--timeout", "120", "app:app"]
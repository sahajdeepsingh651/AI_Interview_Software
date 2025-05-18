# =================== Stage 1: Build ===================
FROM python:3.10-slim AS builder

WORKDIR /app

RUN apt-get update && \
    apt-get install -y --no-install-recommends gcc libpq-dev ffmpeg && \
    rm -rf /var/lib/apt/lists/*

COPY requirements.txt .

RUN pip install --no-cache-dir -r requirements.txt

# =================== Stage 2: Final Image ===================
FROM python:3.10-slim

WORKDIR /app

RUN apt-get update && \
    apt-get install -y --no-install-recommends libpq5 ffmpeg && \
    rm -rf /var/lib/apt/lists/*

COPY --from=builder /usr/local/lib/python3.10/site-packages /usr/local/lib/python3.10/site-packages

COPY . .

ENV FLASK_ENV=production
ENV PYTHONUNBUFFERED=1

# Expose port 8080 (Cloud Run default)
EXPOSE 8080

# Use shell form CMD to expand $PORT environment variable
CMD ["sh", "-c", "gunicorn --bind 0.0.0.0:$PORT app:app"]
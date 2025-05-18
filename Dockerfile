FROM python:3.10-slim

WORKDIR /app

RUN apt-get update && \
    apt-get install -y --no-install-recommends gcc libpq-dev libpq5 ffmpeg && \
    rm -rf /var/lib/apt/lists/*

COPY requirements.txt .

RUN pip install --no-cache-dir -r requirements.txt

COPY . .

ENV FLASK_ENV=production
ENV PYTHONUNBUFFERED=1

EXPOSE 8080

CMD ["sh", "-c", "gunicorn --bind 0.0.0.0:${PORT:-8080} app:app"]


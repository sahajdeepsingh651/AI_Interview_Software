# =================== Stage 1: Build ===================
FROM python:3.10-slim AS builder

WORKDIR /app

RUN apt-get update && \
    apt-get install -y gcc libpq-dev ffmpeg && \
    rm -rf /var/lib/apt/lists/*

COPY requirements.txt .

RUN pip install --no-cache-dir -r requirements.txt

# =================== Stage 2: Final Image ===================
FROM python:3.10-slim

WORKDIR /app

# Install runtime dependencies (ffmpeg, libpq) - needed for your app runtime
RUN apt-get update && \
    apt-get install -y libpq5 ffmpeg && \
    rm -rf /var/lib/apt/lists/*

# Copy python packages from builder stage
COPY --from=builder /usr/local/lib/python3.10/site-packages /usr/local/lib/python3.10/site-packages
COPY --from=builder /usr/local/bin /usr/local/bin

# Copy app source code
COPY . .

ENV FLASK_ENV=production
ENV PYTHONUNBUFFERED=1

EXPOSE 8000

CMD ["gunicorn", "--bind", "0.0.0.0:8000", "app:app"]

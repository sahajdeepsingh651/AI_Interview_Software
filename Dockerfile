# =================== Stage 1: Build ===================
FROM python:3.10-slim AS builder

# Set working directory
WORKDIR /app

# Install necessary system dependencies (only for build stage)
RUN apt-get update && \
    apt-get install -y gcc libpq-dev ffmpeg && \
    rm -rf /var/lib/apt/lists/*

# Copy and install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# =================== Stage 2: Final Image ===================
FROM python:3.10-slim AS final

# Set working directory
WORKDIR /app

# Copy installed dependencies from the builder stage
COPY --from=builder /usr/local/lib/python3.10/site-packages /usr/local/lib/python3.10/site-packages
COPY --from=builder /usr/local/bin /usr/local/bin

# Copy application code
COPY . .

# Set environment variables for production
ENV FLASK_ENV=production
ENV PYTHONUNBUFFERED=1

# Set the entrypoint for the application using Gunicorn
CMD ["gunicorn", "--bind", "0.0.0.0:8000", "app:app"]

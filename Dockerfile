# Use official Python image.
FROM python:3.9-slim

# Set working directory.
WORKDIR /app

# Copy project files to /app.
COPY . .

# Install dependencies.
RUN pip install --no-cache-dir -r requirements.txt

# Expose port 8080 (Google Cloud uses this by default).
EXPOSE 8080

# Run Flask with Gunicorn for production.
CMD ["gunicorn", "-b", "0.0.0.0:8080", "main:app"]

# Use the official Python image as a lightweight base
FROM python:3.12-slim

# Set a working directory
WORKDIR /app

# Install dependencies
COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

# Copy application source
COPY . /app

# Expose the app port
EXPOSE 8000

# Set production environment variables
ENV FLASK_ENV=production
ENV PYTHONUNBUFFERED=1

# Start the app using Gunicorn
CMD ["gunicorn", "--bind", "0.0.0.0:8000", "dashboard:app"]

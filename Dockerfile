FROM python:3.12-slim

# Create app directory
WORKDIR /app

# Install deps
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Create directory for SQLite data
RUN mkdir -p /data

# Copy app code
COPY . .

# Environment for Flask
ENV FLASK_APP=app.py
ENV FLASK_RUN_HOST=0.0.0.0
ENV FLASK_RUN_PORT=5000
ENV PYTHONUNBUFFERED=1

EXPOSE 5000

# Default command: simple Flask dev server (fine for home use)
CMD ["flask", "run"]

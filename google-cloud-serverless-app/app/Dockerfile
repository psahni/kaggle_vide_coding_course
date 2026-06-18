# Use the official lightweight Python image.
# https://hub.docker.com/_/python
FROM python:3.11-slim

# Allow statements and log messages to immediately appear in the Knative logs
ENV PYTHONUNBUFFERED True

# Copy local code to the container image.
ENV APP_HOME /app
WORKDIR $APP_HOME

# Copy requirements first for better layer caching
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY src ./src

# Set Python path to include src directory
ENV PYTHONPATH=/app/src:$PYTHONPATH

# Run the web service on container startup.
# We use the gunicorn webserver, with one worker process and 8 threads.
# Timeout is set to 0 to disable worker timeouts, letting Cloud Run handle scaling.
CMD exec gunicorn --bind :$PORT --workers 1 --threads 8 --timeout 0 --chdir /app/src app:app

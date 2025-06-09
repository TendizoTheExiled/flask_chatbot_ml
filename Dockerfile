# Start with a base Python image. python:3.9-slim-buster is light and stable.
# You can use a higher version like 3.10-slim-buster or 3.11-slim-buster
# based on your Python version locally and requirements.
FROM python:3.9-slim-buster

# Set the working directory inside the container. All your app files will go here.
WORKDIR /app

# Copy the requirements.txt file into the container
# This step is done first for Docker caching efficiency
COPY requirements.txt .

# Install all Python dependencies listed in requirements.txt
# --no-cache-dir saves space by not storing pip's cache.
RUN pip install --no-cache-dir -r requirements.txt

# Copy all the rest of your project files into the container's /app directory.
# This includes app.py, maize_qa.csv, and the 'model/' directory.
COPY . .

# Expose the port where your Gunicorn server will listen.
# We'll configure Gunicorn to listen on port 8000. Railway will manage exposing it publicly.
EXPOSE 8000

# This is the command that runs when your container starts.
# It tells Gunicorn to start your Flask application.
# 'app:app' means: find the 'app.py' file, and inside it, find the 'app' Flask instance.
# '--bind 0.0.0.0:8000' tells Gunicorn to listen on port 8000 on all network interfaces.
CMD ["gunicorn", "--bind", "0.0.0.0:8000", "app:app"]

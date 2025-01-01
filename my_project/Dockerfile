# FROM python:3.8-slim

# # Set the working directory
# WORKDIR /app

# # Install system dependencies
# RUN apt-get update && apt-get install -y --no-install-recommends \
#     curl \
#     && rm -rf /var/lib/apt/lists/*

# # Install Python dependencies
# COPY requirements.txt .
# RUN pip install --no-cache-dir -r requirements.txt

# # Copy the application code
# COPY . .

# # # Set the entrypoint
# # CMD ["python", "your_script.py"]

FROM python:3.9-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy the project files to /app
COPY . /app

# Set PYTHONPATH to /app
ENV PYTHONPATH=/app
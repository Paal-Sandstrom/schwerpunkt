# Use the official Python image
FROM python:3.11-slim

# Set the working directory
WORKDIR /app

# Copy requirements and install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy the rest of the application code
COPY . .

# Expose the dynamic port required by Cloud Run (defaults to 8080)
ENV PORT 8080

# Initialize the database (if it doesn't exist)
RUN python db.py

# Run the web service on container startup using gunicorn
CMD exec gunicorn --bind 0.0.0.0:$PORT --workers 1 --threads 8 --timeout 0 app:app
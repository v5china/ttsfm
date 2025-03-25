# Use Python 3.13 slim image as base
FROM python:3.13-slim

# Set working directory to root
WORKDIR /

# Copy requirements first to leverage Docker cache
COPY requirements.txt .

# Install dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy the application files
COPY server.py .
COPY index.html .
COPY index_zh.html .
COPY script.js .
COPY styles.css .

# Expose port 7000
EXPOSE 7000

# Command to run the application with host set to 0.0.0.0
CMD ["python", "server.py", "--host", "0.0.0.0"] 
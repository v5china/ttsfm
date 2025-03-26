# Use Python 3.13 slim image as base
FROM python:3.13-slim

# Set working directory to root
WORKDIR /

# Copy requirements first to leverage Docker cache
COPY requirements.txt .

# Install dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy all application directories and files
COPY main.py .
COPY server/ server/
COPY proxy/ proxy/
COPY utils/ utils/
COPY static/ static/

# Expose port 7000
EXPOSE 7000

# Command to run the application with host set to 0.0.0.0
CMD ["python", "main.py", "--host", "0.0.0.0"] 
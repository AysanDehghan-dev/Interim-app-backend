FROM python:3.11-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements files
COPY requirements.txt requirements-test.txt ./

# Install production dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Install test dependencies (useful for development)
RUN pip install --no-cache-dir -r requirements-test.txt

# Verify Flask is installed
RUN python -c "import flask; print(f'Flask {flask.__version__} installed successfully')"

# Copy application code
COPY . .

# Expose port
EXPOSE 5000

# Run the application
CMD ["python", "app.py"]
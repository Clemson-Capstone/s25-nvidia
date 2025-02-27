FROM python:3.9-slim

WORKDIR /app

# Copy requirements first for better caching
COPY requirements.txt .

# Install dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Create directory for course data
RUN mkdir -p /app/course_data

# Copy application code
COPY . .

# Expose port
EXPOSE 8012

# Command to run the application
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8012"]
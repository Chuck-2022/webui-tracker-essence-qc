FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Copy requirements first (for better caching)
COPY requirements.txt .

# Install dependencies
RUN pip3 install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Expose port
EXPOSE 5000

# Set database path for Docker environment
ENV DATABASE_PATH=/app/db/essence.db

# Create non-root user
RUN useradd --create-home --shell /bin/bash appuser

# Ensure database directory exists and is writable by appuser
RUN mkdir -p /app/db && chown -R appuser:appuser /app/db && chmod -R 755 /app/db
RUN chown -R appuser:appuser /app && chmod -R 755 /app

USER appuser

# Run the application
CMD ["python", "/app/app.py"]

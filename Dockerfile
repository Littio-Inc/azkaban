FROM python:3.11-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    postgresql-client \
    && rm -rf /var/lib/apt/lists/*

# Install pipenv
RUN pip install pipenv==2023.7.4

# Copy Pipfile first
COPY Pipfile ./

# Install Python dependencies
# Generate lock if not exists, then install
RUN pipenv lock || true
RUN pipenv install --system

# Copy application code
COPY . .

# Expose port
EXPOSE 8000

# Run the application
CMD ["uvicorn", "handler:app", "--host", "0.0.0.0", "--port", "8000", "--reload"]


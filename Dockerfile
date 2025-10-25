# First create a base image
FROM python:3.12.11-slim-bookworm

#Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    UV_SYSTEM_PYTHON=1 \
    PATH="/root/.local/bin:$PATH"

# set the working directory
WORKDIR /app



# Install system dependencies
RUN apt-get update && \
    apt-get install -y --no-install-recommends curl gcc libpq-dev && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/*

# Install uv
RUN curl -LsSf https://astral.sh/uv/install.sh | sh


# Copy requirements file
COPY requirements.txt .

# Install Python dependencies using uv to system Python
RUN uv pip install --system --no-cache-dir -r requirements.txt

# Copy application code
COPY . .


# Copy and give permission to entrypoint
COPY entrypoint.sh /app/entrypoint.sh
RUN chmod +x /app/entrypoint.sh

# Set entrypoint
ENTRYPOINT ["/app/entrypoint.sh"]



# Expose port
EXPOSE 8000

# Run the application
CMD ["gunicorn", "copiqat.wsgi:application", "--bind", "0.0.0.0:8000", "--workers=4"]
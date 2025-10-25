#!/bin/bash

# Exit on any error
set -e

# Apply database migrations
echo "Applying database migrations..."
python manage.py migrate

# Collect static files (optional)
echo "Collecting static files..."
python manage.py collectstatic --noinput

# Run the server
echo "Starting server..."
exec "$@"

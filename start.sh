#!/bin/bash
# Render.com start script for production

echo "Starting Orion Octave Cubes web application..."
echo "Environment: $FLASK_ENV"

# Use gunicorn for production
exec gunicorn \
    --bind 0.0.0.0:$PORT \
    --workers 2 \
    --threads 4 \
    --timeout 120 \
    --access-logfile - \
    --error-logfile - \
    --log-level info \
    app:app

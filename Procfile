web: gunicorn --bind 0.0.0.0:$PORT \
  --workers ${WEB_CONCURRENCY:-2} \
  --threads 4 \
  --timeout 120 \
  --access-logfile - \
  --error-logfile - \
  --log-level info \
  app:app

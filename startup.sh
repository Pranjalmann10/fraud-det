#!/bin/bash

# Initialize the database (if needed)
python init_db.py

# Determine which component to start based on the APP_TYPE environment variable
if [ "$APP_TYPE" = "api" ]; then
    # Start the API server
    cd src/api
    gunicorn main:app --bind 0.0.0.0:${PORT:-8001} --workers 4 --worker-class uvicorn.workers.UvicornWorker --timeout 120
elif [ "$APP_TYPE" = "dashboard" ]; then
    # Start the dashboard
    cd src/dashboard
    gunicorn app:server --bind 0.0.0.0:${PORT:-8050} --workers 2 --timeout 120
else
    echo "Invalid APP_TYPE: must be 'api' or 'dashboard'"
    exit 1
fi

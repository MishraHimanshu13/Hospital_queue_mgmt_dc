#!/bin/bash

# Hospital Queue Management System - Node 3 startup script

# Check if PostgreSQL is running
pg_isready
if [ $? -ne 0 ]; then
    echo "PostgreSQL is not running. Please start PostgreSQL first."
    exit 1
fi

# Activate virtual environment
source venv/bin/activate

# Start the application as Node 3
export NODE_ID="node_3"
export FLASK_APP=app.py
export FLASK_ENV=development
export SECRET_KEY="change_this_in_production"
export DATABASE_URL="postgresql://postgres:postgres@localhost/hospital_queue"

flask run --host=0.0.0.0 --port=5002


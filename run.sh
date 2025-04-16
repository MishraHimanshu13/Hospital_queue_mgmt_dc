#!/bin/bash

# Hospital Queue Management System startup script

# Check if PostgreSQL is running
pg_isready
if [ $? -ne 0 ]; then
    echo "PostgreSQL is not running. Please start PostgreSQL first."
    exit 1
fi

# Create database if it doesn't exist
psql -U postgres -tc "SELECT 1 FROM pg_database WHERE datname = 'hospital_queue'" | grep -q 1 || psql -U postgres -c "CREATE DATABASE hospital_queue"

# Apply schema
psql -U postgres -d hospital_queue -f schema.sql

# Set up Python virtual environment
if [ ! -d "venv" ]; then
    echo "Creating virtual environment..."
    python3 -m venv venv
fi

# Activate virtual environment
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Start the application
# For a single node
export NODE_ID="node_1"
export FLASK_APP=app.py
export FLASK_ENV=development
export SECRET_KEY="change_this_in_production"
export DATABASE_URL="postgresql://postgres:postgres@localhost/hospital_queue"

flask run --host=0.0.0.0 --port=5000


#!/bin/bash
# Start FastAPI server with correct environment variables

export PGHOST=localhost
export PGPORT=5433
export PGUSER=postgres
export PGPASSWORD=postgres
export PGDATABASE=studentperformancedb

cd /home/belysetag/Database---Prediction-Pipeline-Group-12
source venv/bin/activate

echo "Starting FastAPI server on http://localhost:8002"
echo "Database: $PGDATABASE on port $PGPORT"
echo ""

python -m uvicorn api.app:app --reload --port 8002

#!/bin/bash
# Test the prediction pipeline

cd /home/belysetag/Database---Prediction-Pipeline-Group-12/scripts

echo "Testing prediction pipeline..."
echo "API URL: http://localhost:8002"
echo ""

export API_URL=http://localhost:8002
python predict_latest.py

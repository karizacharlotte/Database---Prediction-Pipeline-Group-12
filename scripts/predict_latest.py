"""
Prediction Client Script
Fetches latest student from API, loads trained model, makes prediction, stores result
"""
import os
import sys
import pickle
import json
import requests
import pandas as pd
from datetime import datetime

# Configuration
API_BASE_URL = os.environ.get('API_URL', 'http://localhost:8000')
MODEL_PATH = os.environ.get('MODEL_PATH', '../ml/models/best_gb.pkl')
SCALER_PATH = os.environ.get('SCALER_PATH', '../ml/models/scaler.pkl')
METADATA_PATH = os.environ.get('METADATA_PATH', '../ml/models/metadata.json')

def load_model():
    """Load trained model, scaler, and metadata"""
    print(f"Loading model from {MODEL_PATH}...")
    with open(MODEL_PATH, 'rb') as f:
        model = pickle.load(f)
    
    print(f"Loading scaler from {SCALER_PATH}...")
    with open(SCALER_PATH, 'rb') as f:
        scaler = pickle.load(f)
    
    print(f"Loading metadata from {METADATA_PATH}...")
    with open(METADATA_PATH, 'r') as f:
        metadata = json.load(f)
    
    return model, scaler, metadata

def fetch_latest_student():
    """Fetch the latest student from API"""
    print("Fetching latest student from API...")
    url = f"{API_BASE_URL}/students/latest/one"
    response = requests.get(url)
    
    if response.status_code == 404:
        print("No students found in database")
        return None
    
    response.raise_for_status()
    student = response.json()
    print(f"✓ Fetched student {student['student_id']}")
    return student

def fetch_student_data(student_id):
    """Fetch complete student data including academic records"""
    print(f"Fetching complete data for student {student_id}...")
    
    # Fetch all related records
    student = requests.get(f"{API_BASE_URL}/students/{student_id}").json()
    
    try:
        family_response = requests.get(f"{API_BASE_URL}/family-background/student/{student_id}")
        if family_response.status_code == 200:
            family = family_response.json()
            # If it's a list, take first item
            if isinstance(family, list):
                family = family[0] if len(family) > 0 else {}
        else:
            family = {}
    except Exception as e:
        print(f"⚠ Warning: Could not fetch family background: {e}")
        family = {}
    
    try:
        academic_response = requests.get(f"{API_BASE_URL}/academic-records/student/{student_id}")
        if academic_response.status_code == 200:
            academic = academic_response.json()
            # If it's a list, take first or latest item
            if isinstance(academic, list):
                academic = academic[0] if len(academic) > 0 else {}
        else:
            academic = {}
    except Exception as e:
        print(f"⚠ Warning: Could not fetch academic records: {e}")
        academic = {}
    
    try:
        school_response = requests.get(f"{API_BASE_URL}/school-info/student/{student_id}")
        if school_response.status_code == 200:
            school_info = school_response.json()
            # If it's a list, take first item
            if isinstance(school_info, list):
                school_info = school_info[0] if len(school_info) > 0 else {}
        else:
            school_info = {}
    except Exception as e:
        print(f"⚠ Warning: Could not fetch school info: {e}")
        school_info = {}
    
    # Ensure all are dictionaries before combining
    if not isinstance(student, dict):
        student = {}
    if not isinstance(family, dict):
        family = {}
    if not isinstance(academic, dict):
        academic = {}
    if not isinstance(school_info, dict):
        school_info = {}
    
    # Combine all data
    combined = {**student, **family, **academic, **school_info}
    return combined

def preprocess_features(student_data, selected_features, scaler):
    """Prepare features for prediction"""
    print(f"Preprocessing features ({len(selected_features)} features)...")
    
    # Encoding mappings for categorical variables
    encoding_maps = {
        'school': {'GP': 0, 'MS': 1},
        'sex': {'F': 0, 'M': 1},
        'address': {'U': 0, 'R': 1},
        'famsize': {'LE3': 0, 'GT3': 1},
        'Pstatus': {'T': 0, 'A': 1},
        'Mjob': {'teacher': 0, 'health': 1, 'services': 2, 'at_home': 3, 'other': 4},
        'Fjob': {'teacher': 0, 'health': 1, 'services': 2, 'at_home': 3, 'other': 4},
        'reason': {'home': 0, 'reputation': 1, 'course': 2, 'other': 3},
        'guardian': {'mother': 0, 'father': 1, 'other': 2},
        'schoolsup': {'no': 0, 'yes': 1},
        'famsup': {'no': 0, 'yes': 1},
        'paid': {'no': 0, 'yes': 1},
        'activities': {'no': 0, 'yes': 1},
        'nursery': {'no': 0, 'yes': 1},
        'higher': {'no': 0, 'yes': 1},
        'internet': {'no': 0, 'yes': 1},
        'romantic': {'no': 0, 'yes': 1}
    }
    
    # Create DataFrame with selected features
    features_dict = {}
    for feature in selected_features:
        # Get feature value, default to 0 if missing
        value = student_data.get(feature, 0)
        
        # Handle None values
        if value is None:
            value = 0
        # Handle boolean values
        elif isinstance(value, bool):
            value = 1 if value else 0
        # Handle categorical encoding
        elif feature in encoding_maps and value in encoding_maps[feature]:
            value = encoding_maps[feature][value]
        # Handle yes/no strings not in encoding_maps
        elif isinstance(value, str):
            if value.lower() == 'yes':
                value = 1
            elif value.lower() == 'no':
                value = 0
            else:
                # Try to convert to float, otherwise default to 0
                try:
                    value = float(value)
                except:
                    print(f"⚠ Warning: Could not encode '{feature}' value '{value}', using 0")
                    value = 0
        
        features_dict[feature] = [value]
    
    df = pd.DataFrame(features_dict)
    
    # Convert all to numeric
    for col in df.columns:
        df[col] = pd.to_numeric(df[col], errors='coerce')
    
    # Handle missing values
    df = df.fillna(0)
    
    # Apply scaler
    df_scaled = scaler.transform(df)
    
    return df_scaled

def make_prediction(model, features):
    """Make prediction using loaded model"""
    print("Making prediction...")
    
    # Get probability and prediction
    proba = model.predict_proba(features)[0][1]
    prediction = int(proba >= 0.5)
    
    print(f"✓ Prediction: {'AT RISK' if prediction else 'NOT AT RISK'}")
    print(f"✓ Probability: {proba:.4f}")
    
    return prediction, proba

def store_prediction_postgresql(student_id, probability, predicted_label):
    """Store prediction by updating academic_records at_risk status in PostgreSQL"""
    print("Updating at_risk status in PostgreSQL...")
    
    # First, get academic records for this student
    try:
        response = requests.get(f"{API_BASE_URL}/academic-records/student/{student_id}")
        if response.status_code == 200:
            records = response.json()
            if isinstance(records, list) and len(records) > 0:
                # Update the first/latest record
                record_id = records[0]['record_id']
                
                # Update at_risk status via PUT
                update_url = f"{API_BASE_URL}/academic-records/{record_id}"
                payload = {'at_risk': bool(predicted_label)}
                
                update_response = requests.put(update_url, json=payload)
                if update_response.status_code in [200, 201]:
                    print(f"✓ Updated at_risk status for record {record_id}")
                    return update_response.json()
                else:
                    print(f"⚠ Could not update at_risk status: {update_response.status_code}")
            else:
                print("⚠ No academic records found for student")
        else:
            print(f"⚠ Could not fetch academic records: {response.status_code}")
    except Exception as e:
        print(f"⚠ Could not update prediction in PostgreSQL: {e}")
    
    return None

def store_prediction_mongodb(student_id, probability, predicted_label, selected_features, feature_values):
    """Store prediction in MongoDB for history tracking"""
    print("Storing prediction in MongoDB...")
    
    try:
        # Prepare prediction data
        payload = {
            "student_id": student_id,
            "predicted_label": bool(predicted_label),
            "probability": float(probability),
            "confidence": float(probability * 100),
            "model_name": "GradientBoostingClassifier",
            "model_version": "1.0",
            "features_used": selected_features,
            "feature_values": feature_values,
            "metadata": {
                "threshold": 0.5,
                "at_risk_threshold": 10
            }
        }
        
        # Post to MongoDB endpoint
        response = requests.post(f"{API_BASE_URL}/mongo/predictions", json=payload)
        
        if response.status_code in [200, 201]:
            result = response.json()
            print(f"✓ Prediction stored in MongoDB with ID: {result.get('prediction_id')}")
            return result
        else:
            print(f"⚠ Could not store prediction in MongoDB: {response.status_code}")
            print(f"   Response: {response.text}")
    except Exception as e:
        print(f"⚠ Could not store prediction in MongoDB: {e}")
    
    return None

def main():
    """Main prediction pipeline"""
    print("="*60)
    print("STUDENT AT-RISK PREDICTION PIPELINE")
    print("="*60)
    
    try:
        # Step 1: Load model
        model, scaler, metadata = load_model()
        selected_features = metadata['features']['selected_features']
        print(f"✓ Model loaded: {metadata.get('model_type', 'Unknown')}")
        print(f"✓ Features: {len(selected_features)}")
        
        # Step 2: Fetch latest student
        latest_student = fetch_latest_student()
        if not latest_student:
            print("No students available for prediction")
            return
        
        student_id = latest_student['student_id']
        
        # Step 3: Fetch complete student data
        student_data = fetch_student_data(student_id)
        
        # Step 4: Preprocess features
        features_scaled = preprocess_features(student_data, selected_features, scaler)
        
        # Step 5: Make prediction
        prediction, probability = make_prediction(model, features_scaled)
        
        # Step 6a: Store prediction in PostgreSQL (update at_risk status)
        store_prediction_postgresql(student_id, probability, prediction)
        
        # Step 6b: Store prediction in MongoDB (prediction history)
        # Prepare feature values for MongoDB
        feature_values_dict = {feature: student_data.get(feature, 0) for feature in selected_features}
        store_prediction_mongodb(student_id, probability, prediction, selected_features, feature_values_dict)
        
        print("\n" + "="*60)
        print("PREDICTION COMPLETE!")
        print("="*60)
        print(f"Student ID: {student_id}")
        print(f"Prediction: {'AT RISK ⚠️' if prediction else 'NOT AT RISK ✓'}")
        print(f"Confidence: {probability:.2%}")
        print("="*60)
        
    except FileNotFoundError as e:
        print(f"\n❌ Error: Model files not found")
        print(f"   Make sure you've run the notebook and exported the model to {MODEL_PATH}")
        print(f"   {e}")
        sys.exit(1)
    except requests.exceptions.ConnectionError:
        print(f"\n❌ Error: Cannot connect to API at {API_BASE_URL}")
        print(f"   Make sure the FastAPI server is running:")
        print(f"   uvicorn api.app:app --reload")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

if __name__ == '__main__':
    main()

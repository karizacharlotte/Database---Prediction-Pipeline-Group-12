"""
MongoDB Database Helper for NoSQL operations
Handles prediction history, logs, and flexible document storage
"""
import os
from datetime import datetime
from typing import List, Dict, Optional, Any
from pymongo import MongoClient, DESCENDING, ASCENDING
from pymongo.errors import ConnectionFailure, DuplicateKeyError
import logging

# MongoDB client (singleton pattern)
_client = None
_db = None

def get_mongo_config():
    """Get MongoDB configuration from environment variables"""
    return {
        'uri': os.environ.get('MONGO_URI', 'mongodb://localhost:27017/'),
        'database': os.environ.get('MONGO_DB', 'studentperformancedb')
    }

def connect():
    """Connect to MongoDB and return database instance"""
    global _client, _db
    
    if _db is not None:
        return _db
    
    try:
        config = get_mongo_config()
        _client = MongoClient(
            config['uri'],
            serverSelectionTimeoutMS=5000,
            connectTimeoutMS=10000
        )
        
        # Verify connection
        _client.admin.command('ping')
        
        _db = _client[config['database']]
        logging.info(f"Connected to MongoDB: {config['database']}")
        
        # Create indexes
        _create_indexes()
        
        return _db
    
    except ConnectionFailure as e:
        logging.error(f"Failed to connect to MongoDB: {e}")
        raise

def close():
    """Close MongoDB connection"""
    global _client, _db
    if _client is not None:
        _client.close()
        _client = None
        _db = None
        logging.info("MongoDB connection closed")

def _create_indexes():
    """Create indexes for better query performance"""
    db = get_db()
    
    # Prediction History indexes
    db.prediction_history.create_index([("student_id", ASCENDING)])
    db.prediction_history.create_index([("timestamp", DESCENDING)])
    db.prediction_history.create_index([("predicted_label", ASCENDING)])
    
    # Student Documents indexes
    db.student_documents.create_index([("student_id", ASCENDING)], unique=True)
    db.student_documents.create_index([("created_at", DESCENDING)])
    
    # Activity Logs indexes
    db.activity_logs.create_index([("student_id", ASCENDING)])
    db.activity_logs.create_index([("timestamp", DESCENDING)])
    db.activity_logs.create_index([("action_type", ASCENDING)])
    
    logging.info("MongoDB indexes created")

def get_db():
    """Get database instance (connects if not connected)"""
    if _db is None:
        return connect()
    return _db

# ==================== PREDICTION HISTORY OPERATIONS ====================

def insert_prediction(
    student_id: str,
    prediction_data: Dict[str, Any]
) -> str:
    """
    Insert a new prediction into history
    
    Args:
        student_id: UUID of the student
        prediction_data: Dictionary containing prediction details
    
    Returns:
        str: Inserted document ID
    """
    db = get_db()
    
    document = {
        "student_id": student_id,
        "timestamp": datetime.utcnow(),
        "predicted_label": prediction_data.get("predicted_label"),
        "probability": prediction_data.get("probability"),
        "confidence": prediction_data.get("confidence"),
        "model_name": prediction_data.get("model_name", "GradientBoostingClassifier"),
        "model_version": prediction_data.get("model_version", "1.0"),
        "features_used": prediction_data.get("features_used", []),
        "feature_values": prediction_data.get("feature_values", {}),
        "metadata": prediction_data.get("metadata", {})
    }
    
    result = db.prediction_history.insert_one(document)
    logging.info(f"Inserted prediction for student {student_id}")
    return str(result.inserted_id)

def get_prediction_history(
    student_id: str,
    limit: int = 10
) -> List[Dict]:
    """Get prediction history for a student"""
    db = get_db()
    
    cursor = db.prediction_history.find(
        {"student_id": student_id}
    ).sort("timestamp", DESCENDING).limit(limit)
    
    results = []
    for doc in cursor:
        doc['_id'] = str(doc['_id'])
        results.append(doc)
    
    return results

def get_all_predictions(
    skip: int = 0,
    limit: int = 100,
    filter_at_risk: Optional[bool] = None
) -> List[Dict]:
    """Get all predictions with optional filtering"""
    db = get_db()
    
    query = {}
    if filter_at_risk is not None:
        query["predicted_label"] = filter_at_risk
    
    cursor = db.prediction_history.find(query).sort(
        "timestamp", DESCENDING
    ).skip(skip).limit(limit)
    
    results = []
    for doc in cursor:
        doc['_id'] = str(doc['_id'])
        results.append(doc)
    
    return results

def get_prediction_statistics() -> Dict:
    """Get statistics about predictions"""
    db = get_db()
    
    pipeline = [
        {
            "$group": {
                "_id": "$predicted_label",
                "count": {"$sum": 1},
                "avg_probability": {"$avg": "$probability"}
            }
        }
    ]
    
    results = list(db.prediction_history.aggregate(pipeline))
    
    stats = {
        "total_predictions": db.prediction_history.count_documents({}),
        "by_label": {}
    }
    
    for result in results:
        label = "at_risk" if result['_id'] else "not_at_risk"
        stats["by_label"][label] = {
            "count": result['count'],
            "avg_probability": result['avg_probability']
        }
    
    return stats

# ==================== STUDENT DOCUMENTS OPERATIONS ====================

def upsert_student_document(
    student_id: str,
    student_data: Dict[str, Any]
) -> bool:
    """
    Insert or update student document (flexible schema)
    
    Args:
        student_id: UUID of the student
        student_data: Complete student data
    
    Returns:
        bool: True if successful
    """
    db = get_db()
    
    document = {
        "student_id": student_id,
        "updated_at": datetime.utcnow(),
        **student_data
    }
    
    # Add created_at only for new documents
    result = db.student_documents.update_one(
        {"student_id": student_id},
        {
            "$set": document,
            "$setOnInsert": {"created_at": datetime.utcnow()}
        },
        upsert=True
    )
    
    logging.info(f"Upserted student document for {student_id}")
    return True

def get_student_document(student_id: str) -> Optional[Dict]:
    """Get student document by ID"""
    db = get_db()
    
    doc = db.student_documents.find_one({"student_id": student_id})
    if doc:
        doc['_id'] = str(doc['_id'])
    return doc

def get_all_student_documents(
    skip: int = 0,
    limit: int = 100
) -> List[Dict]:
    """Get all student documents"""
    db = get_db()
    
    cursor = db.student_documents.find().skip(skip).limit(limit)
    
    results = []
    for doc in cursor:
        doc['_id'] = str(doc['_id'])
        results.append(doc)
    
    return results

def delete_student_document(student_id: str) -> bool:
    """Delete student document"""
    db = get_db()
    
    result = db.student_documents.delete_one({"student_id": student_id})
    return result.deleted_count > 0

# ==================== ACTIVITY LOGS OPERATIONS ====================

def insert_activity_log(
    student_id: Optional[str],
    action_type: str,
    description: str,
    metadata: Optional[Dict] = None
) -> str:
    """
    Insert activity log
    
    Args:
        student_id: UUID of student (optional for system logs)
        action_type: Type of action (e.g., 'prediction', 'update', 'delete')
        description: Description of the action
        metadata: Additional metadata
    
    Returns:
        str: Inserted document ID
    """
    db = get_db()
    
    document = {
        "student_id": student_id,
        "action_type": action_type,
        "description": description,
        "timestamp": datetime.utcnow(),
        "metadata": metadata or {}
    }
    
    result = db.activity_logs.insert_one(document)
    return str(result.inserted_id)

def get_activity_logs(
    student_id: Optional[str] = None,
    action_type: Optional[str] = None,
    skip: int = 0,
    limit: int = 100
) -> List[Dict]:
    """Get activity logs with optional filtering"""
    db = get_db()
    
    query = {}
    if student_id:
        query["student_id"] = student_id
    if action_type:
        query["action_type"] = action_type
    
    cursor = db.activity_logs.find(query).sort(
        "timestamp", DESCENDING
    ).skip(skip).limit(limit)
    
    results = []
    for doc in cursor:
        doc['_id'] = str(doc['_id'])
        results.append(doc)
    
    return results

# ==================== AGGREGATION QUERIES ====================

def get_student_summary(student_id: str) -> Dict:
    """Get comprehensive summary for a student"""
    db = get_db()
    
    # Get student document
    student_doc = get_student_document(student_id)
    
    # Get prediction count
    prediction_count = db.prediction_history.count_documents(
        {"student_id": student_id}
    )
    
    # Get latest prediction
    latest_prediction = db.prediction_history.find_one(
        {"student_id": student_id},
        sort=[("timestamp", DESCENDING)]
    )
    
    if latest_prediction:
        latest_prediction['_id'] = str(latest_prediction['_id'])
    
    # Get activity count
    activity_count = db.activity_logs.count_documents(
        {"student_id": student_id}
    )
    
    return {
        "student_id": student_id,
        "student_data": student_doc,
        "prediction_count": prediction_count,
        "latest_prediction": latest_prediction,
        "activity_count": activity_count
    }

def get_at_risk_students(limit: int = 50) -> List[Dict]:
    """Get students with latest at-risk predictions"""
    db = get_db()
    
    pipeline = [
        {"$sort": {"timestamp": DESCENDING}},
        {
            "$group": {
                "_id": "$student_id",
                "latest_prediction": {"$first": "$$ROOT"}
            }
        },
        {"$match": {"latest_prediction.predicted_label": True}},
        {"$limit": limit},
        {"$project": {"_id": 0, "latest_prediction": 1}}
    ]
    
    results = list(db.prediction_history.aggregate(pipeline))
    
    return [r['latest_prediction'] for r in results]

# ==================== UTILITY FUNCTIONS ====================

def clear_collection(collection_name: str) -> int:
    """Clear all documents from a collection (use with caution!)"""
    db = get_db()
    result = db[collection_name].delete_many({})
    logging.warning(f"Cleared {result.deleted_count} documents from {collection_name}")
    return result.deleted_count

def get_collections_info() -> Dict:
    """Get information about all collections"""
    db = get_db()
    
    collections = {}
    for collection_name in db.list_collection_names():
        collections[collection_name] = {
            "document_count": db[collection_name].count_documents({}),
            "indexes": [idx['name'] for idx in db[collection_name].list_indexes()]
        }
    
    return collections

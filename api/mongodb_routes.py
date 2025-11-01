"""
MongoDB/NoSQL API Routes
Handles prediction history, activity logs, and flexible document storage
"""
from fastapi import APIRouter, HTTPException, Query
from typing import List, Optional
import logging

from . import mongodb
from .mongodb_schemas import (
    PredictionCreate, PredictionOut,
    StudentDocumentCreate, StudentDocumentOut,
    ActivityLogCreate, ActivityLogOut,
    PredictionStatistics, StudentSummary
)

router = APIRouter()

# ==================== PREDICTION HISTORY ENDPOINTS ====================

@router.post("/mongo/predictions", response_model=dict, tags=["MongoDB - Predictions"])
async def create_prediction(prediction: PredictionCreate):
    """Store a new prediction in MongoDB"""
    try:
        prediction_id = mongodb.insert_prediction(
            student_id=prediction.student_id,
            prediction_data=prediction.dict()
        )
        
        # Also log the activity
        mongodb.insert_activity_log(
            student_id=prediction.student_id,
            action_type="prediction",
            description=f"Prediction made: {'AT RISK' if prediction.predicted_label else 'NOT AT RISK'}",
            metadata={"probability": prediction.probability}
        )
        
        return {
            "message": "Prediction stored successfully",
            "prediction_id": prediction_id,
            "student_id": prediction.student_id
        }
    except Exception as e:
        logging.error(f"Error storing prediction: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/mongo/predictions/student/{student_id}", response_model=List[dict], tags=["MongoDB - Predictions"])
async def get_student_predictions(
    student_id: str,
    limit: int = Query(10, ge=1, le=100)
):
    """Get prediction history for a specific student"""
    try:
        predictions = mongodb.get_prediction_history(student_id, limit)
        return predictions
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/mongo/predictions", response_model=List[dict], tags=["MongoDB - Predictions"])
async def list_predictions(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=500),
    at_risk: Optional[bool] = None
):
    """List all predictions with optional filtering"""
    try:
        predictions = mongodb.get_all_predictions(skip, limit, at_risk)
        return predictions
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/mongo/predictions/statistics", response_model=PredictionStatistics, tags=["MongoDB - Predictions"])
async def get_prediction_stats():
    """Get prediction statistics"""
    try:
        stats = mongodb.get_prediction_statistics()
        return stats
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/mongo/predictions/at-risk", response_model=List[dict], tags=["MongoDB - Predictions"])
async def get_at_risk_students(limit: int = Query(50, ge=1, le=200)):
    """Get students with latest at-risk predictions"""
    try:
        students = mongodb.get_at_risk_students(limit)
        return students
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# ==================== STUDENT DOCUMENTS ENDPOINTS ====================

@router.post("/mongo/students", response_model=dict, tags=["MongoDB - Students"])
async def create_or_update_student_document(student: StudentDocumentCreate):
    """Create or update student document (flexible schema)"""
    try:
        success = mongodb.upsert_student_document(
            student_id=student.student_id,
            student_data=student.dict(exclude={'student_id'})
        )
        
        # Log the activity
        mongodb.insert_activity_log(
            student_id=student.student_id,
            action_type="upsert",
            description="Student document created/updated",
            metadata={}
        )
        
        return {
            "message": "Student document saved successfully",
            "student_id": student.student_id
        }
    except Exception as e:
        logging.error(f"Error saving student document: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/mongo/students/{student_id}", response_model=dict, tags=["MongoDB - Students"])
async def get_student_document(student_id: str):
    """Get student document by ID"""
    try:
        document = mongodb.get_student_document(student_id)
        if not document:
            raise HTTPException(status_code=404, detail="Student document not found")
        return document
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/mongo/students", response_model=List[dict], tags=["MongoDB - Students"])
async def list_student_documents(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=500)
):
    """List all student documents"""
    try:
        documents = mongodb.get_all_student_documents(skip, limit)
        return documents
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.delete("/mongo/students/{student_id}", tags=["MongoDB - Students"])
async def delete_student_document(student_id: str):
    """Delete student document"""
    try:
        success = mongodb.delete_student_document(student_id)
        if not success:
            raise HTTPException(status_code=404, detail="Student document not found")
        
        # Log the activity
        mongodb.insert_activity_log(
            student_id=student_id,
            action_type="delete",
            description="Student document deleted",
            metadata={}
        )
        
        return {"message": "Student document deleted successfully", "student_id": student_id}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/mongo/students/{student_id}/summary", response_model=StudentSummary, tags=["MongoDB - Students"])
async def get_student_summary(student_id: str):
    """Get comprehensive summary for a student"""
    try:
        summary = mongodb.get_student_summary(student_id)
        return summary
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# ==================== ACTIVITY LOGS ENDPOINTS ====================

@router.post("/mongo/activity-logs", response_model=dict, tags=["MongoDB - Activity Logs"])
async def create_activity_log(log: ActivityLogCreate):
    """Create an activity log entry"""
    try:
        log_id = mongodb.insert_activity_log(
            student_id=log.student_id,
            action_type=log.action_type,
            description=log.description,
            metadata=log.metadata
        )
        return {
            "message": "Activity log created successfully",
            "log_id": log_id
        }
    except Exception as e:
        logging.error(f"Error creating activity log: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/mongo/activity-logs", response_model=List[dict], tags=["MongoDB - Activity Logs"])
async def list_activity_logs(
    student_id: Optional[str] = None,
    action_type: Optional[str] = None,
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=500)
):
    """List activity logs with optional filtering"""
    try:
        logs = mongodb.get_activity_logs(student_id, action_type, skip, limit)
        return logs
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/mongo/activity-logs/student/{student_id}", response_model=List[dict], tags=["MongoDB - Activity Logs"])
async def get_student_activity_logs(
    student_id: str,
    limit: int = Query(50, ge=1, le=200)
):
    """Get activity logs for a specific student"""
    try:
        logs = mongodb.get_activity_logs(student_id=student_id, limit=limit)
        return logs
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# ==================== UTILITY ENDPOINTS ====================

@router.get("/mongo/info", tags=["MongoDB - Utility"])
async def get_mongodb_info():
    """Get information about MongoDB collections"""
    try:
        info = mongodb.get_collections_info()
        return {
            "database": "studentperformancedb",
            "collections": info
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.delete("/mongo/collections/{collection_name}/clear", tags=["MongoDB - Utility"])
async def clear_collection(collection_name: str):
    """Clear all documents from a collection (use with caution!)"""
    try:
        # Only allow clearing these collections
        allowed_collections = ["prediction_history", "activity_logs", "student_documents"]
        if collection_name not in allowed_collections:
            raise HTTPException(
                status_code=400,
                detail=f"Can only clear these collections: {allowed_collections}"
            )
        
        count = mongodb.clear_collection(collection_name)
        return {
            "message": f"Collection '{collection_name}' cleared",
            "documents_deleted": count
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/mongo/health", tags=["MongoDB - Utility"])
async def mongodb_health_check():
    """Check MongoDB connection health"""
    try:
        db = mongodb.get_db()
        # Try to ping the database
        db.command('ping')
        return {
            "status": "healthy",
            "database": "connected",
            "collections": list(db.list_collection_names())
        }
    except Exception as e:
        raise HTTPException(
            status_code=503,
            detail=f"MongoDB unhealthy: {str(e)}"
        )

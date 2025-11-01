"""
Pydantic schemas for MongoDB NoSQL documents
"""
from pydantic import BaseModel, Field
from typing import Optional, Dict, List, Any
from datetime import datetime

# ==================== Prediction History Schemas ====================

class PredictionCreate(BaseModel):
    student_id: str
    predicted_label: bool
    probability: float = Field(..., ge=0.0, le=1.0)
    confidence: Optional[float] = None
    model_name: str = "GradientBoostingClassifier"
    model_version: str = "1.0"
    features_used: List[str] = []
    feature_values: Dict[str, Any] = {}
    metadata: Dict[str, Any] = {}

class PredictionOut(BaseModel):
    id: str = Field(alias="_id")
    student_id: str
    timestamp: datetime
    predicted_label: bool
    probability: float
    confidence: Optional[float]
    model_name: str
    model_version: str
    features_used: List[str]
    feature_values: Dict[str, Any]
    metadata: Dict[str, Any]
    
    class Config:
        populate_by_name = True

# ==================== Student Document Schemas ====================

class StudentDocumentCreate(BaseModel):
    student_id: str
    age: Optional[int] = None
    sex: Optional[str] = None
    address: Optional[str] = None
    famsize: Optional[str] = None
    Pstatus: Optional[str] = None
    Medu: Optional[int] = None
    Fedu: Optional[int] = None
    Mjob: Optional[str] = None
    Fjob: Optional[str] = None
    reason: Optional[str] = None
    guardian: Optional[str] = None
    traveltime: Optional[int] = None
    studytime: Optional[int] = None
    failures: Optional[int] = None
    schoolsup: Optional[bool] = None
    famsup: Optional[bool] = None
    paid: Optional[bool] = None
    activities: Optional[bool] = None
    nursery: Optional[bool] = None
    higher: Optional[bool] = None
    internet: Optional[bool] = None
    romantic: Optional[bool] = None
    famrel: Optional[int] = None
    freetime: Optional[int] = None
    goout: Optional[int] = None
    Dalc: Optional[int] = None
    Walc: Optional[int] = None
    health: Optional[int] = None
    absences: Optional[int] = None
    G1: Optional[int] = None
    G2: Optional[int] = None
    G3: Optional[int] = None
    # Add any custom fields as needed
    custom_fields: Optional[Dict[str, Any]] = {}

class StudentDocumentOut(BaseModel):
    id: str = Field(alias="_id")
    student_id: str
    created_at: datetime
    updated_at: datetime
    # All other fields are dynamic
    
    class Config:
        populate_by_name = True
        extra = "allow"  # Allow additional fields

# ==================== Activity Log Schemas ====================

class ActivityLogCreate(BaseModel):
    student_id: Optional[str] = None
    action_type: str  # 'prediction', 'create', 'update', 'delete', 'view'
    description: str
    metadata: Dict[str, Any] = {}

class ActivityLogOut(BaseModel):
    id: str = Field(alias="_id")
    student_id: Optional[str]
    action_type: str
    description: str
    timestamp: datetime
    metadata: Dict[str, Any]
    
    class Config:
        populate_by_name = True

# ==================== Statistics Schemas ====================

class PredictionStatistics(BaseModel):
    total_predictions: int
    by_label: Dict[str, Dict[str, Any]]

class StudentSummary(BaseModel):
    student_id: str
    student_data: Optional[Dict[str, Any]]
    prediction_count: int
    latest_prediction: Optional[Dict[str, Any]]
    activity_count: int

class CollectionInfo(BaseModel):
    document_count: int
    indexes: List[str]

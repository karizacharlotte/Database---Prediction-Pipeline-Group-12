"""
Pydantic schemas for request/response validation
"""
from typing import Optional
from pydantic import BaseModel, Field
from datetime import datetime
from uuid import UUID

# ==================== Student Schemas ====================
class StudentBase(BaseModel):
    age: Optional[int] = Field(None, ge=15, le=25)
    sex: Optional[str] = Field(None, pattern="^[MF]$")
    address: Optional[str] = Field(None, pattern="^[UR]$")
    famsize: Optional[str] = Field(None, pattern="^(LE3|GT3)$")
    pstatus: Optional[str] = Field(None, pattern="^[TA]$")

class StudentCreate(StudentBase):
    pass

class StudentUpdate(StudentBase):
    pass

class StudentOut(StudentBase):
    student_id: UUID
    created_at: Optional[datetime]
    
    class Config:
        from_attributes = True

# ==================== Family Background Schemas ====================
class FamilyBackgroundBase(BaseModel):
    student_id: UUID
    medu: Optional[int] = Field(None, ge=0, le=4)
    fedu: Optional[int] = Field(None, ge=0, le=4)
    mjob: Optional[str] = None
    fjob: Optional[str] = None
    guardian: Optional[str] = None
    famrel: Optional[int] = Field(None, ge=1, le=5)

class FamilyBackgroundCreate(FamilyBackgroundBase):
    pass

class FamilyBackgroundOut(FamilyBackgroundBase):
    family_id: UUID
    
    class Config:
        from_attributes = True

# ==================== Academic Records Schemas ====================
class AcademicRecordBase(BaseModel):
    student_id: UUID
    subject: Optional[str] = None
    absences: Optional[int] = Field(None, ge=0)
    g1: Optional[int] = Field(None, ge=0, le=20)
    g2: Optional[int] = Field(None, ge=0, le=20)
    g3: Optional[int] = Field(None, ge=0, le=20)
    romantic: Optional[bool] = None
    freetime: Optional[int] = Field(None, ge=1, le=5)
    goout: Optional[int] = Field(None, ge=1, le=5)

class AcademicRecordCreate(AcademicRecordBase):
    pass

class AcademicRecordUpdate(BaseModel):
    subject: Optional[str] = None
    absences: Optional[int] = Field(None, ge=0)
    g1: Optional[int] = Field(None, ge=0, le=20)
    g2: Optional[int] = Field(None, ge=0, le=20)
    g3: Optional[int] = Field(None, ge=0, le=20)
    romantic: Optional[bool] = None
    freetime: Optional[int] = Field(None, ge=1, le=5)
    goout: Optional[int] = Field(None, ge=1, le=5)

class AcademicRecordOut(AcademicRecordBase):
    record_id: UUID
    at_risk: Optional[bool]
    
    class Config:
        from_attributes = True

# ==================== School Info Schemas ====================
class SchoolInfoBase(BaseModel):
    student_id: UUID
    school_name: Optional[str] = None

class SchoolInfoCreate(SchoolInfoBase):
    pass

class SchoolInfoOut(SchoolInfoBase):
    school_info_id: UUID
    
    class Config:
        from_attributes = True

# ==================== Audit Log Schema ====================
class AuditLogOut(BaseModel):
    log_id: UUID
    student_id: Optional[UUID]
    action: str
    changed_at: Optional[datetime]
    old_data: Optional[dict]
    new_data: Optional[dict]
    
    class Config:
        from_attributes = True

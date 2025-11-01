"""
FastAPI Application for Student Performance Database
CRUD operations for:
- PostgreSQL (SQL): students, academic_records, family_background, school_info, student_audit_log
- MongoDB (NoSQL): prediction_history, student_documents, activity_logs
"""
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from typing import List
from uuid import UUID
import json
import logging

from . import db, mongodb
from .schemas import (
    StudentCreate, StudentUpdate, StudentOut,
    FamilyBackgroundCreate, FamilyBackgroundOut,
    AcademicRecordCreate, AcademicRecordUpdate, AcademicRecordOut,
    SchoolInfoCreate, SchoolInfoOut,
    AuditLogOut
)
from .mongodb_routes import router as mongodb_router

app = FastAPI(
    title="Student Performance API",
    description="API for managing student performance data with prediction capabilities (PostgreSQL + MongoDB)",
    version="2.0.0"
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include MongoDB routes
app.include_router(mongodb_router)

@app.on_event("startup")
async def startup():
    """Initialize database connections"""
    # PostgreSQL connection
    await db.connect()
    logging.info("PostgreSQL connected")
    
    # MongoDB connection
    try:
        mongodb.connect()
        logging.info("MongoDB connected")
    except Exception as e:
        logging.warning(f"MongoDB connection failed: {e}")
        logging.warning("MongoDB endpoints will not work")

@app.on_event("shutdown")
async def shutdown():
    """Close database connections"""
    await db.close()
    mongodb.close()
    logging.info("All database connections closed")

# STUDENTS CRUD 

@app.post("/students", response_model=StudentOut, tags=["Students"])
async def create_student(student: StudentCreate):
    """Create a new student"""
    query = """
        INSERT INTO students (age, sex, address, famsize, pstatus)
        VALUES ($1, $2, $3, $4, $5)
        RETURNING student_id, age, sex, address, famsize, pstatus, created_at
    """
    row = await db.fetchrow(
        query, student.age, student.sex, student.address,
        student.famsize, student.pstatus
    )
    if not row:
        raise HTTPException(status_code=500, detail="Failed to create student")
    return dict(row)

@app.get("/students/{student_id}", response_model=StudentOut, tags=["Students"])
async def get_student(student_id: UUID):
    """Get a student by ID"""
    query = "SELECT * FROM students WHERE student_id = $1"
    row = await db.fetchrow(query, student_id)
    if not row:
        raise HTTPException(status_code=404, detail="Student not found")
    return dict(row)

@app.get("/students", response_model=List[StudentOut], tags=["Students"])
async def list_students(skip: int = 0, limit: int = 100):
    """List all students with pagination"""
    query = "SELECT * FROM students ORDER BY student_id LIMIT $1 OFFSET $2"
    rows = await db.fetch(query, limit, skip)
    return [dict(row) for row in rows]

@app.get("/students/latest/one", response_model=StudentOut, tags=["Students"])
async def get_latest_student():
    """Get the most recently created student"""
    query = "SELECT * FROM students ORDER BY created_at DESC LIMIT 1"
    row = await db.fetchrow(query)
    if not row:
        raise HTTPException(status_code=404, detail="No students found")
    return dict(row)

@app.put("/students/{student_id}", response_model=StudentOut, tags=["Students"])
async def update_student(student_id: UUID, student: StudentUpdate):
    """Update a student"""
    # Build dynamic update query
    fields = []
    values = []
    idx = 1
    
    for field, value in student.dict(exclude_unset=True).items():
        if value is not None:
            fields.append(f"{field} = ${idx}")
            values.append(value)
            idx += 1
    
    if not fields:
        raise HTTPException(status_code=400, detail="No fields to update")
    
    values.append(student_id)
    query = f"""
        UPDATE students SET {', '.join(fields)}
        WHERE student_id = ${idx}
        RETURNING *
    """
    row = await db.fetchrow(query, *values)
    if not row:
        raise HTTPException(status_code=404, detail="Student not found")
    return dict(row)

@app.delete("/students/{student_id}", tags=["Students"])
async def delete_student(student_id: UUID):
    """Delete a student (cascades to related records)"""
    query = "DELETE FROM students WHERE student_id = $1"
    await db.execute(query, student_id)
    return {"message": "Student deleted successfully", "student_id": str(student_id)}

# ==================== FAMILY BACKGROUND CRUD ====================

@app.post("/family-background", response_model=FamilyBackgroundOut, tags=["Family Background"])
async def create_family_background(family: FamilyBackgroundCreate):
    """Create family background record"""
    query = """
        INSERT INTO family_background 
        (student_id, medu, fedu, mjob, fjob, guardian, famrel)
        VALUES ($1, $2, $3, $4, $5, $6, $7)
        RETURNING *
    """
    row = await db.fetchrow(
        query, family.student_id, family.medu, family.fedu, family.mjob,
        family.fjob, family.guardian, family.famrel
    )
    return dict(row)

@app.get("/family-background/{family_id}", response_model=FamilyBackgroundOut, tags=["Family Background"])
async def get_family_background(family_id: UUID):
    """Get family background by ID"""
    query = "SELECT * FROM family_background WHERE family_id = $1"
    row = await db.fetchrow(query, family_id)
    if not row:
        raise HTTPException(status_code=404, detail="Family background not found")
    return dict(row)

@app.get("/family-background/student/{student_id}", response_model=FamilyBackgroundOut, tags=["Family Background"])
async def get_family_by_student(student_id: UUID):
    """Get family background by student ID"""
    query = "SELECT * FROM family_background WHERE student_id = $1"
    row = await db.fetchrow(query, student_id)
    if not row:
        raise HTTPException(status_code=404, detail="Family background not found")
    return dict(row)

@app.get("/family-background", response_model=List[FamilyBackgroundOut], tags=["Family Background"])
async def list_family_backgrounds(skip: int = 0, limit: int = 100):
    """List all family background records"""
    query = "SELECT * FROM family_background ORDER BY family_id LIMIT $1 OFFSET $2"
    rows = await db.fetch(query, limit, skip)
    return [dict(row) for row in rows]

@app.delete("/family-background/{family_id}", tags=["Family Background"])
async def delete_family_background(family_id: UUID):
    """Delete family background record"""
    query = "DELETE FROM family_background WHERE family_id = $1"
    await db.execute(query, family_id)
    return {"message": "Family background deleted", "family_id": str(family_id)}

# ==================== ACADEMIC RECORDS CRUD ====================

@app.post("/academic-records", response_model=AcademicRecordOut, tags=["Academic Records"])
async def create_academic_record(record: AcademicRecordCreate):
    """Create academic record (at_risk auto-calculated by trigger)"""
    query = """
        INSERT INTO academic_records 
        (student_id, subject, absences, g1, g2, g3, romantic, freetime, goout)
        VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9)
        RETURNING *
    """
    row = await db.fetchrow(
        query, record.student_id, record.subject, record.absences, 
        record.g1, record.g2, record.g3, record.romantic, 
        record.freetime, record.goout
    )
    return dict(row)

@app.get("/academic-records/{record_id}", response_model=AcademicRecordOut, tags=["Academic Records"])
async def get_academic_record(record_id: UUID):
    """Get academic record by ID"""
    query = "SELECT * FROM academic_records WHERE record_id = $1"
    row = await db.fetchrow(query, record_id)
    if not row:
        raise HTTPException(status_code=404, detail="Academic record not found")
    return dict(row)

@app.get("/academic-records/student/{student_id}", response_model=List[AcademicRecordOut], tags=["Academic Records"])
async def get_academic_by_student(student_id: UUID):
    """Get all academic records for a student"""
    query = "SELECT * FROM academic_records WHERE student_id = $1"
    rows = await db.fetch(query, student_id)
    return [dict(row) for row in rows]

@app.get("/academic-records", response_model=List[AcademicRecordOut], tags=["Academic Records"])
async def list_academic_records(skip: int = 0, limit: int = 100, at_risk: bool = None):
    """List academic records with optional at_risk filter"""
    if at_risk is not None:
        query = "SELECT * FROM academic_records WHERE at_risk = $1 ORDER BY record_id LIMIT $2 OFFSET $3"
        rows = await db.fetch(query, at_risk, limit, skip)
    else:
        query = "SELECT * FROM academic_records ORDER BY record_id LIMIT $1 OFFSET $2"
        rows = await db.fetch(query, limit, skip)
    return [dict(row) for row in rows]

@app.put("/academic-records/{record_id}", response_model=AcademicRecordOut, tags=["Academic Records"])
async def update_academic_record(record_id: UUID, record: AcademicRecordUpdate):
    """Update academic record"""
    updates = record.dict(exclude_unset=True)
    if not updates:
        raise HTTPException(status_code=400, detail="No fields to update")
    
    set_clause = ", ".join([f"{k} = ${i+2}" for i, k in enumerate(updates.keys())])
    query = f"UPDATE academic_records SET {set_clause} WHERE record_id = $1 RETURNING *"
    values = [record_id] + list(updates.values())
    row = await db.fetchrow(query, *values)
    
    if not row:
        raise HTTPException(status_code=404, detail="Academic record not found")
    return dict(row)

@app.delete("/academic-records/{record_id}", tags=["Academic Records"])
async def delete_academic_record(record_id: UUID):
    """Delete academic record"""
    query = "DELETE FROM academic_records WHERE record_id = $1"
    await db.execute(query, record_id)
    return {"message": "Academic record deleted", "record_id": str(record_id)}

# ==================== SCHOOL INFO CRUD ====================

@app.post("/school-info", response_model=SchoolInfoOut, tags=["School Info"])
async def create_school_info(info: SchoolInfoCreate):
    """Create school info record"""
    query = """
        INSERT INTO school_info 
        (student_id, school_name)
        VALUES ($1, $2)
        RETURNING *
    """
    row = await db.fetchrow(query, info.student_id, info.school_name)
    return dict(row)

@app.get("/school-info/{school_info_id}", response_model=SchoolInfoOut, tags=["School Info"])
async def get_school_info(school_info_id: UUID):
    """Get school info by ID"""
    query = "SELECT * FROM school_info WHERE school_info_id = $1"
    row = await db.fetchrow(query, school_info_id)
    if not row:
        raise HTTPException(status_code=404, detail="School info not found")
    return dict(row)

@app.get("/school-info/student/{student_id}", response_model=SchoolInfoOut, tags=["School Info"])
async def get_school_info_by_student(student_id: UUID):
    """Get school info by student ID"""
    query = "SELECT * FROM school_info WHERE student_id = $1"
    row = await db.fetchrow(query, student_id)
    if not row:
        raise HTTPException(status_code=404, detail="School info not found")
    return dict(row)

@app.get("/school-info", response_model=List[SchoolInfoOut], tags=["School Info"])
async def list_school_info(skip: int = 0, limit: int = 100):
    """List all school info records"""
    query = "SELECT * FROM school_info ORDER BY school_info_id LIMIT $1 OFFSET $2"
    rows = await db.fetch(query, limit, skip)
    return [dict(row) for row in rows]

@app.delete("/school-info/{school_info_id}", tags=["School Info"])
async def delete_school_info(school_info_id: UUID):
    """Delete school info"""
    query = "DELETE FROM school_info WHERE school_info_id = $1"
    await db.execute(query, school_info_id)
    return {"message": "School info deleted", "school_info_id": str(school_info_id)}

# ==================== AUDIT LOG (Read-only) ====================

@app.get("/audit-log", response_model=List[AuditLogOut], tags=["Audit Log"])
async def list_audit_logs(skip: int = 0, limit: int = 100, action: str = None):
    """List audit logs with optional action filter"""
    if action:
        query = "SELECT * FROM student_audit_log WHERE action = $1 ORDER BY changed_at DESC LIMIT $2 OFFSET $3"
        rows = await db.fetch(query, action.upper(), limit, skip)
    else:
        query = "SELECT * FROM student_audit_log ORDER BY changed_at DESC LIMIT $1 OFFSET $2"
        rows = await db.fetch(query, limit, skip)
    return [dict(row) for row in rows]

@app.get("/audit-log/student/{student_id}", response_model=List[AuditLogOut], tags=["Audit Log"])
async def get_audit_by_student(student_id: UUID):
    """Get all audit logs for a specific student"""
    query = "SELECT * FROM student_audit_log WHERE student_id = $1 ORDER BY changed_at DESC"
    rows = await db.fetch(query, student_id)
    return [dict(row) for row in rows]

# ==================== HEALTH CHECK ====================

@app.get("/", tags=["Health"])
async def root():
    """API health check"""
    return {
        "status": "healthy",
        "message": "Student Performance API is running",
        "version": "1.0.0"
    }

@app.get("/health", tags=["Health"])
async def health_check():
    """Database connection health check"""
    try:
        await db.fetchrow("SELECT 1")
        return {"status": "healthy", "database": "connected"}
    except Exception as e:
        raise HTTPException(status_code=503, detail=f"Database unhealthy: {str(e)}")

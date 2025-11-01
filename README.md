# Student Performance Prediction Pipeline

This repository contains a complete database-backed prediction pipeline for student academic performance, implementing both SQL and NoSQL databases, a FastAPI REST API, and a machine learning prediction system.

## Assignment: Formative 1 - Database & Prediction Pipeline

### Project Components

1. **Database Layer**: PostgreSQL + MongoDB dual-database system
2. **API Layer**: FastAPI REST API with full CRUD operations
3. **ML Pipeline**: Gradient Boosting prediction system
4. **Documentation**: ERD diagrams and comprehensive documentation

---

## Prerequisites

- Python 3.8 or higher
- PostgreSQL 9.5+ (with JSONB support)
- MongoDB 4.0+
- Git

---

## Installation

### 1. Clone the Repository

```bash
git clone <repository-url>
cd Database---Prediction-Pipeline-Group-12
```

### 2. Install Python Dependencies

```bash
# Install all dependencies
pip install -r requirements.txt

# Or install by component:
pip install -r api/requirements.txt
pip install -r database/requirements.txt
pip install -r scripts/requirements.txt
```

### 3. Set Up PostgreSQL Database

```bash
# Create database
createdb studentperformancedb

# Run schema creation
psql -d studentperformancedb -f database/schema.sql

# Run triggers and stored procedures
psql -d studentperformancedb -f database/triggers_procedures.sql
```

### 4. Set Up MongoDB

```bash
# Start MongoDB service (if not running)
sudo systemctl start mongod

# Run setup script
python database/mongodb_setup.py
```

### 5. Configure Environment Variables

Create a `.env` file in the root directory:

```bash
# PostgreSQL Configuration
PGHOST=localhost
PGPORT=5432
PGUSER=your_username
PGPASSWORD=your_password
PGDATABASE=studentperformancedb

# MongoDB Configuration
MONGO_URI=mongodb://localhost:27017/
MONGO_DB=studentperformancedb

# API Configuration
API_URL=http://localhost:8000
```

### 6. Train and Export ML Model

```bash
# Open the Jupyter notebook
jupyter notebook ml/summative_complete.ipynb

# Run all cells to train the model
# The last cell exports the model files to ml/models/
```

---

## Running the Application

### 1. Start the FastAPI Server

```bash
cd api
uvicorn app:app --reload --host 0.0.0.0 --port 8000
```

The API will be available at `http://localhost:8000`

- API Documentation: http://localhost:8000/docs
- Alternative Documentation: http://localhost:8000/redoc

### 2. Run the Prediction Pipeline

```bash
cd scripts
python predict_latest.py
```

This script will:
1. Fetch the latest student record via API
2. Load the trained ML model
3. Make a prediction
4. Display the results

---

## Project Structure

```
Database---Prediction-Pipeline-Group-12/
├── api/
│   ├── app.py              # FastAPI application with CRUD endpoints
│   ├── db.py               # Database connection pooling
│   ├── schemas.py          # Pydantic validation models
│   └── requirements.txt    # API dependencies
├── database/
│   ├── schema.sql          # PostgreSQL table definitions
│   ├── triggers_procedures.sql  # Stored procedures & triggers
│   ├── mongodb_setup.py    # MongoDB collection setup
│   └── requirements.txt    # Database dependencies
├── ml/
│   ├── summative_complete.ipynb  # Model training notebook
│   ├── models/             # Exported model files (created after training)
│   └── student/            # Dataset files
├── scripts/
│   ├── predict_latest.py   # Prediction pipeline script
│   └── requirements.txt    # Script dependencies
├── docs/                   # Documentation and ERD diagrams
└── requirements.txt        # All dependencies combined
```

---

## Database Schema

### PostgreSQL Tables

1. **students**: Core student information (student_id, school, sex, age, address)
2. **family_background**: Family context (parents' education, jobs, family size)
3. **academic_records**: Grade history (G1, G2, G3, absences, at_risk flag)
4. **school_info**: School-related factors (studytime, failures, activities)
5. **student_audit_log**: Audit trail for all student changes

### MongoDB Collections

Mirror structure of PostgreSQL with additional flexibility for nested documents.

---

## API Endpoints

### Students
- `POST /students` - Create new student
- `GET /students` - List all students
- `GET /students/{id}` - Get specific student
- `PUT /students/{id}` - Update student
- `DELETE /students/{id}` - Delete student
- `GET /students/latest/one` - Get most recent student (for predictions)

### Family Background
- `POST /family-background` - Create family record
- `GET /family-background` - List all records
- `GET /family-background/{student_id}` - Get by student
- `DELETE /family-background/{student_id}` - Delete record

### Academic Records
- `POST /academic-records` - Create academic record
- `GET /academic-records` - List all records (filter by at_risk)
- `GET /academic-records/{record_id}` - Get specific record
- `PUT /academic-records/{record_id}` - Update record
- `DELETE /academic-records/{record_id}` - Delete record

### School Info
- `POST /school-info` - Create school record
- `GET /school-info` - List all records
- `GET /school-info/{student_id}` - Get by student
- `DELETE /school-info/{student_id}` - Delete record

### Audit Logs
- `GET /audit-logs` - List all audit logs
- `GET /audit-logs/student/{student_id}` - Get logs for specific student

---

## Database Features

### Stored Procedures

1. **insert_complete_student()**: Atomically insert student across all tables
   ```sql
   SELECT insert_complete_student(
       'GP', 'F', 18, 'U', 'GT3', 'T', 4, 4, 'teacher', 'services',
       'course', 'mother', 2, 2, 1, 'yes', 'no', 'yes', 'yes', 'yes',
       'yes', 'no', 'yes', 'yes', 4, 3, 4, 1, 1, 3, 6, 5, 6, 10
   );
   ```

2. **update_at_risk_status()**: Batch update at-risk flags for all students
   ```sql
   CALL update_at_risk_status();
   ```

### Triggers

1. **audit_student_changes**: Logs all INSERT/UPDATE/DELETE on students table
2. **auto_update_at_risk**: Automatically calculates at_risk flag (G3 < 10)
3. **update_updated_at_column**: Maintains updated_at timestamps

---

## Machine Learning Model

- **Algorithm**: Gradient Boosting Classifier
- **Target**: Final grade (G3) prediction
- **Features**: 33 student attributes (demographics, family, school factors)
- **Files**:
  - `best_gb.pkl`: Trained model
  - `scaler.pkl`: Feature scaler
  - `metadata.json`: Model configuration and selected features

---

## Testing the System

### 1. Test Database Setup

```bash
# PostgreSQL
psql -d studentperformancedb -c "SELECT * FROM students LIMIT 5;"

# MongoDB
python -c "from database.mongodb_setup import get_all_students; print(get_all_students())"
```

### 2. Test API

```bash
# Health check
curl http://localhost:8000/health

# Create a student
curl -X POST http://localhost:8000/students \
  -H "Content-Type: application/json" \
  -d '{"school":"GP","sex":"F","age":18,"address":"U"}'
```

### 3. Test Prediction Pipeline

```bash
cd scripts
python predict_latest.py
```

---

## Assignment Requirements Checklist

### Task 1: Database Implementation
- [x] PostgreSQL schema with 5 tables
- [x] Primary keys and foreign keys
- [x] CHECK constraints for data validation
- [x] Indexes on frequently queried columns
- [x] At least 1 stored procedure (we have 2)
- [x] At least 1 trigger (we have 3)
- [x] MongoDB collections mirroring SQL structure
- [ ] ERD diagram (to be created manually)

### Task 2: API Development
- [x] FastAPI REST API
- [x] CRUD endpoints for all tables
- [x] Request/response validation with Pydantic
- [x] Async database operations
- [x] Error handling
- [x] API documentation (auto-generated)

### Task 3: Prediction Pipeline
- [x] Load trained ML model
- [x] Fetch data via API endpoints
- [x] Preprocess features
- [x] Make predictions
- [x] Output results

---

## Troubleshooting

### PostgreSQL Connection Issues
- Ensure PostgreSQL service is running: `sudo systemctl status postgresql`
- Check credentials in `.env` file
- Verify database exists: `psql -l`

### MongoDB Connection Issues
- Ensure MongoDB service is running: `sudo systemctl status mongod`
- Check connection string in `.env`
- Test connection: `mongo --eval "db.version()"`

### API Server Won't Start
- Check if port 8000 is already in use: `lsof -i :8000`
- Verify all dependencies installed: `pip list`
- Check environment variables loaded correctly

### Prediction Script Errors
- Ensure API server is running first
- Verify model files exist in `ml/models/`
- Check that at least one student exists in database

---

## Contributors

Group 12 - Database & Prediction Pipeline Project

Belyse NIYONSENGA

Charlotte Kariza

Thierry Shyaka

Jean Jacques JABO



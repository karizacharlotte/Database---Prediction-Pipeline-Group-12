# Database Setup

This directory contains all database-related files for both PostgreSQL and MongoDB implementations.

## Files

- `schema.sql`: PostgreSQL table definitions with constraints and indexes
- `triggers_procedures.sql`: Stored procedures and triggers for automation
- `mongodb_setup.py`: MongoDB collection setup and sample data insertion
- `requirements.txt`: Python dependencies for database setup

## PostgreSQL Setup

### Prerequisites

- PostgreSQL 9.5 or higher (for JSONB support)
- psql command-line tool

### Installation

#### Ubuntu/Debian
```bash
sudo apt update
sudo apt install postgresql postgresql-contrib
```

#### macOS
```bash
brew install postgresql
brew services start postgresql
```

#### Windows
Download and install from: https://www.postgresql.org/download/windows/

### Create Database

```bash
# Create the database
createdb studentperformancedb

# Or using psql
psql -U postgres
CREATE DATABASE studentperformancedb;
\q
```

### Run Schema Creation

```bash
# Navigate to database directory
cd database

# Create tables, constraints, and indexes
psql -d studentperformancedb -f schema.sql

# Create stored procedures and triggers
psql -d studentperformancedb -f triggers_procedures.sql
```

### Verify Setup

```bash
# Connect to database
psql -d studentperformancedb

# List all tables
\dt

# Should show: students, family_background, academic_records, school_info, student_audit_log

# View table structure
\d students

# Test stored procedure
SELECT insert_complete_student(
    'GP', 'F', 18, 'U', 'GT3', 'T', 4, 4, 'teacher', 'services',
    'course', 'mother', 2, 2, 1, 'yes', 'no', 'yes', 'yes', 'yes',
    'yes', 'no', 'yes', 'yes', 4, 3, 4, 1, 1, 3, 6, 5, 6, 10
);

# Verify trigger by checking audit log
SELECT * FROM student_audit_log;

# Exit
\q
```

## MongoDB Setup

### Prerequisites

- MongoDB 4.0 or higher
- pymongo Python package

### Installation

#### Ubuntu/Debian
```bash
# Import MongoDB public key
wget -qO - https://www.mongodb.org/static/pgp/server-6.0.asc | sudo apt-key add -

# Add MongoDB repository
echo "deb [ arch=amd64,arm64 ] https://repo.mongodb.org/apt/ubuntu focal/mongodb-org/6.0 multiverse" | sudo tee /etc/apt/sources.list.d/mongodb-org-6.0.list

# Install MongoDB
sudo apt update
sudo apt install -y mongodb-org

# Start MongoDB
sudo systemctl start mongod
sudo systemctl enable mongod
```

#### macOS
```bash
brew tap mongodb/brew
brew install mongodb-community
brew services start mongodb-community
```

#### Windows
Download and install from: https://www.mongodb.com/try/download/community

### Run MongoDB Setup

```bash
# Install Python dependencies
pip install -r requirements.txt

# Run setup script
python mongodb_setup.py
```

This will:
1. Create the `studentperformancedb` database
2. Create 5 collections with indexes
3. Insert sample student data

### Verify MongoDB Setup

```bash
# Connect to MongoDB
mongosh

# Switch to database
use studentperformancedb

# Show collections
show collections

# Should show: students, family_background, academic_records, school_info, predictions

# View sample data
db.students.find().pretty()

# Check indexes
db.students.getIndexes()

# Count documents
db.students.countDocuments()

# Exit
exit
```

## Database Schema

### Entity Relationship

```
students (1) ──< (1) family_background
    │
    ├──< (1) academic_records
    │
    └──< (1) school_info

students (1) ──< (*) student_audit_log
```

### Tables

#### 1. students
Core student information.

| Column | Type | Constraints |
|--------|------|-------------|
| student_id | SERIAL | PRIMARY KEY |
| school | VARCHAR(5) | NOT NULL |
| sex | CHAR(1) | CHECK (M or F) |
| age | INTEGER | CHECK (15-25) |
| address | CHAR(1) | CHECK (U or R) |

**Indexes**: student_id (PK), school, age

#### 2. family_background
Family context and socioeconomic factors.

| Column | Type | Constraints |
|--------|------|-------------|
| student_id | INTEGER | PRIMARY KEY, FOREIGN KEY |
| famsize | VARCHAR(5) | CHECK (LE3 or GT3) |
| pstatus | CHAR(1) | CHECK (T or A) |
| medu | INTEGER | CHECK (0-4) |
| fedu | INTEGER | CHECK (0-4) |
| mjob | VARCHAR(20) | - |
| fjob | VARCHAR(20) | - |

**Foreign Key**: student_id → students(student_id) ON DELETE CASCADE

#### 3. academic_records
Academic performance history.

| Column | Type | Constraints |
|--------|------|-------------|
| record_id | SERIAL | PRIMARY KEY |
| student_id | INTEGER | FOREIGN KEY |
| g1 | INTEGER | CHECK (0-20) |
| g2 | INTEGER | CHECK (0-20) |
| g3 | INTEGER | CHECK (0-20) |
| absences | INTEGER | CHECK (>= 0) |
| at_risk | BOOLEAN | Auto-calculated |

**Foreign Key**: student_id → students(student_id) ON DELETE CASCADE
**Indexes**: record_id (PK), student_id, at_risk

**Trigger**: Auto-calculates `at_risk = (g3 < 10)` on INSERT/UPDATE

#### 4. school_info
School-related factors and activities.

| Column | Type | Constraints |
|--------|------|-------------|
| student_id | INTEGER | PRIMARY KEY, FOREIGN KEY |
| reason | VARCHAR(20) | - |
| guardian | VARCHAR(20) | - |
| traveltime | INTEGER | CHECK (1-4) |
| studytime | INTEGER | CHECK (1-4) |
| failures | INTEGER | CHECK (0-4) |
| schoolsup | VARCHAR(5) | CHECK (yes or no) |
| famsup | VARCHAR(5) | CHECK (yes or no) |
| paid | VARCHAR(5) | CHECK (yes or no) |
| activities | VARCHAR(5) | CHECK (yes or no) |
| nursery | VARCHAR(5) | CHECK (yes or no) |
| higher | VARCHAR(5) | CHECK (yes or no) |
| internet | VARCHAR(5) | CHECK (yes or no) |
| romantic | VARCHAR(5) | CHECK (yes or no) |

**Foreign Key**: student_id → students(student_id) ON DELETE CASCADE

#### 5. student_audit_log
Audit trail for all student changes.

| Column | Type | Constraints |
|--------|------|-------------|
| log_id | SERIAL | PRIMARY KEY |
| student_id | INTEGER | - |
| action | VARCHAR(10) | INSERT/UPDATE/DELETE |
| old_data | JSONB | Previous values |
| new_data | JSONB | New values |
| changed_at | TIMESTAMP | Auto-set |

**Trigger**: Automatically populated on any students table change

## Stored Procedures

### 1. insert_complete_student()

Atomically insert a student across all related tables in a single transaction.

**Usage**:
```sql
SELECT insert_complete_student(
    p_school VARCHAR(5),
    p_sex CHAR(1),
    p_age INTEGER,
    p_address CHAR(1),
    -- Family info
    p_famsize VARCHAR(5),
    p_pstatus CHAR(1),
    p_medu INTEGER,
    p_fedu INTEGER,
    p_mjob VARCHAR(20),
    p_fjob VARCHAR(20),
    -- School info
    p_reason VARCHAR(20),
    p_guardian VARCHAR(20),
    p_traveltime INTEGER,
    p_studytime INTEGER,
    p_failures INTEGER,
    p_schoolsup VARCHAR(5),
    p_famsup VARCHAR(5),
    p_paid VARCHAR(5),
    p_activities VARCHAR(5),
    p_nursery VARCHAR(5),
    p_higher VARCHAR(5),
    p_internet VARCHAR(5),
    p_romantic VARCHAR(5),
    -- Academic info
    p_g1 INTEGER,
    p_g2 INTEGER,
    p_g3 INTEGER,
    p_absences INTEGER
);
```

**Returns**: The newly created student_id

**Example**:
```sql
SELECT insert_complete_student(
    'GP', 'F', 18, 'U',
    'GT3', 'T', 4, 4, 'teacher', 'services',
    'course', 'mother', 2, 2, 1, 'yes', 'no', 'yes', 'yes', 'yes',
    'yes', 'no', 'yes', 'yes', 4, 3, 4, 1, 1, 3, 6, 5, 6, 10
);
```

### 2. update_at_risk_status()

Batch update the `at_risk` flag for all academic records based on final grade (G3 < 10).

**Usage**:
```sql
CALL update_at_risk_status();
```

**Effect**: Updates `at_risk` column for all records in `academic_records` table.

## Triggers

### 1. audit_student_changes

**Table**: students
**Event**: AFTER INSERT, UPDATE, DELETE
**Function**: audit_student_changes()

**Purpose**: Automatically logs all changes to the students table in `student_audit_log`.

**Behavior**:
- INSERT: Logs new_data only
- UPDATE: Logs both old_data and new_data
- DELETE: Logs old_data only

**Example**:
```sql
-- Insert a student (trigger fires automatically)
INSERT INTO students (school, sex, age, address) VALUES ('GP', 'M', 19, 'U');

-- Check audit log
SELECT * FROM student_audit_log ORDER BY changed_at DESC LIMIT 1;
```

### 2. auto_update_at_risk

**Table**: academic_records
**Event**: BEFORE INSERT, UPDATE
**Function**: auto_update_at_risk()

**Purpose**: Automatically calculates and sets the `at_risk` flag based on final grade (G3).

**Logic**: `at_risk = (g3 < 10)`

**Example**:
```sql
-- Insert academic record (at_risk auto-calculated)
INSERT INTO academic_records (student_id, g1, g2, g3, absences)
VALUES (1, 8, 9, 8, 10);
-- at_risk will be set to TRUE automatically

-- Verify
SELECT student_id, g3, at_risk FROM academic_records WHERE student_id = 1;
```

### 3. update_updated_at_column

**Table**: students
**Event**: BEFORE UPDATE
**Function**: update_updated_at_column()

**Purpose**: Maintains accurate `updated_at` timestamp.

**Example**:
```sql
-- Update student
UPDATE students SET age = 20 WHERE student_id = 1;

-- Check timestamp
SELECT student_id, age, updated_at FROM students WHERE student_id = 1;
```

## Data Validation

### Constraints

The schema enforces data integrity through CHECK constraints:

- **Age**: Between 15 and 25
- **Grades (G1, G2, G3)**: Between 0 and 20
- **Education levels (Medu, Fedu)**: Between 0 and 4
- **Travel/Study time**: Between 1 and 4
- **Failures**: Between 0 and 4
- **Absences**: Greater than or equal to 0
- **Sex**: Must be 'M' or 'F'
- **Address**: Must be 'U' (urban) or 'R' (rural)
- **Yes/No fields**: Must be 'yes' or 'no'

### Foreign Key Cascades

All foreign keys use `ON DELETE CASCADE`:
- Deleting a student automatically deletes all related records
- Maintains referential integrity
- Prevents orphaned records

## MongoDB Collections

MongoDB mirrors the PostgreSQL structure but allows for more flexible schemas:

### Collections Created

1. **students**: Core student documents
2. **family_background**: Family information
3. **academic_records**: Grade history
4. **school_info**: School factors
5. **predictions**: ML prediction results

### Indexes

Each collection has indexes for efficient querying:
- students: student_id, school, age
- family_background: student_id
- academic_records: student_id, at_risk
- school_info: student_id
- predictions: student_id, timestamp

### Sample Document Structure

```json
{
  "_id": ObjectId("..."),
  "student_id": 1,
  "school": "GP",
  "sex": "F",
  "age": 18,
  "address": "U",
  "created_at": ISODate("2024-01-01T00:00:00Z")
}
```

## Maintenance

### Backup PostgreSQL

```bash
# Full database backup
pg_dump studentperformancedb > backup.sql

# Compressed backup
pg_dump studentperformancedb | gzip > backup.sql.gz

# Specific tables
pg_dump -t students -t academic_records studentperformancedb > tables_backup.sql
```

### Restore PostgreSQL

```bash
# Restore from backup
psql studentperformancedb < backup.sql

# From compressed
gunzip -c backup.sql.gz | psql studentperformancedb
```

### Backup MongoDB

```bash
# Full database backup
mongodump --db=studentperformancedb --out=/backup/

# Specific collection
mongodump --db=studentperformancedb --collection=students --out=/backup/
```

### Restore MongoDB

```bash
# Restore database
mongorestore --db=studentperformancedb /backup/studentperformancedb/

# Drop existing before restore
mongorestore --db=studentperformancedb --drop /backup/studentperformancedb/
```

## Troubleshooting

### PostgreSQL

**Connection refused**:
```bash
# Check if PostgreSQL is running
sudo systemctl status postgresql

# Start if not running
sudo systemctl start postgresql
```

**Permission denied**:
```bash
# Modify pg_hba.conf for local connections
sudo nano /etc/postgresql/*/main/pg_hba.conf

# Add or modify:
local   all   all   trust
```

**Database already exists**:
```bash
# Drop and recreate
dropdb studentperformancedb
createdb studentperformancedb
```

### MongoDB

**Connection refused**:
```bash
# Check if MongoDB is running
sudo systemctl status mongod

# Start if not running
sudo systemctl start mongod
```

**Authentication failed**:
```bash
# Connect without auth
mongosh --norc

# Create user
use admin
db.createUser({
  user: "admin",
  pwd: "password",
  roles: ["root"]
})
```

**Port already in use**:
```bash
# Find process on port 27017
sudo lsof -i :27017

# Kill the process
sudo kill -9 <PID>
```

## Performance Optimization

### PostgreSQL

```sql
-- Analyze tables for query planning
ANALYZE students;
ANALYZE academic_records;

-- Vacuum to reclaim space
VACUUM ANALYZE;

-- Check index usage
SELECT schemaname, tablename, indexname, idx_scan
FROM pg_stat_user_indexes
ORDER BY idx_scan;
```

### MongoDB

```javascript
// Check collection stats
db.students.stats()

// Check index usage
db.students.aggregate([{ $indexStats: {} }])

// Explain query plan
db.students.find({ school: "GP" }).explain("executionStats")
```

## Security Recommendations

1. **Use strong passwords** for database users
2. **Limit network access** via firewall rules
3. **Enable SSL/TLS** for connections
4. **Regular backups** with encryption
5. **Monitor logs** for suspicious activity
6. **Use parameterized queries** (already done in API)
7. **Principle of least privilege** for database users
8. **Regular updates** of database software

## Next Steps

After database setup:

1. Configure environment variables for API
2. Start the FastAPI server (`../api/`)
3. Run the prediction pipeline (`../scripts/`)
4. Create the ERD diagram for documentation

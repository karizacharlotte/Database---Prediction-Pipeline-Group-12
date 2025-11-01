# API - FastAPI Student Performance Service

This directory contains the FastAPI REST API for the Student Performance Prediction Pipeline.

## Files

- `app.py`: Main FastAPI application with all CRUD endpoints
- `db.py`: Async PostgreSQL connection pool manager
- `schemas.py`: Pydantic models for request/response validation
- `requirements.txt`: Python dependencies

## Setup

### 1. Install Dependencies

```bash
cd api
pip install -r requirements.txt
```

### 2. Configure Environment Variables

Set the following environment variables (or create a `.env` file in the root):

```bash
PGHOST=localhost
PGPORT=5432
PGUSER=your_username
PGPASSWORD=your_password
PGDATABASE=studentperformancedb
```

### 3. Ensure Database is Set Up

Make sure you've run the database schema scripts first:

```bash
cd ../database
psql -d studentperformancedb -f schema.sql
psql -d studentperformancedb -f triggers_procedures.sql
```

## Running the API

### Development Mode (with auto-reload)

```bash
uvicorn app:app --reload --host 0.0.0.0 --port 8000
```

### Production Mode

```bash
uvicorn app:app --host 0.0.0.0 --port 8000 --workers 4
```

## Accessing the API

- **Base URL**: http://localhost:8000
- **Interactive Docs (Swagger UI)**: http://localhost:8000/docs
- **Alternative Docs (ReDoc)**: http://localhost:8000/redoc
- **Health Check**: http://localhost:8000/health

## Endpoints Overview

### Health & Status
- `GET /` - Welcome message
- `GET /health` - Health check endpoint

### Students
- `POST /students` - Create a new student
- `GET /students` - List all students (with pagination)
- `GET /students/{student_id}` - Get specific student
- `PUT /students/{student_id}` - Update student information
- `DELETE /students/{student_id}` - Delete student
- `GET /students/latest/one` - Get most recent student (used by prediction script)

### Family Background
- `POST /family-background` - Create family background record
- `GET /family-background` - List all family records
- `GET /family-background/{student_id}` - Get family info for specific student
- `DELETE /family-background/{student_id}` - Delete family record

### Academic Records
- `POST /academic-records` - Create new academic record
- `GET /academic-records` - List all records (filter by `at_risk` parameter)
- `GET /academic-records/{record_id}` - Get specific record
- `PUT /academic-records/{record_id}` - Update academic record
- `DELETE /academic-records/{record_id}` - Delete record

### School Info
- `POST /school-info` - Create school information record
- `GET /school-info` - List all school records
- `GET /school-info/{student_id}` - Get school info for specific student
- `DELETE /school-info/{student_id}` - Delete school record

### Audit Logs
- `GET /audit-logs` - List all audit logs
- `GET /audit-logs/student/{student_id}` - Get audit logs for specific student

## Example API Calls

### Create a Complete Student Record

```bash
# 1. Create student
curl -X POST http://localhost:8000/students \
  -H "Content-Type: application/json" \
  -d '{
    "school": "GP",
    "sex": "F",
    "age": 18,
    "address": "U"
  }'

# Response: {"student_id": 1, "school": "GP", "sex": "F", "age": 18, "address": "U"}

# 2. Create family background
curl -X POST http://localhost:8000/family-background \
  -H "Content-Type: application/json" \
  -d '{
    "student_id": 1,
    "famsize": "GT3",
    "pstatus": "T",
    "medu": 4,
    "fedu": 4,
    "mjob": "teacher",
    "fjob": "services"
  }'

# 3. Create academic record
curl -X POST http://localhost:8000/academic-records \
  -H "Content-Type: application/json" \
  -d '{
    "student_id": 1,
    "g1": 15,
    "g2": 16,
    "g3": 17,
    "absences": 4
  }'

# 4. Create school info
curl -X POST http://localhost:8000/school-info \
  -H "Content-Type: application/json" \
  -d '{
    "student_id": 1,
    "reason": "course",
    "guardian": "mother",
    "traveltime": 2,
    "studytime": 3,
    "failures": 0,
    "schoolsup": "yes",
    "famsup": "yes",
    "paid": "no",
    "activities": "yes",
    "nursery": "yes",
    "higher": "yes",
    "internet": "yes",
    "romantic": "no"
  }'
```

### Query Students

```bash
# Get all students
curl http://localhost:8000/students

# Get specific student
curl http://localhost:8000/students/1

# Get latest student (for predictions)
curl http://localhost:8000/students/latest/one
```

### Query At-Risk Students

```bash
# Get all at-risk students (G3 < 10)
curl http://localhost:8000/academic-records?at_risk=true

# Get all students not at risk
curl http://localhost:8000/academic-records?at_risk=false
```

### Update Records

```bash
# Update student age
curl -X PUT http://localhost:8000/students/1 \
  -H "Content-Type: application/json" \
  -d '{"age": 19}'

# Update academic record
curl -X PUT http://localhost:8000/academic-records/1 \
  -H "Content-Type: application/json" \
  -d '{"g3": 18}'
```

### View Audit Logs

```bash
# Get all audit logs
curl http://localhost:8000/audit-logs

# Get audit logs for specific student
curl http://localhost:8000/audit-logs/student/1
```

## Response Formats

All responses are in JSON format.

### Success Response
```json
{
  "student_id": 1,
  "school": "GP",
  "sex": "F",
  "age": 18,
  "address": "U"
}
```

### Error Response
```json
{
  "detail": "Error message describing what went wrong"
}
```

### List Response
```json
[
  {"student_id": 1, "school": "GP", ...},
  {"student_id": 2, "school": "MS", ...}
]
```

## Database Connection Pool

The API uses asyncpg connection pooling for efficient database operations:

- Pool size: 10-100 connections
- Connections are created on startup and closed on shutdown
- All database operations are async for better performance

## Validation

Request validation is handled by Pydantic models in `schemas.py`:

- Age: 15-25 years
- Grades (G1, G2, G3): 0-20
- Sex: M or F
- Yes/No fields: "yes" or "no"
- Education levels (Medu, Fedu): 0-4
- And more...

Invalid requests return 422 Unprocessable Entity with detailed error messages.

## Error Handling

The API handles common errors:

- **404 Not Found**: Resource doesn't exist
- **422 Unprocessable Entity**: Validation error
- **500 Internal Server Error**: Database or server error

## CORS

CORS is enabled for all origins in development. For production, configure specific origins in `app.py`:

```python
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],  # Your frontend URL
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
```

## Testing

### Using Python requests

```python
import requests

# Health check
response = requests.get("http://localhost:8000/health")
print(response.json())

# Create student
student_data = {
    "school": "GP",
    "sex": "F",
    "age": 18,
    "address": "U"
}
response = requests.post("http://localhost:8000/students", json=student_data)
print(response.json())
```

### Using curl

```bash
# Test health endpoint
curl http://localhost:8000/health

# Test student creation with pretty output
curl -X POST http://localhost:8000/students \
  -H "Content-Type: application/json" \
  -d '{"school":"GP","sex":"F","age":18,"address":"U"}' \
  | python -m json.tool
```

## Troubleshooting

### Connection Pool Issues

If you see "too many connections" errors:

```python
# Adjust pool size in db.py
pool = await asyncpg.create_pool(
    min_size=5,   # Reduce minimum
    max_size=20,  # Reduce maximum
    ...
)
```

### Database Connection Refused

1. Check PostgreSQL is running: `sudo systemctl status postgresql`
2. Verify environment variables are set correctly
3. Test connection: `psql -h localhost -U your_user -d studentperformancedb`

### Import Errors

```bash
# Reinstall dependencies
pip install --upgrade -r requirements.txt
```

### Port Already in Use

```bash
# Find process using port 8000
lsof -i :8000

# Kill the process (use PID from above)
kill -9 <PID>

# Or use a different port
uvicorn app:app --port 8001
```

## Performance Considerations

- Use query parameters for filtering (e.g., `?at_risk=true`)
- Implement pagination for large datasets (skip/limit parameters ready in code)
- Use connection pooling (already configured)
- Consider caching for frequently accessed data
- Add indexes on foreign keys (already done in schema.sql)

## Security Notes

For production deployment:

1. Use environment variables for all secrets
2. Enable HTTPS/TLS
3. Restrict CORS origins
4. Implement authentication (JWT tokens)
5. Add rate limiting
6. Use prepared statements (already done with asyncpg)
7. Validate all input (already done with Pydantic)

## Future Enhancements

- [ ] Add authentication and authorization
- [ ] Implement pagination metadata (total count, pages)
- [ ] Add filtering and sorting on more endpoints
- [ ] Create batch operations endpoints
- [ ] Add WebSocket support for real-time updates
- [ ] Implement caching with Redis
- [ ] Add request logging and monitoring

#!/bin/bash

# Test Script for Student Performance Prediction Pipeline
# This script tests all major components to verify the implementation

set -e  # Exit on error

echo "=========================================="
echo "Student Performance Pipeline - Test Suite"
echo "=========================================="
echo ""

# Colors for output
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Test counter
TESTS_PASSED=0
TESTS_FAILED=0

# Function to print test results
test_result() {
    if [ $? -eq 0 ]; then
        echo -e "${GREEN}✓ PASS${NC}: $1"
        ((TESTS_PASSED++))
    else
        echo -e "${RED}✗ FAIL${NC}: $1"
        ((TESTS_FAILED++))
    fi
}

# Test 1: Check PostgreSQL connection
echo -e "${YELLOW}[1] Testing PostgreSQL connection...${NC}"
psql -d studentperformancedb -c "SELECT 1;" > /dev/null 2>&1
test_result "PostgreSQL connection"

# Test 2: Check if tables exist
echo -e "${YELLOW}[2] Testing PostgreSQL tables...${NC}"
TABLE_COUNT=$(psql -d studentperformancedb -t -c "SELECT COUNT(*) FROM information_schema.tables WHERE table_schema='public';" | xargs)
if [ "$TABLE_COUNT" -eq 5 ]; then
    echo -e "${GREEN}✓ PASS${NC}: All 5 tables exist"
    ((TESTS_PASSED++))
else
    echo -e "${RED}✗ FAIL${NC}: Expected 5 tables, found $TABLE_COUNT"
    ((TESTS_FAILED++))
fi

# Test 3: Check stored procedures
echo -e "${YELLOW}[3] Testing stored procedures...${NC}"
PROC_COUNT=$(psql -d studentperformancedb -t -c "SELECT COUNT(*) FROM pg_proc WHERE proname IN ('insert_complete_student', 'update_at_risk_status');" | xargs)
if [ "$PROC_COUNT" -ge 2 ]; then
    echo -e "${GREEN}✓ PASS${NC}: Stored procedures exist"
    ((TESTS_PASSED++))
else
    echo -e "${RED}✗ FAIL${NC}: Stored procedures not found"
    ((TESTS_FAILED++))
fi

# Test 4: Check triggers
echo -e "${YELLOW}[4] Testing triggers...${NC}"
TRIGGER_COUNT=$(psql -d studentperformancedb -t -c "SELECT COUNT(*) FROM pg_trigger WHERE tgname LIKE '%student%';" | xargs)
if [ "$TRIGGER_COUNT" -ge 3 ]; then
    echo -e "${GREEN}✓ PASS${NC}: Triggers exist"
    ((TESTS_PASSED++))
else
    echo -e "${RED}✗ FAIL${NC}: Triggers not found"
    ((TESTS_FAILED++))
fi

# Test 5: Check MongoDB connection
echo -e "${YELLOW}[5] Testing MongoDB connection...${NC}"
if command -v mongosh &> /dev/null; then
    mongosh --quiet --eval "db.version()" > /dev/null 2>&1
    test_result "MongoDB connection"
elif command -v mongo &> /dev/null; then
    mongo --quiet --eval "db.version()" > /dev/null 2>&1
    test_result "MongoDB connection"
else
    echo -e "${RED}✗ FAIL${NC}: MongoDB client not found"
    ((TESTS_FAILED++))
fi

# Test 6: Check MongoDB collections
echo -e "${YELLOW}[6] Testing MongoDB collections...${NC}"
if command -v mongosh &> /dev/null; then
    COLL_COUNT=$(mongosh --quiet --eval "use studentperformancedb; db.getCollectionNames().length" 2>/dev/null | tail -1)
elif command -v mongo &> /dev/null; then
    COLL_COUNT=$(mongo --quiet --eval "use studentperformancedb; db.getCollectionNames().length" 2>/dev/null | tail -1)
fi
if [ "$COLL_COUNT" -ge 4 ]; then
    echo -e "${GREEN}✓ PASS${NC}: MongoDB collections exist"
    ((TESTS_PASSED++))
else
    echo -e "${YELLOW}⚠ WARNING${NC}: MongoDB collections may need setup"
fi

# Test 7: Check Python dependencies
echo -e "${YELLOW}[7] Testing Python dependencies...${NC}"
python3 -c "import fastapi, asyncpg, pydantic, pymongo, pandas, sklearn, requests" 2>/dev/null
test_result "Python dependencies"

# Test 8: Check API files
echo -e "${YELLOW}[8] Testing API files...${NC}"
if [ -f "api/app.py" ] && [ -f "api/db.py" ] && [ -f "api/schemas.py" ]; then
    echo -e "${GREEN}✓ PASS${NC}: API files exist"
    ((TESTS_PASSED++))
else
    echo -e "${RED}✗ FAIL${NC}: API files missing"
    ((TESTS_FAILED++))
fi

# Test 9: Check prediction script
echo -e "${YELLOW}[9] Testing prediction script...${NC}"
if [ -f "scripts/predict_latest.py" ]; then
    echo -e "${GREEN}✓ PASS${NC}: Prediction script exists"
    ((TESTS_PASSED++))
else
    echo -e "${RED}✗ FAIL${NC}: Prediction script missing"
    ((TESTS_FAILED++))
fi

# Test 10: Check model files
echo -e "${YELLOW}[10] Testing model files...${NC}"
if [ -f "ml/models/best_gb.pkl" ] && [ -f "ml/models/scaler.pkl" ]; then
    echo -e "${GREEN}✓ PASS${NC}: Model files exist"
    ((TESTS_PASSED++))
else
    echo -e "${YELLOW}⚠ WARNING${NC}: Model files not found (run notebook to generate)"
fi

# Test 11: Test API (if running)
echo -e "${YELLOW}[11] Testing API server...${NC}"
if curl -s http://localhost:8000/health > /dev/null 2>&1; then
    echo -e "${GREEN}✓ PASS${NC}: API server is running"
    ((TESTS_PASSED++))
    
    # Test specific endpoints
    echo -e "${YELLOW}[12] Testing API endpoints...${NC}"
    
    # Test students endpoint
    STUDENTS_RESPONSE=$(curl -s http://localhost:8000/students)
    if [ $? -eq 0 ]; then
        echo -e "${GREEN}✓ PASS${NC}: GET /students endpoint"
        ((TESTS_PASSED++))
    else
        echo -e "${RED}✗ FAIL${NC}: GET /students endpoint"
        ((TESTS_FAILED++))
    fi
else
    echo -e "${YELLOW}⚠ WARNING${NC}: API server not running (start with: cd api && uvicorn app:app --reload)"
fi

# Test 12: Check documentation
echo -e "${YELLOW}[13] Testing documentation...${NC}"
if [ -f "README.md" ] && [ -f "api/README.md" ] && [ -f "database/README.md" ] && [ -f "scripts/README.md" ]; then
    echo -e "${GREEN}✓ PASS${NC}: All README files exist"
    ((TESTS_PASSED++))
else
    echo -e "${RED}✗ FAIL${NC}: Some README files missing"
    ((TESTS_FAILED++))
fi

# Summary
echo ""
echo "=========================================="
echo "Test Results Summary"
echo "=========================================="
echo -e "Tests Passed: ${GREEN}$TESTS_PASSED${NC}"
echo -e "Tests Failed: ${RED}$TESTS_FAILED${NC}"
echo ""

if [ $TESTS_FAILED -eq 0 ]; then
    echo -e "${GREEN}🎉 All critical tests passed!${NC}"
    echo ""
    echo "Your system is ready for:"
    echo "  1. Training the model (run the notebook)"
    echo "  2. Starting the API server"
    echo "  3. Running predictions"
    exit 0
else
    echo -e "${RED}⚠ Some tests failed. Please check the output above.${NC}"
    echo ""
    echo "Common fixes:"
    echo "  - Run './setup.sh' if you haven't already"
    echo "  - Check database credentials in .env file"
    echo "  - Install missing dependencies: pip install -r requirements.txt"
    exit 1
fi

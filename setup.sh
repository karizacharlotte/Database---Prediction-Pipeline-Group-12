#!/bin/bash

# Student Performance Prediction Pipeline - Setup Script
# This script automates the initial setup process

set -e  # Exit on error

echo "=================================="
echo "Student Performance Pipeline Setup"
echo "=================================="
echo ""

# Colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# Check if PostgreSQL is installed
echo -e "${YELLOW}[1/8] Checking PostgreSQL...${NC}"
if command -v psql &> /dev/null; then
    echo -e "${GREEN}✓ PostgreSQL is installed${NC}"
else
    echo -e "${RED}✗ PostgreSQL is not installed${NC}"
    echo "Please install PostgreSQL: sudo apt install postgresql postgresql-contrib"
    exit 1
fi

# Check if MongoDB is installed
echo -e "${YELLOW}[2/8] Checking MongoDB...${NC}"
if command -v mongosh &> /dev/null || command -v mongo &> /dev/null; then
    echo -e "${GREEN}✓ MongoDB is installed${NC}"
else
    echo -e "${RED}✗ MongoDB is not installed${NC}"
    echo "Please install MongoDB: https://www.mongodb.com/docs/manual/installation/"
    exit 1
fi

# Check Python version
echo -e "${YELLOW}[3/8] Checking Python version...${NC}"
PYTHON_VERSION=$(python3 --version 2>&1 | awk '{print $2}')
REQUIRED_VERSION="3.8"
if [ "$(printf '%s\n' "$REQUIRED_VERSION" "$PYTHON_VERSION" | sort -V | head -n1)" = "$REQUIRED_VERSION" ]; then
    echo -e "${GREEN}✓ Python $PYTHON_VERSION is installed${NC}"
else
    echo -e "${RED}✗ Python 3.8+ is required (found $PYTHON_VERSION)${NC}"
    exit 1
fi

# Install Python dependencies
echo -e "${YELLOW}[4/8] Installing Python dependencies...${NC}"
pip install -r requirements.txt
echo -e "${GREEN}✓ Python packages installed${NC}"

# Set up environment variables
echo -e "${YELLOW}[5/8] Setting up environment variables...${NC}"
if [ ! -f .env ]; then
    cp .env.example .env
    echo -e "${GREEN}✓ Created .env file from template${NC}"
    echo -e "${YELLOW}⚠ Please edit .env with your database credentials${NC}"
else
    echo -e "${YELLOW}ℹ .env file already exists${NC}"
fi

# Create PostgreSQL database
echo -e "${YELLOW}[6/8] Setting up PostgreSQL database...${NC}"
read -p "Create PostgreSQL database 'studentperformancedb'? (y/n) " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
    createdb studentperformancedb 2>/dev/null || echo "Database might already exist"
    
    # Run schema
    psql -d studentperformancedb -f database/schema.sql
    echo -e "${GREEN}✓ Schema created${NC}"
    
    # Run triggers and procedures
    psql -d studentperformancedb -f database/triggers_procedures.sql
    echo -e "${GREEN}✓ Triggers and stored procedures created${NC}"
else
    echo -e "${YELLOW}ℹ Skipping PostgreSQL setup${NC}"
fi

# Set up MongoDB
echo -e "${YELLOW}[7/8] Setting up MongoDB...${NC}"
read -p "Set up MongoDB collections? (y/n) " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
    python3 database/mongodb_setup.py
    echo -e "${GREEN}✓ MongoDB collections created${NC}"
else
    echo -e "${YELLOW}ℹ Skipping MongoDB setup${NC}"
fi

# Create models directory
echo -e "${YELLOW}[8/8] Creating models directory...${NC}"
mkdir -p ml/models
echo -e "${GREEN}✓ Models directory created${NC}"

echo ""
echo -e "${GREEN}=================================="
echo "Setup Complete!"
echo "==================================${NC}"
echo ""
echo "Next steps:"
echo "1. Edit .env file with your database credentials"
echo "2. Run the Jupyter notebook: jupyter notebook ml/summative_complete.ipynb"
echo "3. Execute all cells to train and export the model"
echo "4. Start the API server: cd api && uvicorn app:app --reload"
echo "5. Run predictions: cd scripts && python predict_latest.py"
echo ""
echo "For detailed instructions, see README.md"
echo ""

"""
MongoDB Collections Setup and Data Migration
Creates MongoDB collections mirroring the relational database structure
"""
import os
from pymongo import MongoClient, ASCENDING
from datetime import datetime

# MongoDB connection
MONGO_URI = os.environ.get('MONGO_URI', 'mongodb://localhost:27017/')
MONGO_DB = os.environ.get('MONGO_DB', 'studentperformancedb')

def get_mongo_client():
    """Get MongoDB client"""
    return MongoClient(MONGO_URI)

def setup_collections():
    """Create MongoDB collections with indexes"""
    client = get_mongo_client()
    db = client[MONGO_DB]
    
    # Create collections
    collections_config = {
        'students': [
            ('student_id', ASCENDING),
            ('school', ASCENDING),
            ('sex', ASCENDING)
        ],
        'family_background': [
            ('family_id', ASCENDING),
            ('student_id', ASCENDING)
        ],
        'academic_records': [
            ('record_id', ASCENDING),
            ('student_id', ASCENDING),
            ('at_risk', ASCENDING)
        ],
        'school_info': [
            ('school_info_id', ASCENDING),
            ('student_id', ASCENDING)
        ],
        'audit_log': [
            ('log_id', ASCENDING),
            ('student_id', ASCENDING),
            ('action', ASCENDING),
            ('changed_at', ASCENDING)
        ]
    }
    
    for collection_name, indexes in collections_config.items():
        # Create collection if doesn't exist
        if collection_name not in db.list_collection_names():
            db.create_collection(collection_name)
            print(f"✓ Created collection: {collection_name}")
        
        # Create indexes
        collection = db[collection_name]
        for field, order in indexes:
            collection.create_index([(field, order)])
            print(f"  ✓ Created index on {collection_name}.{field}")
    
    client.close()
    print("\n✅ MongoDB collections setup complete!")

def insert_sample_student():
    """Insert a sample student document"""
    client = get_mongo_client()
    db = client[MONGO_DB]
    
    # Sample student document
    student = {
        'student_id': 1,
        'name': 'Maria Santos',
        'age': 17,
        'sex': 'F',
        'address': 'U',
        'famsize': 'GT3',
        'pstatus': 'T',
        'school': 'GP',
        'created_at': datetime.now(),
        'updated_at': datetime.now()
    }
    
    family = {
        'family_id': 1,
        'student_id': 1,
        'medu': 4,
        'fedu': 4,
        'mjob': 'teacher',
        'fjob': 'teacher',
        'reason': 'reputation',
        'guardian': 'mother',
        'traveltime': 2,
        'famrel': 4,
        'created_at': datetime.now()
    }
    
    academic = {
        'record_id': 1,
        'student_id': 1,
        'studytime': 2,
        'failures': 0,
        'schoolsup': True,
        'famsup': False,
        'paid': False,
        'activities': False,
        'nursery': True,
        'higher': True,
        'internet': False,
        'romantic': False,
        'freetime': 3,
        'goout': 4,
        'dalc': 1,
        'walc': 1,
        'health': 3,
        'absences': 4,
        'g1': 5,
        'g2': 6,
        'g3': 6,
        'at_risk': True,  # G3 < 10
        'created_at': datetime.now()
    }
    
    school_info = {
        'school_info_id': 1,
        'student_id': 1,
        'school_name': 'GP',
        'school_support': True,
        'family_support': False,
        'paid_classes': False,
        'activities': False,
        'nursery': True,
        'higher_ed_aspiration': True,
        'internet_access': False,
        'romantic_relationship': False,
        'created_at': datetime.now()
    }
    
    # Insert documents
    db.students.insert_one(student)
    db.family_background.insert_one(family)
    db.academic_records.insert_one(academic)
    db.school_info.insert_one(school_info)
    
    client.close()
    print("\n✅ Sample student data inserted into MongoDB!")

def get_all_students():
    """Retrieve all students from MongoDB"""
    client = get_mongo_client()
    db = client[MONGO_DB]
    
    students = list(db.students.find({}, {'_id': 0}))
    client.close()
    
    return students

if __name__ == '__main__':
    print("Setting up MongoDB collections...")
    setup_collections()
    
    print("\nInserting sample data...")
    insert_sample_student()
    
    print("\nVerifying data...")
    students = get_all_students()
    print(f"Found {len(students)} students in MongoDB")
    if students:
        print("\nSample student:")
        print(students[0])

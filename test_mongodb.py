#!/usr/bin/env python3
"""
Test MongoDB connection and basic operations
"""
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from api import mongodb

def test_mongodb_connection():
    """Test MongoDB connection"""
    print("="*60)
    print("TESTING MONGODB CONNECTION")
    print("="*60)
    
    try:
        # Connect to MongoDB
        db = mongodb.connect()
        print("✓ Successfully connected to MongoDB")
        print(f"✓ Database: {db.name}")
        
        # List collections
        collections = db.list_collection_names()
        print(f"✓ Collections: {collections if collections else 'None (will be created on first insert)'}")
        
        return True
        
    except Exception as e:
        print(f"❌ Failed to connect to MongoDB: {e}")
        print("\nMake sure MongoDB is running:")
        print("  sudo systemctl start mongod")
        return False

def test_basic_operations():
    """Test basic CRUD operations"""
    print("\n" + "="*60)
    print("TESTING BASIC CRUD OPERATIONS")
    print("="*60)
    
    try:
        # Test 1: Insert a prediction
        print("\n1. Testing prediction insert...")
        prediction_id = mongodb.insert_prediction(
            student_id="test-student-123",
            prediction_data={
                "predicted_label": True,
                "probability": 0.85,
                "confidence": 85.0,
                "model_name": "TestModel",
                "model_version": "1.0",
                "features_used": ["age", "absences", "G1"],
                "feature_values": {"age": 18, "absences": 5, "G1": 12},
                "metadata": {"test": True}
            }
        )
        print(f"✓ Prediction inserted with ID: {prediction_id}")
        
        # Test 2: Retrieve prediction history
        print("\n2. Testing prediction retrieval...")
        history = mongodb.get_prediction_history("test-student-123", limit=5)
        print(f"✓ Retrieved {len(history)} prediction(s)")
        if history:
            print(f"   Latest prediction: {history[0]['predicted_label']} (probability: {history[0]['probability']:.2f})")
        
        # Test 3: Insert activity log
        print("\n3. Testing activity log insert...")
        log_id = mongodb.insert_activity_log(
            student_id="test-student-123",
            action_type="test",
            description="Testing MongoDB operations",
            metadata={"test_run": True}
        )
        print(f"✓ Activity log inserted with ID: {log_id}")
        
        # Test 4: Get activity logs
        print("\n4. Testing activity log retrieval...")
        logs = mongodb.get_activity_logs(student_id="test-student-123", limit=5)
        print(f"✓ Retrieved {len(logs)} activity log(s)")
        
        # Test 5: Upsert student document
        print("\n5. Testing student document upsert...")
        success = mongodb.upsert_student_document(
            student_id="test-student-123",
            student_data={
                "age": 18,
                "sex": "F",
                "school": "GP",
                "absences": 5,
                "G1": 12,
                "G2": 13,
                "G3": 14,
                "custom_field": "test_value"
            }
        )
        print(f"✓ Student document upserted")
        
        # Test 6: Retrieve student document
        print("\n6. Testing student document retrieval...")
        student_doc = mongodb.get_student_document("test-student-123")
        if student_doc:
            print(f"✓ Student document retrieved")
            print(f"   Age: {student_doc.get('age')}, School: {student_doc.get('school')}")
        
        # Test 7: Get statistics
        print("\n7. Testing prediction statistics...")
        stats = mongodb.get_prediction_statistics()
        print(f"✓ Statistics retrieved")
        print(f"   Total predictions: {stats['total_predictions']}")
        print(f"   By label: {stats['by_label']}")
        
        # Test 8: Get collections info
        print("\n8. Testing collections info...")
        info = mongodb.get_collections_info()
        print(f"✓ Collections info retrieved:")
        for coll_name, coll_info in info.items():
            print(f"   {coll_name}: {coll_info['document_count']} documents")
        
        print("\n" + "="*60)
        print("✅ ALL TESTS PASSED!")
        print("="*60)
        return True
        
    except Exception as e:
        print(f"\n❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def cleanup_test_data():
    """Clean up test data"""
    print("\n" + "="*60)
    print("CLEANING UP TEST DATA")
    print("="*60)
    
    try:
        db = mongodb.get_db()
        
        # Delete test predictions
        result = db.prediction_history.delete_many({"student_id": "test-student-123"})
        print(f"✓ Deleted {result.deleted_count} test prediction(s)")
        
        # Delete test logs
        result = db.activity_logs.delete_many({"student_id": "test-student-123"})
        print(f"✓ Deleted {result.deleted_count} test activity log(s)")
        
        # Delete test student document
        result = db.student_documents.delete_one({"student_id": "test-student-123"})
        print(f"✓ Deleted {result.deleted_count} test student document(s)")
        
        print("✓ Cleanup complete")
        
    except Exception as e:
        print(f"⚠ Cleanup failed: {e}")

if __name__ == '__main__':
    # Test connection
    if not test_mongodb_connection():
        print("\nPlease install and start MongoDB:")
        print("  Ubuntu/Debian: sudo apt install mongodb")
        print("  macOS: brew install mongodb-community")
        print("  Start: sudo systemctl start mongod")
        sys.exit(1)
    
    # Test operations
    success = test_basic_operations()
    
    # Cleanup
    cleanup_test_data()
    
    # Close connection
    mongodb.close()
    
    if success:
        print("\n🎉 MongoDB is working correctly!")
        sys.exit(0)
    else:
        sys.exit(1)

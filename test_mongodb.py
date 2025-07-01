"""
MongoDB Connection Test Script
Run this script to test your MongoDB Atlas connection before running the main app.
"""

import os
from pymongo import MongoClient
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

def test_mongodb_connection():
    """Test MongoDB Atlas connection"""
    try:
        # Get password from environment or use placeholder
        mongodb_password = os.getenv('MONGODB_PASSWORD', '<db_password>')
        
        if mongodb_password == '<db_password>':
            print("⚠️  Warning: MONGODB_PASSWORD environment variable not set!")
            print("📝 To set it:")
            print("   1. Create a .env file from .env.example")
            print("   2. Replace <db_password> with your actual MongoDB password")
            print("   3. Or set environment variable: set MONGODB_PASSWORD=your_password")
            print()
            
        # Construct MongoDB URI
        mongo_uri = f'__mongodburl__'
        
        print("🔄 Testing MongoDB connection...")
        
        # Create client and test connection
        client = MongoClient(mongo_uri)
        
        # Test connection with ping
        result = client.admin.command('ping')
        
        if result.get('ok') == 1:
            print("✅ MongoDB connection successful!")
            
            # Test database access
            db = client['license_verification_db']
            collections = db.list_collection_names()
            
            print(f"📊 Database: license_verification_db")
            print(f"📋 Collections: {collections if collections else 'No collections found (this is normal for new databases)'}")
            
            # Test basic operations
            test_collection = db['connection_test']
            test_doc = {'test': True, 'timestamp': 'connection_test'}
            
            # Insert test document
            result = test_collection.insert_one(test_doc)
            print(f"📝 Test document inserted with ID: {result.inserted_id}")
            
            # Read test document
            doc = test_collection.find_one({'_id': result.inserted_id})
            if doc:
                print("📖 Test document read successfully")
                
            # Clean up test document
            test_collection.delete_one({'_id': result.inserted_id})
            print("🗑️  Test document cleaned up")
            
            print("\n🎉 All MongoDB operations successful!")
            print("✨ Your Flask app should be able to connect to MongoDB Atlas")
            
        else:
            print("❌ MongoDB ping failed")
            
    except Exception as e:
        print(f"❌ MongoDB connection failed: {e}")
        print("\n🔧 Troubleshooting tips:")
        print("   1. Check your internet connection")
        print("   2. Verify your MongoDB Atlas cluster is running")
        print("   3. Confirm your username 'ishan' is correct")
        print("   4. Make sure your password is correct")
        print("   5. Check if your IP address is whitelisted in MongoDB Atlas")
        print("   6. Verify the cluster name 'website' is correct")
        
    finally:
        try:
            client.close()
            print("🔌 Connection closed")
        except:
            pass

if __name__ == "__main__":
    print("🚀 MongoDB Atlas Connection Test")
    print("=" * 40)
    test_mongodb_connection()

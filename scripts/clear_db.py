#!/usr/bin/env python3
"""
Clear script for Interim App Database
Removes all data from the database collections
"""

import sys
import os

# Add the app directory to the path
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from app import create_app
from app.database import get_db

def clear_collection(collection_name):
    """Clear a specific collection"""
    try:
        db = get_db()
        collection = db[collection_name]
        result = collection.delete_many({})
        print(f"   ✅ Cleared {collection_name}: {result.deleted_count} documents deleted")
        return result.deleted_count
    except Exception as e:
        print(f"   ❌ Error clearing {collection_name}: {str(e)}")
        return 0

def get_collection_stats():
    """Get statistics before clearing"""
    try:
        db = get_db()
        collections = ['users', 'companies', 'jobs', 'applications']
        stats = {}
        
        for collection_name in collections:
            count = db[collection_name].count_documents({})
            stats[collection_name] = count
        
        return stats
    except Exception as e:
        print(f"❌ Error getting collection stats: {str(e)}")
        return {}

def confirm_deletion():
    """Ask user for confirmation"""
    print("⚠️  WARNING: This will delete ALL data from the database!")
    print("   - All users will be removed")
    print("   - All companies will be removed") 
    print("   - All jobs will be removed")
    print("   - All applications will be removed")
    print()
    
    while True:
        response = input("Are you sure you want to continue? (yes/no): ").lower().strip()
        if response in ['yes', 'y']:
            return True
        elif response in ['no', 'n']:
            return False
        else:
            print("Please enter 'yes' or 'no'")

def main():
    """Main clearing function"""
    print("🗑️  Database Clear Script")
    print("=" * 50)
    
    # Create Flask app context
    app = create_app()
    
    with app.app_context():
        try:
            # Get current stats
            print("📊 Current database statistics:")
            stats = get_collection_stats()
            total_documents = 0
            
            for collection_name, count in stats.items():
                print(f"   📄 {collection_name}: {count} documents")
                total_documents += count
            
            print(f"   📄 Total: {total_documents} documents")
            print()
            
            if total_documents == 0:
                print("✅ Database is already empty!")
                return
            
            # Ask for confirmation
            if not confirm_deletion():
                print("❌ Operation cancelled by user.")
                return
            
            print("\n🗑️  Clearing database...")
            
            # Clear collections in order (to respect relationships)
            collections_to_clear = [
                'applications',  # Clear applications first (references users and jobs)
                'jobs',         # Clear jobs second (references companies) 
                'users',        # Clear users third
                'companies'     # Clear companies last
            ]
            
            total_deleted = 0
            for collection_name in collections_to_clear:
                deleted_count = clear_collection(collection_name)
                total_deleted += deleted_count
            
            print("\n" + "=" * 50)
            print("📊 Clearing Summary:")
            print(f"   🗑️  Total documents deleted: {total_deleted}")
            print("✅ Database cleared successfully!")
            print("\n💡 You can now run 'make seed' to populate with fresh data.")
            
        except Exception as e:
            print(f"\n❌ Error during clearing: {str(e)}")
            sys.exit(1)

def clear_specific_collection(collection_name):
    """Clear a specific collection (utility function)"""
    print(f"🗑️  Clearing {collection_name} collection...")
    
    app = create_app()
    with app.app_context():
        try:
            deleted_count = clear_collection(collection_name)
            print(f"✅ {collection_name} collection cleared: {deleted_count} documents deleted")
        except Exception as e:
            print(f"❌ Error clearing {collection_name}: {str(e)}")

if __name__ == "__main__":
    # Check if specific collection is requested
    if len(sys.argv) > 1:
        collection_name = sys.argv[1]
        valid_collections = ['users', 'companies', 'jobs', 'applications']
        
        if collection_name in valid_collections:
            clear_specific_collection(collection_name)
        else:
            print(f"❌ Invalid collection name: {collection_name}")
            print(f"Valid collections: {', '.join(valid_collections)}")
            print("Usage: python clear_db.py [collection_name]")
            sys.exit(1)
    else:
        main()
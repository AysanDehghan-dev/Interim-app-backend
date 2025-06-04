from pymongo import MongoClient
from flask import current_app, g
import os

def get_db():
    """Get database connection"""
    if 'db' not in g:
        client = MongoClient(current_app.config['MONGODB_URL'])
        g.db = client[current_app.config['MONGODB_DB']]
        g.client = client
    return g.db

def close_db(e=None):
    """Close database connection"""
    client = g.pop('client', None)
    if client is not None:
        client.close()

def init_db(app):
    """Initialize database with app"""
    app.teardown_appcontext(close_db)
    
    # Create indexes for better performance
    with app.app_context():
        db = get_db()
        
        # Users collection indexes
        db.users.create_index("email", unique=True)
        db.users.create_index("type")  # user type (user/company)
        
        # Companies collection indexes  
        db.companies.create_index("email", unique=True)
        db.companies.create_index("nom")
        
        # Jobs collection indexes
        db.jobs.create_index("company_id")
        db.jobs.create_index("titre")
        db.jobs.create_index("date_creation")
        db.jobs.create_index("actif")
        
        # Applications collection indexes
        db.applications.create_index("user_id")
        db.applications.create_index("job_id")
        db.applications.create_index("company_id")
        db.applications.create_index([("user_id", 1), ("job_id", 1)], unique=True)  # Prevent duplicate applications
        db.applications.create_index("date_candidature")

# Database helper functions
def get_collection(collection_name):
    """Get a specific collection"""
    db = get_db()
    return db[collection_name]

def insert_document(collection_name, document):
    """Insert a document into collection"""
    collection = get_collection(collection_name)
    result = collection.insert_one(document)
    return result.inserted_id

def find_document(collection_name, query, projection=None):
    """Find a single document"""
    collection = get_collection(collection_name)
    return collection.find_one(query, projection)

def find_documents(collection_name, query=None, projection=None, limit=None, skip=None, sort=None):
    """Find multiple documents"""
    collection = get_collection(collection_name)
    query = query or {}
    
    cursor = collection.find(query, projection)
    
    if sort:
        cursor = cursor.sort(sort)
    if skip:
        cursor = cursor.skip(skip)
    if limit:
        cursor = cursor.limit(limit)
        
    return list(cursor)

def update_document(collection_name, query, update):
    """Update a document"""
    collection = get_collection(collection_name)
    result = collection.update_one(query, update)
    return result.modified_count > 0

def delete_document(collection_name, query):
    """Delete a document"""
    collection = get_collection(collection_name)
    result = collection.delete_one(query)
    return result.deleted_count > 0

def count_documents(collection_name, query=None):
    """Count documents in collection"""
    collection = get_collection(collection_name)
    query = query or {}
    return collection.count_documents(query)
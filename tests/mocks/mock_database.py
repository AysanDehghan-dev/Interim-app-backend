"""
Mock database layer for testing without MongoDB dependency
Used in CI/CD environments where MongoDB is not available
"""

import os
from datetime import datetime
from bson import ObjectId
from typing import Dict, List, Any, Optional

class MockDatabase:
    """Mock database that simulates MongoDB operations in memory"""
    
    def __init__(self):
        self.collections = {
            'users': [],
            'companies': [],
            'jobs': [],
            'applications': []
        }
        self.indexes = {}
        self._id_counter = 1
    
    def _generate_objectid(self) -> ObjectId:
        """Generate a fake ObjectId for testing"""
        # Create a valid ObjectId using counter
        hex_string = f"{self._id_counter:024d}"
        self._id_counter += 1
        return ObjectId(hex_string[:24])
    
    def _find_by_id(self, collection_name: str, doc_id: str) -> Optional[Dict]:
        """Find document by ID in collection"""
        try:
            target_id = ObjectId(doc_id) if isinstance(doc_id, str) else doc_id
            for doc in self.collections[collection_name]:
                if doc.get('_id') == target_id:
                    return doc
        except:
            pass
        return None
    
    def insert_one(self, collection_name: str, document: Dict) -> ObjectId:
        """Mock insert_one operation"""
        doc = document.copy()
        doc['_id'] = self._generate_objectid()
        self.collections[collection_name].append(doc)
        return doc['_id']
    
    def find_one(self, collection_name: str, query: Dict, projection: Optional[Dict] = None) -> Optional[Dict]:
        """Mock find_one operation"""
        collection = self.collections[collection_name]
        
        for doc in collection:
            if self._matches_query(doc, query):
                result = doc.copy() if doc else None
                if result and projection:
                    result = self._apply_projection(result, projection)
                return result
        return None
    
    def find(self, collection_name: str, query: Optional[Dict] = None, 
             projection: Optional[Dict] = None, limit: Optional[int] = None, 
             skip: Optional[int] = None, sort: Optional[List] = None) -> List[Dict]:
        """Mock find operation"""
        collection = self.collections[collection_name]
        query = query or {}
        
        # Filter documents
        results = []
        for doc in collection:
            if self._matches_query(doc, query):
                result = doc.copy()
                if projection:
                    result = self._apply_projection(result, projection)
                results.append(result)
        
        # Apply sorting
        if sort:
            for field, direction in reversed(sort):
                results.sort(key=lambda x: x.get(field, ''), reverse=(direction == -1))
        
        # Apply skip and limit
        if skip:
            results = results[skip:]
        if limit:
            results = results[:limit]
        
        return results
    
    def update_one(self, collection_name: str, query: Dict, update: Dict) -> bool:
        """Mock update_one operation"""
        collection = self.collections[collection_name]
        
        for doc in collection:
            if self._matches_query(doc, query):
                if '$set' in update:
                    doc.update(update['$set'])
                return True
        return False
    
    def delete_one(self, collection_name: str, query: Dict) -> bool:
        """Mock delete_one operation"""
        collection = self.collections[collection_name]
        
        for i, doc in enumerate(collection):
            if self._matches_query(doc, query):
                del collection[i]
                return True
        return False
    
    def count_documents(self, collection_name: str, query: Optional[Dict] = None) -> int:
        """Mock count_documents operation"""
        query = query or {}
        count = 0
        for doc in self.collections[collection_name]:
            if self._matches_query(doc, query):
                count += 1
        return count
    
    def create_index(self, collection_name: str, index_spec: Any, unique: bool = False):
        """Mock index creation"""
        if collection_name not in self.indexes:
            self.indexes[collection_name] = []
        self.indexes[collection_name].append({
            'spec': index_spec,
            'unique': unique
        })
    
    def drop(self, collection_name: str):
        """Mock collection drop"""
        self.collections[collection_name] = []
    
    def _matches_query(self, doc: Dict, query: Dict) -> bool:
        """Check if document matches query"""
        if not query:
            return True
        
        for key, value in query.items():
            if key == '_id':
                # Handle ObjectId comparison
                doc_id = doc.get('_id')
                if isinstance(value, str):
                    try:
                        value = ObjectId(value)
                    except:
                        pass
                if doc_id != value:
                    return False
            elif key.startswith('$'):
                # Handle MongoDB operators
                if key == '$or':
                    if not any(self._matches_query(doc, sub_query) for sub_query in value):
                        return False
                # Add more operators as needed
            elif isinstance(value, dict) and '$regex' in value:
                # Handle regex queries
                import re
                pattern = value['$regex']
                flags = re.IGNORECASE if value.get('$options') == 'i' else 0
                doc_value = str(doc.get(key, ''))
                if not re.search(pattern, doc_value, flags):
                    return False
            elif isinstance(value, dict) and '$in' in value:
                # Handle $in operator
                if doc.get(key) not in value['$in']:
                    return False
            else:
                # Simple equality check
                if doc.get(key) != value:
                    return False
        return True
    
    def _apply_projection(self, doc: Dict, projection: Dict) -> Dict:
        """Apply projection to document"""
        if not projection:
            return doc
        
        # Handle exclusion projections (e.g., {'password': 0})
        if all(v == 0 for v in projection.values()):
            result = doc.copy()
            for key in projection:
                result.pop(key, None)
            return result
        
        # Handle inclusion projections (e.g., {'name': 1, 'email': 1})
        result = {}
        for key, include in projection.items():
            if include and key in doc:
                result[key] = doc[key]
        
        # Always include _id unless explicitly excluded
        if '_id' not in projection or projection.get('_id') != 0:
            result['_id'] = doc.get('_id')
        
        return result


# Global mock database instance
_mock_db = MockDatabase()

# Mock functions that replace the real database functions
def mock_get_db():
    """Mock version of get_db that returns our mock database"""
    return _mock_db

def mock_get_collection(collection_name: str):
    """Mock version of get_collection"""
    class MockCollection:
        def __init__(self, db, name):
            self.db = db
            self.name = name
        
        def insert_one(self, document):
            class MockResult:
                def __init__(self, inserted_id):
                    self.inserted_id = inserted_id
            
            inserted_id = self.db.insert_one(self.name, document)
            return MockResult(inserted_id)
        
        def find_one(self, query, projection=None):
            return self.db.find_one(self.name, query, projection)
        
        def find(self, query=None, projection=None):
            class MockCursor:
                def __init__(self, documents):
                    self.documents = documents
                    self._skip = 0
                    self._limit = None
                    self._sort = None
                
                def skip(self, count):
                    self._skip = count
                    return self
                
                def limit(self, count):
                    self._limit = count
                    return self
                
                def sort(self, sort_spec):
                    self._sort = sort_spec
                    return self
                
                def __iter__(self):
                    results = self.documents
                    if self._sort:
                        for field, direction in reversed(self._sort):
                            results.sort(key=lambda x: x.get(field, ''), reverse=(direction == -1))
                    if self._skip:
                        results = results[self._skip:]
                    if self._limit:
                        results = results[:self._limit]
                    return iter(results)
            
            docs = self.db.find(self.name, query or {}, projection)
            return MockCursor(docs)
        
        def update_one(self, query, update):
            class MockResult:
                def __init__(self, modified_count):
                    self.modified_count = modified_count
            
            success = self.db.update_one(self.name, query, update)
            return MockResult(1 if success else 0)
        
        def delete_one(self, query):
            class MockResult:
                def __init__(self, deleted_count):
                    self.deleted_count = deleted_count
            
            success = self.db.delete_one(self.name, query)
            return MockResult(1 if success else 0)
        
        def count_documents(self, query=None):
            return self.db.count_documents(self.name, query)
        
        def create_index(self, index_spec, unique=False):
            return self.db.create_index(self.name, index_spec, unique)
        
        def drop(self):
            return self.db.drop(self.name)
    
    return MockCollection(_mock_db, collection_name)

def mock_insert_document(collection_name: str, document: Dict):
    """Mock version of insert_document"""
    return _mock_db.insert_one(collection_name, document)

def mock_find_document(collection_name: str, query: Dict, projection: Optional[Dict] = None):
    """Mock version of find_document"""
    return _mock_db.find_one(collection_name, query, projection)

def mock_find_documents(collection_name: str, query: Optional[Dict] = None, 
                       projection: Optional[Dict] = None, limit: Optional[int] = None, 
                       skip: Optional[int] = None, sort: Optional[List] = None):
    """Mock version of find_documents"""
    return _mock_db.find(collection_name, query, projection, limit, skip, sort)

def mock_update_document(collection_name: str, query: Dict, update: Dict):
    """Mock version of update_document"""
    return _mock_db.update_one(collection_name, query, update)

def mock_delete_document(collection_name: str, query: Dict):
    """Mock version of delete_document"""
    return _mock_db.delete_one(collection_name, query)

def mock_count_documents(collection_name: str, query: Optional[Dict] = None):
    """Mock version of count_documents"""
    return _mock_db.count_documents(collection_name, query)

def mock_init_db(app):
    """Mock version of init_db"""
    # Initialize collections and indexes
    collections = ['users', 'companies', 'jobs', 'applications']
    for collection in collections:
        _mock_db.collections[collection] = []
    
    # Create mock indexes
    _mock_db.create_index('users', 'email', unique=True)
    _mock_db.create_index('users', 'type')
    _mock_db.create_index('companies', 'email', unique=True)
    _mock_db.create_index('companies', 'nom')
    _mock_db.create_index('jobs', 'company_id')
    _mock_db.create_index('jobs', 'titre')
    _mock_db.create_index('jobs', 'date_creation')
    _mock_db.create_index('jobs', 'actif')
    _mock_db.create_index('applications', 'user_id')
    _mock_db.create_index('applications', 'job_id')
    _mock_db.create_index('applications', 'company_id')
    _mock_db.create_index('applications', [('user_id', 1), ('job_id', 1)], unique=True)
    _mock_db.create_index('applications', 'date_candidature')

def mock_close_db(e=None):
    """Mock version of close_db"""
    pass

def reset_mock_database():
    """Reset the mock database to clean state"""
    global _mock_db
    _mock_db = MockDatabase()

def populate_mock_data():
    """Populate mock database with sample data for testing"""
    # Sample user
    user_doc = {
        'email': 'test@example.com',
        'password': '$2b$12$hash',  # Mock bcrypt hash
        'nom': 'Dupont',
        'prenom': 'Jean',
        'telephone': '0123456789',
        'competences': ['Python', 'Flask'],
        'experience': '2 ans',
        'date_creation': datetime.utcnow(),
        'date_modification': datetime.utcnow(),
        'actif': True
    }
    user_id = _mock_db.insert_one('users', user_doc)
    
    # Sample company
    company_doc = {
        'email': 'company@example.com',
        'password': '$2b$12$hash',  # Mock bcrypt hash
        'nom': 'Test Company',
        'description': 'Test description',
        'secteur': 'Tech',
        'adresse': '123 Test St',
        'telephone': '0123456789',
        'site_web': 'https://test.com',
        'date_creation': datetime.utcnow(),
        'date_modification': datetime.utcnow(),
        'actif': True
    }
    company_id = _mock_db.insert_one('companies', company_doc)
    
    # Sample job
    job_doc = {
        'company_id': str(company_id),
        'titre': 'Développeur Python',
        'description': 'Job description',
        'salaire': '35000-45000',
        'type_contrat': 'CDI',
        'localisation': 'Paris',
        'competences_requises': ['Python', 'Django'],
        'experience_requise': '2-3 ans',
        'date_creation': datetime.utcnow(),
        'date_modification': datetime.utcnow(),
        'actif': True,
        'candidatures_count': 0
    }
    job_id = _mock_db.insert_one('jobs', job_doc)
    
    return {
        'user_id': user_id,
        'company_id': company_id,
        'job_id': job_id
    }

def is_ci_environment():
    """Check if running in CI environment"""
    return os.getenv('CI', '').lower() == 'true' or os.getenv('GITHUB_ACTIONS', '').lower() == 'true'
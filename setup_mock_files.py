#!/usr/bin/env python3
"""
Setup script to create mock test files for CI environment
This script creates all necessary mock files with proper error handling
"""

import os
import sys
from pathlib import Path


def detect_test_directory() -> str:
    """Detect the appropriate test directory"""
    if os.path.exists("backend/tests/"):
        return "backend/tests"
    elif os.path.exists("tests/"):
        return "tests"
    else:
        # Default to tests/ and create it
        return "tests"


def create_mock_database_file(test_dir: str) -> bool:
    """Create the mock database file with proper error handling"""
    mock_db_content = '''"""Mock database layer for testing without MongoDB dependency"""
import os
from datetime import datetime
from bson import ObjectId
from bson.errors import InvalidId
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
        self._id_counter = 1
    
    def _generate_objectid(self) -> ObjectId:
        """Generate a fake ObjectId for testing"""
        hex_string = f"{self._id_counter:024d}"
        self._id_counter += 1
        return ObjectId(hex_string[:24])
    
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
                return doc.copy() if doc else None
        return None
    
    def count_documents(self, collection_name: str, query: Optional[Dict] = None) -> int:
        """Mock count_documents operation"""
        query = query or {}
        count = 0
        for doc in self.collections[collection_name]:
            if self._matches_query(doc, query):
                count += 1
        return count
    
    def _matches_query(self, doc: Dict, query: Dict) -> bool:
        """Check if document matches query"""
        if not query:
            return True
        for key, value in query.items():
            if key == '_id':
                doc_id = doc.get('_id')
                if isinstance(value, str):
                    try:
                        value = ObjectId(value)
                    except (ValueError, TypeError, InvalidId):
                        pass
                if doc_id != value:
                    return False
            elif doc.get(key) != value:
                return False
        return True


def is_ci_environment():
    """Check if running in CI environment"""
    return (os.getenv('CI', '').lower() == 'true' or 
            os.getenv('GITHUB_ACTIONS', '').lower() == 'true')
'''
    
    try:
        mock_dir = Path(test_dir) / "mocks"
        mock_dir.mkdir(exist_ok=True)
        
        # Create __init__.py
        (mock_dir / "__init__.py").write_text("")
        
        # Create mock_database.py
        (mock_dir / "mock_database.py").write_text(mock_db_content)
        
        return True
    except Exception as e:
        print(f"Error creating mock database file: {e}")
        return False


def create_mock_conftest_file(test_dir: str) -> bool:
    """Create the mock conftest file"""
    conftest_content = '''import pytest
import os
from app import create_app


class MockTestConfig:
    """Mock test configuration for CI environments"""
    SECRET_KEY = 'test-secret-key'
    TESTING = True
    DEBUG = False
    MONGODB_URL = 'mongodb://mock:27017/mock_db'
    MONGODB_DB = 'mock_test_db'
    JWT_SECRET_KEY = 'test-jwt-secret'
    JWT_ACCESS_TOKEN_EXPIRES = 3600


@pytest.fixture(scope='session')
def mock_app():
    """Create application for mock testing"""
    os.environ['CI'] = 'true'
    app = create_app()
    app.config.from_object(MockTestConfig)
    return app


@pytest.fixture
def mock_client(mock_app):
    """Create test client for mock tests"""
    return mock_app.test_client()
'''
    
    try:
        conftest_file = Path(test_dir) / "conftest_mock.py"
        conftest_file.write_text(conftest_content)
        return True
    except Exception as e:
        print(f"Error creating conftest file: {e}")
        return False


def create_basic_mock_test_file(test_dir: str) -> bool:
    """Create a basic mock test file"""
    test_content = '''"""Basic mock tests for CI environment"""
import pytest
import json
import os


# Only run these tests in CI environment
pytestmark = pytest.mark.skipif(
    not os.getenv('CI', '').lower() == 'true',
    reason="Mock tests only run in CI environment"
)


class TestMockBasic:
    """Basic mock tests for CI environment"""

    def test_mock_home_endpoint(self, mock_client):
        """Test the home endpoint"""
        response = mock_client.get('/')
        
        assert response.status_code == 200
        data = response.get_json()
        assert 'message' in data
        assert 'documentation' in data
        assert 'status' in data
        assert data['status'] == 'Fonctionnel'

    def test_mock_auth_register_missing_fields(self, mock_client):
        """Test user registration with missing required fields"""
        incomplete_data = {
            'email': 'test@example.com',
            'password': 'password123'
            # Missing nom and prenom
        }
        
        response = mock_client.post('/api/auth/register/user',
                                  data=json.dumps(incomplete_data),
                                  content_type='application/json')
        
        assert response.status_code == 400
        data = response.get_json()
        assert 'requis' in data['message']

    def test_mock_invalid_endpoint(self, mock_client):
        """Test invalid endpoint"""
        response = mock_client.get('/api/nonexistent')
        assert response.status_code == 404

    def test_mock_auth_invalid_email(self, mock_client):
        """Test user registration with invalid email"""
        invalid_data = {
            'email': 'invalid-email',
            'password': 'password123',
            'nom': 'Test',
            'prenom': 'User'
        }
        
        response = mock_client.post('/api/auth/register/user',
                                  data=json.dumps(invalid_data),
                                  content_type='application/json')
        
        assert response.status_code == 400
        data = response.get_json()
        assert 'email invalide' in data['message']

    def test_mock_get_users_endpoint(self, mock_client):
        """Test get users endpoint"""
        response = mock_client.get('/api/users')
        # Should work without auth for public endpoint or return 401
        assert response.status_code in [200, 401]

    def test_mock_get_companies_endpoint(self, mock_client):
        """Test get companies endpoint"""
        response = mock_client.get('/api/companies')
        # Should work without auth for public endpoint
        assert response.status_code == 200

    def test_mock_get_jobs_endpoint(self, mock_client):
        """Test get jobs endpoint"""
        response = mock_client.get('/api/jobs')
        # Should work without auth for public endpoint
        assert response.status_code == 200
'''
    
    try:
        test_file = Path(test_dir) / "test_mock_basic.py"
        test_file.write_text(test_content)
        return True
    except Exception as e:
        print(f"Error creating basic test file: {e}")
        return False


def main():
    """Main setup function"""
    print("🔧 Setting up mock test files for CI...")
    
    test_dir = detect_test_directory()
    print(f"📁 Using test directory: {test_dir}")
    
    # Create test directory if it doesn't exist
    Path(test_dir).mkdir(parents=True, exist_ok=True)
    
    success = True
    
    # Create mock database file
    print("📄 Creating mock database file...")
    if create_mock_database_file(test_dir):
        print("   ✅ Mock database created")
    else:
        print("   ❌ Failed to create mock database")
        success = False
    
    # Create conftest file
    print("📄 Creating mock conftest file...")
    if create_mock_conftest_file(test_dir):
        print("   ✅ Mock conftest created")
    else:
        print("   ❌ Failed to create mock conftest")
        success = False
    
    # Create basic test file
    print("📄 Creating basic mock test file...")
    if create_basic_mock_test_file(test_dir):
        print("   ✅ Basic mock test created")
    else:
        print("   ❌ Failed to create basic mock test")
        success = False
    
    if success:
        print("\n✅ All mock files created successfully!")
        print(f"📂 Files created in: {test_dir}/")
        print("   - mocks/mock_database.py")
        print("   - conftest_mock.py") 
        print("   - test_mock_basic.py")
        print("\n🚀 Mock test setup complete!")
    else:
        print("\n❌ Some files failed to create")
        return 1
    
    return 0


if __name__ == "__main__":
    sys.exit(main())
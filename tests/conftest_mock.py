import pytest
import os
from unittest.mock import patch, MagicMock
from app import create_app
from app.auth import generate_token


class MockTestConfig:
    """Mock test configuration for CI environments"""
    SECRET_KEY = 'test-secret-key'
    TESTING = True
    DEBUG = False
    
    # Mock database settings (not used but kept for compatibility)
    MONGODB_URL = 'mongodb://mock:27017/mock_db'
    MONGODB_DB = 'mock_test_db'
    
    JWT_SECRET_KEY = 'test-jwt-secret'
    JWT_ACCESS_TOKEN_EXPIRES = 3600
    
    MAX_CONTENT_LENGTH = 16 * 1024 * 1024
    DEFAULT_PAGE_SIZE = 10
    MAX_PAGE_SIZE = 100


@pytest.fixture(scope='session')
def mock_app():
    """Create application for mock testing"""
    # Set environment to indicate CI
    os.environ['CI'] = 'true'
    
    app = create_app()
    app.config.from_object(MockTestConfig)
    
    return app


@pytest.fixture(scope='function')
def mock_client(mock_app):
    """Create test client for mock tests"""
    return mock_app.test_client()


@pytest.fixture(scope='function', autouse=True)
def mock_database_setup(mock_app):
    """Setup mock database for each test"""
    # Only apply mocking in CI environment
    if not os.getenv('CI', '').lower() == 'true':
        yield
        return
    
    from tests.mocks.mock_database import (
        mock_get_db, mock_get_collection, mock_insert_document,
        mock_find_document, mock_find_documents, mock_update_document,
        mock_delete_document, mock_count_documents, mock_init_db,
        mock_close_db, reset_mock_database, populate_mock_data
    )
    
    with mock_app.app_context():
        # Reset mock database before each test
        reset_mock_database()
        
        # Patch all database functions
        with patch('app.database.get_db', mock_get_db), \
             patch('app.database.get_collection', mock_get_collection), \
             patch('app.database.insert_document', mock_insert_document), \
             patch('app.database.find_document', mock_find_document), \
             patch('app.database.find_documents', mock_find_documents), \
             patch('app.database.update_document', mock_update_document), \
             patch('app.database.delete_document', mock_delete_document), \
             patch('app.database.count_documents', mock_count_documents), \
             patch('app.database.init_db', mock_init_db), \
             patch('app.database.close_db', mock_close_db):
            
            # Initialize mock database
            mock_init_db(mock_app)
            
            yield
            
            # Cleanup after test
            reset_mock_database()


@pytest.fixture
def mock_sample_user_data():
    """Sample user data for mock testing"""
    return {
        'email': 'test@example.com',
        'password': 'password123',
        'nom': 'Dupont',
        'prenom': 'Jean',
        'telephone': '0123456789',
        'competences': ['Python', 'Flask'],
        'experience': '2 ans d\'expérience'
    }


@pytest.fixture
def mock_sample_company_data():
    """Sample company data for mock testing"""
    return {
        'email': 'company@example.com',
        'password': 'password123',
        'nom': 'Test Company',
        'description': 'Une entreprise de test',
        'secteur': 'Technologie',
        'adresse': '123 Test Street',
        'telephone': '0123456789',
        'site_web': 'https://test-company.com'
    }


@pytest.fixture
def mock_sample_job_data():
    """Sample job data for mock testing"""
    return {
        'titre': 'Développeur Python',
        'description': 'Poste de développeur Python',
        'salaire': '35000-45000',
        'type_contrat': 'CDI',
        'localisation': 'Paris',
        'competences_requises': ['Python', 'Django'],
        'experience_requise': '2-3 ans'
    }


@pytest.fixture
def mock_created_user(mock_app, mock_sample_user_data):
    """Create and return a mock test user"""
    # Only works in CI environment with mocking
    if not os.getenv('CI', '').lower() == 'true':
        pytest.skip("Mock fixtures only available in CI environment")
    
    with mock_app.app_context():
        from tests.mocks.mock_database import _mock_db, populate_mock_data
        
        # Use pre-populated data
        data = populate_mock_data()
        
        # Create a mock user object
        class MockUser:
            def __init__(self, user_id, data):
                self._id = user_id
                self.email = data['email']
                self.nom = data['nom']
                self.prenom = data['prenom']
                self.telephone = data.get('telephone')
                self.competences = data.get('competences', [])
                self.experience = data.get('experience', '')
                self.password = data.get('password', '')
            
            def get_id(self):
                return str(self._id)
            
            def check_password(self, password):
                return password == 'password123'  # Mock password check
        
        user_doc = _mock_db.find_one('users', {'_id': data['user_id']})
        return MockUser(data['user_id'], user_doc)


@pytest.fixture
def mock_created_company(mock_app, mock_sample_company_data):
    """Create and return a mock test company"""
    if not os.getenv('CI', '').lower() == 'true':
        pytest.skip("Mock fixtures only available in CI environment")
    
    with mock_app.app_context():
        from tests.mocks.mock_database import _mock_db, populate_mock_data
        
        data = populate_mock_data()
        
        class MockCompany:
            def __init__(self, company_id, data):
                self._id = company_id
                self.email = data['email']
                self.nom = data['nom']
                self.description = data['description']
                self.secteur = data.get('secteur')
                self.adresse = data.get('adresse')
                self.telephone = data.get('telephone')
                self.site_web = data.get('site_web')
                self.password = data.get('password', '')
            
            def get_id(self):
                return str(self._id)
            
            def check_password(self, password):
                return password == 'password123'
            
            def get_jobs_count(self):
                return 1  # Mock count
        
        company_doc = _mock_db.find_one('companies', {'_id': data['company_id']})
        return MockCompany(data['company_id'], company_doc)


@pytest.fixture
def mock_created_job(mock_app, mock_created_company, mock_sample_job_data):
    """Create and return a mock test job"""
    if not os.getenv('CI', '').lower() == 'true':
        pytest.skip("Mock fixtures only available in CI environment")
    
    with mock_app.app_context():
        from tests.mocks.mock_database import _mock_db, populate_mock_data
        
        data = populate_mock_data()
        
        class MockJob:
            def __init__(self, job_id, data):
                self._id = job_id
                self.company_id = data['company_id']
                self.titre = data['titre']
                self.description = data['description']
                self.salaire = data.get('salaire')
                self.type_contrat = data['type_contrat']
                self.localisation = data.get('localisation')
                self.competences_requises = data.get('competences_requises', [])
                self.experience_requise = data.get('experience_requise', '')
                self.actif = data.get('actif', True)
            
            def get_id(self):
                return str(self._id)
            
            def get_applications_count(self):
                return 0  # Mock count
        
        job_doc = _mock_db.find_one('jobs', {'_id': data['job_id']})
        return MockJob(data['job_id'], job_doc)


@pytest.fixture
def mock_user_token(mock_app, mock_created_user):
    """Generate JWT token for mock test user"""
    if not os.getenv('CI', '').lower() == 'true':
        pytest.skip("Mock fixtures only available in CI environment")
    
    with mock_app.app_context():
        return generate_token(mock_created_user.get_id(), 'user')


@pytest.fixture
def mock_company_token(mock_app, mock_created_company):
    """Generate JWT token for mock test company"""
    if not os.getenv('CI', '').lower() == 'true':
        pytest.skip("Mock fixtures only available in CI environment")
    
    with mock_app.app_context():
        return generate_token(mock_created_company.get_id(), 'company')


@pytest.fixture
def mock_auth_headers_user(mock_user_token):
    """Authorization headers for mock user"""
    if not os.getenv('CI', '').lower() == 'true':
        pytest.skip("Mock fixtures only available in CI environment")
    
    return {'Authorization': f'Bearer {mock_user_token}'}


@pytest.fixture
def mock_auth_headers_company(mock_company_token):
    """Authorization headers for mock company"""
    if not os.getenv('CI', '').lower() == 'true':
        pytest.skip("Mock fixtures only available in CI environment")
    
    return {'Authorization': f'Bearer {mock_company_token}'}


@pytest.fixture
def mock_created_application(mock_app, mock_created_user, mock_created_job):
    """Create and return a mock test application"""
    if not os.getenv('CI', '').lower() == 'true':
        pytest.skip("Mock fixtures only available in CI environment")
    
    with mock_app.app_context():
        from tests.mocks.mock_database import _mock_db
        from datetime import datetime
        
        # Create application document
        app_doc = {
            'user_id': mock_created_user.get_id(),
            'job_id': mock_created_job.get_id(),
            'company_id': mock_created_job.company_id,
            'lettre_motivation': 'Test motivation letter',
            'statut': 'En attente',
            'date_candidature': datetime.utcnow(),
            'date_modification': datetime.utcnow(),
            'notes_entreprise': ''
        }
        
        app_id = _mock_db.insert_one('applications', app_doc)
        
        class MockApplication:
            def __init__(self, app_id, data):
                self._id = app_id
                self.user_id = data['user_id']
                self.job_id = data['job_id']
                self.company_id = data['company_id']
                self.lettre_motivation = data['lettre_motivation']
                self.statut = data['statut']
                self.date_candidature = data['date_candidature']
                self.date_modification = data['date_modification']
                self.notes_entreprise = data['notes_entreprise']
            
            def get_id(self):
                return str(self._id)
        
        return MockApplication(app_id, app_doc)
import pytest
import os
import tempfile
from unittest.mock import patch, MagicMock
from pymongo import MongoClient
from app import create_app
from app.models.user import User
from app.models.company import Company
from app.models.job import Job
from app.models.application import Application
from app.auth import generate_token


class TestConfig:
    """Test configuration"""
    SECRET_KEY = 'test-secret-key'
    TESTING = True
    DEBUG = False
    
    # Use test database
    MONGODB_URL = 'mongodb://localhost:27017/test_interim_app'
    MONGODB_DB = 'test_interim_app'
    
    JWT_SECRET_KEY = 'test-jwt-secret'
    JWT_ACCESS_TOKEN_EXPIRES = 3600
    
    MAX_CONTENT_LENGTH = 16 * 1024 * 1024
    DEFAULT_PAGE_SIZE = 10
    MAX_PAGE_SIZE = 100


class MockTestConfig:
    """Mock test configuration for CI environments"""
    SECRET_KEY = 'test-secret-key'
    TESTING = True
    DEBUG = False
    MONGODB_URL = 'mongodb://mock:27017/mock_db'
    MONGODB_DB = 'mock_test_db'
    JWT_SECRET_KEY = 'test-jwt-secret'
    JWT_ACCESS_TOKEN_EXPIRES = 3600
    MAX_CONTENT_LENGTH = 16 * 1024 * 1024
    DEFAULT_PAGE_SIZE = 10
    MAX_PAGE_SIZE = 100


@pytest.fixture(scope='session')
def mock_app():
    """Create application for mock testing with comprehensive database patching"""
    os.environ['CI'] = 'true'
    
    # Mock all database-related functions and model methods
    with patch('app.database.init_db') as mock_init_db, \
         patch('app.database.get_db') as mock_get_db, \
         patch('app.database.close_db') as mock_close_db, \
         patch('app.database.get_collection') as mock_get_collection, \
         patch('app.database.find_documents') as mock_find_documents, \
         patch('app.database.find_document') as mock_find_document, \
         patch('app.database.count_documents') as mock_count_documents, \
         patch('app.database.insert_document') as mock_insert_document, \
         patch('app.database.update_document') as mock_update_document, \
         patch('app.database.delete_document') as mock_delete_document, \
         patch('app.models.user.User.find_all') as mock_user_find_all, \
         patch('app.models.user.User.count_all') as mock_user_count_all, \
         patch('app.models.company.Company.find_all') as mock_company_find_all, \
         patch('app.models.company.Company.count_all') as mock_company_count_all, \
         patch('app.models.job.Job.find_all') as mock_job_find_all, \
         patch('app.models.job.Job.search_jobs') as mock_job_search, \
         patch('app.models.job.Job.count_all') as mock_job_count_all, \
         patch('pymongo.MongoClient') as mock_mongo_client:
        
        # Configure basic mocks
        mock_init_db.return_value = None
        mock_close_db.return_value = None
        
        # Mock database object
        mock_db = MagicMock()
        mock_get_db.return_value = mock_db
        mock_get_collection.return_value = MagicMock()
        
        # Mock database operations
        mock_find_documents.return_value = []
        mock_find_document.return_value = None
        mock_count_documents.return_value = 0
        mock_insert_document.return_value = 'mock_id'
        mock_update_document.return_value = True
        mock_delete_document.return_value = True
        
        # Mock model methods with empty results
        mock_user_find_all.return_value = []
        mock_user_count_all.return_value = 0
        
        mock_company_find_all.return_value = []
        mock_company_count_all.return_value = 0
        
        mock_job_find_all.return_value = []
        mock_job_search.return_value = []
        mock_job_count_all.return_value = 0
        
        # Mock MongoDB client
        mock_client = MagicMock()
        mock_mongo_client.return_value = mock_client
        
        # Create app with mocked database
        app = create_app()
        app.config.from_object(MockTestConfig)
        
        return app


@pytest.fixture
def mock_client(mock_app):
    """Create test client for mock tests"""
    return mock_app.test_client()


@pytest.fixture(scope='session')
def app():
    """Create application for testing"""
    # Override config for testing
    os.environ['MONGODB_DB'] = 'test_interim_app'
    os.environ['MONGODB_URL'] = 'mongodb://localhost:27017/test_interim_app'
    
    app = create_app()
    app.config.from_object(TestConfig)
    
    return app


@pytest.fixture(scope='function')
def client(app):
    """Create test client"""
    return app.test_client()


@pytest.fixture(scope='function')
def db_cleanup(app):
    """Clean database before and after each test"""
    with app.app_context():
        # Clean up before test
        client = MongoClient(app.config['MONGODB_URL'])
        db = client[app.config['MONGODB_DB']]
        
        # Drop all collections
        collections = ['users', 'companies', 'jobs', 'applications']
        for collection in collections:
            db[collection].drop()
        
        yield
        
        # Clean up after test
        for collection in collections:
            db[collection].drop()
        
        client.close()


@pytest.fixture
def sample_user_data():
    """Sample user data for testing"""
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
def sample_company_data():
    """Sample company data for testing"""
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
def sample_job_data():
    """Sample job data for testing"""
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
def created_user(app, db_cleanup, sample_user_data):
    """Create and return a test user"""
    with app.app_context():
        user = User(
            email=sample_user_data['email'],
            password=sample_user_data['password'],
            nom=sample_user_data['nom'],
            prenom=sample_user_data['prenom'],
            telephone=sample_user_data['telephone'],
            competences=sample_user_data['competences'],
            experience=sample_user_data['experience']
        )
        user_id = user.save()
        user._id = user_id
        return user


@pytest.fixture
def created_company(app, db_cleanup, sample_company_data):
    """Create and return a test company"""
    with app.app_context():
        company = Company(
            email=sample_company_data['email'],
            password=sample_company_data['password'],
            nom=sample_company_data['nom'],
            description=sample_company_data['description'],
            secteur=sample_company_data['secteur'],
            adresse=sample_company_data['adresse'],
            telephone=sample_company_data['telephone'],
            site_web=sample_company_data['site_web']
        )
        company_id = company.save()
        company._id = company_id
        return company


@pytest.fixture
def created_job(app, db_cleanup, created_company, sample_job_data):
    """Create and return a test job"""
    with app.app_context():
        job = Job(
            company_id=created_company.get_id(),
            titre=sample_job_data['titre'],
            description=sample_job_data['description'],
            salaire=sample_job_data['salaire'],
            type_contrat=sample_job_data['type_contrat'],
            localisation=sample_job_data['localisation'],
            competences_requises=sample_job_data['competences_requises'],
            experience_requise=sample_job_data['experience_requise']
        )
        job_id = job.save()
        job._id = job_id
        return job


@pytest.fixture
def user_token(app, created_user):
    """Generate JWT token for test user"""
    with app.app_context():
        return generate_token(created_user.get_id(), 'user')


@pytest.fixture
def company_token(app, created_company):
    """Generate JWT token for test company"""
    with app.app_context():
        return generate_token(created_company.get_id(), 'company')


@pytest.fixture
def auth_headers_user(user_token):
    """Authorization headers for user"""
    return {'Authorization': f'Bearer {user_token}'}


@pytest.fixture
def auth_headers_company(company_token):
    """Authorization headers for company"""
    return {'Authorization': f'Bearer {company_token}'}


@pytest.fixture
def created_application(app, db_cleanup, created_user, created_job):
    """Create and return a test application"""
    with app.app_context():
        application = Application(
            user_id=created_user.get_id(),
            job_id=created_job.get_id(),
            company_id=created_job.company_id,
            lettre_motivation='Lettre de motivation de test'
        )
        app_id = application.save()
        application._id = app_id
        return application
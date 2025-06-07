"""Basic mock tests for CI environment"""
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

    def test_mock_auth_weak_password(self, mock_client):
        """Test user registration with weak password"""
        weak_password_data = {
            'email': 'test@example.com',
            'password': '123',  # Too short
            'nom': 'Test',
            'prenom': 'User'
        }
        
        response = mock_client.post('/api/auth/register/user',
                                  data=json.dumps(weak_password_data),
                                  content_type='application/json')
        
        assert response.status_code == 400
        data = response.get_json()
        assert 'au moins 6 caractères' in data['message']

    def test_mock_company_register_missing_fields(self, mock_client):
        """Test company registration with missing fields"""
        incomplete_data = {
            'email': 'company@example.com',
            'password': 'password123'
            # Missing nom and description
        }
        
        response = mock_client.post('/api/auth/register/company',
                                  data=json.dumps(incomplete_data),
                                  content_type='application/json')
        
        assert response.status_code == 400

    def test_mock_login_missing_fields(self, mock_client):
        """Test login with missing fields"""
        incomplete_data = {
            'email': 'test@example.com'
            # Missing password and user_type
        }
        
        response = mock_client.post('/api/auth/login',
                                  data=json.dumps(incomplete_data),
                                  content_type='application/json')
        
        assert response.status_code == 400

    def test_mock_login_invalid_user_type(self, mock_client):
        """Test login with invalid user type"""
        login_data = {
            'email': 'test@example.com',
            'password': 'password123',
            'user_type': 'invalid'
        }
        
        response = mock_client.post('/api/auth/login',
                                  data=json.dumps(login_data),
                                  content_type='application/json')
        
        assert response.status_code == 400

    def test_mock_verify_token_missing(self, mock_client):
        """Test token verification without token"""
        response = mock_client.get('/api/auth/verify')
        assert response.status_code == 401

    def test_mock_verify_token_invalid(self, mock_client):
        """Test token verification with invalid token"""
        headers = {'Authorization': 'Bearer invalid-token'}
        response = mock_client.get('/api/auth/verify', headers=headers)
        assert response.status_code == 401

    def test_mock_logout_without_auth(self, mock_client):
        """Test logout without authentication"""
        response = mock_client.post('/api/auth/logout')
        assert response.status_code == 401

    def test_mock_get_users_endpoint(self, mock_client):
        """Test get users endpoint without authentication"""
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

    def test_mock_create_job_without_auth(self, mock_client):
        """Test creating job without authentication"""
        job_data = {
            'titre': 'Test Job',
            'description': 'Test description'
        }
        
        response = mock_client.post('/api/jobs',
                                  data=json.dumps(job_data),
                                  content_type='application/json')
        
        assert response.status_code == 401

    def test_mock_create_application_without_auth(self, mock_client):
        """Test creating application without authentication"""
        app_data = {
            'job_id': 'test_job_id',
            'lettre_motivation': 'Test motivation'
        }
        
        response = mock_client.post('/api/applications',
                                  data=json.dumps(app_data),
                                  content_type='application/json')
        
        assert response.status_code == 401

    def test_mock_invalid_json(self, mock_client):
        """Test API with invalid JSON"""
        response = mock_client.post('/api/auth/register/user',
                                  data='invalid-json',
                                  content_type='application/json')
        
        # Should return 400 or 500 for malformed JSON
        assert response.status_code in [400, 500]

    def test_mock_invalid_content_type(self, mock_client):
        """Test API without proper content type"""
        data = {
            'email': 'test@example.com',
            'password': 'password123',
            'nom': 'Test',
            'prenom': 'User'
        }
        
        # Send without content-type header
        response = mock_client.post('/api/auth/register/user',
                                  data=json.dumps(data))
        
        # Behavior depends on Flask configuration - accept various responses
        assert response.status_code in [201, 400, 500]

    def test_mock_get_nonexistent_user(self, mock_client):
        """Test getting non-existent user"""
        response = mock_client.get('/api/users/507f1f77bcf86cd799439011')
        assert response.status_code == 404

    def test_mock_get_nonexistent_company(self, mock_client):
        """Test getting non-existent company"""
        response = mock_client.get('/api/companies/507f1f77bcf86cd799439011')
        assert response.status_code == 404

    def test_mock_get_nonexistent_job(self, mock_client):
        """Test getting non-existent job"""
        response = mock_client.get('/api/jobs/507f1f77bcf86cd799439011')
        assert response.status_code == 404

    def test_mock_search_jobs_no_results(self, mock_client):
        """Test job search with no results"""
        response = mock_client.get('/api/jobs?search=nonexistent')
        assert response.status_code == 200
        data = response.get_json()
        assert 'jobs' in data
        # Should return empty list or jobs (depending on mock data)
        assert isinstance(data['jobs'], list)

    def test_mock_pagination_edge_cases(self, mock_client):
        """Test pagination with edge cases"""
        # Test negative page
        response = mock_client.get('/api/users?page=-1&limit=-10')
        assert response.status_code == 200
        
        # Test large limit
        response = mock_client.get('/api/users?limit=1000')
        assert response.status_code == 200
        data = response.get_json()
        if 'limit' in data:
            # Should be capped at MAX_PAGE_SIZE
            assert data['limit'] <= 100
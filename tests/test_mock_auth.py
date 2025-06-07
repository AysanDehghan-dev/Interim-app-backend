import pytest
import json
import os
from unittest.mock import patch
from app.auth import generate_token, verify_token


# Only run these tests in CI environment
pytestmark = pytest.mark.skipif(
    not os.getenv('CI', '').lower() == 'true',
    reason="Mock tests only run in CI environment"
)


class TestMockAuthentication:
    """Mock authentication tests for CI environment"""

    def test_mock_register_user_success(self, mock_client, mock_sample_user_data):
        """Test successful user registration with mocking"""
        with patch('app.models.user.User.find_by_email', return_value=None), \
             patch('app.models.user.User.save', return_value='mock_user_id'):
            
            response = mock_client.post('/api/auth/register/user',
                                      data=json.dumps(mock_sample_user_data),
                                      content_type='application/json')
            
            assert response.status_code == 201
            data = response.get_json()
            assert 'user_id' in data
            assert 'token' in data
            assert data['user_type'] == 'user'

    def test_mock_register_user_missing_fields(self, mock_client):
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

    def test_mock_register_user_invalid_email(self, mock_client, mock_sample_user_data):
        """Test user registration with invalid email"""
        mock_sample_user_data['email'] = 'invalid-email'
        
        response = mock_client.post('/api/auth/register/user',
                                  data=json.dumps(mock_sample_user_data),
                                  content_type='application/json')
        
        assert response.status_code == 400
        data = response.get_json()
        assert 'email invalide' in data['message']

    def test_mock_register_user_duplicate_email(self, mock_client, mock_sample_user_data):
        """Test user registration with existing email"""
        # Mock existing user
        mock_user = type('MockUser', (), {'email': mock_sample_user_data['email']})()
        
        with patch('app.models.user.User.find_by_email', return_value=mock_user):
            response = mock_client.post('/api/auth/register/user',
                                      data=json.dumps(mock_sample_user_data),
                                      content_type='application/json')
            
            assert response.status_code == 409
            data = response.get_json()
            assert 'déjà utilisé' in data['message']

    def test_mock_register_company_success(self, mock_client, mock_sample_company_data):
        """Test successful company registration with mocking"""
        with patch('app.models.company.Company.find_by_email', return_value=None), \
             patch('app.models.company.Company.save', return_value='mock_company_id'):
            
            response = mock_client.post('/api/auth/register/company',
                                      data=json.dumps(mock_sample_company_data),
                                      content_type='application/json')
            
            assert response.status_code == 201
            data = response.get_json()
            assert 'company_id' in data
            assert 'token' in data
            assert data['user_type'] == 'company'

    def test_mock_login_user_success(self, mock_client, mock_sample_user_data):
        """Test successful user login with mocking"""
        # Create mock user with password check method
        mock_user = type('MockUser', (), {
            'email': mock_sample_user_data['email'],
            'get_id': lambda: 'mock_user_id',
            'check_password': lambda pwd: pwd == 'password123'
        })()
        
        with patch('app.models.user.User.find_by_email', return_value=mock_user):
            login_data = {
                'email': mock_sample_user_data['email'],
                'password': 'password123',
                'user_type': 'user'
            }
            
            response = mock_client.post('/api/auth/login',
                                      data=json.dumps(login_data),
                                      content_type='application/json')
            
            assert response.status_code == 200
            data = response.get_json()
            assert 'token' in data
            assert data['user_type'] == 'user'

    def test_mock_login_invalid_credentials(self, mock_client, mock_sample_user_data):
        """Test login with invalid credentials"""
        mock_user = type('MockUser', (), {
            'email': mock_sample_user_data['email'],
            'check_password': lambda pwd: False  # Always fail password check
        })()
        
        with patch('app.models.user.User.find_by_email', return_value=mock_user):
            login_data = {
                'email': mock_sample_user_data['email'],
                'password': 'wrongpassword',
                'user_type': 'user'
            }
            
            response = mock_client.post('/api/auth/login',
                                      data=json.dumps(login_data),
                                      content_type='application/json')
            
            assert response.status_code == 401
            data = response.get_json()
            assert 'Identifiants incorrects' in data['message']

    def test_mock_login_nonexistent_user(self, mock_client):
        """Test login with non-existent user"""
        with patch('app.models.user.User.find_by_email', return_value=None):
            login_data = {
                'email': 'nonexistent@example.com',
                'password': 'password123',
                'user_type': 'user'
            }
            
            response = mock_client.post('/api/auth/login',
                                      data=json.dumps(login_data),
                                      content_type='application/json')
            
            assert response.status_code == 401

    def test_mock_verify_token_valid(self, mock_client, mock_auth_headers_user):
        """Test token verification with valid token"""
        mock_user = type('MockUser', (), {
            'email': 'test@example.com',
            'nom': 'Test',
            'prenom': 'User',
            'actif': True
        })()
        
        with patch('app.models.user.User.find_by_id', return_value=mock_user):
            response = mock_client.get('/api/auth/verify', headers=mock_auth_headers_user)
            
            assert response.status_code == 200
            data = response.get_json()
            assert data['message'] == 'Token valide'
            assert 'user_info' in data

    def test_mock_verify_token_invalid(self, mock_client):
        """Test token verification with invalid token"""
        headers = {'Authorization': 'Bearer invalid-token'}
        response = mock_client.get('/api/auth/verify', headers=headers)
        
        assert response.status_code == 401

    def test_mock_logout_success(self, mock_client, mock_auth_headers_user):
        """Test successful logout"""
        response = mock_client.post('/api/auth/logout', headers=mock_auth_headers_user)
        
        assert response.status_code == 200
        data = response.get_json()
        assert 'Déconnexion réussie' in data['message']

    def test_mock_change_password_success(self, mock_client, mock_auth_headers_user):
        """Test successful password change"""
        mock_user = type('MockUser', (), {
            'check_password': lambda pwd: pwd == 'password123',
            'update': lambda user_id, data: True
        })()
        
        with patch('app.models.user.User.find_by_id', return_value=mock_user):
            password_data = {
                'current_password': 'password123',
                'new_password': 'newpassword123'
            }
            
            response = mock_client.put('/api/auth/change-password',
                                     data=json.dumps(password_data),
                                     content_type='application/json',
                                     headers=mock_auth_headers_user)
            
            assert response.status_code == 200

    def test_mock_change_password_wrong_current(self, mock_client, mock_auth_headers_user):
        """Test password change with wrong current password"""
        mock_user = type('MockUser', (), {
            'check_password': lambda pwd: False  # Wrong password
        })()
        
        with patch('app.models.user.User.find_by_id', return_value=mock_user):
            password_data = {
                'current_password': 'wrongpassword',
                'new_password': 'newpassword123'
            }
            
            response = mock_client.put('/api/auth/change-password',
                                     data=json.dumps(password_data),
                                     content_type='application/json',
                                     headers=mock_auth_headers_user)
            
            assert response.status_code == 401


class TestMockJWTHelpers:
    """Test JWT helper functions with mocking"""

    def test_mock_generate_token(self, mock_app):
        """Test token generation"""
        with mock_app.app_context():
            token = generate_token('user123', 'user')
            assert token is not None
            assert isinstance(token, str)

    def test_mock_verify_valid_token(self, mock_app):
        """Test verifying valid token"""
        with mock_app.app_context():
            token = generate_token('user123', 'user')
            payload = verify_token(token)
            
            assert payload is not None
            assert payload['user_id'] == 'user123'
            assert payload['user_type'] == 'user'

    def test_mock_verify_invalid_token(self, mock_app):
        """Test verifying invalid token"""
        with mock_app.app_context():
            payload = verify_token('invalid-token')
            assert payload is None
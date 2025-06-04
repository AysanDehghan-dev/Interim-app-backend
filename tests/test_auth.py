import pytest
import json
from app.models.user import User
from app.models.company import Company
from app.auth import generate_token, verify_token


class TestAuthentication:
    """Test authentication functionality"""

    def test_register_user_success(self, client, db_cleanup, sample_user_data):
        """Test successful user registration"""
        response = client.post('/api/auth/register/user',
                             data=json.dumps(sample_user_data),
                             content_type='application/json')
        
        assert response.status_code == 201
        data = response.get_json()
        assert 'user_id' in data
        assert 'token' in data
        assert data['user_type'] == 'user'
        assert data['message'] == 'Utilisateur créé avec succès'

    def test_register_user_missing_fields(self, client, db_cleanup):
        """Test user registration with missing required fields"""
        incomplete_data = {
            'email': 'test@example.com',
            'password': 'password123'
            # Missing nom and prenom
        }
        
        response = client.post('/api/auth/register/user',
                             data=json.dumps(incomplete_data),
                             content_type='application/json')
        
        assert response.status_code == 400
        data = response.get_json()
        assert 'requis' in data['message']

    def test_register_user_invalid_email(self, client, db_cleanup, sample_user_data):
        """Test user registration with invalid email"""
        sample_user_data['email'] = 'invalid-email'
        
        response = client.post('/api/auth/register/user',
                             data=json.dumps(sample_user_data),
                             content_type='application/json')
        
        assert response.status_code == 400
        data = response.get_json()
        assert 'email invalide' in data['message']

    def test_register_user_weak_password(self, client, db_cleanup, sample_user_data):
        """Test user registration with weak password"""
        sample_user_data['password'] = '123'  # Too short
        
        response = client.post('/api/auth/register/user',
                             data=json.dumps(sample_user_data),
                             content_type='application/json')
        
        assert response.status_code == 400
        data = response.get_json()
        assert 'au moins 6 caractères' in data['message']

    def test_register_user_duplicate_email(self, client, created_user, sample_user_data):
        """Test user registration with existing email"""
        response = client.post('/api/auth/register/user',
                             data=json.dumps(sample_user_data),
                             content_type='application/json')
        
        assert response.status_code == 409
        data = response.get_json()
        assert 'déjà utilisé' in data['message']

    def test_register_company_success(self, client, db_cleanup, sample_company_data):
        """Test successful company registration"""
        response = client.post('/api/auth/register/company',
                             data=json.dumps(sample_company_data),
                             content_type='application/json')
        
        assert response.status_code == 201
        data = response.get_json()
        assert 'company_id' in data
        assert 'token' in data
        assert data['user_type'] == 'company'

    def test_register_company_missing_fields(self, client, db_cleanup):
        """Test company registration with missing fields"""
        incomplete_data = {
            'email': 'company@example.com',
            'password': 'password123'
            # Missing nom and description
        }
        
        response = client.post('/api/auth/register/company',
                             data=json.dumps(incomplete_data),
                             content_type='application/json')
        
        assert response.status_code == 400

    def test_login_user_success(self, client, created_user):
        """Test successful user login"""
        login_data = {
            'email': created_user.email,
            'password': 'password123',
            'user_type': 'user'
        }
        
        response = client.post('/api/auth/login',
                             data=json.dumps(login_data),
                             content_type='application/json')
        
        assert response.status_code == 200
        data = response.get_json()
        assert 'token' in data
        assert data['user_type'] == 'user'
        assert data['user_id'] == created_user.get_id()

    def test_login_company_success(self, client, created_company):
        """Test successful company login"""
        login_data = {
            'email': created_company.email,
            'password': 'password123',
            'user_type': 'company'
        }
        
        response = client.post('/api/auth/login',
                             data=json.dumps(login_data),
                             content_type='application/json')
        
        assert response.status_code == 200
        data = response.get_json()
        assert 'token' in data
        assert data['user_type'] == 'company'

    def test_login_invalid_credentials(self, client, created_user):
        """Test login with invalid credentials"""
        login_data = {
            'email': created_user.email,
            'password': 'wrongpassword',
            'user_type': 'user'
        }
        
        response = client.post('/api/auth/login',
                             data=json.dumps(login_data),
                             content_type='application/json')
        
        assert response.status_code == 401
        data = response.get_json()
        assert 'Identifiants incorrects' in data['message']

    def test_login_nonexistent_user(self, client, db_cleanup):
        """Test login with non-existent user"""
        login_data = {
            'email': 'nonexistent@example.com',
            'password': 'password123',
            'user_type': 'user'
        }
        
        response = client.post('/api/auth/login',
                             data=json.dumps(login_data),
                             content_type='application/json')
        
        assert response.status_code == 401

    def test_login_missing_fields(self, client, db_cleanup):
        """Test login with missing fields"""
        incomplete_data = {
            'email': 'test@example.com'
            # Missing password and user_type
        }
        
        response = client.post('/api/auth/login',
                             data=json.dumps(incomplete_data),
                             content_type='application/json')
        
        assert response.status_code == 400

    def test_login_invalid_user_type(self, client, created_user):
        """Test login with invalid user type"""
        login_data = {
            'email': created_user.email,
            'password': 'password123',
            'user_type': 'invalid'
        }
        
        response = client.post('/api/auth/login',
                             data=json.dumps(login_data),
                             content_type='application/json')
        
        assert response.status_code == 400

    def test_verify_token_valid(self, client, auth_headers_user):
        """Test token verification with valid token"""
        response = client.get('/api/auth/verify', headers=auth_headers_user)
        
        assert response.status_code == 200
        data = response.get_json()
        assert data['message'] == 'Token valide'
        assert 'user_info' in data

    def test_verify_token_invalid(self, client):
        """Test token verification with invalid token"""
        headers = {'Authorization': 'Bearer invalid-token'}
        response = client.get('/api/auth/verify', headers=headers)
        
        assert response.status_code == 401

    def test_verify_token_missing(self, client):
        """Test token verification without token"""
        response = client.get('/api/auth/verify')
        
        assert response.status_code == 401

    def test_logout_success(self, client, auth_headers_user):
        """Test successful logout"""
        response = client.post('/api/auth/logout', headers=auth_headers_user)
        
        assert response.status_code == 200
        data = response.get_json()
        assert 'Déconnexion réussie' in data['message']

    def test_logout_without_auth(self, client):
        """Test logout without authentication"""
        response = client.post('/api/auth/logout')
        
        assert response.status_code == 401

    def test_change_password_success(self, client, auth_headers_user):
        """Test successful password change"""
        password_data = {
            'current_password': 'password123',
            'new_password': 'newpassword123'
        }
        
        response = client.put('/api/auth/change-password',
                            data=json.dumps(password_data),
                            content_type='application/json',
                            headers=auth_headers_user)
        
        assert response.status_code == 200

    def test_change_password_wrong_current(self, client, auth_headers_user):
        """Test password change with wrong current password"""
        password_data = {
            'current_password': 'wrongpassword',
            'new_password': 'newpassword123'
        }
        
        response = client.put('/api/auth/change-password',
                            data=json.dumps(password_data),
                            content_type='application/json',
                            headers=auth_headers_user)
        
        assert response.status_code == 401

    def test_change_password_weak_new(self, client, auth_headers_user):
        """Test password change with weak new password"""
        password_data = {
            'current_password': 'password123',
            'new_password': '123'  # Too short
        }
        
        response = client.put('/api/auth/change-password',
                            data=json.dumps(password_data),
                            content_type='application/json',
                            headers=auth_headers_user)
        
        assert response.status_code == 400

    def test_change_password_missing_fields(self, client, auth_headers_user):
        """Test password change with missing fields"""
        password_data = {
            'current_password': 'password123'
            # Missing new_password
        }
        
        response = client.put('/api/auth/change-password',
                            data=json.dumps(password_data),
                            content_type='application/json',
                            headers=auth_headers_user)
        
        assert response.status_code == 400


class TestJWTHelpers:
    """Test JWT helper functions"""

    def test_generate_token(self, app):
        """Test token generation"""
        with app.app_context():
            token = generate_token('user123', 'user')
            assert token is not None
            assert isinstance(token, str)

    def test_verify_valid_token(self, app):
        """Test verifying valid token"""
        with app.app_context():
            token = generate_token('user123', 'user')
            payload = verify_token(token)
            
            assert payload is not None
            assert payload['user_id'] == 'user123'
            assert payload['user_type'] == 'user'

    def test_verify_invalid_token(self, app):
        """Test verifying invalid token"""
        with app.app_context():
            payload = verify_token('invalid-token')
            assert payload is None

    def test_verify_malformed_token(self, app):
        """Test verifying malformed token"""
        with app.app_context():
            payload = verify_token('not.a.jwt')
            assert payload is None
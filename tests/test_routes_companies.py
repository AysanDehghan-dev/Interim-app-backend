import pytest
import json


class TestCompanyRoutes:
    """Test company routes functionality"""

    def test_get_all_companies(self, client, created_company):
        """Test getting all companies"""
        response = client.get('/api/companies')
        
        assert response.status_code == 200
        data = response.get_json()
        assert 'companies' in data
        assert 'total' in data
        assert len(data['companies']) == 1
        assert data['companies'][0]['nom'] == created_company.nom

    def test_get_all_companies_pagination(self, client, db_cleanup, app, sample_company_data):
        """Test company pagination"""
        # Create multiple companies
        with app.app_context():
            from app.models.company import Company
            for i in range(15):
                company_data = sample_company_data.copy()
                company_data['email'] = f'company{i}@example.com'
                company_data['nom'] = f'Company {i}'
                company = Company(**company_data)
                company.save()
        
        # Test first page
        response = client.get('/api/companies?page=1&limit=10')
        assert response.status_code == 200
        data = response.get_json()
        assert len(data['companies']) == 10
        
        # Test second page
        response = client.get('/api/companies?page=2&limit=10')
        assert response.status_code == 200
        data = response.get_json()
        assert len(data['companies']) == 5

    def test_get_company_by_id(self, client, created_company):
        """Test getting company by ID"""
        company_id = created_company.get_id()
        response = client.get(f'/api/companies/{company_id}')
        
        assert response.status_code == 200
        data = response.get_json()
        assert 'company' in data
        assert data['company']['nom'] == created_company.nom
        assert 'recent_jobs' in data['company']

    def test_get_nonexistent_company(self, client, db_cleanup):
        """Test getting non-existent company"""
        response = client.get('/api/companies/507f1f77bcf86cd799439011')
        
        assert response.status_code == 404
        data = response.get_json()
        assert 'non trouvée' in data['message']

    def test_create_company_success(self, client, db_cleanup, sample_company_data):
        """Test creating company via API"""
        response = client.post('/api/companies',
                             data=json.dumps(sample_company_data),
                             content_type='application/json')
        
        assert response.status_code == 201
        data = response.get_json()
        assert 'company_id' in data
        assert 'créée avec succès' in data['message']

    def test_create_company_missing_fields(self, client, db_cleanup):
        """Test creating company with missing required fields"""
        incomplete_data = {
            'email': 'company@example.com',
            'password': 'password123'
            # Missing nom and description
        }
        
        response = client.post('/api/companies',
                             data=json.dumps(incomplete_data),
                             content_type='application/json')
        
        assert response.status_code == 400

    def test_create_company_invalid_email(self, client, db_cleanup, sample_company_data):
        """Test creating company with invalid email"""
        sample_company_data['email'] = 'invalid-email'
        
        response = client.post('/api/companies',
                             data=json.dumps(sample_company_data),
                             content_type='application/json')
        
        assert response.status_code == 400

    def test_create_company_duplicate_email(self, client, created_company, sample_company_data):
        """Test creating company with existing email"""
        response = client.post('/api/companies',
                             data=json.dumps(sample_company_data),
                             content_type='application/json')
        
        assert response.status_code == 409

    def test_update_company_success(self, client, auth_headers_company, created_company):
        """Test updating company successfully"""
        company_id = created_company.get_id()
        update_data = {
            'nom': 'Nouveau Nom Entreprise',
            'secteur': 'Nouvelle Industrie'
        }
        
        response = client.put(f'/api/companies/{company_id}',
                            data=json.dumps(update_data),
                            content_type='application/json',
                            headers=auth_headers_company)
        
        assert response.status_code == 200

    def test_update_company_unauthorized(self, client, created_company):
        """Test updating company without authorization"""
        company_id = created_company.get_id()
        update_data = {'nom': 'Hacker Company'}
        
        response = client.put(f'/api/companies/{company_id}',
                            data=json.dumps(update_data),
                            content_type='application/json')
        
        assert response.status_code == 401

    def test_update_company_wrong_company(self, client, auth_headers_company, db_cleanup, app, sample_company_data):
        """Test updating different company"""
        # Create another company
        with app.app_context():
            from app.models.company import Company
            other_company_data = sample_company_data.copy()
            other_company_data['email'] = 'other@example.com'
            other_company_data['nom'] = 'Other Company'
            other_company = Company(**other_company_data)
            other_company_id = other_company.save()
        
        update_data = {'nom': 'Hacker Company'}
        
        response = client.put(f'/api/companies/{other_company_id}',
                            data=json.dumps(update_data),
                            content_type='application/json',
                            headers=auth_headers_company)
        
        assert response.status_code == 403

    def test_update_company_nonexistent(self, client, auth_headers_company):
        """Test updating non-existent company"""
        update_data = {'nom': 'New Name'}
        
        response = client.put('/api/companies/507f1f77bcf86cd799439011',
                            data=json.dumps(update_data),
                            content_type='application/json',
                            headers=auth_headers_company)
        
        assert response.status_code == 404

    def test_update_company_empty_data(self, client, auth_headers_company, created_company):
        """Test updating company with empty data"""
        company_id = created_company.get_id()
        
        response = client.put(f'/api/companies/{company_id}',
                            data=json.dumps({}),
                            content_type='application/json',
                            headers=auth_headers_company)
        
        assert response.status_code == 400

    def test_update_company_invalid_email(self, client, auth_headers_company, created_company):
        """Test updating company with invalid email"""
        company_id = created_company.get_id()
        update_data = {'email': 'invalid-email'}
        
        response = client.put(f'/api/companies/{company_id}',
                            data=json.dumps(update_data),
                            content_type='application/json',
                            headers=auth_headers_company)
        
        assert response.status_code == 400

    def test_delete_company_success(self, client, auth_headers_company, created_company):
        """Test deleting company successfully"""
        company_id = created_company.get_id()
        
        response = client.delete(f'/api/companies/{company_id}',
                               headers=auth_headers_company)
        
        assert response.status_code == 200

    def test_delete_company_unauthorized(self, client, created_company):
        """Test deleting company without authorization"""
        company_id = created_company.get_id()
        
        response = client.delete(f'/api/companies/{company_id}')
        
        assert response.status_code == 401

    def test_delete_company_wrong_company(self, client, auth_headers_company, db_cleanup, app, sample_company_data):
        """Test deleting different company"""
        # Create another company
        with app.app_context():
            from app.models.company import Company
            other_company_data = sample_company_data.copy()
            other_company_data['email'] = 'other@example.com'
            other_company_data['nom'] = 'Other Company'
            other_company = Company(**other_company_data)
            other_company_id = other_company.save()
        
        response = client.delete(f'/api/companies/{other_company_id}',
                               headers=auth_headers_company)
        
        assert response.status_code == 403

    def test_get_company_profile(self, client, auth_headers_company, created_company):
        """Test getting company profile"""
        company_id = created_company.get_id()
        
        response = client.get(f'/api/companies/{company_id}/profile',
                            headers=auth_headers_company)
        
        assert response.status_code == 200
        data = response.get_json()
        assert 'profile' in data
        assert 'jobs' in data['profile']
        assert 'recent_applications' in data['profile']

    def test_get_company_profile_unauthorized(self, client, created_company):
        """Test getting company profile without authorization"""
        company_id = created_company.get_id()
        
        response = client.get(f'/api/companies/{company_id}/profile')
        
        assert response.status_code == 401

    def test_get_company_profile_wrong_company(self, client, auth_headers_company, db_cleanup, app, sample_company_data):
        """Test getting different company's profile"""
        # Create another company
        with app.app_context():
            from app.models.company import Company
            other_company_data = sample_company_data.copy()
            other_company_data['email'] = 'other@example.com'
            other_company_data['nom'] = 'Other Company'
            other_company = Company(**other_company_data)
            other_company_id = other_company.save()
        
        response = client.get(f'/api/companies/{other_company_id}/profile',
                            headers=auth_headers_company)
        
        assert response.status_code == 403

    def test_get_company_jobs(self, client, created_company, created_job):
        """Test getting company jobs"""
        company_id = created_company.get_id()
        
        response = client.get(f'/api/companies/{company_id}/jobs')
        
        assert response.status_code == 200
        data = response.get_json()
        assert 'jobs' in data
        assert 'company_name' in data
        assert len(data['jobs']) == 1
        assert data['jobs'][0]['titre'] == created_job.titre

    def test_get_company_jobs_pagination(self, client, created_company, db_cleanup, app, sample_job_data):
        """Test company jobs pagination"""
        # Create multiple jobs
        with app.app_context():
            from app.models.job import Job
            for i in range(15):
                job_data = sample_job_data.copy()
                job_data['titre'] = f'Job {i}'
                job = Job(company_id=created_company.get_id(), **job_data)
                job.save()
        
        company_id = created_company.get_id()
        
        # Test first page
        response = client.get(f'/api/companies/{company_id}/jobs?page=1&limit=10')
        assert response.status_code == 200
        data = response.get_json()
        assert len(data['jobs']) == 10
        
        # Test second page
        response = client.get(f'/api/companies/{company_id}/jobs?page=2&limit=10')
        assert response.status_code == 200
        data = response.get_json()
        assert len(data['jobs']) == 5

    def test_get_company_jobs_nonexistent_company(self, client, db_cleanup):
        """Test getting jobs for non-existent company"""
        response = client.get('/api/companies/507f1f77bcf86cd799439011/jobs')
        
        assert response.status_code == 404

    def test_get_company_profile_with_jobs_and_applications(self, client, auth_headers_company, created_company, created_job, created_application):
        """Test getting company profile with jobs and applications"""
        company_id = created_company.get_id()
        
        response = client.get(f'/api/companies/{company_id}/profile',
                            headers=auth_headers_company)
        
        assert response.status_code == 200
        data = response.get_json()
        assert len(data['profile']['jobs']) == 1
        assert len(data['profile']['recent_applications']) == 1
        assert data['profile']['jobs'][0]['applications_count'] == 1

    def test_company_routes_user_access_denied(self, client, auth_headers_user, created_company):
        """Test that users cannot access company-only routes"""
        company_id = created_company.get_id()
        
        # Try to access company profile as user
        response = client.get(f'/api/companies/{company_id}/profile',
                            headers=auth_headers_user)
        
        assert response.status_code == 403

    def test_company_data_sanitization(self, client, created_company):
        """Test that sensitive company data is not exposed"""
        company_id = created_company.get_id()
        response = client.get(f'/api/companies/{company_id}')
        
        assert response.status_code == 200
        data = response.get_json()
        # Password should not be in response
        assert 'password' not in data['company']

    def test_company_jobs_count_accuracy(self, client, created_company, created_job):
        """Test that job count is accurate"""
        company_id = created_company.get_id()
        response = client.get(f'/api/companies/{company_id}')
        
        assert response.status_code == 200
        data = response.get_json()
        assert data['company']['jobs_count'] == 1
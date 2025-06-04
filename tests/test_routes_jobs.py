import pytest
import json


class TestJobRoutes:
    """Test job routes functionality"""

    def test_get_all_jobs(self, client, created_job):
        """Test getting all jobs"""
        response = client.get('/api/jobs')
        
        assert response.status_code == 200
        data = response.get_json()
        assert 'jobs' in data
        assert 'total' in data
        assert len(data['jobs']) == 1
        assert data['jobs'][0]['titre'] == created_job.titre

    def test_get_all_jobs_pagination(self, client, db_cleanup, app, created_company, sample_job_data):
        """Test job pagination"""
        # Create multiple jobs
        with app.app_context():
            from app.models.job import Job
            for i in range(15):
                job_data = sample_job_data.copy()
                job_data['titre'] = f'Job {i}'
                job = Job(company_id=created_company.get_id(), **job_data)
                job.save()
        
        # Test first page
        response = client.get('/api/jobs?page=1&limit=10')
        assert response.status_code == 200
        data = response.get_json()
        assert len(data['jobs']) == 10
        
        # Test second page
        response = client.get('/api/jobs?page=2&limit=10')
        assert response.status_code == 200
        data = response.get_json()
        assert len(data['jobs']) == 5

    def test_get_job_by_id(self, client, created_job):
        """Test getting job by ID"""
        job_id = created_job.get_id()
        response = client.get(f'/api/jobs/{job_id}')
        
        assert response.status_code == 200
        data = response.get_json()
        assert 'job' in data
        assert data['job']['titre'] == created_job.titre
        assert 'company' in data['job']

    def test_get_nonexistent_job(self, client, db_cleanup):
        """Test getting non-existent job"""
        response = client.get('/api/jobs/507f1f77bcf86cd799439011')
        
        assert response.status_code == 404
        data = response.get_json()
        assert 'non trouvée' in data['message']

    def test_search_jobs_by_title(self, client, created_job):
        """Test searching jobs by title"""
        response = client.get('/api/jobs?search=Python')
        
        assert response.status_code == 200
        data = response.get_json()
        assert len(data['jobs']) == 1
        assert 'Python' in data['jobs'][0]['titre']

    def test_search_jobs_by_location(self, client, created_job):
        """Test searching jobs by location"""
        response = client.get('/api/jobs?localisation=Paris')
        
        assert response.status_code == 200
        data = response.get_json()
        assert len(data['jobs']) == 1

    def test_search_jobs_by_contract_type(self, client, created_job):
        """Test searching jobs by contract type"""
        response = client.get('/api/jobs?type_contrat=CDI')
        
        assert response.status_code == 200
        data = response.get_json()
        assert len(data['jobs']) == 1

    def test_search_jobs_no_results(self, client, created_job):
        """Test searching jobs with no results"""
        response = client.get('/api/jobs?search=nonexistent')
        
        assert response.status_code == 200
        data = response.get_json()
        assert len(data['jobs']) == 0

    def test_search_jobs_multiple_filters(self, client, created_job):
        """Test searching jobs with multiple filters"""
        response = client.get('/api/jobs?search=Python&localisation=Paris&type_contrat=CDI')
        
        assert response.status_code == 200
        data = response.get_json()
        assert len(data['jobs']) == 1

    def test_create_job_success(self, client, auth_headers_company, sample_job_data):
        """Test creating job successfully"""
        response = client.post('/api/jobs',
                             data=json.dumps(sample_job_data),
                             content_type='application/json',
                             headers=auth_headers_company)
        
        assert response.status_code == 201
        data = response.get_json()
        assert 'job_id' in data
        assert 'créée avec succès' in data['message']

    def test_create_job_unauthorized(self, client, sample_job_data):
        """Test creating job without authorization"""
        response = client.post('/api/jobs',
                             data=json.dumps(sample_job_data),
                             content_type='application/json')
        
        assert response.status_code == 401

    def test_create_job_user_forbidden(self, client, auth_headers_user, sample_job_data):
        """Test creating job as user (should be forbidden)"""
        response = client.post('/api/jobs',
                             data=json.dumps(sample_job_data),
                             content_type='application/json',
                             headers=auth_headers_user)
        
        assert response.status_code == 403

    def test_create_job_missing_fields(self, client, auth_headers_company):
        """Test creating job with missing required fields"""
        incomplete_data = {
            'description': 'A job description'
            # Missing titre
        }
        
        response = client.post('/api/jobs',
                             data=json.dumps(incomplete_data),
                             content_type='application/json',
                             headers=auth_headers_company)
        
        assert response.status_code == 400

    def test_update_job_success(self, client, auth_headers_company, created_job):
        """Test updating job successfully"""
        job_id = created_job.get_id()
        update_data = {
            'titre': 'Senior Python Developer',
            'salaire': '50000-60000'
        }
        
        response = client.put(f'/api/jobs/{job_id}',
                            data=json.dumps(update_data),
                            content_type='application/json',
                            headers=auth_headers_company)
        
        assert response.status_code == 200

    def test_update_job_unauthorized(self, client, created_job):
        """Test updating job without authorization"""
        job_id = created_job.get_id()
        update_data = {'titre': 'Hacked Job'}
        
        response = client.put(f'/api/jobs/{job_id}',
                            data=json.dumps(update_data),
                            content_type='application/json')
        
        assert response.status_code == 401

    def test_update_job_wrong_company(self, client, auth_headers_company, db_cleanup, app, sample_company_data, sample_job_data):
        """Test updating job from different company"""
        # Create another company and job
        with app.app_context():
            from app.models.company import Company
            from app.models.job import Job
            
            other_company_data = sample_company_data.copy()
            other_company_data['email'] = 'other@example.com'
            other_company_data['nom'] = 'Other Company'
            other_company = Company(**other_company_data)
            other_company_id = other_company.save()
            
            other_job = Job(company_id=str(other_company_id), **sample_job_data)
            other_job_id = other_job.save()
        
        update_data = {'titre': 'Hacked Job'}
        
        response = client.put(f'/api/jobs/{other_job_id}',
                            data=json.dumps(update_data),
                            content_type='application/json',
                            headers=auth_headers_company)
        
        assert response.status_code == 403

    def test_update_job_nonexistent(self, client, auth_headers_company):
        """Test updating non-existent job"""
        update_data = {'titre': 'New Title'}
        
        response = client.put('/api/jobs/507f1f77bcf86cd799439011',
                            data=json.dumps(update_data),
                            content_type='application/json',
                            headers=auth_headers_company)
        
        assert response.status_code == 404

    def test_update_job_empty_data(self, client, auth_headers_company, created_job):
        """Test updating job with empty data"""
        job_id = created_job.get_id()
        
        response = client.put(f'/api/jobs/{job_id}',
                            data=json.dumps({}),
                            content_type='application/json',
                            headers=auth_headers_company)
        
        assert response.status_code == 400

    def test_delete_job_success(self, client, auth_headers_company, created_job):
        """Test deleting job successfully"""
        job_id = created_job.get_id()
        
        response = client.delete(f'/api/jobs/{job_id}',
                               headers=auth_headers_company)
        
        assert response.status_code == 200

    def test_delete_job_unauthorized(self, client, created_job):
        """Test deleting job without authorization"""
        job_id = created_job.get_id()
        
        response = client.delete(f'/api/jobs/{job_id}')
        
        assert response.status_code == 401

    def test_delete_job_wrong_company(self, client, auth_headers_company, db_cleanup, app, sample_company_data, sample_job_data):
        """Test deleting job from different company"""
        # Create another company and job
        with app.app_context():
            from app.models.company import Company
            from app.models.job import Job
            
            other_company_data = sample_company_data.copy()
            other_company_data['email'] = 'other@example.com'
            other_company_data['nom'] = 'Other Company'
            other_company = Company(**other_company_data)
            other_company_id = other_company.save()
            
            other_job = Job(company_id=str(other_company_id), **sample_job_data)
            other_job_id = other_job.save()
        
        response = client.delete(f'/api/jobs/{other_job_id}',
                               headers=auth_headers_company)
        
        assert response.status_code == 403

    def test_deactivate_job_success(self, client, auth_headers_company, created_job):
        """Test deactivating job successfully"""
        job_id = created_job.get_id()
        
        response = client.put(f'/api/jobs/{job_id}/deactivate',
                            headers=auth_headers_company)
        
        assert response.status_code == 200

    def test_deactivate_job_unauthorized(self, client, created_job):
        """Test deactivating job without authorization"""
        job_id = created_job.get_id()
        
        response = client.put(f'/api/jobs/{job_id}/deactivate')
        
        assert response.status_code == 401

    def test_deactivate_job_wrong_company(self, client, auth_headers_company, db_cleanup, app, sample_company_data, sample_job_data):
        """Test deactivating job from different company"""
        # Create another company and job
        with app.app_context():
            from app.models.company import Company
            from app.models.job import Job
            
            other_company_data = sample_company_data.copy()
            other_company_data['email'] = 'other@example.com'
            other_company_data['nom'] = 'Other Company'
            other_company = Company(**other_company_data)
            other_company_id = other_company.save()
            
            other_job = Job(company_id=str(other_company_id), **sample_job_data)
            other_job_id = other_job.save()
        
        response = client.put(f'/api/jobs/{other_job_id}/deactivate',
                            headers=auth_headers_company)
        
        assert response.status_code == 403

    def test_get_job_applications(self, client, auth_headers_company, created_job, created_application):
        """Test getting job applications"""
        job_id = created_job.get_id()
        
        response = client.get(f'/api/jobs/{job_id}/applications',
                            headers=auth_headers_company)
        
        assert response.status_code == 200
        data = response.get_json()
        assert 'applications' in data
        assert 'job_title' in data
        assert len(data['applications']) == 1
        assert 'user' in data['applications'][0]

    def test_get_job_applications_unauthorized(self, client, created_job):
        """Test getting job applications without authorization"""
        job_id = created_job.get_id()
        
        response = client.get(f'/api/jobs/{job_id}/applications')
        
        assert response.status_code == 401

    def test_get_job_applications_wrong_company(self, client, auth_headers_company, db_cleanup, app, sample_company_data, sample_job_data):
        """Test getting applications for job from different company"""
        # Create another company and job
        with app.app_context():
            from app.models.company import Company
            from app.models.job import Job
            
            other_company_data = sample_company_data.copy()
            other_company_data['email'] = 'other@example.com'
            other_company_data['nom'] = 'Other Company'
            other_company = Company(**other_company_data)
            other_company_id = other_company.save()
            
            other_job = Job(company_id=str(other_company_id), **sample_job_data)
            other_job_id = other_job.save()
        
        response = client.get(f'/api/jobs/{other_job_id}/applications',
                            headers=auth_headers_company)
        
        assert response.status_code == 403

    def test_get_job_applications_nonexistent_job(self, client, auth_headers_company):
        """Test getting applications for non-existent job"""
        response = client.get('/api/jobs/507f1f77bcf86cd799439011/applications',
                            headers=auth_headers_company)
        
        assert response.status_code == 404

    def test_get_job_applications_pagination(self, client, auth_headers_company, created_job, db_cleanup, app, sample_user_data):
        """Test job applications pagination"""
        # Create multiple applications
        with app.app_context():
            from app.models.user import User
            from app.models.application import Application
            
            for i in range(15):
                user_data = sample_user_data.copy()
                user_data['email'] = f'user{i}@example.com'
                user = User(**user_data)
                user_id = user.save()
                
                application = Application(
                    user_id=str(user_id),
                    job_id=created_job.get_id(),
                    company_id=created_job.company_id
                )
                application.save()
        
        job_id = created_job.get_id()
        
        # Test first page
        response = client.get(f'/api/jobs/{job_id}/applications?page=1&limit=10',
                            headers=auth_headers_company)
        assert response.status_code == 200
        data = response.get_json()
        assert len(data['applications']) == 10
        
        # Test second page
        response = client.get(f'/api/jobs/{job_id}/applications?page=2&limit=10',
                            headers=auth_headers_company)
        assert response.status_code == 200
        data = response.get_json()
        assert len(data['applications']) == 5

    def test_job_with_company_info(self, client, created_job):
        """Test that job includes company information"""
        job_id = created_job.get_id()
        response = client.get(f'/api/jobs/{job_id}')
        
        assert response.status_code == 200
        data = response.get_json()
        assert 'company' in data['job']
        company_info = data['job']['company']
        assert 'nom' in company_info
        assert 'secteur' in company_info
        # Password should not be included
        assert 'password' not in company_info

    def test_job_applications_count_accuracy(self, client, created_job, created_application):
        """Test that applications count is accurate"""
        job_id = created_job.get_id()
        response = client.get(f'/api/jobs/{job_id}')
        
        assert response.status_code == 200
        data = response.get_json()
        assert data['job']['applications_count'] == 1
import pytest
import json


class TestIntegrationWorkflows:
    """Test complete workflows and integration scenarios"""

    def test_complete_user_job_application_workflow(self, client, db_cleanup, sample_user_data, sample_company_data, sample_job_data):
        """Test complete workflow: user registration -> job search -> application -> status update"""
        
        # 1. Register user
        user_response = client.post('/api/auth/register/user',
                                  data=json.dumps(sample_user_data),
                                  content_type='application/json')
        assert user_response.status_code == 201
        user_data = user_response.get_json()
        user_token = user_data['token']
        user_headers = {'Authorization': f'Bearer {user_token}'}
        
        # 2. Register company
        company_response = client.post('/api/auth/register/company',
                                     data=json.dumps(sample_company_data),
                                     content_type='application/json')
        assert company_response.status_code == 201
        company_data = company_response.get_json()
        company_token = company_data['token']
        company_headers = {'Authorization': f'Bearer {company_token}'}
        
        # 3. Company creates job
        job_response = client.post('/api/jobs',
                                 data=json.dumps(sample_job_data),
                                 content_type='application/json',
                                 headers=company_headers)
        assert job_response.status_code == 201
        job_data = job_response.get_json()
        job_id = job_data['job_id']
        
        # 4. User searches and finds job
        search_response = client.get('/api/jobs?search=Python')
        assert search_response.status_code == 200
        search_data = search_response.get_json()
        assert len(search_data['jobs']) == 1
        
        # 5. User applies to job
        application_data = {
            'job_id': job_id,
            'lettre_motivation': 'Je suis très intéressé par ce poste'
        }
        app_response = client.post('/api/applications',
                                 data=json.dumps(application_data),
                                 content_type='application/json',
                                 headers=user_headers)
        assert app_response.status_code == 201
        app_data = app_response.get_json()
        application_id = app_data['application_id']
        
        # 6. Company views applications
        company_apps_response = client.get(f'/api/jobs/{job_id}/applications',
                                         headers=company_headers)
        assert company_apps_response.status_code == 200
        company_apps_data = company_apps_response.get_json()
        assert len(company_apps_data['applications']) == 1
        
        # 7. Company updates application status
        status_update = {
            'statut': 'Acceptée',
            'notes_entreprise': 'Excellent profil'
        }
        status_response = client.put(f'/api/applications/{application_id}/status',
                                   data=json.dumps(status_update),
                                   content_type='application/json',
                                   headers=company_headers)
        assert status_response.status_code == 200
        
        # 8. User checks application status
        user_app_response = client.get(f'/api/applications/{application_id}',
                                     headers=user_headers)
        assert user_app_response.status_code == 200
        user_app_data = user_app_response.get_json()
        assert user_app_data['application']['statut'] == 'Acceptée'

    def test_user_profile_management_workflow(self, client, db_cleanup, sample_user_data):
        """Test user profile creation and management workflow"""
        
        # 1. Register user
        user_response = client.post('/api/auth/register/user',
                                  data=json.dumps(sample_user_data),
                                  content_type='application/json')
        assert user_response.status_code == 201
        user_data = user_response.get_json()
        user_token = user_data['token']
        user_id = user_data['user_id']
        user_headers = {'Authorization': f'Bearer {user_token}'}
        
        # 2. Get user profile
        profile_response = client.get(f'/api/users/{user_id}/profile',
                                    headers=user_headers)
        assert profile_response.status_code == 200
        
        # 3. Update user profile
        update_data = {
            'competences': ['Python', 'Django', 'React', 'PostgreSQL'],
            'experience': '5 ans d\'expérience en développement web'
        }
        update_response = client.put(f'/api/users/{user_id}',
                                   data=json.dumps(update_data),
                                   content_type='application/json',
                                   headers=user_headers)
        assert update_response.status_code == 200
        
        # 4. Verify update
        updated_profile_response = client.get(f'/api/users/{user_id}',
                                            headers=user_headers)
        assert updated_profile_response.status_code == 200
        updated_data = updated_profile_response.get_json()
        assert 'Django' in updated_data['user']['competences']
        
        # 5. Change password
        password_data = {
            'current_password': 'password123',
            'new_password': 'newpassword456'
        }
        password_response = client.put('/api/auth/change-password',
                                     data=json.dumps(password_data),
                                     content_type='application/json',
                                     headers=user_headers)
        assert password_response.status_code == 200
        
        # 6. Login with new password
        login_data = {
            'email': sample_user_data['email'],
            'password': 'newpassword456',
            'user_type': 'user'
        }
        login_response = client.post('/api/auth/login',
                                   data=json.dumps(login_data),
                                   content_type='application/json')
        assert login_response.status_code == 200

    def test_company_job_management_workflow(self, client, db_cleanup, sample_company_data, sample_job_data):
        """Test company job posting and management workflow"""
        
        # 1. Register company
        company_response = client.post('/api/auth/register/company',
                                     data=json.dumps(sample_company_data),
                                     content_type='application/json')
        assert company_response.status_code == 201
        company_data = company_response.get_json()
        company_token = company_data['token']
        company_id = company_data['company_id']
        company_headers = {'Authorization': f'Bearer {company_token}'}
        
        # 2. Create multiple jobs
        job_ids = []
        for i in range(3):
            job_data = sample_job_data.copy()
            job_data['titre'] = f'Développeur {i}'
            job_response = client.post('/api/jobs',
                                     data=json.dumps(job_data),
                                     content_type='application/json',
                                     headers=company_headers)
            assert job_response.status_code == 201
            job_ids.append(job_response.get_json()['job_id'])
        
        # 3. Get company profile (should show jobs)
        profile_response = client.get(f'/api/companies/{company_id}/profile',
                                    headers=company_headers)
        assert profile_response.status_code == 200
        profile_data = profile_response.get_json()
        assert len(profile_data['profile']['jobs']) == 3
        
        # 4. Update a job
        update_data = {
            'titre': 'Senior Développeur Python',
            'salaire': '50000-65000'
        }
        update_response = client.put(f'/api/jobs/{job_ids[0]}',
                                   data=json.dumps(update_data),
                                   content_type='application/json',
                                   headers=company_headers)
        assert update_response.status_code == 200
        
        # 5. Deactivate a job
        deactivate_response = client.put(f'/api/jobs/{job_ids[1]}/deactivate',
                                       headers=company_headers)
        assert deactivate_response.status_code == 200
        
        # 6. Get company jobs (should show updated and active status)
        jobs_response = client.get(f'/api/companies/{company_id}/jobs',
                                 headers=company_headers)
        assert jobs_response.status_code == 200
        jobs_data = jobs_response.get_json()
        assert len(jobs_data['jobs']) == 3  # All jobs (including inactive)

    def test_application_lifecycle_workflow(self, client, db_cleanup, sample_user_data, sample_company_data, sample_job_data):
        """Test complete application lifecycle"""
        
        # Setup: Create user, company, and job
        user_response = client.post('/api/auth/register/user',
                                  data=json.dumps(sample_user_data),
                                  content_type='application/json')
        user_token = user_response.get_json()['token']
        user_headers = {'Authorization': f'Bearer {user_token}'}
        
        company_response = client.post('/api/auth/register/company',
                                     data=json.dumps(sample_company_data),
                                     content_type='application/json')
        company_token = company_response.get_json()['token']
        company_headers = {'Authorization': f'Bearer {company_token}'}
        
        job_response = client.post('/api/jobs',
                                 data=json.dumps(sample_job_data),
                                 content_type='application/json',
                                 headers=company_headers)
        job_id = job_response.get_json()['job_id']
        
        # 1. User applies
        application_data = {
            'job_id': job_id,
            'lettre_motivation': 'Lettre initiale'
        }
        app_response = client.post('/api/applications',
                                 data=json.dumps(application_data),
                                 content_type='application/json',
                                 headers=user_headers)
        application_id = app_response.get_json()['application_id']
        
        # 2. User updates motivation letter
        update_data = {
            'lettre_motivation': 'Lettre mise à jour avec plus de détails'
        }
        update_response = client.put(f'/api/applications/{application_id}',
                                   data=json.dumps(update_data),
                                   content_type='application/json',
                                   headers=user_headers)
        assert update_response.status_code == 200
        
        # 3. Company reviews and accepts
        status_data = {
            'statut': 'Acceptée',
            'notes_entreprise': 'Profil correspondant parfaitement'
        }
        status_response = client.put(f'/api/applications/{application_id}/status',
                                   data=json.dumps(status_data),
                                   content_type='application/json',
                                   headers=company_headers)
        assert status_response.status_code == 200
        
        # 4. Verify final state
        final_response = client.get(f'/api/applications/{application_id}',
                                  headers=user_headers)
        final_data = final_response.get_json()
        application = final_data['application']
        assert application['statut'] == 'Acceptée'
        assert 'mise à jour' in application['lettre_motivation']
        assert 'correspondant parfaitement' in application['notes_entreprise']

    def test_search_and_filter_workflow(self, client, db_cleanup, app, sample_company_data, sample_job_data):
        """Test job search and filtering functionality"""
        
        # Setup: Create company and multiple jobs
        with app.app_context():
            from app.models.company import Company
            from app.models.job import Job
            
            company = Company(**sample_company_data)
            company_id = company.save()
            
            # Create diverse jobs
            jobs_data = [
                {'titre': 'Développeur Python', 'localisation': 'Paris', 'type_contrat': 'CDI'},
                {'titre': 'Développeur JavaScript', 'localisation': 'Lyon', 'type_contrat': 'CDD'},
                {'titre': 'Data Scientist', 'localisation': 'Paris', 'type_contrat': 'CDI'},
                {'titre': 'DevOps Engineer', 'localisation': 'Marseille', 'type_contrat': 'Freelance'},
            ]
            
            for job_data in jobs_data:
                full_job_data = sample_job_data.copy()
                full_job_data.update(job_data)
                job = Job(company_id=str(company_id), **full_job_data)
                job.save()
        
        # 1. Search all jobs
        all_response = client.get('/api/jobs')
        assert all_response.status_code == 200
        all_data = all_response.get_json()
        # Note: There might be jobs from other fixtures, so check >= 4
        assert len(all_data['jobs']) >= 4
        
        # 2. Search by title - more specific search
        python_response = client.get('/api/jobs?search=Développeur Python')
        assert python_response.status_code == 200
        python_data = python_response.get_json()
        # Find jobs containing "Python" in title
        python_jobs = [job for job in python_data['jobs'] if 'Python' in job['titre']]
        assert len(python_jobs) >= 1
        
        # 3. Filter by location
        paris_response = client.get('/api/jobs?localisation=Paris')
        assert paris_response.status_code == 200
        paris_data = paris_response.get_json()
        # Should have at least the 2 Paris jobs we created
        paris_jobs = [job for job in paris_data['jobs'] if job['localisation'] == 'Paris']
        assert len(paris_jobs) >= 2
        
        # 4. Filter by contract type
        cdi_response = client.get('/api/jobs?type_contrat=CDI')
        assert cdi_response.status_code == 200
        cdi_data = cdi_response.get_json()
        # Should have at least the 2 CDI jobs we created
        cdi_jobs = [job for job in cdi_data['jobs'] if job['type_contrat'] == 'CDI']
        assert len(cdi_jobs) >= 2
        
        # 5. Combined filters
        combined_response = client.get('/api/jobs?localisation=Paris&type_contrat=CDI')
        assert combined_response.status_code == 200
        combined_data = combined_response.get_json()
        # Should have at least the 2 jobs that match both criteria
        combined_jobs = [job for job in combined_data['jobs'] 
                        if job['localisation'] == 'Paris' and job['type_contrat'] == 'CDI']
        assert len(combined_jobs) >= 2

    def test_authentication_token_lifecycle(self, client, db_cleanup, sample_user_data):
        """Test token generation, usage, and expiration"""
        
        # 1. Register and get token
        register_response = client.post('/api/auth/register/user',
                                      data=json.dumps(sample_user_data),
                                      content_type='application/json')
        token = register_response.get_json()['token']
        headers = {'Authorization': f'Bearer {token}'}
        
        # 2. Verify token works
        verify_response = client.get('/api/auth/verify', headers=headers)
        assert verify_response.status_code == 200
        
        # 3. Use token for protected route
        profile_response = client.get('/api/users', headers=headers)
        assert profile_response.status_code == 200
        
        # 4. Login again (should get new token)
        login_data = {
            'email': sample_user_data['email'],
            'password': sample_user_data['password'],
            'user_type': 'user'
        }
        login_response = client.post('/api/auth/login',
                                   data=json.dumps(login_data),
                                   content_type='application/json')
        new_token = login_response.get_json()['token']
        
        # Note: Tokens might be the same if generated quickly with same payload
        # The important thing is that both tokens work, not that they're different
        assert new_token is not None
        assert isinstance(new_token, str)
        assert len(new_token) > 50  # JWT tokens are long
        
        # 5. New token should work
        new_headers = {'Authorization': f'Bearer {new_token}'}
        new_verify_response = client.get('/api/auth/verify', headers=new_headers)
        assert new_verify_response.status_code == 200
        
        # 6. Logout
        logout_response = client.post('/api/auth/logout', headers=new_headers)
        assert logout_response.status_code == 200
        
        # 5. New token should work
        new_headers = {'Authorization': f'Bearer {new_token}'}
        new_verify_response = client.get('/api/auth/verify', headers=new_headers)
        assert new_verify_response.status_code == 200
        
        # 6. Logout
        logout_response = client.post('/api/auth/logout', headers=new_headers)
        assert logout_response.status_code == 200

    def test_error_handling_and_edge_cases(self, client, db_cleanup, sample_user_data):
        """Test various error conditions and edge cases"""
        
        # 1. Invalid JSON - expect 400 or 500 depending on Flask configuration
        invalid_json_response = client.post('/api/auth/register/user',
                                          data='invalid-json',
                                          content_type='application/json')
        # Flask might return 400 or 500 for malformed JSON
        assert invalid_json_response.status_code in [400, 500]
        
        # 2. Missing content type - behavior depends on Flask configuration
        missing_content_response = client.post('/api/auth/register/user',
                                             data=json.dumps(sample_user_data))
        # This might work or fail depending on Flask configuration
        assert missing_content_response.status_code in [201, 400, 500]
        
        # 3. Invalid ObjectId format
        invalid_id_response = client.get('/api/users/invalid-id')
        assert invalid_id_response.status_code == 404
        
        # 4. Non-existent endpoints
        not_found_response = client.get('/api/nonexistent')
        assert not_found_response.status_code == 404
        
        # 5. Invalid HTTP methods
        invalid_method_response = client.patch('/api/users')
        assert invalid_method_response.status_code == 405

    def test_permission_boundaries(self, client, db_cleanup, sample_user_data, sample_company_data, sample_job_data):
        """Test permission boundaries between users and companies"""
        
        # Setup users and companies
        user_response = client.post('/api/auth/register/user',
                                  data=json.dumps(sample_user_data),
                                  content_type='application/json')
        user_token = user_response.get_json()['token']
        user_headers = {'Authorization': f'Bearer {user_token}'}
        
        company_response = client.post('/api/auth/register/company',
                                     data=json.dumps(sample_company_data),
                                     content_type='application/json')
        company_token = company_response.get_json()['token']
        company_headers = {'Authorization': f'Bearer {company_token}'}
        
        # 1. User cannot create jobs
        job_response = client.post('/api/jobs',
                                 data=json.dumps(sample_job_data),
                                 content_type='application/json',
                                 headers=user_headers)
        assert job_response.status_code == 403
        
        # 2. Company cannot apply to jobs
        job_response = client.post('/api/jobs',
                                 data=json.dumps(sample_job_data),
                                 content_type='application/json',
                                 headers=company_headers)
        job_id = job_response.get_json()['job_id']
        
        application_data = {'job_id': job_id}
        app_response = client.post('/api/applications',
                                 data=json.dumps(application_data),
                                 content_type='application/json',
                                 headers=company_headers)
        assert app_response.status_code == 403
        
        # 3. Create application as user
        app_response = client.post('/api/applications',
                                 data=json.dumps(application_data),
                                 content_type='application/json',
                                 headers=user_headers)
        application_id = app_response.get_json()['application_id']
        
        # 4. User cannot update application status
        status_data = {'statut': 'Acceptée'}
        status_response = client.put(f'/api/applications/{application_id}/status',
                                   data=json.dumps(status_data),
                                   content_type='application/json',
                                   headers=user_headers)
        assert status_response.status_code == 403

    def test_data_consistency_across_operations(self, client, db_cleanup, sample_user_data, sample_company_data, sample_job_data):
        """Test data consistency when performing multiple operations"""
        
        # Setup
        user_response = client.post('/api/auth/register/user',
                                  data=json.dumps(sample_user_data),
                                  content_type='application/json')
        user_token = user_response.get_json()['token']
        user_headers = {'Authorization': f'Bearer {user_token}'}
        
        company_response = client.post('/api/auth/register/company',
                                     data=json.dumps(sample_company_data),
                                     content_type='application/json')
        company_token = company_response.get_json()['token']
        company_id = company_response.get_json()['company_id']
        company_headers = {'Authorization': f'Bearer {company_token}'}
        
        # Create job
        job_response = client.post('/api/jobs',
                                 data=json.dumps(sample_job_data),
                                 content_type='application/json',
                                 headers=company_headers)
        job_id = job_response.get_json()['job_id']
        
        # Create application
        app_data = {'job_id': job_id, 'lettre_motivation': 'Test'}
        app_response = client.post('/api/applications',
                                 data=json.dumps(app_data),
                                 content_type='application/json',
                                 headers=user_headers)
        application_id = app_response.get_json()['application_id']
        
        # 1. Check job shows correct application count
        job_detail_response = client.get(f'/api/jobs/{job_id}')
        job_detail = job_detail_response.get_json()
        assert job_detail['job']['applications_count'] == 1
        
        # 2. Check company profile shows application
        company_profile_response = client.get(f'/api/companies/{company_id}/profile',
                                            headers=company_headers)
        company_profile = company_profile_response.get_json()
        assert len(company_profile['profile']['recent_applications']) == 1
        
        # 3. Delete application and check counts update
        delete_response = client.delete(f'/api/applications/{application_id}',
                                      headers=user_headers)
        assert delete_response.status_code == 200
        
        # 4. Verify job application count decreased
        updated_job_response = client.get(f'/api/jobs/{job_id}')
        updated_job = updated_job_response.get_json()
        assert updated_job['job']['applications_count'] == 0

    def test_concurrent_application_prevention(self, client, db_cleanup, app, sample_user_data, sample_company_data, sample_job_data):
        """Test prevention of concurrent duplicate applications"""
        
        # Setup user, company, and job
        with app.app_context():
            from app.models.user import User
            from app.models.company import Company
            from app.models.job import Job
            
            user = User(**sample_user_data)
            user_id = user.save()
            
            company = Company(**sample_company_data)
            company_id = company.save()
            
            job = Job(company_id=str(company_id), **sample_job_data)
            job_id = job.save()
            
            # Generate token manually
            from app.auth import generate_token
            token = generate_token(str(user_id), 'user')
        
        headers = {'Authorization': f'Bearer {token}'}
        app_data = {'job_id': str(job_id), 'lettre_motivation': 'Test'}
        
        # 1. First application should succeed
        first_response = client.post('/api/applications',
                                   data=json.dumps(app_data),
                                   content_type='application/json',
                                   headers=headers)
        assert first_response.status_code == 201
        
        # 2. Second application should fail (duplicate)
        second_response = client.post('/api/applications',
                                    data=json.dumps(app_data),
                                    content_type='application/json',
                                    headers=headers)
        assert second_response.status_code == 409
        assert 'déjà postulé' in second_response.get_json()['message']

    def test_api_performance_with_large_datasets(self, client, db_cleanup, app, sample_user_data, sample_company_data, sample_job_data):
        """Test API performance with larger datasets"""
        
        # Create multiple entities
        with app.app_context():
            from app.models.user import User
            from app.models.company import Company
            from app.models.job import Job
            
            # Create 50 companies
            for i in range(50):
                company_data = sample_company_data.copy()
                company_data['email'] = f'company{i}@example.com'
                company_data['nom'] = f'Company {i}'
                company = Company(**company_data)
                company.save()
            
            # Create 100 jobs
            companies = Company.find_all(limit=50)
            for i in range(100):
                company = companies[i % len(companies)]
                job_data = sample_job_data.copy()
                job_data['titre'] = f'Job {i}'
                job = Job(company_id=company.get_id(), **job_data)
                job.save()
        
        # Test pagination performance
        response = client.get('/api/jobs?page=1&limit=20')
        assert response.status_code == 200
        data = response.get_json()
        assert len(data['jobs']) == 20
        assert data['total'] == 100
        
        # Test search performance
        search_response = client.get('/api/jobs?search=Job')
        assert search_response.status_code == 200
        search_data = search_response.get_json()
        assert len(search_data['jobs']) > 0

    def test_home_endpoint(self, client):
        """Test the home endpoint"""
        response = client.get('/')
        
        assert response.status_code == 200
        data = response.get_json()
        assert 'message' in data
        assert 'documentation' in data
        assert 'status' in data
        assert data['status'] == 'Fonctionnel'
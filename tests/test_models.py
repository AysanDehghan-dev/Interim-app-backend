import pytest
from datetime import datetime
from app.models.user import User
from app.models.company import Company
from app.models.job import Job
from app.models.application import Application


class TestUserModel:
    """Test User model functionality"""

    def test_user_creation(self, app, db_cleanup):
        """Test user creation with valid data"""
        with app.app_context():
            user = User(
                email='test@example.com',
                password='password123',
                nom='Dupont',
                prenom='Jean',
                telephone='0123456789',
                competences=['Python', 'Flask'],
                experience='2 ans'
            )
            
            user_id = user.save()
            assert user_id is not None
            assert user.email == 'test@example.com'
            assert user.nom == 'Dupont'
            assert user.prenom == 'Jean'

    def test_user_password_hashing(self, app, db_cleanup):
        """Test password is properly hashed"""
        with app.app_context():
            user = User(
                email='test@example.com',
                password='password123',
                nom='Dupont',
                prenom='Jean'
            )
            
            # Password should be hashed, not plain text
            assert user.password != 'password123'
            assert user.check_password('password123') is True
            assert user.check_password('wrongpassword') is False

    def test_user_to_dict(self, app, db_cleanup):
        """Test user to_dict method"""
        with app.app_context():
            user = User(
                email='test@example.com',
                password='password123',
                nom='Dupont',
                prenom='Jean',
                competences=['Python']
            )
            
            user_dict = user.to_dict()
            assert 'email' in user_dict
            assert 'nom' in user_dict
            assert 'prenom' in user_dict
            assert 'competences' in user_dict
            assert 'password' not in user_dict  # Password should not be in dict

    def test_find_user_by_id(self, app, created_user):
        """Test finding user by ID"""
        with app.app_context():
            found_user = User.find_by_id(created_user.get_id())
            assert found_user is not None
            assert found_user.email == created_user.email

    def test_find_user_by_email(self, app, created_user):
        """Test finding user by email"""
        with app.app_context():
            found_user = User.find_by_email(created_user.email)
            assert found_user is not None
            assert found_user.get_id() == created_user.get_id()

    def test_find_nonexistent_user(self, app, db_cleanup):
        """Test finding non-existent user"""
        with app.app_context():
            user = User.find_by_id('507f1f77bcf86cd799439011')  # Valid ObjectId format
            assert user is None

    def test_update_user(self, app, created_user):
        """Test updating user information"""
        with app.app_context():
            user_id = created_user.get_id()
            update_data = {
                'nom': 'Nouveau Nom',
                'competences': ['Python', 'Django', 'React']
            }
            
            success = created_user.update(user_id, update_data)
            assert success is True
            
            updated_user = User.find_by_id(user_id)
            assert updated_user.nom == 'Nouveau Nom'
            assert 'Django' in updated_user.competences

    def test_delete_user(self, app, created_user):
        """Test deleting user"""
        with app.app_context():
            user_id = created_user.get_id()
            success = User.delete_by_id(user_id)
            assert success is True
            
            deleted_user = User.find_by_id(user_id)
            assert deleted_user is None

    def test_user_count(self, app, db_cleanup, created_user):
        """Test counting users"""
        with app.app_context():
            count = User.count_all()
            assert count == 1


class TestCompanyModel:
    """Test Company model functionality"""

    def test_company_creation(self, app, db_cleanup):
        """Test company creation"""
        with app.app_context():
            company = Company(
                email='company@example.com',
                password='password123',
                nom='Test Company',
                description='Test description',
                secteur='Tech'
            )
            
            company_id = company.save()
            assert company_id is not None
            assert company.email == 'company@example.com'

    def test_company_password_hashing(self, app, db_cleanup):
        """Test company password hashing"""
        with app.app_context():
            company = Company(
                email='company@example.com',
                password='password123',
                nom='Test Company',
                description='Test description'
            )
            
            assert company.password != 'password123'
            assert company.check_password('password123') is True

    def test_find_company_by_email(self, app, created_company):
        """Test finding company by email"""
        with app.app_context():
            found_company = Company.find_by_email(created_company.email)
            assert found_company is not None
            assert found_company.get_id() == created_company.get_id()

    def test_company_jobs_count(self, app, created_company, created_job):
        """Test getting company's job count"""
        with app.app_context():
            count = created_company.get_jobs_count()
            assert count == 1


class TestJobModel:
    """Test Job model functionality"""

    def test_job_creation(self, app, db_cleanup, created_company):
        """Test job creation"""
        with app.app_context():
            job = Job(
                company_id=created_company.get_id(),
                titre='Developer',
                description='Job description',
                type_contrat='CDI',
                localisation='Paris'
            )
            
            job_id = job.save()
            assert job_id is not None
            assert job.titre == 'Developer'
            assert job.actif is True  # Should be active by default

    def test_job_to_dict(self, app, created_job):
        """Test job to_dict method"""
        with app.app_context():
            job_dict = created_job.to_dict()
            assert 'titre' in job_dict
            assert 'description' in job_dict
            assert 'company_id' in job_dict
            assert 'actif' in job_dict

    def test_find_jobs_by_company(self, app, created_job):
        """Test finding jobs by company"""
        with app.app_context():
            jobs = Job.find_by_company(created_job.company_id)
            assert len(jobs) == 1
            assert jobs[0].get_id() == created_job.get_id()

    def test_search_jobs(self, app, created_job):
        """Test job search functionality"""
        with app.app_context():
            # Search by title
            jobs = Job.search_jobs(query_text='Python')
            assert len(jobs) == 1
            
            # Search by location
            jobs = Job.search_jobs(localisation='Paris')
            assert len(jobs) == 1
            
            # Search with no results
            jobs = Job.search_jobs(query_text='nonexistent')
            assert len(jobs) == 0

    def test_job_update(self, app, created_job):
        """Test updating job"""
        with app.app_context():
            job_id = created_job.get_id()
            update_data = {
                'titre': 'Senior Developer',
                'salaire': '50000-60000'
            }
            
            success = created_job.update(job_id, update_data)
            assert success is True
            
            updated_job = Job.find_by_id(job_id)
            assert updated_job.titre == 'Senior Developer'

    def test_deactivate_job(self, app, created_job):
        """Test deactivating job"""
        with app.app_context():
            job_id = created_job.get_id()
            success = created_job.deactivate(job_id)
            assert success is True
            
            updated_job = Job.find_by_id(job_id)
            assert updated_job.actif is False

    def test_job_applications_count(self, app, created_job, created_application):
        """Test getting job applications count"""
        with app.app_context():
            count = created_job.get_applications_count()
            assert count == 1


class TestApplicationModel:
    """Test Application model functionality"""

    def test_application_creation(self, app, db_cleanup, created_user, created_job):
        """Test application creation"""
        with app.app_context():
            application = Application(
                user_id=created_user.get_id(),
                job_id=created_job.get_id(),
                company_id=created_job.company_id,
                lettre_motivation='Test letter'
            )
            
            app_id = application.save()
            assert app_id is not None
            assert application.statut == 'En attente'  # Default status

    def test_duplicate_application_prevention(self, app, created_application):
        """Test prevention of duplicate applications"""
        with app.app_context():
            # Try to create duplicate application
            duplicate_app = Application(
                user_id=created_application.user_id,
                job_id=created_application.job_id,
                company_id=created_application.company_id
            )
            
            result = duplicate_app.save()
            assert result is None  # Should not save duplicate

    def test_check_existing_application(self, app, created_application):
        """Test checking for existing application"""
        with app.app_context():
            exists = Application.check_existing_application(
                created_application.user_id,
                created_application.job_id
            )
            assert exists is True
            
            # Check non-existing
            exists = Application.check_existing_application(
                'nonexistent_user',
                'nonexistent_job'
            )
            assert exists is False

    def test_find_applications_by_user(self, app, created_application):
        """Test finding applications by user"""
        with app.app_context():
            applications = Application.find_by_user(created_application.user_id)
            assert len(applications) == 1
            assert applications[0].get_id() == created_application.get_id()

    def test_find_applications_by_company(self, app, created_application):
        """Test finding applications by company"""
        with app.app_context():
            applications = Application.find_by_company(created_application.company_id)
            assert len(applications) == 1

    def test_find_applications_by_job(self, app, created_application):
        """Test finding applications by job"""
        with app.app_context():
            applications = Application.find_by_job(created_application.job_id)
            assert len(applications) == 1

    def test_find_applications_by_status(self, app, created_application):
        """Test finding applications by status"""
        with app.app_context():
            applications = Application.find_by_status('En attente')
            assert len(applications) == 1
            
            applications = Application.find_by_status('Acceptée')
            assert len(applications) == 0

    def test_update_application_status(self, app, created_application):
        """Test updating application status"""
        with app.app_context():
            app_id = created_application.get_id()
            success = created_application.update_status(
                app_id, 
                'Acceptée', 
                'Candidat intéressant'
            )
            assert success is True
            
            updated_app = Application.find_by_id(app_id)
            assert updated_app.statut == 'Acceptée'
            assert updated_app.notes_entreprise == 'Candidat intéressant'

    def test_application_get_user_info(self, app, created_application):
        """Test getting user info from application"""
        with app.app_context():
            user_info = created_application.get_user_info()
            assert user_info is not None
            assert user_info.email == 'test@example.com'

    def test_application_get_job_info(self, app, created_application):
        """Test getting job info from application"""
        with app.app_context():
            job_info = created_application.get_job_info()
            assert job_info is not None
            assert job_info.titre == 'Développeur Python'

    def test_application_get_company_info(self, app, created_application):
        """Test getting company info from application"""
        with app.app_context():
            company_info = created_application.get_company_info()
            assert company_info is not None
            assert company_info.nom == 'Test Company'

    def test_delete_application(self, app, created_application):
        """Test deleting application"""
        with app.app_context():
            app_id = created_application.get_id()
            success = Application.delete_by_id(app_id)
            assert success is True
            
            deleted_app = Application.find_by_id(app_id)
            assert deleted_app is None

    def test_application_count_by_status(self, app, created_application):
        """Test counting applications by status"""
        with app.app_context():
            count = Application.count_by_status('En attente')
            assert count == 1
            
            count = Application.count_by_status('Acceptée')
            assert count == 0


class TestModelEdgeCases:
    """Test edge cases and error handling"""

    def test_user_with_invalid_objectid(self, app, db_cleanup):
        """Test finding user with invalid ObjectId"""
        with app.app_context():
            user = User.find_by_id('invalid-id')
            assert user is None

    def test_company_with_empty_fields(self, app, db_cleanup):
        """Test company with minimal required fields"""
        with app.app_context():
            company = Company(
                email='minimal@example.com',
                password='password123',
                nom='Minimal Company',
                description='Minimal description'
            )
            
            company_id = company.save()
            assert company_id is not None
            assert company.secteur is None
            assert company.adresse is None

    def test_job_with_empty_lists(self, app, db_cleanup, created_company):
        """Test job with empty competences list"""
        with app.app_context():
            job = Job(
                company_id=created_company.get_id(),
                titre='Basic Job',
                description='Basic description'
            )
            
            job_id = job.save()
            assert job_id is not None
            assert job.competences_requises == []

    def test_application_without_motivation_letter(self, app, db_cleanup, created_user, created_job):
        """Test application without motivation letter"""
        with app.app_context():
            application = Application(
                user_id=created_user.get_id(),
                job_id=created_job.get_id(),
                company_id=created_job.company_id
            )
            
            app_id = application.save()
            assert app_id is not None
            assert application.lettre_motivation == ""

    def test_model_from_dict_missing_fields(self, app, db_cleanup):
        """Test creating models from incomplete data"""
        with app.app_context():
            # Test User.from_dict with missing fields
            incomplete_data = {
                'email': 'test@example.com',
                'nom': 'Test'
                # Missing other fields
            }
            
            user = User.from_dict(incomplete_data)
            assert user.email == 'test@example.com'
            assert user.nom == 'Test'
            assert user.prenom is None
            assert user.competences == []

    def test_update_nonexistent_record(self, app, db_cleanup, created_user):
        """Test updating non-existent record"""
        with app.app_context():
            success = created_user.update('507f1f77bcf86cd799439011', {'nom': 'New Name'})
            assert success is False

    def test_delete_nonexistent_record(self, app, db_cleanup):
        """Test deleting non-existent record"""
        with app.app_context():
            success = User.delete_by_id('507f1f77bcf86cd799439011')
            assert success is False
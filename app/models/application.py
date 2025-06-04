from datetime import datetime
from bson import ObjectId
from app.database import get_collection, insert_document, find_document, find_documents, update_document, delete_document

class Application:
    def __init__(self, user_id, job_id, company_id, lettre_motivation=None):
        self.user_id = str(user_id)
        self.job_id = str(job_id)
        self.company_id = str(company_id)
        self.lettre_motivation = lettre_motivation or ""
        self.statut = "En attente"  # En attente, Acceptée, Refusée
        self.date_candidature = datetime.utcnow()
        self.date_modification = datetime.utcnow()
        self.notes_entreprise = ""

    def to_dict(self):
        """Convert application object to dictionary"""
        return {
            'user_id': self.user_id,
            'job_id': self.job_id,
            'company_id': self.company_id,
            'lettre_motivation': self.lettre_motivation,
            'statut': self.statut,
            'date_candidature': self.date_candidature,
            'date_modification': self.date_modification,
            'notes_entreprise': self.notes_entreprise
        }

    def save(self):
        """Save application to database"""
        # Check if application already exists
        existing = find_document('applications', {
            'user_id': self.user_id,
            'job_id': self.job_id
        })
        
        if existing:
            return None  # Application already exists
        
        application_data = self.to_dict()
        application_id = insert_document('applications', application_data)
        
        # Update job applications count
        if application_id:
            self.update_job_applications_count()
        
        return application_id

    def update_job_applications_count(self):
        """Update applications count in job"""
        from app.database import count_documents
        count = count_documents('applications', {'job_id': self.job_id})
        update_document('jobs', 
                       {'_id': ObjectId(self.job_id)}, 
                       {'$set': {'candidatures_count': count}})

    @staticmethod
    def find_by_id(application_id):
        """Find application by ID"""
        try:
            application_data = find_document('applications', {'_id': ObjectId(application_id)})
            if application_data:
                return Application.from_dict(application_data)
            return None
        except:
            return None

    @staticmethod
    def find_all(skip=0, limit=10):
        """Find all applications with pagination"""
        applications_data = find_documents('applications', 
                                         skip=skip, 
                                         limit=limit,
                                         sort=[('date_candidature', -1)])
        return [Application.from_dict(app_data) for app_data in applications_data]

    @staticmethod
    def find_by_user(user_id, skip=0, limit=10):
        """Find applications by user ID"""
        applications_data = find_documents('applications', 
                                         query={'user_id': str(user_id)},
                                         skip=skip, 
                                         limit=limit,
                                         sort=[('date_candidature', -1)])
        return [Application.from_dict(app_data) for app_data in applications_data]

    @staticmethod
    def find_by_company(company_id, skip=0, limit=10):
        """Find applications by company ID"""
        applications_data = find_documents('applications', 
                                         query={'company_id': str(company_id)},
                                         skip=skip, 
                                         limit=limit,
                                         sort=[('date_candidature', -1)])
        return [Application.from_dict(app_data) for app_data in applications_data]

    @staticmethod
    def find_by_job(job_id, skip=0, limit=10):
        """Find applications by job ID"""
        applications_data = find_documents('applications', 
                                         query={'job_id': str(job_id)},
                                         skip=skip, 
                                         limit=limit,
                                         sort=[('date_candidature', -1)])
        return [Application.from_dict(app_data) for app_data in applications_data]

    @staticmethod
    def find_by_status(statut, skip=0, limit=10):
        """Find applications by status"""
        applications_data = find_documents('applications', 
                                         query={'statut': statut},
                                         skip=skip, 
                                         limit=limit,
                                         sort=[('date_candidature', -1)])
        return [Application.from_dict(app_data) for app_data in applications_data]

    @staticmethod
    def from_dict(data):
        """Create Application object from dictionary"""
        application = Application.__new__(Application)
        application.user_id = data.get('user_id')
        application.job_id = data.get('job_id')
        application.company_id = data.get('company_id')
        application.lettre_motivation = data.get('lettre_motivation', '')
        application.statut = data.get('statut', 'En attente')
        application.date_candidature = data.get('date_candidature')
        application.date_modification = data.get('date_modification')
        application.notes_entreprise = data.get('notes_entreprise', '')
        application._id = data.get('_id')
        return application

    def update(self, application_id, update_data):
        """Update application information"""
        update_data['date_modification'] = datetime.utcnow()
        
        success = update_document('applications', 
                                {'_id': ObjectId(application_id)}, 
                                {'$set': update_data})
        return success

    def update_status(self, application_id, new_status, notes=None):
        """Update application status"""
        update_data = {
            'statut': new_status,
            'date_modification': datetime.utcnow()
        }
        
        if notes:
            update_data['notes_entreprise'] = notes
        
        success = update_document('applications', 
                                {'_id': ObjectId(application_id)}, 
                                {'$set': update_data})
        return success

    @staticmethod
    def delete_by_id(application_id):
        """Delete application by ID"""
        try:
            # Get application data before deletion to update job count
            app_data = find_document('applications', {'_id': ObjectId(application_id)})
            
            success = delete_document('applications', {'_id': ObjectId(application_id)})
            
            # Update job applications count
            if success and app_data:
                from app.database import count_documents
                count = count_documents('applications', {'job_id': app_data['job_id']})
                update_document('jobs', 
                              {'_id': ObjectId(app_data['job_id'])}, 
                              {'$set': {'candidatures_count': count}})
            
            return success
        except:
            return False

    @staticmethod
    def count_all():
        """Count total applications"""
        from app.database import count_documents
        return count_documents('applications')

    @staticmethod
    def count_by_status(statut):
        """Count applications by status"""
        from app.database import count_documents
        return count_documents('applications', {'statut': statut})

    def get_id(self):
        """Get application ID as string"""
        return str(self._id) if hasattr(self, '_id') else None

    def get_user_info(self):
        """Get user information for this application"""
        from app.models.user import User
        return User.find_by_id(self.user_id)

    def get_job_info(self):
        """Get job information for this application"""
        from app.models.job import Job
        return Job.find_by_id(self.job_id)

    def get_company_info(self):
        """Get company information for this application"""
        from app.models.company import Company
        return Company.find_by_id(self.company_id)

    @staticmethod
    def check_existing_application(user_id, job_id):
        """Check if user has already applied to this job"""
        existing = find_document('applications', {
            'user_id': str(user_id),
            'job_id': str(job_id)
        })
        return existing is not None
from datetime import datetime
from bson import ObjectId
from app.database import get_collection, insert_document, find_document, find_documents, update_document, delete_document

class Job:
    def __init__(self, company_id, titre, description, salaire=None, type_contrat="CDI", 
                 localisation=None, competences_requises=None, experience_requise=None):
        self.company_id = str(company_id)
        self.titre = titre
        self.description = description
        self.salaire = salaire
        self.type_contrat = type_contrat  # CDI, CDD, Interim, Stage, etc.
        self.localisation = localisation
        self.competences_requises = competences_requises or []
        self.experience_requise = experience_requise or ""
        self.date_creation = datetime.utcnow()
        self.date_modification = datetime.utcnow()
        self.actif = True
        self.candidatures_count = 0

    def to_dict(self):
        """Convert job object to dictionary"""
        return {
            'company_id': self.company_id,
            'titre': self.titre,
            'description': self.description,
            'salaire': self.salaire,
            'type_contrat': self.type_contrat,
            'localisation': self.localisation,
            'competences_requises': self.competences_requises,
            'experience_requise': self.experience_requise,
            'date_creation': self.date_creation,
            'date_modification': self.date_modification,
            'actif': self.actif,
            'candidatures_count': self.candidatures_count
        }

    def save(self):
        """Save job to database"""
        job_data = self.to_dict()
        job_id = insert_document('jobs', job_data)
        return job_id

    @staticmethod
    def find_by_id(job_id):
        """Find job by ID"""
        try:
            job_data = find_document('jobs', {'_id': ObjectId(job_id)})
            if job_data:
                return Job.from_dict(job_data)
            return None
        except:
            return None

    @staticmethod
    def find_all(skip=0, limit=10, active_only=True):
        """Find all jobs with pagination"""
        query = {'actif': True} if active_only else {}
        jobs_data = find_documents('jobs', 
                                 query=query,
                                 skip=skip, 
                                 limit=limit,
                                 sort=[('date_creation', -1)])
        return [Job.from_dict(job_data) for job_data in jobs_data]

    @staticmethod
    def find_by_company(company_id, skip=0, limit=10):
        """Find jobs by company ID"""
        jobs_data = find_documents('jobs', 
                                 query={'company_id': str(company_id)},
                                 skip=skip, 
                                 limit=limit,
                                 sort=[('date_creation', -1)])
        return [Job.from_dict(job_data) for job_data in jobs_data]

    @staticmethod
    def search_jobs(query_text=None, localisation=None, type_contrat=None, skip=0, limit=10):
        """Search jobs with filters"""
        query = {'actif': True}
        
        if query_text:
            query['$or'] = [
                {'titre': {'$regex': query_text, '$options': 'i'}},
                {'description': {'$regex': query_text, '$options': 'i'}},
                {'competences_requises': {'$regex': query_text, '$options': 'i'}}
            ]
        
        if localisation:
            query['localisation'] = {'$regex': localisation, '$options': 'i'}
            
        if type_contrat:
            query['type_contrat'] = type_contrat

        jobs_data = find_documents('jobs', 
                                 query=query,
                                 skip=skip, 
                                 limit=limit,
                                 sort=[('date_creation', -1)])
        return [Job.from_dict(job_data) for job_data in jobs_data]

    @staticmethod
    def from_dict(data):
        """Create Job object from dictionary"""
        job = Job.__new__(Job)
        job.company_id = data.get('company_id')
        job.titre = data.get('titre')
        job.description = data.get('description')
        job.salaire = data.get('salaire')
        job.type_contrat = data.get('type_contrat', 'CDI')
        job.localisation = data.get('localisation')
        job.competences_requises = data.get('competences_requises', [])
        job.experience_requise = data.get('experience_requise', '')
        job.date_creation = data.get('date_creation')
        job.date_modification = data.get('date_modification')
        job.actif = data.get('actif', True)
        job.candidatures_count = data.get('candidatures_count', 0)
        job._id = data.get('_id')
        return job

    def update(self, job_id, update_data):
        """Update job information"""
        update_data['date_modification'] = datetime.utcnow()
        
        success = update_document('jobs', 
                                {'_id': ObjectId(job_id)}, 
                                {'$set': update_data})
        return success

    @staticmethod
    def delete_by_id(job_id):
        """Delete job by ID"""
        try:
            success = delete_document('jobs', {'_id': ObjectId(job_id)})
            return success
        except:
            return False

    def deactivate(self, job_id):
        """Deactivate job instead of deleting"""
        success = update_document('jobs', 
                                {'_id': ObjectId(job_id)}, 
                                {'$set': {'actif': False, 'date_modification': datetime.utcnow()}})
        return success

    @staticmethod
    def count_all(active_only=True):
        """Count total jobs"""
        from app.database import count_documents
        query = {'actif': True} if active_only else {}
        return count_documents('jobs', query)

    def get_id(self):
        """Get job ID as string"""
        return str(self._id) if hasattr(self, '_id') else None

    def get_company_info(self):
        """Get company information for this job"""
        from app.models.company import Company
        return Company.find_by_id(self.company_id)

    def get_applications_count(self):
        """Get number of applications for this job"""
        from app.database import count_documents
        return count_documents('applications', {'job_id': self.get_id()})

    def update_applications_count(self):
        """Update the applications count for this job"""
        count = self.get_applications_count()
        if hasattr(self, '_id'):
            update_document('jobs', 
                          {'_id': self._id}, 
                          {'$set': {'candidatures_count': count}})
        return count
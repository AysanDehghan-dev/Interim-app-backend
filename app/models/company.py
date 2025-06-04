from datetime import datetime
from bson import ObjectId
import bcrypt
from app.database import get_collection, insert_document, find_document, find_documents, update_document, delete_document

class Company:
    def __init__(self, email, password, nom, description, secteur=None, adresse=None, telephone=None, site_web=None):
        self.email = email
        self.password = self.hash_password(password)
        self.nom = nom
        self.description = description
        self.secteur = secteur
        self.adresse = adresse
        self.telephone = telephone
        self.site_web = site_web
        self.date_creation = datetime.utcnow()
        self.date_modification = datetime.utcnow()
        self.actif = True

    def hash_password(self, password):
        """Hash password using bcrypt"""
        return bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')

    def check_password(self, password):
        """Check if password matches hash"""
        return bcrypt.checkpw(password.encode('utf-8'), self.password.encode('utf-8'))

    def to_dict(self):
        """Convert company object to dictionary"""
        return {
            'email': self.email,
            'nom': self.nom,
            'description': self.description,
            'secteur': self.secteur,
            'adresse': self.adresse,
            'telephone': self.telephone,
            'site_web': self.site_web,
            'date_creation': self.date_creation,
            'date_modification': self.date_modification,
            'actif': self.actif
        }

    def save(self):
        """Save company to database"""
        company_data = self.to_dict()
        company_data['password'] = self.password
        company_id = insert_document('companies', company_data)
        return company_id

    @staticmethod
    def find_by_id(company_id):
        """Find company by ID"""
        try:
            company_data = find_document('companies', {'_id': ObjectId(company_id)})
            if company_data:
                return Company.from_dict(company_data)
            return None
        except:
            return None

    @staticmethod
    def find_by_email(email):
        """Find company by email"""
        company_data = find_document('companies', {'email': email})
        if company_data:
            return Company.from_dict(company_data)
        return None

    @staticmethod
    def find_all(skip=0, limit=10):
        """Find all companies with pagination"""
        companies_data = find_documents('companies', 
                                      projection={'password': 0}, 
                                      skip=skip, 
                                      limit=limit,
                                      sort=[('date_creation', -1)])
        return [Company.from_dict(company_data) for company_data in companies_data]

    @staticmethod
    def from_dict(data):
        """Create Company object from dictionary"""
        company = Company.__new__(Company)
        company.email = data.get('email')
        company.password = data.get('password', '')
        company.nom = data.get('nom')
        company.description = data.get('description')
        company.secteur = data.get('secteur')
        company.adresse = data.get('adresse')
        company.telephone = data.get('telephone')
        company.site_web = data.get('site_web')
        company.date_creation = data.get('date_creation')
        company.date_modification = data.get('date_modification')
        company.actif = data.get('actif', True)
        company._id = data.get('_id')
        return company

    def update(self, company_id, update_data):
        """Update company information"""
        # Remove password from update if present (handle separately)
        if 'password' in update_data:
            update_data['password'] = self.hash_password(update_data['password'])
        
        update_data['date_modification'] = datetime.utcnow()
        
        success = update_document('companies', 
                                {'_id': ObjectId(company_id)}, 
                                {'$set': update_data})
        return success

    @staticmethod
    def delete_by_id(company_id):
        """Delete company by ID"""
        try:
            success = delete_document('companies', {'_id': ObjectId(company_id)})
            return success
        except:
            return False

    @staticmethod
    def count_all():
        """Count total companies"""
        from app.database import count_documents
        return count_documents('companies')

    def get_id(self):
        """Get company ID as string"""
        return str(self._id) if hasattr(self, '_id') else None

    def get_jobs_count(self):
        """Get number of jobs posted by this company"""
        from app.database import count_documents
        return count_documents('jobs', {'company_id': self.get_id()})
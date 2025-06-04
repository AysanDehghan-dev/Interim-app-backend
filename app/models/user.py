from datetime import datetime
from bson import ObjectId
import bcrypt
from app.database import get_collection, insert_document, find_document, find_documents, update_document, delete_document

class User:
    def __init__(self, email, password, nom, prenom, telephone=None, competences=None, experience=None, cv_url=None):
        self.email = email
        self.password = self.hash_password(password)
        self.nom = nom
        self.prenom = prenom
        self.telephone = telephone
        self.competences = competences or []
        self.experience = experience or ""
        self.cv_url = cv_url
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
        """Convert user object to dictionary"""
        return {
            'email': self.email,
            'nom': self.nom,
            'prenom': self.prenom,
            'telephone': self.telephone,
            'competences': self.competences,
            'experience': self.experience,
            'cv_url': self.cv_url,
            'date_creation': self.date_creation,
            'date_modification': self.date_modification,
            'actif': self.actif
        }

    def save(self):
        """Save user to database"""
        user_data = self.to_dict()
        user_data['password'] = self.password
        user_id = insert_document('users', user_data)
        return user_id

    @staticmethod
    def find_by_id(user_id):
        """Find user by ID"""
        try:
            user_data = find_document('users', {'_id': ObjectId(user_id)})
            if user_data:
                return User.from_dict(user_data)
            return None
        except:
            return None

    @staticmethod
    def find_by_email(email):
        """Find user by email"""
        user_data = find_document('users', {'email': email})
        if user_data:
            return User.from_dict(user_data)
        return None

    @staticmethod
    def find_all(skip=0, limit=10):
        """Find all users with pagination"""
        users_data = find_documents('users', 
                                  projection={'password': 0}, 
                                  skip=skip, 
                                  limit=limit,
                                  sort=[('date_creation', -1)])
        return [User.from_dict(user_data) for user_data in users_data]

    @staticmethod
    def from_dict(data):
        """Create User object from dictionary"""
        user = User.__new__(User)
        user.email = data.get('email')
        user.password = data.get('password', '')
        user.nom = data.get('nom')
        user.prenom = data.get('prenom')
        user.telephone = data.get('telephone')
        user.competences = data.get('competences', [])
        user.experience = data.get('experience', '')
        user.cv_url = data.get('cv_url')
        user.date_creation = data.get('date_creation')
        user.date_modification = data.get('date_modification')
        user.actif = data.get('actif', True)
        user._id = data.get('_id')
        return user

    def update(self, user_id, update_data):
        """Update user information"""
        # Remove password from update if present (handle separately)
        if 'password' in update_data:
            update_data['password'] = self.hash_password(update_data['password'])
        
        update_data['date_modification'] = datetime.utcnow()
        
        success = update_document('users', 
                                {'_id': ObjectId(user_id)}, 
                                {'$set': update_data})
        return success

    @staticmethod
    def delete_by_id(user_id):
        """Delete user by ID"""
        try:
            success = delete_document('users', {'_id': ObjectId(user_id)})
            return success
        except:
            return False

    @staticmethod
    def count_all():
        """Count total users"""
        from app.database import count_documents
        return count_documents('users')

    def get_id(self):
        """Get user ID as string"""
        return str(self._id) if hasattr(self, '_id') else None
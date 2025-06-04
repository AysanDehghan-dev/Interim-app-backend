import jwt
from datetime import datetime, timedelta
from functools import wraps
from flask import request, jsonify, current_app, session
from app.models.user import User
from app.models.company import Company

def generate_token(user_id, user_type):
    """Generate JWT token for user"""
    payload = {
        'user_id': str(user_id),
        'user_type': user_type,  # 'user' or 'company'
        'exp': datetime.utcnow() + timedelta(seconds=current_app.config['JWT_ACCESS_TOKEN_EXPIRES']),
        'iat': datetime.utcnow()
    }
    
    token = jwt.encode(
        payload,
        current_app.config['JWT_SECRET_KEY'],
        algorithm='HS256'
    )
    
    return token

def verify_token(token):
    """Verify JWT token"""
    try:
        payload = jwt.decode(
            token,
            current_app.config['JWT_SECRET_KEY'],
            algorithms=['HS256']
        )
        return payload
    except jwt.ExpiredSignatureError:
        return None
    except jwt.InvalidTokenError:
        return None

def login_required(f):
    """Decorator to require authentication"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        token = None
        
        # Check for token in Authorization header
        if 'Authorization' in request.headers:
            auth_header = request.headers['Authorization']
            try:
                token = auth_header.split(" ")[1]  # Bearer <token>
            except IndexError:
                return jsonify({'message': 'Format du token invalide'}), 401
        
        # Check for token in session (fallback)
        elif 'token' in session:
            token = session['token']
        
        if not token:
            return jsonify({'message': 'Token d\'authentification requis'}), 401
        
        # Verify token
        payload = verify_token(token)
        if not payload:
            return jsonify({'message': 'Token invalide ou expiré'}), 401
        
        # Add user info to request context
        request.current_user_id = payload['user_id']
        request.current_user_type = payload['user_type']
        
        return f(*args, **kwargs)
    
    return decorated_function

def company_required(f):
    """Decorator to require company authentication"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        token = None
        
        # Check for token in Authorization header
        if 'Authorization' in request.headers:
            auth_header = request.headers['Authorization']
            try:
                token = auth_header.split(" ")[1]
            except IndexError:
                return jsonify({'message': 'Format du token invalide'}), 401
        
        # Check for token in session
        elif 'token' in session:
            token = session['token']
        
        if not token:
            return jsonify({'message': 'Token d\'authentification requis'}), 401
        
        payload = verify_token(token)
        if not payload:
            return jsonify({'message': 'Token invalide ou expiré'}), 401
        
        if payload['user_type'] != 'company':
            return jsonify({'message': 'Accès réservé aux entreprises'}), 403
        
        request.current_user_id = payload['user_id']
        request.current_user_type = payload['user_type']
        
        return f(*args, **kwargs)
    
    return decorated_function

def get_current_user():
    """Get current authenticated user"""
    if not hasattr(request, 'current_user_id'):
        return None
    
    user_id = request.current_user_id
    user_type = request.current_user_type
    
    if user_type == 'user':
        return User.find_by_id(user_id)
    elif user_type == 'company':
        return Company.find_by_id(user_id)
    
    return None

def validate_email(email):
    """Basic email validation"""
    import re
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return re.match(pattern, email) is not None

def validate_password(password):
    """Basic password validation"""
    if len(password) < 6:
        return False, "Le mot de passe doit contenir au moins 6 caractères"
    
    return True, "Mot de passe valide"
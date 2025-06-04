from flask import Blueprint, request, jsonify, session
from flasgger import swag_from
from app.models.user import User
from app.models.company import Company
from app.auth import generate_token, verify_token, validate_email, validate_password, login_required

auth_bp = Blueprint('auth', __name__)

@auth_bp.route('/register/user', methods=['POST'])
def register_user():
    """
    Inscription d'un utilisateur
    ---
    tags:
      - Authentification
    parameters:
      - in: body
        name: user
        required: true
        schema:
          type: object
          required:
            - email
            - password
            - nom
            - prenom
          properties:
            email:
              type: string
              example: "user@example.com"
            password:
              type: string
              example: "motdepasse123"
            nom:
              type: string
              example: "Dupont"
            prenom:
              type: string
              example: "Jean"
            telephone:
              type: string
              example: "0123456789"
            competences:
              type: array
              items:
                type: string
              example: ["Python", "Flask", "MongoDB"]
            experience:
              type: string
              example: "2 ans d'expérience en développement web"
    responses:
      201:
        description: Utilisateur créé avec succès
      400:
        description: Données invalides
      409:
        description: Email déjà utilisé
    """
    try:
        data = request.get_json()
        
        # Validation des champs requis
        required_fields = ['email', 'password', 'nom', 'prenom']
        for field in required_fields:
            if not data.get(field):
                return jsonify({'message': f'Le champ {field} est requis'}), 400
        
        # Validation email
        if not validate_email(data['email']):
            return jsonify({'message': 'Format d\'email invalide'}), 400
        
        # Validation mot de passe
        is_valid, message = validate_password(data['password'])
        if not is_valid:
            return jsonify({'message': message}), 400
        
        # Vérifier si l'email existe déjà
        if User.find_by_email(data['email']):
            return jsonify({'message': 'Cet email est déjà utilisé'}), 409
        
        # Créer l'utilisateur
        user = User(
            email=data['email'],
            password=data['password'],
            nom=data['nom'],
            prenom=data['prenom'],
            telephone=data.get('telephone'),
            competences=data.get('competences', []),
            experience=data.get('experience', '')
        )
        
        user_id = user.save()
        
        if user_id:
            # Générer token
            token = generate_token(user_id, 'user')
            
            return jsonify({
                'message': 'Utilisateur créé avec succès',
                'user_id': str(user_id),
                'token': token,
                'user_type': 'user'
            }), 201
        else:
            return jsonify({'message': 'Erreur lors de la création de l\'utilisateur'}), 500
            
    except Exception as e:
        return jsonify({'message': 'Erreur serveur', 'error': str(e)}), 500

@auth_bp.route('/register/company', methods=['POST'])
def register_company():
    """
    Inscription d'une entreprise
    ---
    tags:
      - Authentification
    parameters:
      - in: body
        name: company
        required: true
        schema:
          type: object
          required:
            - email
            - password
            - nom
            - description
          properties:
            email:
              type: string
              example: "contact@entreprise.com"
            password:
              type: string
              example: "motdepasse123"
            nom:
              type: string
              example: "Ma Société SARL"
            description:
              type: string
              example: "Entreprise spécialisée dans le développement web"
            secteur:
              type: string
              example: "Informatique"
            adresse:
              type: string
              example: "123 Rue de la Paix, 75001 Paris"
            telephone:
              type: string
              example: "0123456789"
            site_web:
              type: string
              example: "https://www.entreprise.com"
    responses:
      201:
        description: Entreprise créée avec succès
      400:
        description: Données invalides
      409:
        description: Email déjà utilisé
    """
    try:
        data = request.get_json()
        
        # Validation des champs requis
        required_fields = ['email', 'password', 'nom', 'description']
        for field in required_fields:
            if not data.get(field):
                return jsonify({'message': f'Le champ {field} est requis'}), 400
        
        # Validation email
        if not validate_email(data['email']):
            return jsonify({'message': 'Format d\'email invalide'}), 400
        
        # Validation mot de passe
        is_valid, message = validate_password(data['password'])
        if not is_valid:
            return jsonify({'message': message}), 400
        
        # Vérifier si l'email existe déjà
        if Company.find_by_email(data['email']):
            return jsonify({'message': 'Cet email est déjà utilisé'}), 409
        
        # Créer l'entreprise
        company = Company(
            email=data['email'],
            password=data['password'],
            nom=data['nom'],
            description=data['description'],
            secteur=data.get('secteur'),
            adresse=data.get('adresse'),
            telephone=data.get('telephone'),
            site_web=data.get('site_web')
        )
        
        company_id = company.save()
        
        if company_id:
            # Générer token
            token = generate_token(company_id, 'company')
            
            return jsonify({
                'message': 'Entreprise créée avec succès',
                'company_id': str(company_id),
                'token': token,
                'user_type': 'company'
            }), 201
        else:
            return jsonify({'message': 'Erreur lors de la création de l\'entreprise'}), 500
            
    except Exception as e:
        return jsonify({'message': 'Erreur serveur', 'error': str(e)}), 500

@auth_bp.route('/login', methods=['POST'])
def login():
    """
    Connexion utilisateur ou entreprise
    ---
    tags:
      - Authentification
    parameters:
      - in: body
        name: credentials
        required: true
        schema:
          type: object
          required:
            - email
            - password
            - user_type
          properties:
            email:
              type: string
              example: "user@example.com"
            password:
              type: string
              example: "motdepasse123"
            user_type:
              type: string
              enum: ["user", "company"]
              example: "user"
    responses:
      200:
        description: Connexion réussie
      400:
        description: Données invalides
      401:
        description: Identifiants incorrects
    """
    try:
        data = request.get_json()
        
        # Validation des champs requis
        required_fields = ['email', 'password', 'user_type']
        for field in required_fields:
            if not data.get(field):
                return jsonify({'message': f'Le champ {field} est requis'}), 400
        
        email = data['email']
        password = data['password']
        user_type = data['user_type']
        
        if user_type not in ['user', 'company']:
            return jsonify({'message': 'Type d\'utilisateur invalide'}), 400
        
        # Rechercher l'utilisateur
        if user_type == 'user':
            user = User.find_by_email(email)
        else:
            user = Company.find_by_email(email)
        
        if not user:
            return jsonify({'message': 'Identifiants incorrects'}), 401
        
        # Vérifier le mot de passe
        if not user.check_password(password):
            return jsonify({'message': 'Identifiants incorrects'}), 401
        
        # Générer token
        token = generate_token(user.get_id(), user_type)
        
        # Stocker en session (optionnel)
        session['token'] = token
        session['user_id'] = user.get_id()
        session['user_type'] = user_type
        
        return jsonify({
            'message': 'Connexion réussie',
            'token': token,
            'user_type': user_type,
            'user_id': user.get_id(),
            'user_info': {
                'email': user.email,
                'nom': user.nom,
                'prenom': getattr(user, 'prenom', None)  # Only for users
            }
        }), 200
        
    except Exception as e:
        return jsonify({'message': 'Erreur serveur', 'error': str(e)}), 500

@auth_bp.route('/logout', methods=['POST'])
@login_required
def logout():
    """
    Déconnexion
    ---
    tags:
      - Authentification
    security:
      - Bearer: []
    responses:
      200:
        description: Déconnexion réussie
      401:
        description: Non authentifié
    """
    try:
        # Supprimer de la session
        session.pop('token', None)
        session.pop('user_id', None)
        session.pop('user_type', None)
        
        return jsonify({'message': 'Déconnexion réussie'}), 200
        
    except Exception as e:
        return jsonify({'message': 'Erreur serveur', 'error': str(e)}), 500

@auth_bp.route('/verify', methods=['GET'])
@login_required
def verify_token_route():
    """
    Vérifier la validité du token
    ---
    tags:
      - Authentification
    security:
      - Bearer: []
    responses:
      200:
        description: Token valide
      401:
        description: Token invalide
    """
    try:
        user_id = request.current_user_id
        user_type = request.current_user_type
        
        # Récupérer les infos utilisateur
        if user_type == 'user':
            user = User.find_by_id(user_id)
        else:
            user = Company.find_by_id(user_id)
        
        if not user:
            return jsonify({'message': 'Utilisateur non trouvé'}), 404
        
        return jsonify({
            'message': 'Token valide',
            'user_type': user_type,
            'user_id': user_id,
            'user_info': {
                'email': user.email,
                'nom': user.nom,
                'prenom': getattr(user, 'prenom', None),
                'actif': user.actif
            }
        }), 200
        
    except Exception as e:
        return jsonify({'message': 'Erreur serveur', 'error': str(e)}), 500

@auth_bp.route('/change-password', methods=['PUT'])
@login_required
def change_password():
    """
    Changer le mot de passe
    ---
    tags:
      - Authentification
    security:
      - Bearer: []
    parameters:
      - in: body
        name: passwords
        required: true
        schema:
          type: object
          required:
            - current_password
            - new_password
          properties:
            current_password:
              type: string
              example: "ancienmdp123"
            new_password:
              type: string
              example: "nouveaumdp123"
    responses:
      200:
        description: Mot de passe modifié avec succès
      400:
        description: Données invalides
      401:
        description: Mot de passe actuel incorrect
    """
    try:
        data = request.get_json()
        
        current_password = data.get('current_password')
        new_password = data.get('new_password')
        
        if not current_password or not new_password:
            return jsonify({'message': 'Mots de passe requis'}), 400
        
        # Validation nouveau mot de passe
        is_valid, message = validate_password(new_password)
        if not is_valid:
            return jsonify({'message': message}), 400
        
        # Récupérer l'utilisateur
        user_id = request.current_user_id
        user_type = request.current_user_type
        
        if user_type == 'user':
            user = User.find_by_id(user_id)
        else:
            user = Company.find_by_id(user_id)
        
        if not user:
            return jsonify({'message': 'Utilisateur non trouvé'}), 404
        
        # Vérifier mot de passe actuel
        if not user.check_password(current_password):
            return jsonify({'message': 'Mot de passe actuel incorrect'}), 401
        
        # Mettre à jour le mot de passe
        success = user.update(user_id, {'password': new_password})
        
        if success:
            return jsonify({'message': 'Mot de passe modifié avec succès'}), 200
        else:
            return jsonify({'message': 'Erreur lors de la modification'}), 500
        
    except Exception as e:
        return jsonify({'message': 'Erreur serveur', 'error': str(e)}), 500
from flask import Blueprint, request, jsonify
from flasgger import swag_from
from app.models.user import User
from app.auth import login_required, validate_email

users_bp = Blueprint('users', __name__)

@users_bp.route('', methods=['GET'])
def get_all_users():
    """
    Récupérer tous les utilisateurs
    ---
    tags:
      - Utilisateurs
    parameters:
      - in: query
        name: page
        type: integer
        default: 1
        description: Numéro de page
      - in: query
        name: limit
        type: integer
        default: 10
        description: Nombre d'éléments par page
    responses:
      200:
        description: Liste des utilisateurs
        schema:
          type: object
          properties:
            users:
              type: array
              items:
                type: object
            total:
              type: integer
            page:
              type: integer
            limit:
              type: integer
    """
    try:
        page = int(request.args.get('page', 1))
        limit = int(request.args.get('limit', 10))
        limit = min(limit, 100)  # Maximum 100 items per page
        skip = (page - 1) * limit
        
        users = User.find_all(skip=skip, limit=limit)
        total = User.count_all()
        
        users_data = []
        for user in users:
            user_dict = user.to_dict()
            user_dict['id'] = user.get_id()
            users_data.append(user_dict)
        
        return jsonify({
            'users': users_data,
            'total': total,
            'page': page,
            'limit': limit,
            'pages': (total + limit - 1) // limit
        }), 200
        
    except Exception as e:
        return jsonify({'message': 'Erreur serveur', 'error': str(e)}), 500

@users_bp.route('/<user_id>', methods=['GET'])
def get_user(user_id):
    """
    Récupérer un utilisateur par ID
    ---
    tags:
      - Utilisateurs
    parameters:
      - in: path
        name: user_id
        type: string
        required: true
        description: ID de l'utilisateur
    responses:
      200:
        description: Informations de l'utilisateur
      404:
        description: Utilisateur non trouvé
    """
    try:
        user = User.find_by_id(user_id)
        
        if not user:
            return jsonify({'message': 'Utilisateur non trouvé'}), 404
        
        user_dict = user.to_dict()
        user_dict['id'] = user.get_id()
        
        return jsonify({'user': user_dict}), 200
        
    except Exception as e:
        return jsonify({'message': 'Erreur serveur', 'error': str(e)}), 500

@users_bp.route('', methods=['POST'])
def create_user():
    """
    Créer un nouvel utilisateur
    ---
    tags:
      - Utilisateurs
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
              example: "nouveau@example.com"
            password:
              type: string
              example: "motdepasse123"
            nom:
              type: string
              example: "Martin"
            prenom:
              type: string
              example: "Paul"
            telephone:
              type: string
              example: "0123456789"
            competences:
              type: array
              items:
                type: string
              example: ["JavaScript", "React", "Node.js"]
            experience:
              type: string
              example: "3 ans d'expérience en développement frontend"
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
            return jsonify({
                'message': 'Utilisateur créé avec succès',
                'user_id': str(user_id)
            }), 201
        else:
            return jsonify({'message': 'Erreur lors de la création'}), 500
            
    except Exception as e:
        return jsonify({'message': 'Erreur serveur', 'error': str(e)}), 500

@users_bp.route('/<user_id>', methods=['PUT'])
@login_required
def update_user(user_id):
    """
    Mettre à jour un utilisateur
    ---
    tags:
      - Utilisateurs
    security:
      - Bearer: []
    parameters:
      - in: path
        name: user_id
        type: string
        required: true
        description: ID de l'utilisateur
      - in: body
        name: user
        required: true
        schema:
          type: object
          properties:
            nom:
              type: string
              example: "Nouveau Nom"
            prenom:
              type: string
              example: "Nouveau Prénom"
            telephone:
              type: string
              example: "0987654321"
            competences:
              type: array
              items:
                type: string
              example: ["Python", "Django", "PostgreSQL"]
            experience:
              type: string
              example: "5 ans d'expérience en développement backend"
            cv_url:
              type: string
              example: "https://example.com/cv.pdf"
    responses:
      200:
        description: Utilisateur mis à jour avec succès
      400:
        description: Données invalides
      403:
        description: Non autorisé à modifier cet utilisateur
      404:
        description: Utilisateur non trouvé
    """
    try:
        # Vérifier que l'utilisateur existe
        user = User.find_by_id(user_id)
        if not user:
            return jsonify({'message': 'Utilisateur non trouvé'}), 404
        
        # Vérifier les permissions (utilisateur peut modifier son profil)
        current_user_id = request.current_user_id
        current_user_type = request.current_user_type
        
        if current_user_type != 'user' or current_user_id != user_id:
            return jsonify({'message': 'Non autorisé à modifier cet utilisateur'}), 403
        
        data = request.get_json()
        
        # Champs modifiables
        allowed_fields = ['nom', 'prenom', 'telephone', 'competences', 'experience', 'cv_url']
        update_data = {}
        
        for field in allowed_fields:
            if field in data:
                update_data[field] = data[field]
        
        if not update_data:
            return jsonify({'message': 'Aucune donnée à mettre à jour'}), 400
        
        # Validation email si fourni
        if 'email' in data:
            if not validate_email(data['email']):
                return jsonify({'message': 'Format d\'email invalide'}), 400
            
            # Vérifier unicité email
            existing_user = User.find_by_email(data['email'])
            if existing_user and existing_user.get_id() != user_id:
                return jsonify({'message': 'Cet email est déjà utilisé'}), 409
            
            update_data['email'] = data['email']
        
        success = user.update(user_id, update_data)
        
        if success:
            return jsonify({'message': 'Utilisateur mis à jour avec succès'}), 200
        else:
            return jsonify({'message': 'Erreur lors de la mise à jour'}), 500
            
    except Exception as e:
        return jsonify({'message': 'Erreur serveur', 'error': str(e)}), 500

@users_bp.route('/<user_id>', methods=['DELETE'])
@login_required
def delete_user(user_id):
    """
    Supprimer un utilisateur
    ---
    tags:
      - Utilisateurs
    security:
      - Bearer: []
    parameters:
      - in: path
        name: user_id
        type: string
        required: true
        description: ID de l'utilisateur
    responses:
      200:
        description: Utilisateur supprimé avec succès
      403:
        description: Non autorisé à supprimer cet utilisateur
      404:
        description: Utilisateur non trouvé
    """
    try:
        # Vérifier que l'utilisateur existe
        user = User.find_by_id(user_id)
        if not user:
            return jsonify({'message': 'Utilisateur non trouvé'}), 404
        
        # Vérifier les permissions
        current_user_id = request.current_user_id
        current_user_type = request.current_user_type
        
        if current_user_type != 'user' or current_user_id != user_id:
            return jsonify({'message': 'Non autorisé à supprimer cet utilisateur'}), 403
        
        success = User.delete_by_id(user_id)
        
        if success:
            return jsonify({'message': 'Utilisateur supprimé avec succès'}), 200
        else:
            return jsonify({'message': 'Erreur lors de la suppression'}), 500
            
    except Exception as e:
        return jsonify({'message': 'Erreur serveur', 'error': str(e)}), 500

@users_bp.route('/<user_id>/profile', methods=['GET'])
@login_required
def get_user_profile(user_id):
    """
    Récupérer le profil complet d'un utilisateur
    ---
    tags:
      - Utilisateurs
    security:
      - Bearer: []
    parameters:
      - in: path
        name: user_id
        type: string
        required: true
        description: ID de l'utilisateur
    responses:
      200:
        description: Profil complet de l'utilisateur
      403:
        description: Non autorisé à voir ce profil
      404:
        description: Utilisateur non trouvé
    """
    try:
        user = User.find_by_id(user_id)
        if not user:
            return jsonify({'message': 'Utilisateur non trouvé'}), 404
        
        # Vérifier les permissions
        current_user_id = request.current_user_id
        current_user_type = request.current_user_type
        
        if current_user_type != 'user' or current_user_id != user_id:
            return jsonify({'message': 'Non autorisé à voir ce profil'}), 403
        
        user_dict = user.to_dict()
        user_dict['id'] = user.get_id()
        
        # Récupérer les candidatures de l'utilisateur
        from app.models.application import Application
        applications = Application.find_by_user(user_id, limit=5)
        
        user_dict['recent_applications'] = []
        for app in applications:
            app_dict = app.to_dict()
            app_dict['id'] = app.get_id()
            # Ajouter les infos du job
            job_info = app.get_job_info()
            if job_info:
                app_dict['job_title'] = job_info.titre
                app_dict['company_name'] = job_info.get_company_info().nom if job_info.get_company_info() else None
            user_dict['recent_applications'].append(app_dict)
        
        return jsonify({'profile': user_dict}), 200
        
    except Exception as e:
        return jsonify({'message': 'Erreur serveur', 'error': str(e)}), 500
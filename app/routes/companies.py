from flask import Blueprint, request, jsonify
from flasgger import swag_from
from app.models.company import Company
from app.auth import login_required, company_required, validate_email

companies_bp = Blueprint('companies', __name__)

@companies_bp.route('', methods=['GET'])
def get_all_companies():
    """
    Récupérer toutes les entreprises
    ---
    tags:
      - Entreprises
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
        description: Liste des entreprises
        schema:
          type: object
          properties:
            companies:
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
        
        companies = Company.find_all(skip=skip, limit=limit)
        total = Company.count_all()
        
        companies_data = []
        for company in companies:
            company_dict = company.to_dict()
            company_dict['id'] = company.get_id()
            company_dict['jobs_count'] = company.get_jobs_count()
            companies_data.append(company_dict)
        
        return jsonify({
            'companies': companies_data,
            'total': total,
            'page': page,
            'limit': limit,
            'pages': (total + limit - 1) // limit
        }), 200
        
    except Exception as e:
        return jsonify({'message': 'Erreur serveur', 'error': str(e)}), 500

@companies_bp.route('/<company_id>', methods=['GET'])
def get_company(company_id):
    """
    Récupérer une entreprise par ID
    ---
    tags:
      - Entreprises
    parameters:
      - in: path
        name: company_id
        type: string
        required: true
        description: ID de l'entreprise
    responses:
      200:
        description: Informations de l'entreprise
      404:
        description: Entreprise non trouvée
    """
    try:
        company = Company.find_by_id(company_id)
        
        if not company:
            return jsonify({'message': 'Entreprise non trouvée'}), 404
        
        company_dict = company.to_dict()
        company_dict['id'] = company.get_id()
        company_dict['jobs_count'] = company.get_jobs_count()
        
        # Récupérer quelques offres récentes de l'entreprise
        from app.models.job import Job
        recent_jobs = Job.find_by_company(company_id, limit=3)
        company_dict['recent_jobs'] = []
        
        for job in recent_jobs:
            job_dict = job.to_dict()
            job_dict['id'] = job.get_id()
            company_dict['recent_jobs'].append(job_dict)
        
        return jsonify({'company': company_dict}), 200
        
    except Exception as e:
        return jsonify({'message': 'Erreur serveur', 'error': str(e)}), 500

@companies_bp.route('', methods=['POST'])
def create_company():
    """
    Créer une nouvelle entreprise
    ---
    tags:
      - Entreprises
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
              example: "contact@nouvelle-entreprise.com"
            password:
              type: string
              example: "motdepasse123"
            nom:
              type: string
              example: "Nouvelle Entreprise SAS"
            description:
              type: string
              example: "Entreprise innovante dans le domaine de la technologie"
            secteur:
              type: string
              example: "Technologie"
            adresse:
              type: string
              example: "456 Avenue de l'Innovation, 69000 Lyon"
            telephone:
              type: string
              example: "0123456789"
            site_web:
              type: string
              example: "https://www.nouvelle-entreprise.com"
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
            return jsonify({
                'message': 'Entreprise créée avec succès',
                'company_id': str(company_id)
            }), 201
        else:
            return jsonify({'message': 'Erreur lors de la création'}), 500
            
    except Exception as e:
        return jsonify({'message': 'Erreur serveur', 'error': str(e)}), 500

@companies_bp.route('/<company_id>', methods=['PUT'])
@company_required
def update_company(company_id):
    """
    Mettre à jour une entreprise
    ---
    tags:
      - Entreprises
    security:
      - Bearer: []
    parameters:
      - in: path
        name: company_id
        type: string
        required: true
        description: ID de l'entreprise
      - in: body
        name: company
        required: true
        schema:
          type: object
          properties:
            nom:
              type: string
              example: "Nouveau Nom Entreprise"
            description:
              type: string
              example: "Nouvelle description de l'entreprise"
            secteur:
              type: string
              example: "Finance"
            adresse:
              type: string
              example: "789 Rue du Commerce, 33000 Bordeaux"
            telephone:
              type: string
              example: "0987654321"
            site_web:
              type: string
              example: "https://www.nouveau-site.com"
    responses:
      200:
        description: Entreprise mise à jour avec succès
      400:
        description: Données invalides
      403:
        description: Non autorisé à modifier cette entreprise
      404:
        description: Entreprise non trouvée
    """
    try:
        # Vérifier que l'entreprise existe
        company = Company.find_by_id(company_id)
        if not company:
            return jsonify({'message': 'Entreprise non trouvée'}), 404
        
        # Vérifier les permissions
        current_user_id = request.current_user_id
        if current_user_id != company_id:
            return jsonify({'message': 'Non autorisé à modifier cette entreprise'}), 403
        
        data = request.get_json()
        
        # Champs modifiables
        allowed_fields = ['nom', 'description', 'secteur', 'adresse', 'telephone', 'site_web']
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
            existing_company = Company.find_by_email(data['email'])
            if existing_company and existing_company.get_id() != company_id:
                return jsonify({'message': 'Cet email est déjà utilisé'}), 409
            
            update_data['email'] = data['email']
        
        success = company.update(company_id, update_data)
        
        if success:
            return jsonify({'message': 'Entreprise mise à jour avec succès'}), 200
        else:
            return jsonify({'message': 'Erreur lors de la mise à jour'}), 500
            
    except Exception as e:
        return jsonify({'message': 'Erreur serveur', 'error': str(e)}), 500

@companies_bp.route('/<company_id>', methods=['DELETE'])
@company_required
def delete_company(company_id):
    """
    Supprimer une entreprise
    ---
    tags:
      - Entreprises
    security:
      - Bearer: []
    parameters:
      - in: path
        name: company_id
        type: string
        required: true
        description: ID de l'entreprise
    responses:
      200:
        description: Entreprise supprimée avec succès
      403:
        description: Non autorisé à supprimer cette entreprise
      404:
        description: Entreprise non trouvée
    """
    try:
        # Vérifier que l'entreprise existe
        company = Company.find_by_id(company_id)
        if not company:
            return jsonify({'message': 'Entreprise non trouvée'}), 404
        
        # Vérifier les permissions
        current_user_id = request.current_user_id
        if current_user_id != company_id:
            return jsonify({'message': 'Non autorisé à supprimer cette entreprise'}), 403
        
        success = Company.delete_by_id(company_id)
        
        if success:
            return jsonify({'message': 'Entreprise supprimée avec succès'}), 200
        else:
            return jsonify({'message': 'Erreur lors de la suppression'}), 500
            
    except Exception as e:
        return jsonify({'message': 'Erreur serveur', 'error': str(e)}), 500

@companies_bp.route('/<company_id>/profile', methods=['GET'])
@company_required
def get_company_profile(company_id):
    """
    Récupérer le profil complet d'une entreprise
    ---
    tags:
      - Entreprises
    security:
      - Bearer: []
    parameters:
      - in: path
        name: company_id
        type: string
        required: true
        description: ID de l'entreprise
    responses:
      200:
        description: Profil complet de l'entreprise
      403:
        description: Non autorisé à voir ce profil
      404:
        description: Entreprise non trouvée
    """
    try:
        company = Company.find_by_id(company_id)
        if not company:
            return jsonify({'message': 'Entreprise non trouvée'}), 404
        
        # Vérifier les permissions
        current_user_id = request.current_user_id
        if current_user_id != company_id:
            return jsonify({'message': 'Non autorisé à voir ce profil'}), 403
        
        company_dict = company.to_dict()
        company_dict['id'] = company.get_id()
        company_dict['jobs_count'] = company.get_jobs_count()
        
        # Récupérer les offres de l'entreprise
        from app.models.job import Job
        jobs = Job.find_by_company(company_id, limit=10)
        company_dict['jobs'] = []
        
        for job in jobs:
            job_dict = job.to_dict()
            job_dict['id'] = job.get_id()
            job_dict['applications_count'] = job.get_applications_count()
            company_dict['jobs'].append(job_dict)
        
        # Récupérer les candidatures récentes
        from app.models.application import Application
        applications = Application.find_by_company(company_id, limit=5)
        company_dict['recent_applications'] = []
        
        for app in applications:
            app_dict = app.to_dict()
            app_dict['id'] = app.get_id()
            # Ajouter les infos de l'utilisateur
            user_info = app.get_user_info()
            if user_info:
                app_dict['user_name'] = f"{user_info.prenom} {user_info.nom}"
                app_dict['user_email'] = user_info.email
            # Ajouter les infos du job
            job_info = app.get_job_info()
            if job_info:
                app_dict['job_title'] = job_info.titre
            company_dict['recent_applications'].append(app_dict)
        
        return jsonify({'profile': company_dict}), 200
        
    except Exception as e:
        return jsonify({'message': 'Erreur serveur', 'error': str(e)}), 500

@companies_bp.route('/<company_id>/jobs', methods=['GET'])
def get_company_jobs(company_id):
    """
    Récupérer toutes les offres d'une entreprise
    ---
    tags:
      - Entreprises
    parameters:
      - in: path
        name: company_id
        type: string
        required: true
        description: ID de l'entreprise
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
        description: Liste des offres de l'entreprise
      404:
        description: Entreprise non trouvée
    """
    try:
        # Vérifier que l'entreprise existe
        company = Company.find_by_id(company_id)
        if not company:
            return jsonify({'message': 'Entreprise non trouvée'}), 404
        
        page = int(request.args.get('page', 1))
        limit = int(request.args.get('limit', 10))
        limit = min(limit, 100)
        skip = (page - 1) * limit
        
        from app.models.job import Job
        jobs = Job.find_by_company(company_id, skip=skip, limit=limit)
        
        jobs_data = []
        for job in jobs:
            job_dict = job.to_dict()
            job_dict['id'] = job.get_id()
            job_dict['applications_count'] = job.get_applications_count()
            jobs_data.append(job_dict)
        
        # Compter le total des jobs
        from app.database import count_documents
        total = count_documents('jobs', {'company_id': company_id})
        
        return jsonify({
            'jobs': jobs_data,
            'company_name': company.nom,
            'total': total,
            'page': page,
            'limit': limit,
            'pages': (total + limit - 1) // limit
        }), 200
        
    except Exception as e:
        return jsonify({'message': 'Erreur serveur', 'error': str(e)}), 500
from flask import Blueprint, request, jsonify
from flasgger import swag_from
from app.models.job import Job
from app.models.company import Company
from app.auth import login_required, company_required

jobs_bp = Blueprint('jobs', __name__)

@jobs_bp.route('', methods=['GET'])
def get_all_jobs():
    """
    Récupérer toutes les offres d'emploi
    ---
    tags:
      - Emplois
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
      - in: query
        name: search
        type: string
        description: Recherche par titre ou description
      - in: query
        name: localisation
        type: string
        description: Filtrer par localisation
      - in: query
        name: type_contrat
        type: string
        description: Filtrer par type de contrat
    responses:
      200:
        description: Liste des offres d'emploi
        schema:
          type: object
          properties:
            jobs:
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
        limit = min(limit, 100)
        skip = (page - 1) * limit
        
        search = request.args.get('search')
        localisation = request.args.get('localisation')
        type_contrat = request.args.get('type_contrat')
        
        if search or localisation or type_contrat:
            jobs = Job.search_jobs(
                query_text=search,
                localisation=localisation,
                type_contrat=type_contrat,
                skip=skip,
                limit=limit
            )
        else:
            jobs = Job.find_all(skip=skip, limit=limit)
        
        total = Job.count_all()
        
        jobs_data = []
        for job in jobs:
            job_dict = job.to_dict()
            job_dict['id'] = job.get_id()
            
            # Ajouter les infos de l'entreprise
            company_info = job.get_company_info()
            if company_info:
                job_dict['company_name'] = company_info.nom
                job_dict['company_secteur'] = company_info.secteur
            
            jobs_data.append(job_dict)
        
        return jsonify({
            'jobs': jobs_data,
            'total': total,
            'page': page,
            'limit': limit,
            'pages': (total + limit - 1) // limit
        }), 200
        
    except Exception as e:
        return jsonify({'message': 'Erreur serveur', 'error': str(e)}), 500

@jobs_bp.route('/<job_id>', methods=['GET'])
def get_job(job_id):
    """
    Récupérer une offre d'emploi par ID
    ---
    tags:
      - Emplois
    parameters:
      - in: path
        name: job_id
        type: string
        required: true
        description: ID de l'offre d'emploi
    responses:
      200:
        description: Informations de l'offre d'emploi
      404:
        description: Offre d'emploi non trouvée
    """
    try:
        job = Job.find_by_id(job_id)
        
        if not job:
            return jsonify({'message': 'Offre d\'emploi non trouvée'}), 404
        
        job_dict = job.to_dict()
        job_dict['id'] = job.get_id()
        job_dict['applications_count'] = job.get_applications_count()
        
        # Ajouter les infos de l'entreprise
        company_info = job.get_company_info()
        if company_info:
            job_dict['company'] = {
                'id': company_info.get_id(),
                'nom': company_info.nom,
                'description': company_info.description,
                'secteur': company_info.secteur,
                'adresse': company_info.adresse,
                'site_web': company_info.site_web
            }
        
        return jsonify({'job': job_dict}), 200
        
    except Exception as e:
        return jsonify({'message': 'Erreur serveur', 'error': str(e)}), 500

@jobs_bp.route('', methods=['POST'])
@company_required
def create_job():
    """
    Créer une nouvelle offre d'emploi
    ---
    tags:
      - Emplois
    security:
      - Bearer: []
    parameters:
      - in: body
        name: job
        required: true
        schema:
          type: object
          required:
            - titre
            - description
          properties:
            titre:
              type: string
              example: "Développeur Full Stack"
            description:
              type: string
              example: "Nous recherchons un développeur Full Stack expérimenté..."
            salaire:
              type: string
              example: "35000-45000 EUR"
            type_contrat:
              type: string
              example: "CDI"
            localisation:
              type: string
              example: "Paris, France"
            competences_requises:
              type: array
              items:
                type: string
              example: ["JavaScript", "React", "Node.js", "MongoDB"]
            experience_requise:
              type: string
              example: "3-5 ans d'expérience"
    responses:
      201:
        description: Offre d'emploi créée avec succès
      400:
        description: Données invalides
      403:
        description: Accès réservé aux entreprises
    """
    try:
        data = request.get_json()
        
        # Validation des champs requis
        required_fields = ['titre', 'description']
        for field in required_fields:
            if not data.get(field):
                return jsonify({'message': f'Le champ {field} est requis'}), 400
        
        company_id = request.current_user_id
        
        # Créer l'offre d'emploi
        job = Job(
            company_id=company_id,
            titre=data['titre'],
            description=data['description'],
            salaire=data.get('salaire'),
            type_contrat=data.get('type_contrat', 'CDI'),
            localisation=data.get('localisation'),
            competences_requises=data.get('competences_requises', []),
            experience_requise=data.get('experience_requise', '')
        )
        
        job_id = job.save()
        
        if job_id:
            return jsonify({
                'message': 'Offre d\'emploi créée avec succès',
                'job_id': str(job_id)
            }), 201
        else:
            return jsonify({'message': 'Erreur lors de la création'}), 500
            
    except Exception as e:
        return jsonify({'message': 'Erreur serveur', 'error': str(e)}), 500

@jobs_bp.route('/<job_id>', methods=['PUT'])
@company_required
def update_job(job_id):
    """
    Mettre à jour une offre d'emploi
    ---
    tags:
      - Emplois
    security:
      - Bearer: []
    parameters:
      - in: path
        name: job_id
        type: string
        required: true
        description: ID de l'offre d'emploi
      - in: body
        name: job
        required: true
        schema:
          type: object
          properties:
            titre:
              type: string
              example: "Nouveau titre"
            description:
              type: string
              example: "Nouvelle description"
            salaire:
              type: string
              example: "40000-50000 EUR"
            type_contrat:
              type: string
              example: "CDD"
            localisation:
              type: string
              example: "Lyon, France"
            competences_requises:
              type: array
              items:
                type: string
              example: ["Python", "Django", "PostgreSQL"]
            experience_requise:
              type: string
              example: "5+ ans d'expérience"
            actif:
              type: boolean
              example: true
    responses:
      200:
        description: Offre d'emploi mise à jour avec succès
      400:
        description: Données invalides
      403:
        description: Non autorisé à modifier cette offre
      404:
        description: Offre d'emploi non trouvée
    """
    try:
        # Vérifier que l'offre existe
        job = Job.find_by_id(job_id)
        if not job:
            return jsonify({'message': 'Offre d\'emploi non trouvée'}), 404
        
        # Vérifier les permissions
        current_company_id = request.current_user_id
        if job.company_id != current_company_id:
            return jsonify({'message': 'Non autorisé à modifier cette offre'}), 403
        
        data = request.get_json()
        
        # Champs modifiables
        allowed_fields = ['titre', 'description', 'salaire', 'type_contrat', 
                         'localisation', 'competences_requises', 'experience_requise', 'actif']
        update_data = {}
        
        for field in allowed_fields:
            if field in data:
                update_data[field] = data[field]
        
        if not update_data:
            return jsonify({'message': 'Aucune donnée à mettre à jour'}), 400
        
        success = job.update(job_id, update_data)
        
        if success:
            return jsonify({'message': 'Offre d\'emploi mise à jour avec succès'}), 200
        else:
            return jsonify({'message': 'Erreur lors de la mise à jour'}), 500
            
    except Exception as e:
        return jsonify({'message': 'Erreur serveur', 'error': str(e)}), 500

@jobs_bp.route('/<job_id>', methods=['DELETE'])
@company_required
def delete_job(job_id):
    """
    Supprimer une offre d'emploi
    ---
    tags:
      - Emplois
    security:
      - Bearer: []
    parameters:
      - in: path
        name: job_id
        type: string
        required: true
        description: ID de l'offre d'emploi
    responses:
      200:
        description: Offre d'emploi supprimée avec succès
      403:
        description: Non autorisé à supprimer cette offre
      404:
        description: Offre d'emploi non trouvée
    """
    try:
        # Vérifier que l'offre existe
        job = Job.find_by_id(job_id)
        if not job:
            return jsonify({'message': 'Offre d\'emploi non trouvée'}), 404
        
        # Vérifier les permissions
        current_company_id = request.current_user_id
        if job.company_id != current_company_id:
            return jsonify({'message': 'Non autorisé à supprimer cette offre'}), 403
        
        success = Job.delete_by_id(job_id)
        
        if success:
            return jsonify({'message': 'Offre d\'emploi supprimée avec succès'}), 200
        else:
            return jsonify({'message': 'Erreur lors de la suppression'}), 500
            
    except Exception as e:
        return jsonify({'message': 'Erreur serveur', 'error': str(e)}), 500

@jobs_bp.route('/<job_id>/deactivate', methods=['PUT'])
@company_required
def deactivate_job(job_id):
    """
    Désactiver une offre d'emploi
    ---
    tags:
      - Emplois
    security:
      - Bearer: []
    parameters:
      - in: path
        name: job_id
        type: string
        required: true
        description: ID de l'offre d'emploi
    responses:
      200:
        description: Offre d'emploi désactivée avec succès
      403:
        description: Non autorisé à modifier cette offre
      404:
        description: Offre d'emploi non trouvée
    """
    try:
        # Vérifier que l'offre existe
        job = Job.find_by_id(job_id)
        if not job:
            return jsonify({'message': 'Offre d\'emploi non trouvée'}), 404
        
        # Vérifier les permissions
        current_company_id = request.current_user_id
        if job.company_id != current_company_id:
            return jsonify({'message': 'Non autorisé à modifier cette offre'}), 403
        
        success = job.deactivate(job_id)
        
        if success:
            return jsonify({'message': 'Offre d\'emploi désactivée avec succès'}), 200
        else:
            return jsonify({'message': 'Erreur lors de la désactivation'}), 500
            
    except Exception as e:
        return jsonify({'message': 'Erreur serveur', 'error': str(e)}), 500

@jobs_bp.route('/<job_id>/applications', methods=['GET'])
@company_required
def get_job_applications(job_id):
    """
    Récupérer les candidatures pour une offre d'emploi
    ---
    tags:
      - Emplois
    security:
      - Bearer: []
    parameters:
      - in: path
        name: job_id
        type: string
        required: true
        description: ID de l'offre d'emploi
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
        description: Liste des candidatures
      403:
        description: Non autorisé à voir ces candidatures
      404:
        description: Offre d'emploi non trouvée
    """
    try:
        # Vérifier que l'offre existe
        job = Job.find_by_id(job_id)
        if not job:
            return jsonify({'message': 'Offre d\'emploi non trouvée'}), 404
        
        # Vérifier les permissions
        current_company_id = request.current_user_id
        if job.company_id != current_company_id:
            return jsonify({'message': 'Non autorisé à voir ces candidatures'}), 403
        
        page = int(request.args.get('page', 1))
        limit = int(request.args.get('limit', 10))
        limit = min(limit, 100)
        skip = (page - 1) * limit
        
        from app.models.application import Application
        applications = Application.find_by_job(job_id, skip=skip, limit=limit)
        
        applications_data = []
        for app in applications:
            app_dict = app.to_dict()
            app_dict['id'] = app.get_id()
            
            # Ajouter les infos de l'utilisateur
            user_info = app.get_user_info()
            if user_info:
                app_dict['user'] = {
                    'id': user_info.get_id(),
                    'nom': user_info.nom,
                    'prenom': user_info.prenom,
                    'email': user_info.email,
                    'telephone': user_info.telephone,
                    'competences': user_info.competences,
                    'experience': user_info.experience,
                    'cv_url': user_info.cv_url
                }
            
            applications_data.append(app_dict)
        
        # Compter le total des candidatures
        from app.database import count_documents
        total = count_documents('applications', {'job_id': job_id})
        
        return jsonify({
            'applications': applications_data,
            'job_title': job.titre,
            'total': total,
            'page': page,
            'limit': limit,
            'pages': (total + limit - 1) // limit
        }), 200
        
    except Exception as e:
        return jsonify({'message': 'Erreur serveur', 'error': str(e)}), 500
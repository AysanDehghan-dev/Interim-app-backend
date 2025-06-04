from flask import Blueprint, request, jsonify
from flasgger import swag_from
from app.models.application import Application
from app.models.job import Job
from app.models.user import User
from app.models.company import Company
from app.auth import login_required, company_required

applications_bp = Blueprint('applications', __name__)

@applications_bp.route('', methods=['GET'])
@login_required
def get_all_applications():
    """
    Récupérer toutes les candidatures (admin ou filtré par utilisateur/entreprise)
    ---
    tags:
      - Candidatures
    security:
      - Bearer: []
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
        name: statut
        type: string
        description: Filtrer par statut
        enum: ["En attente", "Acceptée", "Refusée"]
    responses:
      200:
        description: Liste des candidatures
        schema:
          type: object
          properties:
            applications:
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
        statut = request.args.get('statut')
        
        current_user_id = request.current_user_id
        current_user_type = request.current_user_type
        
        # Filtrer selon le type d'utilisateur
        if current_user_type == 'user':
            if statut:
                applications_data = Application.find_by_status(statut, skip=skip, limit=limit)
                applications = [app for app in applications_data if app.user_id == current_user_id]
            else:
                applications = Application.find_by_user(current_user_id, skip=skip, limit=limit)
        elif current_user_type == 'company':
            if statut:
                applications_data = Application.find_by_status(statut, skip=skip, limit=limit)
                applications = [app for app in applications_data if app.company_id == current_user_id]
            else:
                applications = Application.find_by_company(current_user_id, skip=skip, limit=limit)
        else:
            # Admin ou autre cas
            if statut:
                applications = Application.find_by_status(statut, skip=skip, limit=limit)
            else:
                applications = Application.find_all(skip=skip, limit=limit)
        
        applications_data = []
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
                app_dict['job_localisation'] = job_info.localisation
            
            # Ajouter les infos de l'entreprise
            company_info = app.get_company_info()
            if company_info:
                app_dict['company_name'] = company_info.nom
            
            applications_data.append(app_dict)
        
        total = len(applications_data)  # Simple count for filtered results
        
        return jsonify({
            'applications': applications_data,
            'total': total,
            'page': page,
            'limit': limit,
            'pages': (total + limit - 1) // limit if total > 0 else 1
        }), 200
        
    except Exception as e:
        return jsonify({'message': 'Erreur serveur', 'error': str(e)}), 500

@applications_bp.route('/<application_id>', methods=['GET'])
@login_required
def get_application(application_id):
    """
    Récupérer une candidature par ID
    ---
    tags:
      - Candidatures
    security:
      - Bearer: []
    parameters:
      - in: path
        name: application_id
        type: string
        required: true
        description: ID de la candidature
    responses:
      200:
        description: Informations de la candidature
      403:
        description: Non autorisé à voir cette candidature
      404:
        description: Candidature non trouvée
    """
    try:
        application = Application.find_by_id(application_id)
        
        if not application:
            return jsonify({'message': 'Candidature non trouvée'}), 404
        
        # Vérifier les permissions
        current_user_id = request.current_user_id
        current_user_type = request.current_user_type
        
        if current_user_type == 'user' and application.user_id != current_user_id:
            return jsonify({'message': 'Non autorisé à voir cette candidature'}), 403
        elif current_user_type == 'company' and application.company_id != current_user_id:
            return jsonify({'message': 'Non autorisé à voir cette candidature'}), 403
        
        app_dict = application.to_dict()
        app_dict['id'] = application.get_id()
        
        # Ajouter les informations complètes
        user_info = application.get_user_info()
        if user_info:
            app_dict['user'] = user_info.to_dict()
            app_dict['user']['id'] = user_info.get_id()
        
        job_info = application.get_job_info()
        if job_info:
            app_dict['job'] = job_info.to_dict()
            app_dict['job']['id'] = job_info.get_id()
        
        company_info = application.get_company_info()
        if company_info:
            app_dict['company'] = company_info.to_dict()
            app_dict['company']['id'] = company_info.get_id()
        
        return jsonify({'application': app_dict}), 200
        
    except Exception as e:
        return jsonify({'message': 'Erreur serveur', 'error': str(e)}), 500

@applications_bp.route('', methods=['POST'])
@login_required
def create_application():
    """
    Créer une nouvelle candidature
    ---
    tags:
      - Candidatures
    security:
      - Bearer: []
    parameters:
      - in: body
        name: application
        required: true
        schema:
          type: object
          required:
            - job_id
          properties:
            job_id:
              type: string
              example: "507f1f77bcf86cd799439011"
            lettre_motivation:
              type: string
              example: "Je suis très intéressé par ce poste car..."
    responses:
      201:
        description: Candidature créée avec succès
      400:
        description: Données invalides
      403:
        description: Accès réservé aux utilisateurs
      404:
        description: Offre d'emploi non trouvée
      409:
        description: Candidature déjà existante
    """
    try:
        # Vérifier que c'est un utilisateur (pas une entreprise)
        if request.current_user_type != 'user':
            return jsonify({'message': 'Seuls les utilisateurs peuvent postuler'}), 403
        
        data = request.get_json()
        
        # Validation des champs requis
        if not data.get('job_id'):
            return jsonify({'message': 'Le champ job_id est requis'}), 400
        
        job_id = data['job_id']
        user_id = request.current_user_id
        
        # Vérifier que l'offre existe et est active
        job = Job.find_by_id(job_id)
        if not job:
            return jsonify({'message': 'Offre d\'emploi non trouvée'}), 404
        
        if not job.actif:
            return jsonify({'message': 'Cette offre d\'emploi n\'est plus active'}), 400
        
        # Vérifier que l'utilisateur n'a pas déjà postulé
        if Application.check_existing_application(user_id, job_id):
            return jsonify({'message': 'Vous avez déjà postulé à cette offre'}), 409
        
        # Créer la candidature
        application = Application(
            user_id=user_id,
            job_id=job_id,
            company_id=job.company_id,
            lettre_motivation=data.get('lettre_motivation', '')
        )
        
        application_id = application.save()
        
        if application_id:
            return jsonify({
                'message': 'Candidature envoyée avec succès',
                'application_id': str(application_id)
            }), 201
        else:
            return jsonify({'message': 'Erreur lors de l\'envoi de la candidature'}), 500
            
    except Exception as e:
        return jsonify({'message': 'Erreur serveur', 'error': str(e)}), 500

@applications_bp.route('/<application_id>', methods=['PUT'])
@login_required
def update_application(application_id):
    """
    Mettre à jour une candidature
    ---
    tags:
      - Candidatures
    security:
      - Bearer: []
    parameters:
      - in: path
        name: application_id
        type: string
        required: true
        description: ID de la candidature
      - in: body
        name: application
        required: true
        schema:
          type: object
          properties:
            lettre_motivation:
              type: string
              example: "Nouvelle lettre de motivation..."
            statut:
              type: string
              enum: ["En attente", "Acceptée", "Refusée"]
              example: "Acceptée"
            notes_entreprise:
              type: string
              example: "Candidat très intéressant"
    responses:
      200:
        description: Candidature mise à jour avec succès
      400:
        description: Données invalides
      403:
        description: Non autorisé à modifier cette candidature
      404:
        description: Candidature non trouvée
    """
    try:
        # Vérifier que la candidature existe
        application = Application.find_by_id(application_id)
        if not application:
            return jsonify({'message': 'Candidature non trouvée'}), 404
        
        current_user_id = request.current_user_id
        current_user_type = request.current_user_type
        
        data = request.get_json()
        update_data = {}
        
        # Permissions selon le type d'utilisateur
        if current_user_type == 'user':
            # L'utilisateur peut modifier sa lettre de motivation seulement
            if application.user_id != current_user_id:
                return jsonify({'message': 'Non autorisé à modifier cette candidature'}), 403
            
            if 'lettre_motivation' in data:
                update_data['lettre_motivation'] = data['lettre_motivation']
                
        elif current_user_type == 'company':
            # L'entreprise peut modifier le statut et les notes
            if application.company_id != current_user_id:
                return jsonify({'message': 'Non autorisé à modifier cette candidature'}), 403
            
            if 'statut' in data:
                valid_statuts = ['En attente', 'Acceptée', 'Refusée']
                if data['statut'] in valid_statuts:
                    update_data['statut'] = data['statut']
                else:
                    return jsonify({'message': 'Statut invalide'}), 400
            
            if 'notes_entreprise' in data:
                update_data['notes_entreprise'] = data['notes_entreprise']
        
        if not update_data:
            return jsonify({'message': 'Aucune donnée à mettre à jour'}), 400
        
        success = application.update(application_id, update_data)
        
        if success:
            return jsonify({'message': 'Candidature mise à jour avec succès'}), 200
        else:
            return jsonify({'message': 'Erreur lors de la mise à jour'}), 500
            
    except Exception as e:
        return jsonify({'message': 'Erreur serveur', 'error': str(e)}), 500

@applications_bp.route('/<application_id>', methods=['DELETE'])
@login_required
def delete_application(application_id):
    """
    Supprimer une candidature
    ---
    tags:
      - Candidatures
    security:
      - Bearer: []
    parameters:
      - in: path
        name: application_id
        type: string
        required: true
        description: ID de la candidature
    responses:
      200:
        description: Candidature supprimée avec succès
      403:
        description: Non autorisé à supprimer cette candidature
      404:
        description: Candidature non trouvée
    """
    try:
        # Vérifier que la candidature existe
        application = Application.find_by_id(application_id)
        if not application:
            return jsonify({'message': 'Candidature non trouvée'}), 404
        
        current_user_id = request.current_user_id
        current_user_type = request.current_user_type
        
        # Vérifier les permissions
        if current_user_type == 'user' and application.user_id != current_user_id:
            return jsonify({'message': 'Non autorisé à supprimer cette candidature'}), 403
        elif current_user_type == 'company' and application.company_id != current_user_id:
            return jsonify({'message': 'Non autorisé à supprimer cette candidature'}), 403
        
        success = Application.delete_by_id(application_id)
        
        if success:
            return jsonify({'message': 'Candidature supprimée avec succès'}), 200
        else:
            return jsonify({'message': 'Erreur lors de la suppression'}), 500
            
    except Exception as e:
        return jsonify({'message': 'Erreur serveur', 'error': str(e)}), 500

@applications_bp.route('/<application_id>/status', methods=['PUT'])
@company_required
def update_application_status(application_id):
    """
    Mettre à jour le statut d'une candidature (entreprise seulement)
    ---
    tags:
      - Candidatures
    security:
      - Bearer: []
    parameters:
      - in: path
        name: application_id
        type: string
        required: true
        description: ID de la candidature
      - in: body
        name: status
        required: true
        schema:
          type: object
          required:
            - statut
          properties:
            statut:
              type: string
              enum: ["En attente", "Acceptée", "Refusée"]
              example: "Acceptée"
            notes_entreprise:
              type: string
              example: "Profil très intéressant, bon match avec nos besoins"
    responses:
      200:
        description: Statut mis à jour avec succès
      400:
        description: Statut invalide
      403:
        description: Non autorisé à modifier cette candidature
      404:
        description: Candidature non trouvée
    """
    try:
        # Vérifier que la candidature existe
        application = Application.find_by_id(application_id)
        if not application:
            return jsonify({'message': 'Candidature non trouvée'}), 404
        
        # Vérifier les permissions
        current_company_id = request.current_user_id
        if application.company_id != current_company_id:
            return jsonify({'message': 'Non autorisé à modifier cette candidature'}), 403
        
        data = request.get_json()
        
        if not data.get('statut'):
            return jsonify({'message': 'Le statut est requis'}), 400
        
        valid_statuts = ['En attente', 'Acceptée', 'Refusée']
        if data['statut'] not in valid_statuts:
            return jsonify({'message': 'Statut invalide'}), 400
        
        success = application.update_status(
            application_id, 
            data['statut'], 
            data.get('notes_entreprise')
        )
        
        if success:
            return jsonify({'message': 'Statut mis à jour avec succès'}), 200
        else:
            return jsonify({'message': 'Erreur lors de la mise à jour'}), 500
            
    except Exception as e:
        return jsonify({'message': 'Erreur serveur', 'error': str(e)}), 500

@applications_bp.route('/statistics', methods=['GET'])
@login_required
def get_applications_statistics():
    """
    Récupérer les statistiques des candidatures
    ---
    tags:
      - Candidatures
    security:
      - Bearer: []
    responses:
      200:
        description: Statistiques des candidatures
        schema:
          type: object
          properties:
            total_applications:
              type: integer
            by_status:
              type: object
              properties:
                en_attente:
                  type: integer
                acceptees:
                  type: integer
                refusees:
                  type: integer
    """
    try:
        current_user_id = request.current_user_id
        current_user_type = request.current_user_type
        
        # Statistiques selon le type d'utilisateur
        if current_user_type == 'user':
            # Statistiques pour l'utilisateur
            user_applications = Application.find_by_user(current_user_id, limit=1000)
            total = len(user_applications)
            
            en_attente = len([app for app in user_applications if app.statut == 'En attente'])
            acceptees = len([app for app in user_applications if app.statut == 'Acceptée'])
            refusees = len([app for app in user_applications if app.statut == 'Refusée'])
            
        elif current_user_type == 'company':
            # Statistiques pour l'entreprise
            company_applications = Application.find_by_company(current_user_id, limit=1000)
            total = len(company_applications)
            
            en_attente = len([app for app in company_applications if app.statut == 'En attente'])
            acceptees = len([app for app in company_applications if app.statut == 'Acceptée'])
            refusees = len([app for app in company_applications if app.statut == 'Refusée'])
        
        else:
            # Statistiques globales (admin)
            total = Application.count_all()
            en_attente = Application.count_by_status('En attente')
            acceptees = Application.count_by_status('Acceptée')
            refusees = Application.count_by_status('Refusée')
        
        return jsonify({
            'total_applications': total,
            'by_status': {
                'en_attente': en_attente,
                'acceptees': acceptees,
                'refusees': refusees
            },
            'user_type': current_user_type
        }), 200
        
    except Exception as e:
        return jsonify({'message': 'Erreur serveur', 'error': str(e)}), 500

@applications_bp.route('/user/<user_id>', methods=['GET'])
@login_required
def get_user_applications(user_id):
    """
    Récupérer les candidatures d'un utilisateur spécifique
    ---
    tags:
      - Candidatures
    security:
      - Bearer: []
    parameters:
      - in: path
        name: user_id
        type: string
        required: true
        description: ID de l'utilisateur
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
        description: Liste des candidatures de l'utilisateur
      403:
        description: Non autorisé à voir ces candidatures
    """
    try:
        # Vérifier les permissions
        current_user_id = request.current_user_id
        current_user_type = request.current_user_type
        
        if current_user_type == 'user' and current_user_id != user_id:
            return jsonify({'message': 'Non autorisé à voir ces candidatures'}), 403
        
        page = int(request.args.get('page', 1))
        limit = int(request.args.get('limit', 10))
        limit = min(limit, 100)
        skip = (page - 1) * limit
        
        applications = Application.find_by_user(user_id, skip=skip, limit=limit)
        
        applications_data = []
        for app in applications:
            app_dict = app.to_dict()
            app_dict['id'] = app.get_id()
            
            # Ajouter les infos du job et de l'entreprise
            job_info = app.get_job_info()
            if job_info:
                app_dict['job_title'] = job_info.titre
                app_dict['job_localisation'] = job_info.localisation
                app_dict['job_type_contrat'] = job_info.type_contrat
            
            company_info = app.get_company_info()
            if company_info:
                app_dict['company_name'] = company_info.nom
                app_dict['company_secteur'] = company_info.secteur
            
            applications_data.append(app_dict)
        
        # Compter le total
        from app.database import count_documents
        total = count_documents('applications', {'user_id': user_id})
        
        return jsonify({
            'applications': applications_data,
            'total': total,
            'page': page,
            'limit': limit,
            'pages': (total + limit - 1) // limit
        }), 200
        
    except Exception as e:
        return jsonify({'message': 'Erreur serveur', 'error': str(e)}), 500

@applications_bp.route('/company/<company_id>', methods=['GET'])
@company_required
def get_company_applications(company_id):
    """
    Récupérer les candidatures d'une entreprise spécifique
    ---
    tags:
      - Candidatures
    security:
      - Bearer: []
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
      - in: query
        name: statut
        type: string
        description: Filtrer par statut
    responses:
      200:
        description: Liste des candidatures de l'entreprise
      403:
        description: Non autorisé à voir ces candidatures
    """
    try:
        # Vérifier les permissions
        current_company_id = request.current_user_id
        if current_company_id != company_id:
            return jsonify({'message': 'Non autorisé à voir ces candidatures'}), 403
        
        page = int(request.args.get('page', 1))
        limit = int(request.args.get('limit', 10))
        limit = min(limit, 100)
        skip = (page - 1) * limit
        statut = request.args.get('statut')
        
        if statut:
            # Filtrer par statut
            all_applications = Application.find_by_company(company_id, limit=1000)
            applications = [app for app in all_applications if app.statut == statut]
            # Pagination manuelle pour les résultats filtrés
            applications = applications[skip:skip+limit]
        else:
            applications = Application.find_by_company(company_id, skip=skip, limit=limit)
        
        applications_data = []
        for app in applications:
            app_dict = app.to_dict()
            app_dict['id'] = app.get_id()
            
            # Ajouter les infos de l'utilisateur et du job
            user_info = app.get_user_info()
            if user_info:
                app_dict['user'] = {
                    'id': user_info.get_id(),
                    'nom': user_info.nom,
                    'prenom': user_info.prenom,
                    'email': user_info.email,
                    'competences': user_info.competences,
                    'experience': user_info.experience
                }
            
            job_info = app.get_job_info()
            if job_info:
                app_dict['job_title'] = job_info.titre
                app_dict['job_id'] = job_info.get_id()
            
            applications_data.append(app_dict)
        
        # Compter le total
        from app.database import count_documents
        query = {'company_id': company_id}
        if statut:
            query['statut'] = statut
        total = count_documents('applications', query)
        
        return jsonify({
            'applications': applications_data,
            'total': total,
            'page': page,
            'limit': limit,
            'pages': (total + limit - 1) // limit
        }), 200
        
    except Exception as e:
        return jsonify({'message': 'Erreur serveur', 'error': str(e)}), 500
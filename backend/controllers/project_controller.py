"""
Contrôleur de projets de recherche pour Georges Medical Chatbot.
Gestion des projets, demandes d'accès, consentements, critères d'inclusion.
"""

import logging
from flask import Blueprint, request, jsonify, current_app
from backend.core.security import require_auth
from backend.middleware.session_manager import require_active_session

logger = logging.getLogger(__name__)

project_bp = Blueprint('project', __name__, url_prefix='/api/projects')


@project_bp.route('/', methods=['GET'])
@require_auth()
def list_projects():
    """Liste tous les projets actifs."""
    try:
        dm = current_app.data_manager
        status = request.args.get('status', 'active')

        projects = dm.get_all_projects(status=status)

        # Nettoyer les _id MongoDB
        for project in projects:
            project.pop('_id', None)

        return jsonify({'projects': projects}), 200

    except Exception as e:
        logger.error(f"Erreur de listage des projets: {e}")
        return jsonify({'error': 'Erreur interne du serveur'}), 500


@project_bp.route('/', methods=['POST'])
@require_auth(roles=['admin'])
def create_project():
    """Crée un nouveau projet de recherche (admin uniquement)."""
    try:
        user_id = request.current_user['user_id']
        data = request.get_json()
        if not data:
            return jsonify({'error': 'Données requises'}), 400

        security = current_app.security_manager
        dm = current_app.data_manager

        name = data.get('name', '').strip()
        description = data.get('description', '').strip()
        slug = data.get('slug', '').strip().lower()

        if not name or not slug:
            return jsonify({'error': 'Le nom et le slug sont requis'}), 400

        # Valider le slug (alphanumeric + tirets)
        import re
        if not re.match(r'^[a-z0-9-]+$', slug):
            return jsonify({'error': 'Le slug ne peut contenir que des lettres minuscules, chiffres et tirets'}), 400

        name = security.sanitize_input(name, max_length=200)
        description = security.sanitize_input(description, max_length=5000)

        model_config = data.get('model_config', {})
        inclusion_criteria = data.get('inclusion_criteria', [])

        project = dm.create_project(
            name=name,
            description=description,
            slug=slug,
            created_by=user_id,
            model_config=model_config,
            inclusion_criteria=inclusion_criteria
        )

        if not project:
            return jsonify({'error': 'Ce slug est déjà utilisé'}), 409

        project.pop('_id', None)

        return jsonify({
            'message': 'Projet créé',
            'project': project
        }), 201

    except Exception as e:
        logger.error(f"Erreur de création de projet: {e}")
        return jsonify({'error': 'Erreur interne du serveur'}), 500


@project_bp.route('/<slug>', methods=['GET'])
@require_auth()
def get_project(slug):
    """Récupère un projet par son slug."""
    try:
        dm = current_app.data_manager

        project = dm.get_project_by_slug(slug)
        if not project:
            return jsonify({'error': 'Projet non trouvé'}), 404

        project.pop('_id', None)

        return jsonify({'project': project}), 200

    except Exception as e:
        logger.error(f"Erreur de récupération du projet: {e}")
        return jsonify({'error': 'Erreur interne du serveur'}), 500


@project_bp.route('/<slug>/request-access', methods=['POST'])
@require_auth()
def request_access(slug):
    """Demande l'accès à un projet de recherche."""
    try:
        user_id = request.current_user['user_id']
        data = request.get_json() or {}

        dm = current_app.data_manager
        security = current_app.security_manager

        project = dm.get_project_by_slug(slug)
        if not project:
            return jsonify({'error': 'Projet non trouvé'}), 404

        # Vérifier si l'utilisateur est déjà participant
        if user_id in project.get('participants', []):
            return jsonify({'error': 'Vous êtes déjà participant à ce projet'}), 409

        # Vérifier si une demande est déjà en attente
        for req in project.get('access_requests', []):
            if req['userId'] == user_id and req['status'] == 'pending':
                return jsonify({'error': 'Une demande est déjà en attente'}), 409

        message = security.sanitize_input(data.get('message', ''), max_length=1000)

        access_request = dm.add_access_request(
            project_id=project['projectId'],
            user_id=user_id,
            message=message
        )

        return jsonify({
            'message': 'Demande d\'accès envoyée',
            'request': access_request
        }), 201

    except Exception as e:
        logger.error(f"Erreur de demande d'accès: {e}")
        return jsonify({'error': 'Erreur interne du serveur'}), 500


@project_bp.route('/<slug>/consent', methods=['POST'])
@require_auth()
def give_consent(slug):
    """Donne le consentement pour participer à un projet."""
    try:
        user_id = request.current_user['user_id']
        data = request.get_json() or {}

        dm = current_app.data_manager

        project = dm.get_project_by_slug(slug)
        if not project:
            return jsonify({'error': 'Projet non trouvé'}), 404

        granted = data.get('granted', False)
        ip_address = request.remote_addr

        consent = dm.add_user_consent(
            user_id=user_id,
            project_id=project['projectId'],
            consent_type='project_participation',
            granted=granted,
            ip_address=ip_address
        )

        return jsonify({
            'message': 'Consentement enregistré',
            'consent': consent
        }), 201

    except Exception as e:
        logger.error(f"Erreur d'enregistrement du consentement: {e}")
        return jsonify({'error': 'Erreur interne du serveur'}), 500


@project_bp.route('/<slug>/check-inclusion', methods=['POST'])
@require_auth()
def check_inclusion(slug):
    """Vérifie les critères d'inclusion d'un utilisateur pour un projet."""
    try:
        user_id = request.current_user['user_id']
        data = request.get_json() or {}

        dm = current_app.data_manager

        project = dm.get_project_by_slug(slug)
        if not project:
            return jsonify({'error': 'Projet non trouvé'}), 404

        inclusion_criteria = project.get('inclusion_criteria', [])
        user_responses = data.get('responses', {})

        if not inclusion_criteria:
            return jsonify({
                'eligible': True,
                'message': 'Aucun critère d\'inclusion défini pour ce projet'
            }), 200

        # Vérifier chaque critère
        eligible = True
        failed_criteria = []
        for criterion in inclusion_criteria:
            criterion_key = criterion.get('key', '')
            criterion_type = criterion.get('type', 'boolean')
            required_value = criterion.get('required_value')

            user_value = user_responses.get(criterion_key)

            if user_value is None:
                eligible = False
                failed_criteria.append({
                    'key': criterion_key,
                    'reason': 'Réponse manquante'
                })
                continue

            if criterion_type == 'boolean':
                if bool(user_value) != bool(required_value):
                    eligible = False
                    failed_criteria.append({
                        'key': criterion_key,
                        'reason': 'Critère non satisfait'
                    })
            elif criterion_type == 'range':
                min_val = criterion.get('min')
                max_val = criterion.get('max')
                try:
                    val = float(user_value)
                    if min_val is not None and val < float(min_val):
                        eligible = False
                        failed_criteria.append({
                            'key': criterion_key,
                            'reason': f'Valeur inférieure au minimum ({min_val})'
                        })
                    if max_val is not None and val > float(max_val):
                        eligible = False
                        failed_criteria.append({
                            'key': criterion_key,
                            'reason': f'Valeur supérieure au maximum ({max_val})'
                        })
                except (ValueError, TypeError):
                    eligible = False
                    failed_criteria.append({
                        'key': criterion_key,
                        'reason': 'Valeur non numérique'
                    })

        return jsonify({
            'eligible': eligible,
            'failed_criteria': failed_criteria,
            'total_criteria': len(inclusion_criteria)
        }), 200

    except Exception as e:
        logger.error(f"Erreur de vérification d'inclusion: {e}")
        return jsonify({'error': 'Erreur interne du serveur'}), 500


@project_bp.route('/<project_id>', methods=['PUT'])
@require_auth(roles=['admin'])
def update_project(project_id):
    """Met à jour un projet (admin uniquement)."""
    try:
        data = request.get_json()
        if not data:
            return jsonify({'error': 'Données requises'}), 400

        dm = current_app.data_manager
        security = current_app.security_manager

        project = dm.get_project_by_id(project_id)
        if not project:
            return jsonify({'error': 'Projet non trouvé'}), 404

        # Champs modifiables
        allowed_fields = ['name', 'description', 'model_config',
                          'inclusion_criteria', 'consent_form_text', 'status']
        updates = {}
        for field in allowed_fields:
            if field in data:
                if isinstance(data[field], str):
                    updates[field] = security.sanitize_input(data[field], max_length=5000)
                else:
                    updates[field] = data[field]

        if not updates:
            return jsonify({'error': 'Aucun champ à mettre à jour'}), 400

        success = dm.update_project(project_id, updates)
        if not success:
            return jsonify({'error': 'Erreur de mise à jour'}), 500

        current_app.audit_logger.log_action(
            user_id=request.current_user['user_id'],
            action='update_project',
            resource_type='project',
            resource_id=project_id,
            status='success',
            details={'fields': list(updates.keys())}
        )

        return jsonify({'message': 'Projet mis à jour'}), 200

    except Exception as e:
        logger.error(f"Erreur de mise à jour du projet: {e}")
        return jsonify({'error': 'Erreur interne du serveur'}), 500

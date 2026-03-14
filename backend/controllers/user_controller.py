"""
Contrôleur utilisateur pour Georges Medical Chatbot.
Profil, consentements, export de données (RGPD), suppression de compte.
"""

import logging
from flask import Blueprint, request, jsonify, current_app
from backend.core.security import require_auth
from backend.middleware.session_manager import require_active_session

logger = logging.getLogger(__name__)

user_bp = Blueprint('user', __name__, url_prefix='/api/user')


@user_bp.route('/profile', methods=['GET'])
@require_auth()
@require_active_session
def get_profile():
    """Récupère le profil de l'utilisateur connecté."""
    try:
        user_id = request.current_user['user_id']
        dm = current_app.data_manager

        user = dm.get_user_by_id(user_id)
        if not user:
            return jsonify({'error': 'Utilisateur non trouvé'}), 404

        from backend.models.user import sanitize_user_response
        user_response = sanitize_user_response(user, include_sensitive=True)

        return jsonify({'user': user_response}), 200

    except Exception as e:
        logger.error(f"Erreur de récupération du profil: {e}")
        return jsonify({'error': 'Erreur interne du serveur'}), 500


@user_bp.route('/profile', methods=['PUT'])
@require_auth()
@require_active_session
def update_profile():
    """Met à jour le profil de l'utilisateur connecté."""
    try:
        user_id = request.current_user['user_id']
        data = request.get_json()
        if not data:
            return jsonify({'error': 'Données requises'}), 400

        dm = current_app.data_manager
        security = current_app.security_manager

        # Champs modifiables
        allowed_fields = ['nom', 'prenom', 'date_naissance']
        updates = {}
        for field in allowed_fields:
            if field in data:
                updates[field] = security.sanitize_input(data[field], max_length=200)

        if not updates:
            return jsonify({'error': 'Aucun champ à mettre à jour'}), 400

        success = dm.update_user(user_id, updates)
        if not success:
            return jsonify({'error': 'Erreur de mise à jour'}), 500

        current_app.audit_logger.log_action(
            user_id=user_id,
            action='update_profile',
            resource_type='user',
            resource_id=user_id,
            status='success',
            details={'fields': list(updates.keys())}
        )

        # Récupérer le profil mis à jour
        user = dm.get_user_by_id(user_id)
        from backend.models.user import sanitize_user_response
        user_response = sanitize_user_response(user, include_sensitive=True)

        return jsonify({
            'message': 'Profil mis à jour',
            'user': user_response
        }), 200

    except Exception as e:
        logger.error(f"Erreur de mise à jour du profil: {e}")
        return jsonify({'error': 'Erreur interne du serveur'}), 500


@user_bp.route('/consents', methods=['GET'])
@require_auth()
def get_consents():
    """Récupère les consentements de l'utilisateur."""
    try:
        user_id = request.current_user['user_id']
        dm = current_app.data_manager

        # Récupérer depuis la collection consents
        if hasattr(dm, 'db'):
            # MongoDB
            consents = list(dm.db.consents.find(
                {'userId': user_id},
                {'_id': 0}
            ).sort('timestamp', -1))
        else:
            # Elasticsearch
            result = dm.es.search(
                index=dm._index('consents'),
                body={
                    'query': {'term': {'userId': user_id}},
                    'sort': [{'timestamp': {'order': 'desc'}}],
                    'size': 100
                }
            )
            consents = [hit['_source'] for hit in result['hits']['hits']]

        return jsonify({'consents': consents}), 200

    except Exception as e:
        logger.error(f"Erreur de récupération des consentements: {e}")
        return jsonify({'error': 'Erreur interne du serveur'}), 500


@user_bp.route('/consents', methods=['POST'])
@require_auth()
def add_consent():
    """Enregistre un nouveau consentement."""
    try:
        user_id = request.current_user['user_id']
        data = request.get_json()
        if not data:
            return jsonify({'error': 'Données requises'}), 400

        consent_type = data.get('consent_type')
        granted = data.get('granted', False)
        project_id = data.get('project_id')

        if not consent_type:
            return jsonify({'error': 'Le type de consentement est requis'}), 400

        valid_types = ['data_processing', 'research', 'cookies', 'marketing',
                       'project_participation', 'data_sharing']
        if consent_type not in valid_types:
            return jsonify({'error': f'Type de consentement invalide. Types valides: {", ".join(valid_types)}'}), 400

        dm = current_app.data_manager
        ip_address = request.remote_addr

        consent = dm.add_user_consent(
            user_id=user_id,
            project_id=project_id,
            consent_type=consent_type,
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


@user_bp.route('/data-export', methods=['GET'])
@require_auth()
def export_user_data():
    """
    Exporte toutes les données de l'utilisateur (droit à la portabilité RGPD).
    """
    try:
        user_id = request.current_user['user_id']
        dm = current_app.data_manager

        # Récupérer le profil
        user = dm.get_user_by_id(user_id)
        if not user:
            return jsonify({'error': 'Utilisateur non trouvé'}), 404

        from backend.models.user import sanitize_user_response
        user_data = sanitize_user_response(user, include_sensitive=True)

        # Récupérer les conversations
        conversations, _ = dm.get_user_conversations(user_id, limit=1000)

        # Récupérer les conversations complètes avec messages déchiffrés
        full_conversations = []
        for conv in conversations:
            full_conv = dm.get_conversation(conv['conversationId'], decrypt=True)
            if full_conv:
                # Nettoyer pour l'export
                clean_conv = {
                    'conversationId': full_conv.get('conversationId'),
                    'created_at': full_conv.get('created_at'),
                    'messages': []
                }
                for msg in full_conv.get('messages', []):
                    clean_conv['messages'].append({
                        'role': msg.get('role'),
                        'content': msg.get('content_decrypted', ''),
                        'timestamp': msg.get('timestamp')
                    })
                full_conversations.append(clean_conv)

        # Récupérer les consentements
        if hasattr(dm, 'db'):
            consents = list(dm.db.consents.find(
                {'userId': user_id}, {'_id': 0}
            ))
        else:
            result = dm.es.search(
                index=dm._index('consents'),
                body={
                    'query': {'term': {'userId': user_id}},
                    'size': 1000
                }
            )
            consents = [hit['_source'] for hit in result['hits']['hits']]

        # Récupérer le journal d'audit
        audit_trail = current_app.audit_logger.get_user_audit_trail(user_id)

        export_data = {
            'user_profile': user_data,
            'conversations': full_conversations,
            'consents': consents,
            'audit_trail': audit_trail,
            'export_date': __import__('datetime').datetime.now(
                __import__('datetime').timezone.utc
            ).isoformat()
        }

        current_app.audit_logger.log_action(
            user_id=user_id,
            action='data_export',
            resource_type='user',
            resource_id=user_id,
            status='success'
        )

        return jsonify(export_data), 200

    except Exception as e:
        logger.error(f"Erreur d'export des données: {e}")
        return jsonify({'error': 'Erreur interne du serveur'}), 500


@user_bp.route('/delete-account', methods=['DELETE'])
@require_auth()
def delete_account():
    """
    Supprime le compte de l'utilisateur (droit à l'effacement RGPD).
    """
    try:
        user_id = request.current_user['user_id']
        dm = current_app.data_manager

        # Vérifier que l'utilisateur existe
        user = dm.get_user_by_id(user_id)
        if not user:
            return jsonify({'error': 'Utilisateur non trouvé'}), 404

        # Supprimer les conversations
        if hasattr(dm, 'db'):
            dm.db.conversations.delete_many({'userId': user_id})
            dm.db.consents.delete_many({'userId': user_id})
            dm.db.users.delete_one({'userId': user_id})
        else:
            # Elasticsearch
            dm.es.delete_by_query(
                index=dm._index('conversations'),
                body={'query': {'term': {'userId': user_id}}}
            )
            dm.es.delete_by_query(
                index=dm._index('consents'),
                body={'query': {'term': {'userId': user_id}}}
            )
            dm.es.delete(
                index=dm._index('users'),
                id=user_id,
                refresh='wait_for'
            )

        # Terminer la session
        auth_header = request.headers.get('Authorization', '')
        token = auth_header.split('Bearer ')[1].strip()
        current_app.session_manager.terminate_session(token)

        current_app.audit_logger.log_action(
            user_id=user_id,
            action='delete_account',
            resource_type='user',
            resource_id=user_id,
            status='success'
        )

        logger.info(f"Compte supprimé: {user_id}")
        return jsonify({'message': 'Compte supprimé avec succès'}), 200

    except Exception as e:
        logger.error(f"Erreur de suppression du compte: {e}")
        return jsonify({'error': 'Erreur interne du serveur'}), 500

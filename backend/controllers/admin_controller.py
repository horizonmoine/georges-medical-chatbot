"""
Contrôleur d'administration pour Georges Medical Chatbot.
Gestion des utilisateurs, analytics, audit, projets (admin/médecin).
"""

import logging
from flask import Blueprint, request, jsonify, current_app
from backend.core.security import require_auth
from backend.models.user import sanitize_user_response

logger = logging.getLogger(__name__)

admin_bp = Blueprint('admin', __name__, url_prefix='/api/admin')


@admin_bp.route('/users', methods=['GET'])
@require_auth(roles=['admin'])
def list_users():
    """Liste tous les utilisateurs (admin uniquement)."""
    try:
        dm = current_app.data_manager
        limit = request.args.get('limit', 50, type=int)
        offset = request.args.get('offset', 0, type=int)

        limit = min(limit, 200)
        offset = max(offset, 0)

        if hasattr(dm, 'db'):
            # MongoDB
            cursor = dm.db.users.find().skip(offset).limit(limit)
            users = []
            for user in cursor:
                user = dm._decrypt_user_fields(user)
                users.append(sanitize_user_response(user, include_sensitive=True))
            total = dm.db.users.count_documents({})
        else:
            # Elasticsearch
            result = dm.es.search(
                index=dm._index('users'),
                body={
                    'query': {'match_all': {}},
                    'size': limit,
                    'from': offset,
                    'sort': [{'created_at': {'order': 'desc'}}]
                }
            )
            users = []
            for hit in result['hits']['hits']:
                user = dm._decrypt_user_fields(hit['_source'])
                users.append(sanitize_user_response(user, include_sensitive=True))
            total = result['hits']['total']['value']

        return jsonify({
            'users': users,
            'total': total,
            'limit': limit,
            'offset': offset
        }), 200

    except Exception as e:
        logger.error(f"Erreur de listage des utilisateurs: {e}")
        return jsonify({'error': 'Erreur interne du serveur'}), 500


@admin_bp.route('/users/<user_id>', methods=['PUT'])
@require_auth(roles=['admin'])
def update_user(user_id):
    """Met à jour un utilisateur (admin uniquement)."""
    try:
        data = request.get_json()
        if not data:
            return jsonify({'error': 'Données requises'}), 400

        dm = current_app.data_manager

        user = dm.get_user_by_id(user_id)
        if not user:
            return jsonify({'error': 'Utilisateur non trouvé'}), 404

        # Champs modifiables par l'admin
        allowed_fields = ['role', 'is_active', 'is_confirmed']
        updates = {}
        for field in allowed_fields:
            if field in data:
                updates[field] = data[field]

        if not updates:
            return jsonify({'error': 'Aucun champ à mettre à jour'}), 400

        # Valider le rôle
        if 'role' in updates:
            valid_roles = ['patient', 'medecin', 'admin', 'investigateur']
            if updates['role'] not in valid_roles:
                return jsonify({'error': f'Rôle invalide. Rôles valides: {", ".join(valid_roles)}'}), 400

        success = dm.update_user(user_id, updates)
        if not success:
            return jsonify({'error': 'Erreur de mise à jour'}), 500

        current_app.audit_logger.log_action(
            user_id=request.current_user['user_id'],
            action='admin_update_user',
            resource_type='user',
            resource_id=user_id,
            status='success',
            details={'fields': list(updates.keys())}
        )

        return jsonify({'message': 'Utilisateur mis à jour'}), 200

    except Exception as e:
        logger.error(f"Erreur de mise à jour utilisateur: {e}")
        return jsonify({'error': 'Erreur interne du serveur'}), 500


@admin_bp.route('/analytics', methods=['GET'])
@require_auth(roles=['admin'])
def get_analytics():
    """Récupère les analytics (admin uniquement)."""
    try:
        dm = current_app.data_manager
        days = request.args.get('days', 30, type=int)
        days = min(days, 365)

        summary = dm.get_analytics_summary(days=days)

        return jsonify({'analytics': summary}), 200

    except Exception as e:
        logger.error(f"Erreur de récupération analytics: {e}")
        return jsonify({'error': 'Erreur interne du serveur'}), 500


@admin_bp.route('/audit-logs', methods=['GET'])
@require_auth(roles=['admin'])
def get_audit_logs():
    """Récupère les logs d'audit (admin uniquement)."""
    try:
        user_id_filter = request.args.get('user_id')
        limit = request.args.get('limit', 100, type=int)
        limit = min(limit, 500)

        audit_logger = current_app.audit_logger

        if user_id_filter:
            logs = audit_logger.get_user_audit_trail(user_id_filter, limit=limit)
        else:
            # Récupérer les logs récents pour tous les utilisateurs
            dm = current_app.data_manager
            if hasattr(dm, 'db'):
                logs = list(dm.db.audit_logs.find(
                    {}, {'_id': 0}
                ).sort('timestamp', -1).limit(limit))
            elif hasattr(audit_logger, 'elastic_manager') and audit_logger.elastic_manager:
                result = audit_logger.elastic_manager.es.search(
                    index=f"{audit_logger.elastic_manager.index_prefix}_audit_logs",
                    body={
                        'query': {'match_all': {}},
                        'sort': [{'timestamp': {'order': 'desc'}}],
                        'size': limit
                    }
                )
                logs = [hit['_source'] for hit in result['hits']['hits']]
            else:
                logs = []

        return jsonify({'audit_logs': logs, 'count': len(logs)}), 200

    except Exception as e:
        logger.error(f"Erreur de récupération des logs d'audit: {e}")
        return jsonify({'error': 'Erreur interne du serveur'}), 500


@admin_bp.route('/conversations', methods=['GET'])
@require_auth(roles=['admin', 'medecin'])
def list_all_conversations():
    """Liste toutes les conversations (admin/médecin)."""
    try:
        dm = current_app.data_manager
        limit = request.args.get('limit', 50, type=int)
        offset = request.args.get('offset', 0, type=int)
        user_id_filter = request.args.get('user_id')

        limit = min(limit, 200)
        offset = max(offset, 0)

        if hasattr(dm, 'db'):
            # MongoDB
            query = {}
            if user_id_filter:
                query['userId'] = user_id_filter

            cursor = dm.db.conversations.find(
                query, {'messages': 0}
            ).sort('updated_at', -1).skip(offset).limit(limit)

            conversations = []
            for conv in cursor:
                conv.pop('_id', None)
                conversations.append(conv)
            total = dm.db.conversations.count_documents(query)
        else:
            # Elasticsearch
            body = {
                'sort': [{'updated_at': {'order': 'desc'}}],
                'size': limit,
                'from': offset,
                '_source': {'excludes': ['messages']}
            }
            if user_id_filter:
                body['query'] = {'term': {'userId': user_id_filter}}
            else:
                body['query'] = {'match_all': {}}

            result = dm.es.search(
                index=dm._index('conversations'),
                body=body
            )
            conversations = [hit['_source'] for hit in result['hits']['hits']]
            total = result['hits']['total']['value']

        return jsonify({
            'conversations': conversations,
            'total': total,
            'limit': limit,
            'offset': offset
        }), 200

    except Exception as e:
        logger.error(f"Erreur de listage des conversations: {e}")
        return jsonify({'error': 'Erreur interne du serveur'}), 500


@admin_bp.route('/conversations/<conversation_id>', methods=['GET'])
@require_auth(roles=['admin', 'medecin'])
def get_conversation_detail(conversation_id):
    """Récupère le détail d'une conversation (admin/médecin)."""
    try:
        dm = current_app.data_manager

        conversation = dm.get_conversation(conversation_id, decrypt=True)
        if not conversation:
            return jsonify({'error': 'Conversation non trouvée'}), 404

        conversation.pop('_id', None)

        # Formater les messages
        messages = []
        for msg in conversation.get('messages', []):
            messages.append({
                'messageId': msg.get('messageId'),
                'role': msg.get('role'),
                'content': msg.get('content_decrypted', ''),
                'metadata': msg.get('metadata', {}),
                'timestamp': msg.get('timestamp')
            })
        conversation['messages'] = messages

        current_app.audit_logger.log_action(
            user_id=request.current_user['user_id'],
            action='admin_read_conversation',
            resource_type='conversation',
            resource_id=conversation_id,
            status='success'
        )

        return jsonify({'conversation': conversation}), 200

    except Exception as e:
        logger.error(f"Erreur de récupération de conversation: {e}")
        return jsonify({'error': 'Erreur interne du serveur'}), 500


@admin_bp.route('/projects/<project_id>/requests', methods=['GET'])
@require_auth(roles=['admin'])
def list_access_requests(project_id):
    """Liste les demandes d'accès d'un projet (admin)."""
    try:
        dm = current_app.data_manager

        project = dm.get_project_by_id(project_id)
        if not project:
            return jsonify({'error': 'Projet non trouvé'}), 404

        status_filter = request.args.get('status')
        access_requests = project.get('access_requests', [])

        if status_filter:
            access_requests = [r for r in access_requests if r.get('status') == status_filter]

        return jsonify({
            'requests': access_requests,
            'total': len(access_requests)
        }), 200

    except Exception as e:
        logger.error(f"Erreur de listage des demandes d'accès: {e}")
        return jsonify({'error': 'Erreur interne du serveur'}), 500


@admin_bp.route('/projects/<project_id>/requests/<request_id>/approve', methods=['POST'])
@require_auth(roles=['admin'])
def approve_request(project_id, request_id):
    """Approuve une demande d'accès (admin)."""
    try:
        dm = current_app.data_manager
        admin_id = request.current_user['user_id']

        project = dm.get_project_by_id(project_id)
        if not project:
            return jsonify({'error': 'Projet non trouvé'}), 404

        # Vérifier que la demande existe
        request_found = False
        for req in project.get('access_requests', []):
            if req['requestId'] == request_id:
                request_found = True
                if req['status'] != 'pending':
                    return jsonify({'error': 'Cette demande a déjà été traitée'}), 409
                break

        if not request_found:
            return jsonify({'error': 'Demande non trouvée'}), 404

        success = dm.approve_access_request(project_id, request_id, admin_id)
        if not success:
            return jsonify({'error': 'Erreur lors de l\'approbation'}), 500

        return jsonify({'message': 'Demande approuvée'}), 200

    except Exception as e:
        logger.error(f"Erreur d'approbation de demande: {e}")
        return jsonify({'error': 'Erreur interne du serveur'}), 500


@admin_bp.route('/projects/<project_id>/requests/<request_id>/reject', methods=['POST'])
@require_auth(roles=['admin'])
def reject_request(project_id, request_id):
    """Rejette une demande d'accès (admin)."""
    try:
        dm = current_app.data_manager
        admin_id = request.current_user['user_id']
        data = request.get_json() or {}
        reason = data.get('reason', '')

        project = dm.get_project_by_id(project_id)
        if not project:
            return jsonify({'error': 'Projet non trouvé'}), 404

        # Mettre à jour le statut de la demande
        from datetime import datetime, timezone
        now = datetime.now(timezone.utc).isoformat()

        if hasattr(dm, 'db'):
            dm.db.projects.update_one(
                {
                    'projectId': project_id,
                    'access_requests.requestId': request_id
                },
                {
                    '$set': {
                        'access_requests.$.status': 'rejected',
                        'access_requests.$.reviewed_at': now,
                        'access_requests.$.reviewed_by': admin_id,
                        'access_requests.$.rejection_reason': reason
                    }
                }
            )
        else:
            dm.es.update(
                index=dm._index('projects'),
                id=project_id,
                body={
                    'script': {
                        'source': """
                            for (int i = 0; i < ctx._source.access_requests.size(); i++) {
                                if (ctx._source.access_requests[i].requestId == params.request_id) {
                                    ctx._source.access_requests[i].status = 'rejected';
                                    ctx._source.access_requests[i].reviewed_at = params.now;
                                    ctx._source.access_requests[i].reviewed_by = params.admin_id;
                                    ctx._source.access_requests[i].rejection_reason = params.reason;
                                }
                            }
                        """,
                        'params': {
                            'request_id': request_id,
                            'now': now,
                            'admin_id': admin_id,
                            'reason': reason
                        }
                    }
                },
                refresh='wait_for'
            )

        current_app.audit_logger.log_action(
            user_id=admin_id,
            action='reject_access',
            resource_type='project',
            resource_id=project_id,
            status='success',
            details={'request_id': request_id, 'reason': reason}
        )

        return jsonify({'message': 'Demande rejetée'}), 200

    except Exception as e:
        logger.error(f"Erreur de rejet de demande: {e}")
        return jsonify({'error': 'Erreur interne du serveur'}), 500

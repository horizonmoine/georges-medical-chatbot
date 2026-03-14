"""
Contrôleur d'export de données pour Georges Medical Chatbot.
Export RGPD (portabilité) et export recherche (pseudonymisé).
"""

import logging
import hashlib
from datetime import datetime, timezone
from flask import Blueprint, request, jsonify, current_app
from backend.core.security import require_auth

logger = logging.getLogger(__name__)

export_bp = Blueprint('export', __name__, url_prefix='/api/export')


@export_bp.route('/user-data', methods=['GET'])
@require_auth()
def export_user_data():
    """
    Export des données utilisateur (portabilité RGPD - Article 20).
    Retourne toutes les données personnelles de l'utilisateur dans un format structuré.
    """
    try:
        user_id = request.current_user['user_id']
        dm = current_app.data_manager

        # Profil utilisateur
        user = dm.get_user_by_id(user_id)
        if not user:
            return jsonify({'error': 'Utilisateur non trouvé'}), 404

        from backend.models.user import sanitize_user_response
        user_profile = sanitize_user_response(user, include_sensitive=True)

        # Conversations avec messages déchiffrés
        conversations_list, total = dm.get_user_conversations(user_id, limit=10000)
        full_conversations = []
        for conv_summary in conversations_list:
            conv = dm.get_conversation(conv_summary['conversationId'], decrypt=True)
            if conv:
                clean_conv = {
                    'conversationId': conv.get('conversationId'),
                    'projectId': conv.get('projectId'),
                    'created_at': conv.get('created_at'),
                    'updated_at': conv.get('updated_at'),
                    'messages': []
                }
                for msg in conv.get('messages', []):
                    clean_conv['messages'].append({
                        'role': msg.get('role'),
                        'content': msg.get('content_decrypted', ''),
                        'timestamp': msg.get('timestamp')
                    })
                full_conversations.append(clean_conv)

        # Consentements
        if hasattr(dm, 'db'):
            consents = list(dm.db.consents.find({'userId': user_id}, {'_id': 0}))
        else:
            result = dm.es.search(
                index=dm._index('consents'),
                body={
                    'query': {'term': {'userId': user_id}},
                    'size': 1000
                }
            )
            consents = [hit['_source'] for hit in result['hits']['hits']]

        export = {
            'export_metadata': {
                'export_date': datetime.now(timezone.utc).isoformat(),
                'format_version': '1.0',
                'regulation': 'RGPD Article 20 - Droit à la portabilité'
            },
            'user_profile': user_profile,
            'conversations': full_conversations,
            'consents': consents,
            'total_conversations': len(full_conversations)
        }

        current_app.audit_logger.log_action(
            user_id=user_id,
            action='rgpd_export',
            resource_type='user',
            resource_id=user_id,
            status='success'
        )

        return jsonify(export), 200

    except Exception as e:
        logger.error(f"Erreur d'export des données utilisateur: {e}")
        return jsonify({'error': 'Erreur interne du serveur'}), 500


@export_bp.route('/research-data', methods=['POST'])
@require_auth(roles=['admin', 'investigateur'])
def export_research_data():
    """
    Export pseudonymisé des données pour la recherche.
    Les données personnelles sont remplacées par des identifiants pseudonymisés.
    Accessible aux administrateurs et investigateurs.
    """
    try:
        user_id = request.current_user['user_id']
        data = request.get_json() or {}

        project_id = data.get('project_id')
        date_from = data.get('date_from')
        date_to = data.get('date_to')

        dm = current_app.data_manager

        # Construire le filtre de requête
        if hasattr(dm, 'db'):
            query = {}
            if project_id:
                query['projectId'] = project_id
            if date_from or date_to:
                query['created_at'] = {}
                if date_from:
                    query['created_at']['$gte'] = date_from
                if date_to:
                    query['created_at']['$lte'] = date_to

            conversations_cursor = dm.db.conversations.find(query).limit(5000)
            conversations_raw = list(conversations_cursor)
        else:
            must = []
            if project_id:
                must.append({'term': {'projectId': project_id}})
            if date_from or date_to:
                range_query = {}
                if date_from:
                    range_query['gte'] = date_from
                if date_to:
                    range_query['lte'] = date_to
                must.append({'range': {'created_at': range_query}})

            body = {
                'query': {'bool': {'must': must}} if must else {'match_all': {}},
                'size': 5000
            }
            result = dm.es.search(
                index=dm._index('conversations'),
                body=body
            )
            conversations_raw = [hit['_source'] for hit in result['hits']['hits']]

        # Pseudonymiser les données
        pseudonymized_conversations = []
        pseudonym_map = {}

        for conv in conversations_raw:
            original_user_id = conv.get('userId', '')

            # Créer un pseudonyme stable (même utilisateur = même pseudo)
            if original_user_id not in pseudonym_map:
                pseudo_hash = hashlib.sha256(
                    f"research_pseudo_{original_user_id}".encode()
                ).hexdigest()[:12]
                pseudonym_map[original_user_id] = f"PARTICIPANT_{pseudo_hash}"

            pseudo_conv = {
                'participant_id': pseudonym_map[original_user_id],
                'conversation_id': conv.get('conversationId'),
                'project_id': conv.get('projectId'),
                'created_at': conv.get('created_at'),
                'message_count': len(conv.get('messages', [])),
                'messages': []
            }

            # Déchiffrer et pseudonymiser les messages
            for msg in conv.get('messages', []):
                try:
                    content = dm.security.decrypt_data(msg.get('content', ''))
                except Exception:
                    content = '[Contenu indisponible]'

                pseudo_conv['messages'].append({
                    'role': msg.get('role'),
                    'content': content,
                    'metadata': msg.get('metadata', {}),
                    'timestamp': msg.get('timestamp')
                })

            pseudonymized_conversations.append(pseudo_conv)

        export = {
            'export_metadata': {
                'export_date': datetime.now(timezone.utc).isoformat(),
                'exported_by': user_id,
                'format_version': '1.0',
                'pseudonymized': True,
                'project_id': project_id,
                'date_range': {'from': date_from, 'to': date_to}
            },
            'total_participants': len(pseudonym_map),
            'total_conversations': len(pseudonymized_conversations),
            'conversations': pseudonymized_conversations
        }

        current_app.audit_logger.log_action(
            user_id=user_id,
            action='research_export',
            resource_type='project',
            resource_id=project_id,
            status='success',
            details={
                'total_conversations': len(pseudonymized_conversations),
                'total_participants': len(pseudonym_map)
            }
        )

        return jsonify(export), 200

    except Exception as e:
        logger.error(f"Erreur d'export recherche: {e}")
        return jsonify({'error': 'Erreur interne du serveur'}), 500

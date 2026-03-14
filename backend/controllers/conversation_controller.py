"""
Contrôleur de conversations pour Georges Medical Chatbot.
CRUD des conversations.
"""

import logging
from flask import Blueprint, request, jsonify, current_app
from backend.core.security import require_auth
from backend.middleware.session_manager import require_active_session

logger = logging.getLogger(__name__)

conversation_bp = Blueprint('conversation', __name__, url_prefix='/api')


@conversation_bp.route('/conversations', methods=['GET'])
@require_auth()
@require_active_session
def list_conversations():
    """Liste les conversations de l'utilisateur connecté."""
    try:
        user_id = request.current_user['user_id']
        dm = current_app.data_manager

        limit = request.args.get('limit', 50, type=int)
        offset = request.args.get('offset', 0, type=int)

        # Limiter les valeurs
        limit = min(limit, 100)
        offset = max(offset, 0)

        conversations, total = dm.get_user_conversations(
            user_id, limit=limit, offset=offset
        )

        # Nettoyer les _id MongoDB
        for conv in conversations:
            conv.pop('_id', None)

        return jsonify({
            'conversations': conversations,
            'total': total,
            'limit': limit,
            'offset': offset
        }), 200

    except Exception as e:
        logger.error(f"Erreur de listage des conversations: {e}")
        return jsonify({'error': 'Erreur interne du serveur'}), 500


@conversation_bp.route('/conversations', methods=['POST'])
@require_auth()
@require_active_session
def create_conversation():
    """Crée une nouvelle conversation."""
    try:
        user_id = request.current_user['user_id']
        dm = current_app.data_manager

        data = request.get_json() or {}
        project_id = data.get('project_id')

        conversation = dm.create_conversation(user_id, project_id=project_id)
        conversation.pop('_id', None)

        return jsonify({
            'message': 'Conversation créée',
            'conversation': conversation
        }), 201

    except Exception as e:
        logger.error(f"Erreur de création de conversation: {e}")
        return jsonify({'error': 'Erreur interne du serveur'}), 500


@conversation_bp.route('/conversations/<conversation_id>', methods=['GET'])
@require_auth()
@require_active_session
def get_conversation(conversation_id):
    """Récupère une conversation avec tous ses messages déchiffrés."""
    try:
        user_id = request.current_user['user_id']
        dm = current_app.data_manager

        conversation = dm.get_conversation(conversation_id, decrypt=True)
        if not conversation:
            return jsonify({'error': 'Conversation non trouvée'}), 404

        # Vérifier que la conversation appartient à l'utilisateur
        if conversation.get('userId') != user_id:
            return jsonify({'error': 'Accès non autorisé'}), 403

        conversation.pop('_id', None)

        # Formater les messages pour la réponse
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
            user_id=user_id,
            action='read',
            resource_type='conversation',
            resource_id=conversation_id,
            status='success'
        )

        return jsonify({'conversation': conversation}), 200

    except Exception as e:
        logger.error(f"Erreur de récupération de conversation: {e}")
        return jsonify({'error': 'Erreur interne du serveur'}), 500


@conversation_bp.route('/conversations/<conversation_id>', methods=['DELETE'])
@require_auth()
@require_active_session
def delete_conversation(conversation_id):
    """Supprime une conversation."""
    try:
        user_id = request.current_user['user_id']
        dm = current_app.data_manager

        success = dm.delete_conversation(conversation_id, user_id)
        if not success:
            return jsonify({'error': 'Conversation non trouvée ou accès non autorisé'}), 404

        return jsonify({'message': 'Conversation supprimée'}), 200

    except Exception as e:
        logger.error(f"Erreur de suppression de conversation: {e}")
        return jsonify({'error': 'Erreur interne du serveur'}), 500

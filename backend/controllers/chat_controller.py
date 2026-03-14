"""
Contrôleur de chat pour Georges Medical Chatbot.
Envoi de messages et génération de résumés patients.
"""

import logging
from flask import Blueprint, request, jsonify, current_app
from backend.core.security import require_auth
from backend.middleware.session_manager import require_active_session

logger = logging.getLogger(__name__)

chat_bp = Blueprint('chat', __name__, url_prefix='/api')


@chat_bp.route('/chat', methods=['POST'])
@require_auth()
@require_active_session
def send_message():
    """
    Envoie un message et reçoit une réponse du LLM.
    Chiffre et stocke les messages dans la conversation.
    """
    try:
        user_id = request.current_user['user_id']
        data = request.get_json()
        if not data:
            return jsonify({'error': 'Données requises'}), 400

        message = data.get('message', '').strip()
        conversation_id = data.get('conversation_id')
        project_id = data.get('project_id')
        model_name = data.get('model_name')

        if not message:
            return jsonify({'error': 'Le message ne peut pas être vide'}), 400

        security = current_app.security_manager
        dm = current_app.data_manager
        llm_client = current_app.llm_client

        # Nettoyer l'entrée utilisateur
        message = security.sanitize_input(message)

        # Créer la conversation si elle n'existe pas
        if not conversation_id:
            conversation = dm.create_conversation(user_id, project_id=project_id)
            conversation_id = conversation['conversationId']
        else:
            # Vérifier que la conversation appartient à l'utilisateur
            conversation = dm.get_conversation(conversation_id, decrypt=False)
            if not conversation or conversation.get('userId') != user_id:
                return jsonify({'error': 'Conversation non trouvée'}), 404

        # Sauvegarder le message utilisateur
        user_msg = dm.add_message_to_conversation(
            conversation_id, 'user', message
        )

        # Récupérer l'historique pour le contexte
        full_conv = dm.get_conversation(conversation_id, decrypt=True)
        conversation_history = []
        if full_conv:
            for msg in full_conv.get('messages', []):
                conversation_history.append({
                    'role': msg.get('role'),
                    'content': msg.get('content_decrypted', '')
                })

        # Générer la réponse du LLM
        llm_response = llm_client.generate_response(
            message=message,
            conversation_history=conversation_history,
            model_name=model_name,
            project_id=project_id
        )

        # Extraire les entités médicales (en arrière-plan conceptuellement)
        metadata = {}
        try:
            entities = llm_client.extract_medical_entities(message)
            if entities and not entities.get('error'):
                metadata['medical_entities'] = entities.get('entities', {})
        except Exception as e:
            logger.warning(f"Extraction d'entités échouée: {e}")

        # Sauvegarder la réponse du LLM
        assistant_msg = dm.add_message_to_conversation(
            conversation_id, 'assistant', llm_response, metadata=metadata
        )

        # Enregistrer l'événement analytics
        dm.record_analytics_event(
            'chat_message',
            user_id=user_id,
            data={
                'conversation_id': conversation_id,
                'project_id': project_id
            }
        )

        return jsonify({
            'conversation_id': conversation_id,
            'response': llm_response,
            'message_id': assistant_msg.get('messageId'),
            'metadata': metadata
        }), 200

    except Exception as e:
        logger.error(f"Erreur de chat: {e}")
        return jsonify({'error': 'Erreur interne du serveur'}), 500


@chat_bp.route('/chat/summary', methods=['POST'])
@require_auth()
@require_active_session
def generate_summary():
    """
    Génère un résumé patient à partir d'une conversation.
    Utile pour les médecins qui veulent un aperçu rapide.
    """
    try:
        user_id = request.current_user['user_id']
        data = request.get_json()
        if not data:
            return jsonify({'error': 'Données requises'}), 400

        conversation_id = data.get('conversation_id')
        if not conversation_id:
            return jsonify({'error': 'conversation_id requis'}), 400

        dm = current_app.data_manager
        llm_client = current_app.llm_client

        # Récupérer la conversation
        conversation = dm.get_conversation(conversation_id, decrypt=True)
        if not conversation:
            return jsonify({'error': 'Conversation non trouvée'}), 404

        # Vérifier l'accès (propriétaire ou médecin/admin)
        role = request.current_user.get('role')
        if conversation.get('userId') != user_id and role not in ('medecin', 'admin'):
            return jsonify({'error': 'Accès non autorisé'}), 403

        # Préparer les messages pour le résumé
        messages = []
        for msg in conversation.get('messages', []):
            messages.append({
                'role': msg.get('role'),
                'content': msg.get('content_decrypted', '')
            })

        if not messages:
            return jsonify({'error': 'Conversation vide, impossible de générer un résumé'}), 400

        # Générer le résumé
        summary = llm_client.generate_summary(messages)

        if not summary:
            return jsonify({'error': 'Impossible de générer le résumé'}), 500

        current_app.audit_logger.log_action(
            user_id=user_id,
            action='generate_summary',
            resource_type='conversation',
            resource_id=conversation_id,
            status='success'
        )

        return jsonify({
            'conversation_id': conversation_id,
            'summary': summary,
            'message_count': len(messages)
        }), 200

    except Exception as e:
        logger.error(f"Erreur de génération du résumé: {e}")
        return jsonify({'error': 'Erreur interne du serveur'}), 500

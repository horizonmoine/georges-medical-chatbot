"""
Modèle de conversation pour Georges Medical Chatbot.
"""

from datetime import datetime, timezone
from uuid import uuid4


def create_conversation_doc(user_id, project_id=None):
    """
    Crée un document de conversation.

    Args:
        user_id: Identifiant de l'utilisateur
        project_id: Identifiant du projet (optionnel)

    Returns:
        dict: Document de conversation prêt pour insertion
    """
    now = datetime.now(timezone.utc).isoformat()
    return {
        'conversationId': str(uuid4()),
        'userId': user_id,
        'projectId': project_id,
        'messages': [],
        'status': 'active',
        'created_at': now,
        'updated_at': now
    }


def create_message_doc(role, content_encrypted, metadata=None):
    """
    Crée un document de message pour une conversation.

    Args:
        role: Rôle de l'émetteur (user, assistant, system)
        content_encrypted: Contenu du message chiffré
        metadata: Métadonnées supplémentaires (scores, entités, etc.)

    Returns:
        dict: Document de message
    """
    return {
        'messageId': str(uuid4()),
        'role': role,
        'content': content_encrypted,
        'metadata': metadata or {},
        'timestamp': datetime.now(timezone.utc).isoformat()
    }

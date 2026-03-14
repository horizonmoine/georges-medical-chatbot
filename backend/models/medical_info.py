"""
Modèle d'informations médicales pour Georges Medical Chatbot.
"""

from datetime import datetime, timezone
from uuid import uuid4


def create_medical_info_doc(user_id, conversation_id):
    """
    Crée un document d'informations médicales extrait d'une conversation.

    Args:
        user_id: Identifiant de l'utilisateur
        conversation_id: Identifiant de la conversation source

    Returns:
        dict: Document d'informations médicales
    """
    now = datetime.now(timezone.utc).isoformat()
    return {
        'medicalInfoId': str(uuid4()),
        'userId': user_id,
        'conversationId': conversation_id,
        'symptoms': [],
        'medical_history': [],
        'current_treatments': [],
        'allergies': [],
        'clinical_scores': {},
        'vital_signs': {},
        'created_at': now,
        'updated_at': now
    }

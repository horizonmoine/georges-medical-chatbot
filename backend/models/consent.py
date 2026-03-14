"""
Modèle de consentement pour Georges Medical Chatbot.
Conformité RGPD et consentement éclairé pour la recherche médicale.
"""

from datetime import datetime, timezone
from uuid import uuid4


def create_consent_doc(user_id, project_id, consent_type, granted, ip_address):
    """
    Crée un document de consentement.

    Args:
        user_id: Identifiant de l'utilisateur
        project_id: Identifiant du projet (peut être None pour consentements généraux)
        consent_type: Type de consentement (data_processing, research, cookies, etc.)
        granted: True si le consentement est accordé
        ip_address: Adresse IP du client au moment du consentement

    Returns:
        dict: Document de consentement prêt pour insertion
    """
    return {
        'consentId': str(uuid4()),
        'userId': user_id,
        'projectId': project_id,
        'consent_type': consent_type,
        'granted': granted,
        'ip_address': ip_address,
        'timestamp': datetime.now(timezone.utc).isoformat(),
        'revoked': False,
        'revoked_at': None
    }

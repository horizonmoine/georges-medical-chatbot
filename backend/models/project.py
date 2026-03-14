"""
Modèle de projet de recherche pour Georges Medical Chatbot.
"""

from datetime import datetime, timezone
from uuid import uuid4


def create_project_doc(name, description, slug, created_by,
                       model_config=None, inclusion_criteria=None):
    """
    Crée un document de projet de recherche.

    Args:
        name: Nom du projet
        description: Description du projet
        slug: Identifiant URL-friendly unique
        created_by: userId du créateur
        model_config: Configuration du modèle LLM pour ce projet
        inclusion_criteria: Critères d'inclusion pour les participants

    Returns:
        dict: Document de projet prêt pour insertion
    """
    now = datetime.now(timezone.utc).isoformat()
    return {
        'projectId': str(uuid4()),
        'name': name,
        'description': description,
        'slug': slug,
        'created_by': created_by,
        'model_config': model_config or {},
        'inclusion_criteria': inclusion_criteria or [],
        'participants': [],
        'access_requests': [],
        'consent_form_text': '',
        'status': 'active',
        'created_at': now,
        'updated_at': now
    }

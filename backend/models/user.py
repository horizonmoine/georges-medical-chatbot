"""
Modèle utilisateur pour Georges Medical Chatbot.
"""

from datetime import datetime, timezone
from uuid import uuid4


def create_user_doc(email, password_hash, nom_encrypted, prenom_encrypted,
                    date_naissance_encrypted, role='patient',
                    confirmation_token=None):
    """
    Crée un document utilisateur.

    Args:
        email: Adresse email (en clair, indexée)
        password_hash: Hash bcrypt du mot de passe
        nom_encrypted: Nom chiffré
        prenom_encrypted: Prénom chiffré
        date_naissance_encrypted: Date de naissance chiffrée
        role: Rôle de l'utilisateur (patient, medecin, admin, investigateur)
        confirmation_token: Token de confirmation d'email

    Returns:
        dict: Document utilisateur prêt pour insertion
    """
    now = datetime.now(timezone.utc).isoformat()
    return {
        'userId': str(uuid4()),
        'email': email,
        'password_hash': password_hash,
        'nom': nom_encrypted,
        'prenom': prenom_encrypted,
        'date_naissance': date_naissance_encrypted,
        'role': role,
        'is_active': True,
        'is_confirmed': False,
        'confirmation_token': confirmation_token,
        'consents': [],
        'created_at': now,
        'updated_at': now
    }


def sanitize_user_response(user_data, include_sensitive=False):
    """
    Nettoie un document utilisateur pour la réponse API.
    Supprime les champs sensibles.

    Args:
        user_data: Document utilisateur brut
        include_sensitive: Si True, inclut les champs chiffrés déchiffrés

    Returns:
        dict: Document utilisateur nettoyé
    """
    if not user_data:
        return None

    # Champs à toujours exclure
    excluded_fields = [
        'password_hash', '_id', 'confirmation_token'
    ]

    # Champs chiffrés à exclure si include_sensitive est False
    encrypted_fields = ['nom', 'prenom', 'date_naissance']

    sanitized = {}
    for key, value in user_data.items():
        if key in excluded_fields:
            continue
        if key in encrypted_fields and not include_sensitive:
            continue
        sanitized[key] = value

    return sanitized

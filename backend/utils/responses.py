"""
Fonctions utilitaires pour les réponses API standardisées.
"""

from flask import jsonify


def success_response(data, status=200):
    """
    Crée une réponse de succès standardisée.

    Args:
        data: Données à inclure dans la réponse
        status: Code de statut HTTP (défaut: 200)

    Returns:
        tuple: (response, status_code)
    """
    response = {
        'success': True,
        'data': data
    }
    return jsonify(response), status


def error_response(message, status=400):
    """
    Crée une réponse d'erreur standardisée.

    Args:
        message: Message d'erreur
        status: Code de statut HTTP (défaut: 400)

    Returns:
        tuple: (response, status_code)
    """
    response = {
        'success': False,
        'error': message
    }
    return jsonify(response), status

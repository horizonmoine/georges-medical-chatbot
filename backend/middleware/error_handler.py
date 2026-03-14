"""
Gestionnaire d'erreurs centralisé pour Georges Medical Chatbot.
"""

import logging
import traceback
from flask import jsonify
from werkzeug.exceptions import HTTPException

logger = logging.getLogger(__name__)


class APIError(Exception):
    """Erreur API personnalisée avec code de statut et détails."""

    def __init__(self, message, status_code=400, details=None):
        super().__init__(message)
        self.message = message
        self.status_code = status_code
        self.details = details


def register_error_handlers(app):
    """Enregistre les gestionnaires d'erreurs sur l'application Flask."""

    @app.errorhandler(APIError)
    def handle_api_error(error):
        response = {
            'error': error.message,
            'status_code': error.status_code
        }
        if error.details:
            response['details'] = error.details
        logger.warning(f"APIError: {error.message} ({error.status_code})")
        return jsonify(response), error.status_code

    @app.errorhandler(HTTPException)
    def handle_http_exception(error):
        response = {
            'error': error.description or error.name,
            'status_code': error.code
        }
        logger.warning(f"HTTPException: {error.description} ({error.code})")
        return jsonify(response), error.code

    @app.errorhandler(Exception)
    def handle_generic_exception(error):
        logger.error(f"Erreur non gérée: {str(error)}")
        logger.error(traceback.format_exc())
        response = {
            'error': 'Erreur interne du serveur',
            'status_code': 500
        }
        return jsonify(response), 500

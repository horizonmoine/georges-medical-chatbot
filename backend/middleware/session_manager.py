"""
Gestionnaire de sessions pour Georges Medical Chatbot.
Gestion des sessions actives avec expiration et nettoyage automatique.
"""

import logging
from datetime import datetime, timezone, timedelta
from functools import wraps
from flask import request, jsonify, current_app

logger = logging.getLogger(__name__)


class SessionManager:
    """Gestionnaire de sessions en mémoire avec expiration."""

    def __init__(self, session_timeout_minutes=30):
        self.active_sessions = {}
        self.session_timeout = timedelta(minutes=session_timeout_minutes)

    def create_session(self, user_id, token, user_data=None):
        """
        Crée une nouvelle session pour un utilisateur.

        Args:
            user_id: Identifiant de l'utilisateur
            token: Token JWT associé à la session
            user_data: Données utilisateur supplémentaires
        """
        now = datetime.now(timezone.utc)
        self.active_sessions[token] = {
            'user_id': user_id,
            'created_at': now,
            'last_activity': now,
            'expires_at': now + self.session_timeout,
            'user_data': user_data or {}
        }
        logger.info(f"Session créée pour l'utilisateur {user_id}")

    def validate_session(self, token):
        """
        Valide une session active.

        Args:
            token: Token JWT de la session

        Returns:
            tuple: (is_valid, session_data ou None)
        """
        session = self.active_sessions.get(token)
        if not session:
            return False, None

        now = datetime.now(timezone.utc)
        if now > session['expires_at']:
            del self.active_sessions[token]
            logger.info(f"Session expirée pour l'utilisateur {session['user_id']}")
            return False, None

        return True, session

    def refresh_session(self, token):
        """
        Rafraîchit le timestamp d'activité d'une session.

        Args:
            token: Token JWT de la session

        Returns:
            bool: True si la session a été rafraîchie
        """
        session = self.active_sessions.get(token)
        if not session:
            return False

        now = datetime.now(timezone.utc)
        if now > session['expires_at']:
            del self.active_sessions[token]
            return False

        session['last_activity'] = now
        session['expires_at'] = now + self.session_timeout
        return True

    def terminate_session(self, token):
        """
        Termine une session active.

        Args:
            token: Token JWT de la session

        Returns:
            bool: True si la session existait et a été terminée
        """
        if token in self.active_sessions:
            user_id = self.active_sessions[token].get('user_id', 'unknown')
            del self.active_sessions[token]
            logger.info(f"Session terminée pour l'utilisateur {user_id}")
            return True
        return False

    def cleanup_expired_sessions(self):
        """Nettoie toutes les sessions expirées."""
        now = datetime.now(timezone.utc)
        expired_tokens = [
            token for token, session in self.active_sessions.items()
            if now > session['expires_at']
        ]
        for token in expired_tokens:
            user_id = self.active_sessions[token].get('user_id', 'unknown')
            del self.active_sessions[token]
            logger.debug(f"Session expirée nettoyée pour l'utilisateur {user_id}")

        if expired_tokens:
            logger.info(f"{len(expired_tokens)} session(s) expirée(s) nettoyée(s)")


def require_active_session(f):
    """
    Décorateur qui vérifie qu'une session active existe pour le token courant.
    Doit être utilisé après @require_auth().
    """
    @wraps(f)
    def decorated_function(*args, **kwargs):
        auth_header = request.headers.get('Authorization', '')
        if not auth_header.startswith('Bearer '):
            return jsonify({'error': 'Token requis'}), 401

        token = auth_header.split('Bearer ')[1].strip()
        session_manager = current_app.session_manager

        is_valid, session_data = session_manager.validate_session(token)
        if not is_valid:
            return jsonify({'error': 'Session expirée ou invalide'}), 401

        # Rafraîchir la session
        session_manager.refresh_session(token)

        return f(*args, **kwargs)
    return decorated_function

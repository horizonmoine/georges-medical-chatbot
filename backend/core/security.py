"""
Module de sécurité pour Georges Medical Chatbot.
Gestion du chiffrement, authentification JWT, validation des entrées.
"""

import os
import re
import jwt
import bcrypt
import secrets
import html
import base64
import logging
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
from cryptography.hazmat.primitives import padding
from cryptography.hazmat.backends import default_backend
from flask import request, jsonify, current_app
from functools import wraps
from datetime import datetime, timezone, timedelta

logger = logging.getLogger(__name__)


class SecurityManager:
    """Gestionnaire centralisé de sécurité pour l'application."""

    def __init__(self, encryption_key):
        if isinstance(encryption_key, str):
            encryption_key = encryption_key.encode('utf-8')
        self.encryption_key = encryption_key[:32].ljust(32, b'\0')
        self.jwt_secret = os.environ.get('JWT_SECRET_KEY', 'dev-jwt-secret-change-in-production')
        self.jwt_algorithm = 'HS256'

    def encrypt_data(self, data: str) -> str:
        """Chiffre une chaîne avec AES-256-CBC, IV aléatoire, padding PKCS7."""
        if not data:
            return ''
        try:
            iv = os.urandom(16)
            padder = padding.PKCS7(128).padder()
            padded_data = padder.update(data.encode('utf-8')) + padder.finalize()
            cipher = Cipher(
                algorithms.AES(self.encryption_key),
                modes.CBC(iv),
                backend=default_backend()
            )
            encryptor = cipher.encryptor()
            encrypted = encryptor.update(padded_data) + encryptor.finalize()
            result = base64.b64encode(iv + encrypted).decode('utf-8')
            return result
        except Exception as e:
            logger.error(f"Erreur de chiffrement: {e}")
            raise

    def decrypt_data(self, encrypted_data: str) -> str:
        """Déchiffre une chaîne chiffrée avec AES-256-CBC."""
        if not encrypted_data:
            return ''
        try:
            raw = base64.b64decode(encrypted_data)
            iv = raw[:16]
            ciphertext = raw[16:]
            cipher = Cipher(
                algorithms.AES(self.encryption_key),
                modes.CBC(iv),
                backend=default_backend()
            )
            decryptor = cipher.decryptor()
            padded_data = decryptor.update(ciphertext) + decryptor.finalize()
            unpadder = padding.PKCS7(128).unpadder()
            data = unpadder.update(padded_data) + unpadder.finalize()
            return data.decode('utf-8')
        except Exception as e:
            logger.error(f"Erreur de déchiffrement: {e}")
            raise

    def hash_password(self, password: str) -> str:
        """Hache un mot de passe avec bcrypt."""
        salt = bcrypt.gensalt(rounds=12)
        hashed = bcrypt.hashpw(password.encode('utf-8'), salt)
        return hashed.decode('utf-8')

    def verify_password(self, password: str, hashed: str) -> bool:
        """Vérifie un mot de passe contre son hash bcrypt."""
        try:
            return bcrypt.checkpw(
                password.encode('utf-8'),
                hashed.encode('utf-8')
            )
        except Exception as e:
            logger.error(f"Erreur de vérification du mot de passe: {e}")
            return False

    @staticmethod
    def generate_secure_token(length=32) -> str:
        """Génère un token sécurisé URL-safe."""
        return secrets.token_urlsafe(length)

    def create_access_token(self, user_id, role) -> str:
        """Crée un token JWT d'accès (expiration: 5 minutes)."""
        payload = {
            'user_id': user_id,
            'role': role,
            'type': 'access',
            'exp': datetime.now(timezone.utc) + timedelta(minutes=5),
            'iat': datetime.now(timezone.utc)
        }
        return jwt.encode(payload, self.jwt_secret, algorithm=self.jwt_algorithm)

    def create_refresh_token(self, user_id) -> str:
        """Crée un token JWT de rafraîchissement (expiration: 7 jours)."""
        payload = {
            'user_id': user_id,
            'type': 'refresh',
            'exp': datetime.now(timezone.utc) + timedelta(days=7),
            'iat': datetime.now(timezone.utc)
        }
        return jwt.encode(payload, self.jwt_secret, algorithm=self.jwt_algorithm)

    def verify_token(self, token) -> tuple:
        """Vérifie et décode un token JWT. Retourne (is_valid, payload)."""
        try:
            payload = jwt.decode(
                token,
                self.jwt_secret,
                algorithms=[self.jwt_algorithm]
            )
            return True, payload
        except jwt.ExpiredSignatureError:
            return False, {'error': 'Token expiré'}
        except jwt.InvalidTokenError as e:
            return False, {'error': f'Token invalide: {str(e)}'}

    def validate_email(self, email) -> bool:
        """Valide le format d'une adresse email."""
        pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        return bool(re.match(pattern, email))

    def validate_password_strength(self, password) -> tuple:
        """
        Valide la robustesse d'un mot de passe.
        Retourne (is_valid, message).
        """
        if len(password) < 8:
            return False, "Le mot de passe doit contenir au moins 8 caractères"
        if not re.search(r'[A-Z]', password):
            return False, "Le mot de passe doit contenir au moins une majuscule"
        if not re.search(r'[a-z]', password):
            return False, "Le mot de passe doit contenir au moins une minuscule"
        if not re.search(r'[0-9]', password):
            return False, "Le mot de passe doit contenir au moins un chiffre"
        if not re.search(r'[!@#$%^&*(),.?\":{}|<>]', password):
            return False, "Le mot de passe doit contenir au moins un caractère spécial"
        return True, "Mot de passe valide"

    def sanitize_input(self, text, max_length=2000) -> str:
        """Nettoie une entrée utilisateur: supprime les tags HTML et tronque."""
        if not text:
            return ''
        # Suppression des tags HTML
        clean = re.sub(r'<[^>]+>', '', str(text))
        # Échappement des entités HTML restantes
        clean = html.escape(clean)
        # Troncature
        if len(clean) > max_length:
            clean = clean[:max_length]
        return clean.strip()


def require_auth(roles=None):
    """
    Décorateur d'authentification.
    Vérifie le token Bearer JWT et optionnellement les rôles autorisés.
    Définit request.current_user = {'user_id': ..., 'role': ...}.
    """
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            auth_header = request.headers.get('Authorization', '')
            if not auth_header.startswith('Bearer '):
                return jsonify({'error': 'Token d\'authentification requis'}), 401

            token = auth_header.split('Bearer ')[1].strip()
            security_manager = current_app.security_manager

            is_valid, payload = security_manager.verify_token(token)
            if not is_valid:
                return jsonify({'error': payload.get('error', 'Token invalide')}), 401

            if payload.get('type') != 'access':
                return jsonify({'error': 'Type de token invalide'}), 401

            if roles and payload.get('role') not in roles:
                return jsonify({'error': 'Accès non autorisé pour ce rôle'}), 403

            request.current_user = {
                'user_id': payload.get('user_id'),
                'role': payload.get('role')
            }

            return f(*args, **kwargs)
        return decorated_function
    return decorator

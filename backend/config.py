"""
Configuration multi-environnement pour Georges Medical Chatbot.
"""

import os
import logging
from datetime import timedelta

logger = logging.getLogger(__name__)


class BaseConfig:
    """Configuration de base partagée par tous les environnements."""

    APP_NAME = "Georges Medical Chatbot"
    VERSION = "1.0.0"

    # Sécurité
    SECRET_KEY = os.environ.get('SECRET_KEY', 'dev-secret-key-change-in-production')
    JWT_SECRET_KEY = os.environ.get('JWT_SECRET_KEY', 'dev-jwt-secret-change-in-production')
    JWT_ACCESS_TOKEN_EXPIRES = timedelta(minutes=5)
    JWT_REFRESH_TOKEN_EXPIRES = timedelta(days=7)

    # CORS
    CORS_ORIGINS = os.environ.get('CORS_ORIGINS', 'http://localhost:3000,http://localhost:5173').split(',')

    # MongoDB
    MONGO_URI = os.environ.get('MONGO_URI', 'mongodb://localhost:27017')
    MONGO_DB_NAME = os.environ.get('MONGO_DB_NAME', 'georges_medical')

    # Elasticsearch
    ELASTIC_HOST = os.environ.get('ELASTIC_HOST', 'http://localhost:9200')
    ELASTIC_INDEX_PREFIX = os.environ.get('ELASTIC_INDEX_PREFIX', 'georges')

    # Chiffrement
    ENCRYPTION_KEY = os.environ.get('ENCRYPTION_KEY', 'dev-encryption-key-32-chars-long!')

    # LLM / Gemini
    GEMINI_API_KEY = os.environ.get('GEMINI_API_KEY', '')
    LLM_SERVICE_URL = os.environ.get('LLM_SERVICE_URL', 'http://localhost:8000')

    # Email (Mailgun)
    MAILGUN_API_KEY = os.environ.get('MAILGUN_API_KEY', '')
    MAILGUN_DOMAIN = os.environ.get('MAILGUN_DOMAIN', '')

    # Rate Limiting
    RATELIMIT_DEFAULT = os.environ.get('RATELIMIT_DEFAULT', '100 per hour')
    RATELIMIT_STORAGE_URL = os.environ.get('RATELIMIT_STORAGE_URL', 'memory://')

    # LDAP (optionnel)
    LDAP_SERVER = os.environ.get('LDAP_SERVER', '')
    LDAP_BASE_DN = os.environ.get('LDAP_BASE_DN', '')
    LDAP_BIND_DN = os.environ.get('LDAP_BIND_DN', '')

    # Frontend
    FRONTEND_URL = os.environ.get('FRONTEND_URL', 'http://localhost:3000')

    # Base de données backend
    DB_BACKEND = os.environ.get('DB_BACKEND', 'elasticsearch')

    @classmethod
    def validate(cls):
        """Valide la configuration et retourne les avertissements."""
        warnings = []
        errors = []

        if cls.SECRET_KEY == 'dev-secret-key-change-in-production':
            warnings.append("SECRET_KEY utilise la valeur par défaut de développement")

        if cls.JWT_SECRET_KEY == 'dev-jwt-secret-change-in-production':
            warnings.append("JWT_SECRET_KEY utilise la valeur par défaut de développement")

        if cls.DB_BACKEND not in ('mongodb', 'elasticsearch'):
            errors.append(f"DB_BACKEND invalide: {cls.DB_BACKEND}. Doit être 'mongodb' ou 'elasticsearch'")

        return warnings, errors


class DevelopmentConfig(BaseConfig):
    """Configuration pour l'environnement de développement."""

    DEBUG = True
    TESTING = False

    @classmethod
    def validate(cls):
        warnings, errors = super().validate()
        # En dev, les avertissements de sécurité ne sont pas bloquants
        return warnings, errors


class StagingConfig(BaseConfig):
    """Configuration pour l'environnement de pré-production."""

    DEBUG = False
    TESTING = False
    RATELIMIT_DEFAULT = os.environ.get('RATELIMIT_DEFAULT', '200 per hour')

    @classmethod
    def validate(cls):
        warnings, errors = super().validate()
        if cls.SECRET_KEY == 'dev-secret-key-change-in-production':
            errors.append("SECRET_KEY doit être défini en staging")
        return warnings, errors


class ProductionConfig(BaseConfig):
    """Configuration pour l'environnement de production."""

    DEBUG = False
    TESTING = False
    RATELIMIT_DEFAULT = os.environ.get('RATELIMIT_DEFAULT', '300 per hour')
    RATELIMIT_STORAGE_URL = os.environ.get('RATELIMIT_STORAGE_URL', 'redis://localhost:6379')

    @classmethod
    def validate(cls):
        warnings, errors = super().validate()

        if cls.SECRET_KEY == 'dev-secret-key-change-in-production':
            errors.append("SECRET_KEY DOIT être défini en production")

        if cls.JWT_SECRET_KEY == 'dev-jwt-secret-change-in-production':
            errors.append("JWT_SECRET_KEY DOIT être défini en production")

        if cls.ENCRYPTION_KEY == 'dev-encryption-key-32-chars-long!':
            errors.append("ENCRYPTION_KEY DOIT être défini en production")

        if not cls.GEMINI_API_KEY:
            warnings.append("GEMINI_API_KEY non défini")

        return warnings, errors


class TestingConfig(BaseConfig):
    """Configuration pour les tests."""

    DEBUG = True
    TESTING = True
    MONGO_DB_NAME = 'georges_medical_test'
    ELASTIC_INDEX_PREFIX = 'georges_test'


config = {
    'development': DevelopmentConfig,
    'staging': StagingConfig,
    'production': ProductionConfig,
    'testing': TestingConfig,
    'default': DevelopmentConfig
}

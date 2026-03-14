"""
Pytest fixtures for Georges Medical Chatbot test suite.
"""

import os
import pytest
from flask import Flask

from backend.core.security import SecurityManager


@pytest.fixture(scope="session")
def encryption_key():
    """A fixed encryption key for deterministic test runs."""
    return "test-encryption-key-32-bytes!!"


@pytest.fixture(scope="session")
def security_manager(encryption_key):
    """SecurityManager instance configured for testing."""
    os.environ["JWT_SECRET_KEY"] = "test-jwt-secret-for-unit-tests"
    manager = SecurityManager(encryption_key)
    return manager


@pytest.fixture()
def app(security_manager):
    """Create a Flask application configured for testing."""
    app = Flask(__name__)
    app.config.update(
        {
            "TESTING": True,
            "SECRET_KEY": "test-secret-key",
            "MONGO_URI": "mongodb://localhost:27017/georges_medical_test",
            "MONGO_DB_NAME": "georges_medical_test",
            "DB_BACKEND": "pymongo",
            "JWT_SECRET_KEY": "test-jwt-secret-for-unit-tests",
            "ENCRYPTION_KEY": "test-encryption-key-32-bytes!!",
            "CORS_ORIGINS": "http://localhost:3000",
            "FLASK_ENV": "testing",
            "LOG_LEVEL": "DEBUG",
        }
    )
    app.security_manager = security_manager
    yield app


@pytest.fixture()
def client(app):
    """Flask test client."""
    return app.test_client()

"""
Tests for backend.core.security.SecurityManager.
Covers encryption, password hashing, JWT tokens, and input validation.
"""

import time
import pytest

from backend.core.security import SecurityManager


class TestEncryption:
    """AES-256-CBC encrypt/decrypt round-trip tests."""

    def test_encrypt_decrypt_roundtrip(self, security_manager):
        plaintext = "Patient: Jean Dupont, dossier 12345"
        encrypted = security_manager.encrypt_data(plaintext)
        assert encrypted != plaintext
        decrypted = security_manager.decrypt_data(encrypted)
        assert decrypted == plaintext

    def test_encrypt_empty_string(self, security_manager):
        assert security_manager.encrypt_data("") == ""

    def test_decrypt_empty_string(self, security_manager):
        assert security_manager.decrypt_data("") == ""

    def test_encrypt_unicode(self, security_manager):
        plaintext = "Symptomes: fievre, maux de tete, nausees"
        encrypted = security_manager.encrypt_data(plaintext)
        decrypted = security_manager.decrypt_data(encrypted)
        assert decrypted == plaintext

    def test_different_encryptions_differ(self, security_manager):
        """Each encryption should produce a different ciphertext due to random IV."""
        plaintext = "same plaintext"
        enc1 = security_manager.encrypt_data(plaintext)
        enc2 = security_manager.encrypt_data(plaintext)
        assert enc1 != enc2

    def test_decrypt_with_wrong_key_fails(self, encryption_key):
        manager_a = SecurityManager(encryption_key)
        manager_b = SecurityManager("completely-different-key-abcdef!")
        encrypted = manager_a.encrypt_data("secret data")
        with pytest.raises(Exception):
            manager_b.decrypt_data(encrypted)


class TestPasswordHashing:
    """bcrypt password hash and verify tests."""

    def test_hash_and_verify(self, security_manager):
        password = "S3cur3P@ssw0rd!"
        hashed = security_manager.hash_password(password)
        assert hashed != password
        assert security_manager.verify_password(password, hashed) is True

    def test_wrong_password_fails(self, security_manager):
        hashed = security_manager.hash_password("correct-password")
        assert security_manager.verify_password("wrong-password", hashed) is False

    def test_hash_is_unique(self, security_manager):
        password = "SamePassword1!"
        hash1 = security_manager.hash_password(password)
        hash2 = security_manager.hash_password(password)
        assert hash1 != hash2  # different salts


class TestJWT:
    """JWT access and refresh token tests."""

    def test_create_and_verify_access_token(self, security_manager):
        token = security_manager.create_access_token("user_123", "medecin")
        is_valid, payload = security_manager.verify_token(token)
        assert is_valid is True
        assert payload["user_id"] == "user_123"
        assert payload["role"] == "medecin"
        assert payload["type"] == "access"

    def test_create_and_verify_refresh_token(self, security_manager):
        token = security_manager.create_refresh_token("user_456")
        is_valid, payload = security_manager.verify_token(token)
        assert is_valid is True
        assert payload["user_id"] == "user_456"
        assert payload["type"] == "refresh"

    def test_invalid_token_rejected(self, security_manager):
        is_valid, payload = security_manager.verify_token("this.is.not.a.real.token")
        assert is_valid is False
        assert "error" in payload

    def test_tampered_token_rejected(self, security_manager):
        token = security_manager.create_access_token("user_1", "admin")
        tampered = token[:-4] + "XXXX"
        is_valid, _ = security_manager.verify_token(tampered)
        assert is_valid is False


class TestEmailValidation:
    """Email format validation tests."""

    @pytest.mark.parametrize(
        "email",
        [
            "docteur@hegp.aphp.fr",
            "jean.dupont@hospital.com",
            "user+tag@example.org",
            "a@b.co",
        ],
    )
    def test_valid_emails(self, security_manager, email):
        assert security_manager.validate_email(email) is True

    @pytest.mark.parametrize(
        "email",
        [
            "",
            "not-an-email",
            "@no-local.com",
            "no-domain@",
            "spaces in@email.com",
            "missing@tld.",
        ],
    )
    def test_invalid_emails(self, security_manager, email):
        assert security_manager.validate_email(email) is False


class TestPasswordStrength:
    """Password strength validation tests."""

    def test_strong_password_accepted(self, security_manager):
        is_valid, msg = security_manager.validate_password_strength("MyStr0ng!Pass")
        assert is_valid is True

    def test_short_password_rejected(self, security_manager):
        is_valid, msg = security_manager.validate_password_strength("Ab1!")
        assert is_valid is False
        assert "8" in msg

    def test_no_uppercase_rejected(self, security_manager):
        is_valid, msg = security_manager.validate_password_strength("lowercase1!")
        assert is_valid is False
        assert "majuscule" in msg

    def test_no_lowercase_rejected(self, security_manager):
        is_valid, msg = security_manager.validate_password_strength("UPPERCASE1!")
        assert is_valid is False
        assert "minuscule" in msg

    def test_no_digit_rejected(self, security_manager):
        is_valid, msg = security_manager.validate_password_strength("NoDigits!!")
        assert is_valid is False
        assert "chiffre" in msg

    def test_no_special_char_rejected(self, security_manager):
        is_valid, msg = security_manager.validate_password_strength("NoSpecial1A")
        assert is_valid is False
        assert "special" in msg.lower() or "spécial" in msg.lower()

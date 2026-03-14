"""
Tests for model document helper functions.
Validates that create_user_doc, create_conversation_doc, and create_project_doc
produce well-formed MongoDB documents with the correct default values.
"""

import pytest
from datetime import datetime, timezone

from backend.models import create_user_doc, create_conversation_doc, create_project_doc


class TestCreateUserDoc:
    """Tests for the create_user_doc helper."""

    def test_basic_user_doc(self):
        doc = create_user_doc(
            email="docteur@hegp.aphp.fr",
            hashed_password="$2b$12$hashedpasswordvalue",
            first_name="Jean",
            last_name="Dupont",
        )
        assert doc["email"] == "docteur@hegp.aphp.fr"
        assert doc["password"] == "$2b$12$hashedpasswordvalue"
        assert doc["first_name"] == "Jean"
        assert doc["last_name"] == "Dupont"

    def test_default_role_is_user(self):
        doc = create_user_doc(
            email="user@example.com",
            hashed_password="hashed",
            first_name="A",
            last_name="B",
        )
        assert doc["role"] == "user"

    def test_custom_role(self):
        doc = create_user_doc(
            email="admin@example.com",
            hashed_password="hashed",
            first_name="Admin",
            last_name="User",
            role="admin",
        )
        assert doc["role"] == "admin"

    def test_timestamps_are_set(self):
        before = datetime.now(timezone.utc)
        doc = create_user_doc(
            email="ts@example.com",
            hashed_password="hashed",
            first_name="T",
            last_name="S",
        )
        after = datetime.now(timezone.utc)
        assert before <= doc["created_at"] <= after
        assert before <= doc["updated_at"] <= after

    def test_is_active_default_true(self):
        doc = create_user_doc(
            email="active@example.com",
            hashed_password="hashed",
            first_name="A",
            last_name="B",
        )
        assert doc["is_active"] is True


class TestCreateConversationDoc:
    """Tests for the create_conversation_doc helper."""

    def test_basic_conversation_doc(self):
        doc = create_conversation_doc(
            user_id="user_abc123",
            title="Consultation initiale",
        )
        assert doc["user_id"] == "user_abc123"
        assert doc["title"] == "Consultation initiale"

    def test_messages_default_empty(self):
        doc = create_conversation_doc(user_id="u1", title="Test")
        assert doc["messages"] == []

    def test_project_id_optional(self):
        doc_without = create_conversation_doc(user_id="u1", title="No project")
        assert doc_without["project_id"] is None

        doc_with = create_conversation_doc(
            user_id="u1", title="With project", project_id="proj_xyz"
        )
        assert doc_with["project_id"] == "proj_xyz"

    def test_timestamps_are_set(self):
        before = datetime.now(timezone.utc)
        doc = create_conversation_doc(user_id="u1", title="T")
        after = datetime.now(timezone.utc)
        assert before <= doc["created_at"] <= after
        assert before <= doc["updated_at"] <= after


class TestCreateProjectDoc:
    """Tests for the create_project_doc helper."""

    def test_basic_project_doc(self):
        doc = create_project_doc(
            name="Cardiologie IA",
            owner_id="user_owner1",
            description="Projet de chatbot cardiologie",
        )
        assert doc["name"] == "Cardiologie IA"
        assert doc["owner_id"] == "user_owner1"
        assert doc["description"] == "Projet de chatbot cardiologie"

    def test_members_contains_owner(self):
        doc = create_project_doc(
            name="Test",
            owner_id="owner_1",
        )
        assert "owner_1" in doc["members"]

    def test_default_description_empty(self):
        doc = create_project_doc(name="Minimal", owner_id="o1")
        assert doc["description"] == ""

    def test_timestamps_are_set(self):
        before = datetime.now(timezone.utc)
        doc = create_project_doc(name="TS", owner_id="o1")
        after = datetime.now(timezone.utc)
        assert before <= doc["created_at"] <= after
        assert before <= doc["updated_at"] <= after

    def test_is_active_default_true(self):
        doc = create_project_doc(name="Active", owner_id="o1")
        assert doc["is_active"] is True

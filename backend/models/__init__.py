"""
Model document helpers for Georges Medical Chatbot.
These functions produce MongoDB-ready document dictionaries with sensible defaults.
"""

from datetime import datetime, timezone


def create_user_doc(email, hashed_password, first_name, last_name, role="user"):
    """
    Create a user document ready for MongoDB insertion.

    Args:
        email: User email address.
        hashed_password: bcrypt-hashed password string.
        first_name: User's first name.
        last_name: User's last name.
        role: User role ("user", "medecin", "admin"). Defaults to "user".

    Returns:
        dict: A user document with timestamps and default fields.
    """
    now = datetime.now(timezone.utc)
    return {
        "email": email,
        "password": hashed_password,
        "first_name": first_name,
        "last_name": last_name,
        "role": role,
        "is_active": True,
        "created_at": now,
        "updated_at": now,
    }


def create_conversation_doc(user_id, title, project_id=None):
    """
    Create a conversation document ready for MongoDB insertion.

    Args:
        user_id: ID of the user who owns this conversation.
        title: Display title for the conversation.
        project_id: Optional project ID this conversation belongs to.

    Returns:
        dict: A conversation document with empty messages list and timestamps.
    """
    now = datetime.now(timezone.utc)
    return {
        "user_id": user_id,
        "title": title,
        "project_id": project_id,
        "messages": [],
        "created_at": now,
        "updated_at": now,
    }


def create_project_doc(name, owner_id, description=""):
    """
    Create a project document ready for MongoDB insertion.

    Args:
        name: Project name.
        owner_id: ID of the user who owns the project.
        description: Optional project description.

    Returns:
        dict: A project document with the owner in the members list.
    """
    now = datetime.now(timezone.utc)
    return {
        "name": name,
        "owner_id": owner_id,
        "description": description,
        "members": [owner_id],
        "is_active": True,
        "created_at": now,
        "updated_at": now,
    }

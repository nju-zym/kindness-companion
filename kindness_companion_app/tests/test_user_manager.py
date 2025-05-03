import pytest
import os
import tempfile
from pathlib import Path

from kindness_companion_app.backend.database_manager import DatabaseManager
from kindness_companion_app.backend.user_manager import UserManager


@pytest.fixture
def db_manager():
    """Create a temporary database for testing."""
    # Create a temporary file
    fd, path = tempfile.mkstemp()
    os.close(fd)

    # Create database manager with the temporary file
    db_manager = DatabaseManager(path)

    yield db_manager

    # Clean up
    os.unlink(path)


@pytest.fixture
def user_manager(db_manager):
    """Create a user manager for testing."""
    return UserManager(db_manager)


def test_register_user(user_manager):
    """Test user registration."""
    # Register a new user
    user = user_manager.register_user("testuser", "password123", "test@example.com")

    # Check that the user was registered successfully
    assert user is not None
    assert user["username"] == "testuser"
    assert user["email"] == "test@example.com"

    # Try to register the same user again
    duplicate = user_manager.register_user("testuser", "password456", "other@example.com")

    # Check that the duplicate registration failed
    assert duplicate is None


def test_login(user_manager):
    """Test user login."""
    # Register a user
    user_manager.register_user("logintest", "password123", "login@example.com")

    # Login with correct credentials
    user = user_manager.login("logintest", "password123")

    # Check that login was successful
    assert user is not None
    assert user["username"] == "logintest"
    assert user["email"] == "login@example.com"

    # Login with incorrect password
    user = user_manager.login("logintest", "wrongpassword")

    # Check that login failed
    assert user is None

    # Login with non-existent user
    user = user_manager.login("nonexistent", "password123")

    # Check that login failed
    assert user is None


def test_update_profile(user_manager):
    """Test profile update."""
    # Register a user
    user = user_manager.register_user("updatetest", "password123", "update@example.com")

    # Update email
    success = user_manager.update_profile(user["id"], new_email="newemail@example.com")

    # Check that update was successful
    assert success

    # Login to verify the update
    updated_user = user_manager.login("updatetest", "password123")
    assert updated_user["email"] == "newemail@example.com"

    # Update password
    success = user_manager.update_profile(user["id"], new_password="newpassword123")

    # Check that update was successful
    assert success

    # Login with old password should fail
    failed_login = user_manager.login("updatetest", "password123")
    assert failed_login is None

    # Login with new password should succeed
    success_login = user_manager.login("updatetest", "newpassword123")
    assert success_login is not None

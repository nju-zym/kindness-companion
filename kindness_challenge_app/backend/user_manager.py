import hashlib
import secrets
import time
import sqlite3
from .database_manager import DatabaseManager


class UserManager:
    """
    Manages user authentication and profile operations.
    """

    def __init__(self, db_manager=None):
        """
        Initialize the user manager.

        Args:
            db_manager (DatabaseManager, optional): Database manager instance.
                If None, a new instance will be created.
        """
        self.db_manager = db_manager or DatabaseManager()
        self.current_user = None

    def _hash_password(self, password, salt=None):
        """
        Hash a password using SHA-256 with a salt.

        Args:
            password (str): The password to hash
            salt (str, optional): Salt to use. If None, a new salt will be generated.

        Returns:
            tuple: (hash, salt)
        """
        if salt is None:
            salt = secrets.token_hex(16)

        # Combine password and salt, then hash
        password_hash = hashlib.sha256((password + salt).encode()).hexdigest()
        return password_hash, salt

    def register_user(self, username, password, email=None):
        """
        Register a new user.

        Args:
            username (str): Username
            password (str): Password
            email (str, optional): Email address

        Returns:
            dict: User information if registration is successful, None otherwise
        """
        # Check if username already exists
        existing_user = self.db_manager.execute_query(
            "SELECT * FROM users WHERE username = ?",
            (username,)
        )

        if existing_user:
            return None  # Username already exists

        # Hash the password with a new salt
        password_hash, salt = self._hash_password(password)

        # Store the hash and salt in the database
        # Format: "hash:salt"
        stored_hash = f"{password_hash}:{salt}"

        user_id = self.db_manager.execute_insert(
            "INSERT INTO users (username, password_hash, email) VALUES (?, ?, ?)",
            (username, stored_hash, email)
        )

        if user_id:
            return {
                "id": user_id,
                "username": username,
                "email": email
            }

        return None

    def login(self, username, password):
        """
        Authenticate a user.

        Args:
            username (str): Username
            password (str): Password

        Returns:
            dict: User information if authentication is successful, None otherwise
        """
        user = self.db_manager.execute_query(
            "SELECT * FROM users WHERE username = ?",
            (username,)
        )

        if not user:
            return None  # User not found

        user = user[0]  # Get the first (and only) user

        # Extract hash and salt
        stored_hash, salt = user["password_hash"].split(":")

        # Hash the provided password with the stored salt
        password_hash, _ = self._hash_password(password, salt)

        if password_hash == stored_hash:
            # Update last login time
            self.db_manager.execute_update(
                "UPDATE users SET last_login = CURRENT_TIMESTAMP WHERE id = ?",
                (user["id"],)
            )

            # Set current user
            self.current_user = {
                "id": user["id"],
                "username": user["username"],
                "email": user["email"]
            }

            return self.current_user

        return None  # Authentication failed

    def logout(self):
        """Log out the current user."""
        self.current_user = None

    def get_current_user(self):
        """
        Get the current logged-in user.

        Returns:
            dict: Current user information, or None if no user is logged in
        """
        return self.current_user

    def update_profile(self, user_id, new_password=None):
        """
        Update user profile (currently only password).

        Args:
            user_id (int): User ID.
            new_password (str, optional): New password. Defaults to None.

        Returns:
            bool: True if update was successful, False otherwise.
        """
        updates = {}
        params = []

        # Only update password if provided
        if new_password:
            hashed_password = self._hash_password(new_password)
            updates["password"] = "?"
            params.append(hashed_password)

        if not updates:
            return True # Nothing to update

        set_clause = ", ".join([f"{key} = {value}" for key, value in updates.items()])
        query = f"UPDATE users SET {set_clause} WHERE id = ?"
        params.append(user_id)

        try:
            self.db_manager.execute_query(query, tuple(params))
            self.logger.info(f"User profile updated for user_id: {user_id}")
            return True
        except sqlite3.Error as e:
            self.logger.error(f"Error updating user profile for user_id {user_id}: {e}")
            return False

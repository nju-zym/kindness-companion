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

        # Insert user with default empty bio and default avatar path
        user_id = self.db_manager.execute_insert(
            "INSERT INTO users (username, password_hash, email, bio, avatar_path) VALUES (?, ?, ?, ?, ?)",
            (username, stored_hash, email, "", ":/images/profilePicture.png") # Default bio="", avatar_path=":/images/profilePicture.png"
        )

        if user_id:
            # Fetch the newly created user including the creation timestamp
            new_user = self.db_manager.execute_query(
                "SELECT id, username, email, bio, avatar_path, created_at FROM users WHERE id = ?",
                (user_id,)
            )
            if new_user:
                user_data = new_user[0]
                return {
                    "id": user_data["id"],
                    "username": user_data["username"],
                    "email": user_data["email"],
                    "bio": user_data["bio"],
                    "avatar_path": user_data["avatar_path"],
                    "registration_date": user_data["created_at"] # Use created_at as registration_date
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

            # Set current user with all relevant fields, using .get() for robustness
            self.current_user = {
                "id": user["id"],
                "username": user["username"],
                "email": user.get("email"), # Use get for optional fields
                "bio": user.get("bio", ""), # Default to empty string if bio doesn't exist
                "avatar_path": user.get("avatar_path", ":/images/profilePicture.png"), # Default avatar if not exist
                "registration_date": user.get("created_at") # Use get, might be None if not exist
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

    def update_profile(self, user_id, new_password=None, bio=None, avatar_path=None):
        """
        Update user profile information.

        Args:
            user_id (int): User ID.
            new_password (str, optional): New password. Defaults to None.
            bio (str, optional): New bio. Defaults to None.
            avatar_path (str, optional): New avatar path. Defaults to None.

        Returns:
            bool: True if update was successful, False otherwise.
        """
        updates = {}
        params = []

        # Update password if provided
        if new_password:
            password_hash, salt = self._hash_password(new_password)
            updates["password_hash"] = "?" # Use placeholder
            params.append(f"{password_hash}:{salt}")

        # Update bio if provided (allow empty string)
        if bio is not None:
            updates["bio"] = "?" # Use placeholder
            params.append(bio)

        # Update avatar path if provided
        if avatar_path is not None:
            updates["avatar_path"] = "?" # Use placeholder
            params.append(avatar_path)

        if not updates:
            print("No profile updates provided.") # Add some logging/print
            return True # Nothing to update

        set_clause = ", ".join([f"{key} = ?" for key in updates.keys()]) # Placeholders in SET clause
        query = f"UPDATE users SET {set_clause} WHERE id = ?"
        params.append(user_id)

        try:
            # Use execute_update for UPDATE operations
            affected_rows = self.db_manager.execute_update(query, tuple(params))
            if affected_rows > 0:
                print(f"User profile updated successfully for user_id: {user_id}") # Add logging/print
                # Optionally update self.current_user if the updated user is the current one
                if self.current_user and self.current_user["id"] == user_id:
                    if new_password: # Password changed, force re-login for security? Or just update locally?
                        pass # Decide on security implications
                    if bio is not None:
                        self.current_user["bio"] = bio
                    if avatar_path is not None:
                        self.current_user["avatar_path"] = avatar_path
                return True
            else:
                print(f"No user found with id {user_id} or no changes made.") # Add logging/print
                return False # Or True if no change is not an error?
        except sqlite3.Error as e:
            print(f"Error updating user profile for user_id {user_id}: {e}") # Add logging/print
            # self.logger.error(...) # Use proper logging if available
            return False

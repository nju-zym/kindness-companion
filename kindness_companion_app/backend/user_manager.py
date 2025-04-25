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
        stored_hash = f"{password_hash}:{salt}"

        # Insert user with default empty bio, default avatar path, and NULL avatar blob
        user_id = self.db_manager.execute_insert(
            "INSERT INTO users (username, password_hash, email, bio, avatar_path, avatar) VALUES (?, ?, ?, ?, ?, ?)",
            (username, stored_hash, email, "", ":/images/profilePicture.png", None) # Set avatar blob to None initially
        )

        if user_id:
            # Fetch the newly created user including the avatar blob
            new_user = self.db_manager.execute_query(
                "SELECT id, username, email, bio, avatar_path, avatar, created_at FROM users WHERE id = ?", # Select avatar blob
                (user_id,)
            )
            if new_user:
                user_data = new_user[0]
                return {
                    "id": user_data["id"],
                    "username": user_data["username"],
                    "email": user_data["email"],
                    "bio": user_data["bio"],
                    "avatar_path": user_data["avatar_path"], # Keep path for now
                    "avatar": user_data["avatar"], # Add avatar blob (bytes or None)
                    "registration_date": user_data["created_at"]
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
        # Fetch user including the avatar blob
        user_result = self.db_manager.execute_query(
            "SELECT * FROM users WHERE username = ?",
            (username,)
        )

        if not user_result:
            return None  # User not found

        user = user_result[0]  # Get the first (and only) user

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

            # Set current user, including the avatar blob
            self.current_user = {
                "id": user["id"],
                "username": user["username"],
                "email": user.get("email"),
                "bio": user.get("bio", ""),
                "avatar_path": user.get("avatar_path", ":/images/profilePicture.png"), # Keep path
                "avatar": user.get("avatar"), # Get avatar blob (bytes or None)
                "registration_date": user.get("created_at")
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

    def update_profile(self, user_id, new_password=None, bio=None, avatar_path=None, avatar_data=None): # Add avatar_data parameter
        """
        Update user profile information. Now accepts avatar_data (bytes).
        avatar_path is kept for potential future use but not actively updated here.
        """
        updates = {}
        params = []

        # Update password if provided
        if new_password:
            password_hash, salt = self._hash_password(new_password)
            updates["password_hash"] = "?"
            params.append(f"{password_hash}:{salt}")

        # Update bio if provided
        if bio is not None:
            updates["bio"] = "?"
            params.append(bio)

        # Update avatar blob if provided
        if avatar_data is not None:
            updates["avatar"] = "?"
            # Pass bytes directly, sqlite3 handles BLOB binding
            params.append(avatar_data)
            # Optionally clear avatar_path if switching to blob storage?
            # updates["avatar_path"] = "?"
            # params.append(None)

        # Update avatar path (kept for now, but maybe remove later)
        # if avatar_path is not None:
        #     updates["avatar_path"] = "?"
        #     params.append(avatar_path)

        if not updates:
            print("No profile updates provided.")
            return True # Nothing to update

        set_clause = ", ".join([f"{key} = ?" for key in updates.keys()])
        query = f"UPDATE users SET {set_clause} WHERE id = ?"
        params.append(user_id)

        try:
            affected_rows = self.db_manager.execute_update(query, tuple(params))
            if affected_rows > 0:
                print(f"User profile updated successfully for user_id: {user_id}")
                # Update self.current_user if the updated user is the current one
                if self.current_user and self.current_user["id"] == user_id:
                    # Password changed, force re-login for security? Or just update locally?
                    if new_password:
                        pass # Decide on security implications
                    if bio is not None:
                        self.current_user["bio"] = bio
                    if avatar_data is not None:
                        self.current_user["avatar"] = avatar_data # Store bytes
                        # self.current_user["avatar_path"] = None # Optionally clear path
                return True
            else:
                print(f"No user found with id {user_id} or no changes made.")
                return False # Or True if no change is not an error?
        except sqlite3.Error as e:
            print(f"Error updating user profile for user_id {user_id}: {e}")
            # self.logger.error(...) # Use proper logging if available
            return False

    def get_user_by_id(self, user_id):
        """Fetch user details by ID, including avatar blob."""
        user_result = self.db_manager.execute_query(
            "SELECT * FROM users WHERE id = ?",
            (user_id,)
        )
        if user_result:
            # Convert Row object to a standard dictionary if needed,
            # ensuring blob data is included.
            user_data = dict(user_result[0])
            return user_data
        return None

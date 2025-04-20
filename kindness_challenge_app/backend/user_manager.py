import hashlib
import secrets
import time
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
    
    def update_profile(self, user_id, new_email=None, new_password=None):
        """
        Update user profile information.
        
        Args:
            user_id (int): User ID
            new_email (str, optional): New email address
            new_password (str, optional): New password
            
        Returns:
            bool: True if update is successful, False otherwise
        """
        if new_email is None and new_password is None:
            return False  # Nothing to update
        
        updates = []
        params = []
        
        if new_email is not None:
            updates.append("email = ?")
            params.append(new_email)
        
        if new_password is not None:
            password_hash, salt = self._hash_password(new_password)
            stored_hash = f"{password_hash}:{salt}"
            updates.append("password_hash = ?")
            params.append(stored_hash)
        
        # Add user_id to params
        params.append(user_id)
        
        query = f"UPDATE users SET {', '.join(updates)} WHERE id = ?"
        
        affected_rows = self.db_manager.execute_update(query, tuple(params))
        
        return affected_rows > 0

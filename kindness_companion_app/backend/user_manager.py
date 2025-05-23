import hashlib
import secrets
import time
import sqlite3
from .database_manager import DatabaseManager
import logging  # Add logging

logger = logging.getLogger(__name__)  # Add logger


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
        self._initialize_login_state_table()

    def _initialize_login_state_table(self):
        """初始化保存登录状态的数据库表"""
        try:
            self.db_manager.execute_query("""
                CREATE TABLE IF NOT EXISTS login_state (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER NOT NULL,
                    username TEXT NOT NULL,
                    password_hash TEXT NOT NULL,
                    last_login TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (user_id) REFERENCES users (id)
                )
            """)
        except Exception as e:
            logger.error(f"Error initializing login_state table: {e}")

    def save_login_state(self, user_id: int, username: str, password_hash: str) -> bool:
        """
        保存用户的登录状态

        Args:
            user_id (int): 用户ID
            username (str): 用户名
            password_hash (str): 密码哈希

        Returns:
            bool: 是否保存成功
        """
        try:
            # 先删除旧的登录状态
            self.db_manager.execute_update(
                "DELETE FROM login_state WHERE user_id = ?",
                (user_id,)
            )
            
            # 保存新的登录状态
            self.db_manager.execute_insert(
                """
                INSERT INTO login_state (user_id, username, password_hash)
                VALUES (?, ?, ?)
                """,
                (user_id, username, password_hash)
            )
            return True
        except Exception as e:
            logger.error(f"Error saving login state: {e}")
            return False

    def clear_login_state(self) -> bool:
        """
        清除所有保存的登录状态

        Returns:
            bool: 是否清除成功
        """
        try:
            self.db_manager.execute_update("DELETE FROM login_state")
            return True
        except Exception as e:
            logger.error(f"Error clearing login state: {e}")
            return False

    def get_saved_login_state(self) -> dict | None:
        """
        获取保存的登录状态

        Returns:
            dict | None: 包含登录信息的字典，如果没有保存的状态则返回None
        """
        try:
            result = self.db_manager.execute_query(
                "SELECT * FROM login_state ORDER BY last_login DESC LIMIT 1"
            )
            if result:
                return dict(result[0])
            return None
        except Exception as e:
            logger.error(f"Error getting saved login state: {e}")
            return None

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
            "SELECT * FROM users WHERE username = ?", (username,)
        )

        if existing_user:
            return None  # Username already exists

        # Hash the password with a new salt
        password_hash, salt = self._hash_password(password)
        stored_hash = f"{password_hash}:{salt}"

        # Insert user with default empty bio, default avatar path, NULL avatar blob, and AI consent TRUE
        user_id = self.db_manager.execute_insert(
            "INSERT INTO users (username, password_hash, email, bio, avatar_path, avatar, ai_consent_given) VALUES (?, ?, ?, ?, ?, ?, ?)",
            (
                username,
                stored_hash,
                email,
                "",
                ":/images/profilePicture.png",
                None,
                1,
            ),  # Set ai_consent_given to 1 (True)
        )

        if user_id:
            # Fetch the newly created user including the avatar blob and AI consent
            new_user = self.db_manager.execute_query(
                "SELECT id, username, email, bio, avatar_path, avatar, created_at, ai_consent_given FROM users WHERE id = ?",
                (user_id,),
            )
            if new_user:
                user_data = new_user[0]
                return {
                    "id": user_data["id"],
                    "username": user_data["username"],
                    "email": user_data["email"],
                    "bio": user_data["bio"],
                    "avatar_path": user_data["avatar_path"],
                    "avatar": user_data["avatar"],
                    "registration_date": user_data["created_at"],
                    "ai_consent_given": True,  # Always return True for new users
                }

        return None

    def login(self, username, password):
        """
        Authenticate a user. AI consent is assumed True.
        """
        # Fetch user including the avatar blob
        user_result = self.db_manager.execute_query(
            "SELECT * FROM users WHERE username = ?", (username,)
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

            # 保存登录状态
            self.save_login_state(user["id"], username, user["password_hash"])

            # Check and potentially update NULL AI consent for existing users
            current_consent = user.get("ai_consent_given")
            if current_consent is None:
                logger.info(
                    f"User {user['id']} has NULL AI consent. Updating to True (1) in database."
                )
                self.set_ai_consent(user["id"], True)  # Update DB
                ai_consent_status = True  # Set status to True for the session
            else:
                ai_consent_status = bool(
                    current_consent
                )  # Use existing status (should be 1 or 0)
                # We still override to True for the session as per the request
                ai_consent_status = True

            # Set current user, always assuming AI consent is True for the session
            self.current_user = {
                "id": user["id"],
                "username": user["username"],
                "email": user.get("email"),
                "bio": user.get("bio", ""),
                "avatar_path": user.get("avatar_path", ":/images/profilePicture.png"),
                "avatar": user.get("avatar"),
                "registration_date": user.get("created_at"),
                "ai_consent_given": True,  # Always return True
            }

            return self.current_user

        return None  # Authentication failed

    def logout(self):
        """Log out the current user."""
        self.current_user = None
        # 清除保存的登录状态
        self.clear_login_state()

    def get_current_user(self):
        """
        Get the current logged-in user.

        Returns:
            dict: Current user information, or None if no user is logged in
        """
        return self.current_user

    def update_profile(
        self, user_id, new_password=None, bio=None, avatar_path=None, avatar_data=None
    ):  # Add avatar_data parameter
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
            return True  # Nothing to update

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
                        pass  # Decide on security implications
                    if bio is not None:
                        self.current_user["bio"] = bio
                    if avatar_data is not None:
                        self.current_user["avatar"] = avatar_data  # Store bytes
                        # self.current_user["avatar_path"] = None # Optionally clear path
                return True
            else:
                print(f"No user found with id {user_id} or no changes made.")
                return False  # Or True if no change is not an error?
        except sqlite3.Error as e:
            print(f"Error updating user profile for user_id {user_id}: {e}")
            # self.logger.error(...) # Use proper logging if available
            return False

    def get_user_by_id(self, user_id):
        """Fetch user details by ID, including avatar blob."""
        user_result = self.db_manager.execute_query(
            "SELECT * FROM users WHERE id = ?", (user_id,)
        )
        if user_result:
            # Convert Row object to a standard dictionary if needed,
            # ensuring blob data is included.
            user_data = dict(user_result[0])
            return user_data
        return None

    # --- AI Consent Methods ---

    def get_ai_consent(self, user_id: int) -> bool | None:
        """
        Get the AI consent status for a given user.
        NOTE: This method might become less relevant if consent is always assumed True.
              Keeping it for potential internal checks but UI/feature gates should assume True.

        Args:
            user_id (int): The ID of the user.

        Returns:
            bool | None: True if consented (or assumed), False if explicitly denied (legacy), None if error/not found.
        """
        # Simplified: Always return True as per the new requirement
        logger.debug(
            f"get_ai_consent called for user {user_id}, returning True (default behavior)."
        )
        return True

    def set_ai_consent(self, user_id: int, consent_status: bool) -> bool:
        """
        Set the AI consent status for a given user.
        NOTE: This is mainly used internally now (e.g., during login for legacy users).
              UI toggles are removed.

        Args:
            user_id (int): The ID of the user.
            consent_status (bool): True to grant consent, False to deny.

        Returns:
            bool: True if the update was successful, False otherwise.
        """
        try:
            # First, check if the user exists and log the current consent status
            user_check = self.db_manager.execute_query(
                "SELECT id, ai_consent_given FROM users WHERE id = ?", (user_id,)
            )

            if not user_check:
                logger.warning(
                    f"User with ID {user_id} not found when trying to set AI consent."
                )
                return False

            current_consent = user_check[0].get("ai_consent_given")
            logger.info(
                f"Current AI consent for user {user_id}: {current_consent}, attempting to set to: {consent_status}"
            )

            # Convert boolean to integer for storage
            consent_int = 1 if consent_status else 0

            affected_rows = self.db_manager.execute_update(
                "UPDATE users SET ai_consent_given = ? WHERE id = ?",
                (consent_int, user_id),  # Store as 1 or 0
            )

            if affected_rows > 0:
                logger.info(
                    f"AI consent status successfully set to {consent_status} for user {user_id} in DB."
                )
                # Update current user if applicable
                if self.current_user and self.current_user["id"] == user_id:
                    # Even though we always return True from login, update the underlying dict too
                    self.current_user["ai_consent_given"] = True
                    logger.info(
                        f"Updated in-memory current_user AI consent to: {self.current_user.get('ai_consent_given')}"
                    )
                return True
            else:
                # This might happen if the value was already set to the target value
                logger.info(
                    f"DB update query executed but no rows affected for user {user_id} when setting AI consent (value might already be correct)."
                )
                # Return True because the desired state is achieved or already exists
                return True
        except sqlite3.Error as e:
            logger.error(f"Database error setting AI consent for user {user_id}: {e}")
            return False
        except Exception as e:
            logger.error(f"Unexpected error setting AI consent for user {user_id}: {e}")
            return False

    # --- End AI Consent Methods ---

    def delete_user_account(self, user_id, password):
        """
        Permanently delete a user account and all associated data after verifying the password.

        Args:
            user_id (int): The ID of the user to delete.
            password (str): The user's current password for verification.

        Returns:
            bool: True if the account was successfully deleted, False otherwise.
        """
        # Step 1: Verify the password
        user_result = self.db_manager.execute_query(
            "SELECT password_hash FROM users WHERE id = ?", (user_id,)
        )

        if not user_result:
            print(f"Delete failed: User with ID {user_id} not found.")
            return False  # User not found

        user_data = user_result[0]
        stored_hash_full = user_data["password_hash"]

        try:
            stored_hash, salt = stored_hash_full.split(":")
            provided_hash, _ = self._hash_password(password, salt)
        except (ValueError, AttributeError):
            # Handle cases where password_hash might be malformed or None
            print(f"Delete failed: Could not parse password hash for user {user_id}.")
            return False

        if provided_hash != stored_hash:
            print(f"Delete failed: Incorrect password for user {user_id}.")
            return False  # Incorrect password

        # Step 2: Delete associated data (use transaction for atomicity)
        try:
            # Delete reminders
            self.db_manager.execute_update(
                "DELETE FROM reminders WHERE user_id = ?", (user_id,)
            )
            print(f"Deleted reminders for user {user_id}.")

            # Delete progress
            self.db_manager.execute_update(
                "DELETE FROM progress WHERE user_id = ?", (user_id,)
            )
            print(f"Deleted progress records for user {user_id}.")

            # Delete challenge subscriptions
            self.db_manager.execute_update(
                "DELETE FROM user_challenges WHERE user_id = ?", (user_id,)
            )
            print(f"Deleted challenge subscriptions for user {user_id}.")

            # Step 3: Delete the user record
            self.db_manager.execute_update("DELETE FROM users WHERE id = ?", (user_id,))
            print(f"Deleted user record for user {user_id}.")

            print(f"Account deletion successful for user {user_id}.")

            # If the deleted user is the currently logged-in user, log them out
            if self.current_user and self.current_user["id"] == user_id:
                self.logout()

            return True

        except sqlite3.Error as e:
            print(f"Error during account deletion transaction for user {user_id}: {e}")
            return False

    def auto_login(self) -> dict | None:
        """
        尝试使用保存的登录状态自动登录

        Returns:
            dict | None: 登录成功返回用户信息，失败返回None
        """
        saved_state = self.get_saved_login_state()
        if not saved_state:
            return None

        try:
            # 验证用户是否存在
            user_result = self.db_manager.execute_query(
                "SELECT * FROM users WHERE id = ? AND username = ?",
                (saved_state["user_id"], saved_state["username"])
            )

            if not user_result:
                self.clear_login_state()
                return None

            user = user_result[0]
            
            # 验证密码哈希是否匹配
            if user["password_hash"] != saved_state["password_hash"]:
                self.clear_login_state()
                return None

            # 更新最后登录时间
            self.db_manager.execute_update(
                "UPDATE users SET last_login = CURRENT_TIMESTAMP WHERE id = ?",
                (user["id"],)
            )

            # 设置当前用户
            self.current_user = {
                "id": user["id"],
                "username": user["username"],
                "email": user.get("email"),
                "bio": user.get("bio", ""),
                "avatar_path": user.get("avatar_path", ":/images/profilePicture.png"),
                "avatar": user.get("avatar"),
                "registration_date": user.get("created_at"),
                "ai_consent_given": True,
            }

            return self.current_user

        except Exception as e:
            logger.error(f"Error during auto login: {e}")
            self.clear_login_state()
            return None

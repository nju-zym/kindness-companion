import os
import json
import shutil
import logging
from datetime import datetime
from pathlib import Path
import hashlib
import uuid


class SyncManager:
    """
    Manages data synchronization between users.
    """

    def __init__(self, db_manager):
        """
        Initialize the sync manager.

        Args:
            db_manager: Database manager instance
        """
        self.db_manager = db_manager
        self.sync_dir = os.path.expanduser("~/KindnessCompanion/sync")
        self.ensure_sync_directory()
        self.version = "1.3"  # Updated version for enhanced sync support
        self._ensure_sync_tables()

    def _ensure_sync_tables(self):
        """Ensure sync-related database tables exist."""
        try:
            # Add a sync_id column to users table if it doesn't exist
            self.db_manager.execute_query(
                """
                CREATE TABLE IF NOT EXISTS user_sync_info (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER NOT NULL,
                    sync_uuid TEXT UNIQUE NOT NULL,
                    original_username TEXT,
                    device_name TEXT,
                    last_sync TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (user_id) REFERENCES users (id),
                    UNIQUE (user_id)
                )
            """
            )
        except Exception as e:
            logging.error(f"Error creating sync tables: {e}")

    def _get_or_create_user_sync_uuid(self, user_id):
        """Get or create a unique sync UUID for a user."""
        try:
            # Check if sync UUID already exists
            result = self.db_manager.execute_query(
                "SELECT sync_uuid FROM user_sync_info WHERE user_id = ?", (user_id,)
            )

            if result:
                return result[0]["sync_uuid"]

            # Create new sync UUID
            sync_uuid = str(uuid.uuid4())
            user_info = self.db_manager.execute_query(
                "SELECT username FROM users WHERE id = ?", (user_id,)
            )

            username = user_info[0]["username"] if user_info else "Unknown"

            self.db_manager.execute_insert(
                """
                INSERT INTO user_sync_info (user_id, sync_uuid, original_username, device_name)
                VALUES (?, ?, ?, ?)
                """,
                (user_id, sync_uuid, username, os.uname().nodename),
            )

            return sync_uuid
        except Exception as e:
            logging.error(f"Error getting/creating sync UUID: {e}")
            return None

    def ensure_sync_directory(self):
        """Ensure the sync directory exists."""
        os.makedirs(self.sync_dir, exist_ok=True)

    def _calculate_post_hash(self, post):
        """
        Calculate a unique hash for a post.

        Args:
            post (dict): Post data

        Returns:
            str: MD5 hash of the post
        """
        # Create a string representation of the post data
        post_str = f"{post['id']}{post['content']}{post.get('image_data', '')}{post['created_at']}"
        return hashlib.md5(post_str.encode()).hexdigest()

    def _calculate_comment_hash(self, comment):
        """
        Calculate a unique hash for a comment.

        Args:
            comment (dict): Comment data

        Returns:
            str: MD5 hash of the comment
        """
        # Create a string representation of the comment data
        comment_str = f"{comment['id']}{comment['content']}{comment['created_at']}"
        return hashlib.md5(comment_str.encode()).hexdigest()

    def _get_current_user_id(self):
        """
        Get the current user's ID.
        Uses multiple fallback methods to find the currently logged in user.

        Returns:
            int: Current user ID or None if not logged in
        """
        try:
            # Method 1: Try to get from login_state table (most recent login)
            current_user = self.db_manager.execute_query(
                "SELECT user_id FROM login_state ORDER BY last_login DESC LIMIT 1"
            )
            if current_user:
                return current_user[0]["user_id"]

            # Method 2: If no login_state, try to get the most recently active user
            recent_user = self.db_manager.execute_query(
                "SELECT id FROM users ORDER BY last_login DESC LIMIT 1"
            )
            if recent_user:
                return recent_user[0]["id"]

            # Method 3: Fallback to first user if single user system
            first_user = self.db_manager.execute_query(
                "SELECT id FROM users ORDER BY id ASC LIMIT 1"
            )
            if first_user:
                return first_user[0]["id"]

            return None
        except Exception as e:
            logging.error(f"Error getting current user ID: {e}")
            return None

    def initialize_sync_for_user(self, user_id):
        """Initialize sync UUID for an existing user if not already present."""
        try:
            sync_uuid = self._get_or_create_user_sync_uuid(user_id)
            if sync_uuid:
                logging.info(f"Initialized sync UUID for user {user_id}: {sync_uuid}")
                return sync_uuid
            return None
        except Exception as e:
            logging.error(f"Error initializing sync for user {user_id}: {e}")
            return None

    def get_user_sync_info(self, user_id):
        """Get sync information for a user."""
        try:
            result = self.db_manager.execute_query(
                """
                SELECT usi.sync_uuid, usi.original_username, usi.device_name, usi.last_sync,
                       u.username, u.avatar, u.bio
                FROM user_sync_info usi
                JOIN users u ON usi.user_id = u.id
                WHERE usi.user_id = ?
                """,
                (user_id,),
            )
            return result[0] if result else None
        except Exception as e:
            logging.error(f"Error getting sync info for user {user_id}: {e}")
            return None

    def export_data(self):
        """
        Export wall posts and comments to a JSON file for sharing.
        Enhanced with better user identification.

        Returns:
            str: Path to the exported file
        """
        try:
            # Ensure current user has sync UUID before export
            current_user_id = self._get_current_user_id()
            if current_user_id:
                self.initialize_sync_for_user(current_user_id)

            # Get all posts with enhanced user information
            posts = self.db_manager.execute_query(
                """
                SELECT w.*,
                       CASE
                           WHEN w.is_anonymous = 1 THEN 'Anonymous'
                           ELSE u.username
                       END as display_name,
                       u.username,
                       u.avatar,
                       u.bio,
                       usi.sync_uuid,
                       usi.original_username,
                       usi.device_name
                FROM kindness_wall w
                LEFT JOIN users u ON w.user_id = u.id
                LEFT JOIN user_sync_info usi ON u.id = usi.user_id
                ORDER BY w.created_at DESC
                """
            )

            # Get all comments with enhanced user information
            comments = self.db_manager.execute_query(
                """
                SELECT c.*,
                       CASE
                           WHEN c.is_anonymous = 1 THEN 'Anonymous'
                           ELSE u.username
                       END as display_name,
                       u.username,
                       u.avatar,
                       u.bio,
                       usi.sync_uuid,
                       usi.original_username,
                       usi.device_name
                FROM wall_comments c
                LEFT JOIN users u ON c.user_id = u.id
                LEFT JOIN user_sync_info usi ON u.id = usi.user_id
                ORDER BY c.created_at ASC
                """
            )

            # Add hash to each post and include enhanced user info
            for post in posts:
                post["hash"] = self._calculate_post_hash(post)
                # Include enhanced user information for proper sync
                post["user_info"] = {
                    "username": post.get("username", "Unknown"),
                    "original_username": post.get(
                        "original_username", post.get("username", "Unknown")
                    ),
                    "avatar": post.get("avatar", ""),
                    "bio": post.get("bio", ""),
                    "display_name": post.get("display_name", "Unknown"),
                    "sync_uuid": post.get("sync_uuid"),
                    "device_name": post.get("device_name", "Unknown"),
                }

            # Add hash to each comment and include enhanced user info
            for comment in comments:
                comment["hash"] = self._calculate_comment_hash(comment)
                # Include enhanced user information for proper sync
                comment["user_info"] = {
                    "username": comment.get("username", "Unknown"),
                    "original_username": comment.get(
                        "original_username", comment.get("username", "Unknown")
                    ),
                    "avatar": comment.get("avatar", ""),
                    "bio": comment.get("bio", ""),
                    "display_name": comment.get("display_name", "Unknown"),
                    "sync_uuid": comment.get("sync_uuid"),
                    "device_name": comment.get("device_name", "Unknown"),
                }

            # Create export data with enhanced metadata
            export_data = {
                "version": self.version,
                "export_date": datetime.now().isoformat(),
                "export_device": os.uname().nodename,
                "posts": posts,
                "comments": comments,
                "metadata": {
                    "total_posts": len(posts),
                    "total_comments": len(comments),
                    "last_modified": datetime.now().isoformat(),
                    "format_version": self.version,
                },
            }

            # Create export file
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            export_file = os.path.join(self.sync_dir, f"wall_export_{timestamp}.json")

            with open(export_file, "w", encoding="utf-8") as f:
                json.dump(export_data, f, ensure_ascii=False, indent=2)

            # Clean up old exports
            self.cleanup_old_exports()

            return export_file
        except Exception as e:
            logging.error(f"Error exporting data: {e}")
            return None

    def import_data(self, import_file):
        """
        Import wall posts from a JSON file.
        Enhanced to handle ID conflicts and better user synchronization.

        Args:
            import_file (str): Path to the import file

        Returns:
            tuple: (bool, dict) - Success status and import statistics
        """
        try:
            with open(import_file, "r", encoding="utf-8") as f:
                import_data = json.load(f)

            # Verify data format
            if not isinstance(import_data, dict) or "posts" not in import_data:
                raise ValueError("Invalid import file format")

            # Check version compatibility
            if import_data.get("version", "1.0") != self.version:
                logging.warning(
                    f"Importing data from version {import_data.get('version', '1.0')}, current version is {self.version}"
                )

            # Get current user ID for likes
            current_user_id = self._get_current_user_id()
            if not current_user_id:
                logging.warning(
                    "No current user found, imported posts will not be auto-liked"
                )

            stats = {
                "total": len(import_data["posts"]),
                "imported": 0,
                "skipped": 0,
                "conflicts": 0,
                "users_created": 0,
                "comments_total": len(import_data.get("comments", [])),
                "comments_imported": 0,
                "comments_skipped": 0,
                "comments_conflicts": 0,
                "id_mapping": {},  # Track ID mapping for comments
            }

            # Import posts
            for post in import_data["posts"]:
                try:
                    original_post_id = post["id"]

                    # Check if a post with the same hash already exists (to avoid duplicates)
                    post_hash = post.get("hash", self._calculate_post_hash(post))
                    existing_by_hash = self.db_manager.execute_query(
                        """
                        SELECT w.id, w.content, w.created_at, w.user_id
                        FROM kindness_wall w
                        WHERE w.content = ? AND w.created_at = ?
                        """,
                        (post["content"], post["created_at"]),
                    )

                    if existing_by_hash:
                        # Post with same content and timestamp exists, likely duplicate
                        existing_post = existing_by_hash[0]
                        existing_hash = self._calculate_post_hash(existing_post)

                        if existing_hash == post_hash:
                            stats["skipped"] += 1
                            stats["id_mapping"][original_post_id] = existing_post["id"]
                            continue

                    # Handle user for the post
                    target_user_id = None
                    user_created = False

                    if post.get("user_info"):
                        # Try to create/find user from user_info
                        existing_user_count = self.db_manager.execute_query(
                            "SELECT COUNT(*) as count FROM users WHERE username = ?",
                            (post["user_info"].get("username", "Unknown"),),
                        )[0]["count"]

                        target_user_id = self._ensure_user_exists(post["user_info"])

                        if target_user_id:
                            # Check if this was a new user creation
                            new_user_count = self.db_manager.execute_query(
                                "SELECT COUNT(*) as count FROM users WHERE username LIKE ?",
                                (f"{post['user_info'].get('username', 'Unknown')}%",),
                            )[0]["count"]

                            if new_user_count > existing_user_count:
                                user_created = True

                    # If user_info didn't work, try to handle the original user_id
                    if target_user_id is None:
                        # Check if original user_id exists
                        existing_user = self.db_manager.execute_query(
                            "SELECT id FROM users WHERE id = ?", (post["user_id"],)
                        )

                        if existing_user:
                            target_user_id = post["user_id"]
                        else:
                            # For posts without user_info, create a placeholder user
                            # This preserves the original post authorship instead of making everything anonymous
                            placeholder_user_info = {
                                "username": f"user_{post['user_id']}",
                                "original_username": f"user_{post['user_id']}",
                                "bio": "同步用户（原用户信息不完整）",
                                "sync_uuid": None,
                                "device_name": "Unknown",
                                "avatar": None,
                            }

                            target_user_id = self._ensure_user_exists(
                                placeholder_user_info
                            )
                            if target_user_id:
                                user_created = True
                                logging.info(
                                    f"Created placeholder user for post {post['id']} (original user_id: {post['user_id']})"
                                )
                            else:
                                # Only fallback to current user as last resort
                                if current_user_id:
                                    target_user_id = current_user_id
                                    # Mark as anonymous since we couldn't preserve original authorship
                                    post["is_anonymous"] = 1
                                    logging.warning(
                                        f"Falling back to anonymous post for {post['id']} due to user creation failure"
                                    )
                                else:
                                    logging.error(
                                        f"Cannot import post {post['id']}: no valid user found and no current user"
                                    )
                                    stats["conflicts"] += 1
                                    continue

                    # Insert new post (let database assign new ID to avoid conflicts)
                    new_post_id = self.db_manager.execute_insert(
                        """
                        INSERT INTO kindness_wall
                        (user_id, content, image_data, created_at, likes, is_anonymous)
                        VALUES (?, ?, ?, ?, ?, ?)
                        """,
                        (
                            target_user_id,
                            post["content"],
                            post.get("image_data"),
                            post["created_at"],
                            post.get("likes", 0),
                            post.get("is_anonymous", 0),
                        ),
                    )

                    if new_post_id:
                        stats["imported"] += 1
                        stats["id_mapping"][original_post_id] = new_post_id

                        if user_created:
                            stats["users_created"] += 1

                        # Import likes (only if current user exists and likes > 0)
                        if current_user_id and post.get("likes", 0) > 0:
                            # Check if like already exists
                            existing_like = self.db_manager.execute_query(
                                "SELECT id FROM wall_likes WHERE wall_post_id = ? AND user_id = ?",
                                (new_post_id, current_user_id),
                            )

                            if not existing_like:
                                self.db_manager.execute_insert(
                                    """
                                    INSERT INTO wall_likes (wall_post_id, user_id)
                                    VALUES (?, ?)
                                    """,
                                    (new_post_id, current_user_id),
                                )
                    else:
                        stats["conflicts"] += 1

                except Exception as post_error:
                    logging.error(
                        f"Error importing post {post.get('id', 'unknown')}: {post_error}"
                    )
                    stats["conflicts"] += 1
                    continue

            # Import comments if they exist in the import data
            if "comments" in import_data and import_data["comments"]:
                for comment in import_data["comments"]:
                    try:
                        original_comment_id = comment["id"]
                        original_post_id = comment["wall_post_id"]

                        # Map the wall_post_id to the new ID if it was remapped
                        target_post_id = stats["id_mapping"].get(
                            original_post_id, original_post_id
                        )

                        # Check if the wall post exists
                        post_exists = self.db_manager.execute_query(
                            "SELECT id FROM kindness_wall WHERE id = ?",
                            (target_post_id,),
                        )

                        if not post_exists:
                            logging.warning(
                                f"Cannot import comment {comment['id']}: wall post {target_post_id} does not exist"
                            )
                            stats["comments_conflicts"] += 1
                            continue

                        # Check if a comment with the same hash already exists
                        comment_hash = comment.get(
                            "hash", self._calculate_comment_hash(comment)
                        )
                        existing_by_hash = self.db_manager.execute_query(
                            """
                            SELECT id, content, created_at
                            FROM wall_comments
                            WHERE wall_post_id = ? AND content = ? AND created_at = ?
                            """,
                            (target_post_id, comment["content"], comment["created_at"]),
                        )

                        if existing_by_hash:
                            # Comment with same content and timestamp exists, likely duplicate
                            existing_comment = existing_by_hash[0]
                            existing_hash = self._calculate_comment_hash(
                                existing_comment
                            )

                            if existing_hash == comment_hash:
                                stats["comments_skipped"] += 1
                                continue

                        # Handle user for new comment
                        target_user_id = None
                        user_created = False

                        if comment.get("user_info"):
                            # Try to create/find user from user_info
                            existing_user_count = self.db_manager.execute_query(
                                "SELECT COUNT(*) as count FROM users WHERE username = ?",
                                (comment["user_info"].get("username", "Unknown"),),
                            )[0]["count"]

                            target_user_id = self._ensure_user_exists(
                                comment["user_info"]
                            )

                            if target_user_id:
                                # Check if this was a new user creation
                                new_user_count = self.db_manager.execute_query(
                                    "SELECT COUNT(*) as count FROM users WHERE username LIKE ?",
                                    (
                                        f"{comment['user_info'].get('username', 'Unknown')}%",
                                    ),
                                )[0]["count"]

                                if new_user_count > existing_user_count:
                                    user_created = True

                        # If user_info didn't work, try to handle the original user_id
                        if target_user_id is None:
                            # Check if original user_id exists
                            existing_user = self.db_manager.execute_query(
                                "SELECT id FROM users WHERE id = ?",
                                (comment["user_id"],),
                            )

                            if existing_user:
                                target_user_id = comment["user_id"]
                            else:
                                # For comments without user_info, create a placeholder user
                                # This preserves the original comment authorship
                                placeholder_user_info = {
                                    "username": f"user_{comment['user_id']}",
                                    "original_username": f"user_{comment['user_id']}",
                                    "bio": "同步用户（原用户信息不完整）",
                                    "sync_uuid": None,
                                    "device_name": "Unknown",
                                    "avatar": None,
                                }

                                target_user_id = self._ensure_user_exists(
                                    placeholder_user_info
                                )
                                if target_user_id:
                                    user_created = True
                                    logging.info(
                                        f"Created placeholder user for comment {comment['id']} (original user_id: {comment['user_id']})"
                                    )
                                else:
                                    # Only fallback to current user as last resort
                                    if current_user_id:
                                        target_user_id = current_user_id
                                        # Mark as anonymous since we couldn't preserve original authorship
                                        comment["is_anonymous"] = 1
                                        logging.warning(
                                            f"Falling back to anonymous comment for {comment['id']} due to user creation failure"
                                        )
                                    else:
                                        logging.error(
                                            f"Cannot import comment {comment['id']}: no valid user found and no current user"
                                        )
                                        stats["comments_conflicts"] += 1
                                        continue

                        # Insert new comment (let database assign new ID)
                        new_comment_id = self.db_manager.execute_insert(
                            """
                            INSERT INTO wall_comments
                            (wall_post_id, user_id, content, created_at, likes, is_anonymous)
                            VALUES (?, ?, ?, ?, ?, ?)
                            """,
                            (
                                target_post_id,
                                target_user_id,
                                comment["content"],
                                comment["created_at"],
                                comment.get("likes", 0),
                                comment.get("is_anonymous", 0),
                            ),
                        )

                        if new_comment_id:
                            stats["comments_imported"] += 1

                            if user_created:
                                stats["users_created"] += 1

                            # Import comment likes (only if current user exists and likes > 0)
                            if current_user_id and comment.get("likes", 0) > 0:
                                # Check if like already exists
                                existing_like = self.db_manager.execute_query(
                                    "SELECT id FROM comment_likes WHERE comment_id = ? AND user_id = ?",
                                    (new_comment_id, current_user_id),
                                )

                                if not existing_like:
                                    self.db_manager.execute_insert(
                                        """
                                        INSERT INTO comment_likes (comment_id, user_id)
                                        VALUES (?, ?)
                                        """,
                                        (new_comment_id, current_user_id),
                                    )
                        else:
                            stats["comments_conflicts"] += 1

                    except Exception as comment_error:
                        logging.error(
                            f"Error importing comment {comment.get('id', 'unknown')}: {comment_error}"
                        )
                        stats["comments_conflicts"] += 1
                        continue

            # Remove id_mapping from stats before returning (internal use only)
            del stats["id_mapping"]

            return True, stats
        except Exception as e:
            logging.error(f"Error importing data: {e}")
            return False, None

    def get_export_files(self):
        """
        Get list of available export files.

        Returns:
            list: List of export file paths
        """
        try:
            files = []
            for file in os.listdir(self.sync_dir):
                if file.startswith("wall_export_") and file.endswith(".json"):
                    files.append(os.path.join(self.sync_dir, file))
            return sorted(files, reverse=True)
        except Exception as e:
            logging.error(f"Error getting export files: {e}")
            return []

    def cleanup_old_exports(self, keep_last=5):
        """
        Clean up old export files, keeping only the most recent ones.

        Args:
            keep_last (int): Number of most recent files to keep
        """
        try:
            files = self.get_export_files()
            for file in files[keep_last:]:
                os.remove(file)
        except Exception as e:
            logging.error(f"Error cleaning up old exports: {e}")

    def get_sync_stats(self):
        """
        Get synchronization statistics.

        Returns:
            dict: Statistics about the sync data
        """
        try:
            total_posts = self.db_manager.execute_query(
                "SELECT COUNT(*) as count FROM kindness_wall"
            )[0]["count"]

            total_likes = self.db_manager.execute_query(
                "SELECT COUNT(*) as count FROM wall_likes"
            )[0]["count"]

            total_comments = self.db_manager.execute_query(
                "SELECT COUNT(*) as count FROM wall_comments"
            )[0]["count"]

            total_comment_likes = self.db_manager.execute_query(
                "SELECT COUNT(*) as count FROM comment_likes"
            )[0]["count"]

            latest_post = self.db_manager.execute_query(
                "SELECT created_at FROM kindness_wall ORDER BY created_at DESC LIMIT 1"
            )

            latest_comment = self.db_manager.execute_query(
                "SELECT created_at FROM wall_comments ORDER BY created_at DESC LIMIT 1"
            )

            return {
                "total_posts": total_posts,
                "total_likes": total_likes,
                "total_comments": total_comments,
                "total_comment_likes": total_comment_likes,
                "latest_post": latest_post[0]["created_at"] if latest_post else None,
                "latest_comment": (
                    latest_comment[0]["created_at"] if latest_comment else None
                ),
            }
        except Exception as e:
            logging.error(f"Error getting sync stats: {e}")
            return None

    def initialize_all_users_sync(self):
        """Initialize sync UUIDs for all existing users who don't have one."""
        try:
            # Get all users without sync info
            users_without_sync = self.db_manager.execute_query(
                """
                SELECT u.id, u.username
                FROM users u
                LEFT JOIN user_sync_info usi ON u.id = usi.user_id
                WHERE usi.user_id IS NULL
                """
            )

            initialized_count = 0
            for user in users_without_sync:
                sync_uuid = self.initialize_sync_for_user(user["id"])
                if sync_uuid:
                    initialized_count += 1

            logging.info(f"Initialized sync for {initialized_count} users")
            return initialized_count

        except Exception as e:
            logging.error(f"Error initializing sync for all users: {e}")
            return 0

    def get_sync_status_summary(self):
        """Get a summary of sync status for the current database."""
        try:
            total_users = self.db_manager.execute_query(
                "SELECT COUNT(*) as count FROM users"
            )[0]["count"]

            users_with_sync = self.db_manager.execute_query(
                "SELECT COUNT(*) as count FROM user_sync_info"
            )[0]["count"]

            total_posts = self.db_manager.execute_query(
                "SELECT COUNT(*) as count FROM kindness_wall"
            )[0]["count"]

            total_comments = self.db_manager.execute_query(
                "SELECT COUNT(*) as count FROM wall_comments"
            )[0]["count"]

            return {
                "total_users": total_users,
                "users_with_sync": users_with_sync,
                "users_without_sync": total_users - users_with_sync,
                "total_posts": total_posts,
                "total_comments": total_comments,
                "sync_ready": users_with_sync == total_users,
            }

        except Exception as e:
            logging.error(f"Error getting sync status summary: {e}")
            return None

    def _ensure_user_exists(self, user_data):
        """
        Ensure a user exists in the database, create if not exists.
        Enhanced to handle user identification via sync_uuid and username combination.
        Improved to preserve original user identity for proper multi-user sync.

        Args:
            user_data (dict): User information from export

        Returns:
            int: User ID (existing or newly created)
        """
        try:
            sync_uuid = user_data.get("sync_uuid")
            username = user_data.get("username", "Unknown")
            original_username = user_data.get("original_username", username)

            # First try to find user by sync_uuid (most reliable method)
            if sync_uuid:
                existing_user = self.db_manager.execute_query(
                    """
                    SELECT u.id, u.username, u.avatar, u.bio
                    FROM users u
                    JOIN user_sync_info usi ON u.id = usi.user_id
                    WHERE usi.sync_uuid = ?
                    """,
                    (sync_uuid,),
                )

                if existing_user:
                    user_id = existing_user[0]["id"]
                    # Update user info if needed (but preserve identity)
                    self._update_user_if_needed(user_id, user_data, existing_user[0])
                    logging.info(
                        f"Found existing user by sync_uuid: {username} (ID: {user_id})"
                    )
                    return user_id

            # Try to find by exact username match, but be more careful about uniqueness
            existing_user = self.db_manager.execute_query(
                "SELECT id, username, avatar, bio FROM users WHERE username = ?",
                (username,),
            )

            if existing_user:
                user_id = existing_user[0]["id"]
                # Only update if this is likely the same user (has sync info or similar data)
                if sync_uuid:
                    # Update user info and create/update sync info
                    self._update_user_if_needed(user_id, user_data, existing_user[0])

                    # Create or update sync info
                    existing_sync = self.db_manager.execute_query(
                        "SELECT id FROM user_sync_info WHERE user_id = ?", (user_id,)
                    )
                    if not existing_sync:
                        self.db_manager.execute_insert(
                            """
                            INSERT INTO user_sync_info (user_id, sync_uuid, original_username, device_name)
                            VALUES (?, ?, ?, ?)
                            """,
                            (
                                user_id,
                                sync_uuid,
                                original_username,
                                user_data.get("device_name", "Unknown"),
                            ),
                        )
                        logging.info(
                            f"Added sync info for existing user: {username} (ID: {user_id})"
                        )
                    else:
                        # Update existing sync info if needed
                        self.db_manager.execute_update(
                            """
                            UPDATE user_sync_info
                            SET sync_uuid = ?, original_username = ?, device_name = ?, last_sync = CURRENT_TIMESTAMP
                            WHERE user_id = ?
                            """,
                            (
                                sync_uuid,
                                original_username,
                                user_data.get("device_name", "Unknown"),
                                user_id,
                            ),
                        )
                        logging.info(
                            f"Updated sync info for existing user: {username} (ID: {user_id})"
                        )

                return user_id

            # Create a new user for sync - this is crucial for multi-user support
            # Generate a unique username to avoid conflicts
            final_username = self._generate_unique_username(username, original_username)

            user_id = self.db_manager.execute_insert(
                """
                INSERT INTO users (username, password_hash, email, avatar_path, bio, avatar, ai_consent_given)
                VALUES (?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    final_username,
                    "synced_user:no_password",  # Placeholder password hash for synced users
                    None,  # No email for synced users
                    ":/images/profilePicture.png",  # Default avatar path
                    user_data.get(
                        "bio", f"来自 {user_data.get('device_name', '其他设备')} 的用户"
                    ),
                    user_data.get("avatar", None),  # Avatar blob if available
                    1,  # AI consent given
                ),
            )

            # Create sync info for the new user
            if user_id and sync_uuid:
                self.db_manager.execute_insert(
                    """
                    INSERT INTO user_sync_info (user_id, sync_uuid, original_username, device_name)
                    VALUES (?, ?, ?, ?)
                    """,
                    (
                        user_id,
                        sync_uuid,
                        original_username,
                        user_data.get("device_name", "Unknown"),
                    ),
                )

            logging.info(
                f"Created new synced user: {final_username} (ID: {user_id}, Original: {original_username})"
            )
            return user_id

        except Exception as e:
            logging.error(f"Error ensuring user exists: {e}")
            return None

    def _generate_unique_username(self, preferred_username, original_username):
        """Generate a unique username for synced users."""
        base_username = preferred_username
        counter = 1

        while True:
            if counter == 1:
                test_username = base_username
            else:
                test_username = f"{base_username}_sync{counter}"

            existing = self.db_manager.execute_query(
                "SELECT id FROM users WHERE username = ?", (test_username,)
            )

            if not existing:
                return test_username

            counter += 1
            if counter > 100:  # Prevent infinite loop
                return f"{base_username}_{uuid.uuid4().hex[:8]}"

    def _update_user_if_needed(self, user_id, new_user_data, existing_user_data):
        """Update user information if the imported data is more recent or different."""
        try:
            updates = {}
            params = []

            # Update avatar if provided and different
            new_avatar = new_user_data.get("avatar")
            if new_avatar and new_avatar != existing_user_data.get("avatar"):
                updates["avatar"] = "?"
                params.append(new_avatar)

            # Update bio if provided and different
            new_bio = new_user_data.get("bio")
            if new_bio and new_bio != existing_user_data.get("bio"):
                # Only update if the new bio is not the default sync message
                if not new_bio.startswith("Synced user from"):
                    updates["bio"] = "?"
                    params.append(new_bio)

            if updates:
                set_clause = ", ".join([f"{key} = ?" for key in updates.keys()])
                query = f"UPDATE users SET {set_clause} WHERE id = ?"
                params.append(user_id)

                self.db_manager.execute_update(query, tuple(params))
                logging.info(f"Updated user {user_id} with sync data")

        except Exception as e:
            logging.error(f"Error updating user {user_id}: {e}")

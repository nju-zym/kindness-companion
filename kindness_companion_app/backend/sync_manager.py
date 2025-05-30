import os
import json
import shutil
import logging
from datetime import datetime
from pathlib import Path
import hashlib


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
        self.version = "1.2"  # Updated version for better sync support

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

    def _ensure_user_exists(self, user_data):
        """
        Ensure a user exists in the database, create if not exists.

        Args:
            user_data (dict): User information from export

        Returns:
            int: User ID (existing or newly created)
        """
        try:
            # Check if user already exists by username
            existing_user = self.db_manager.execute_query(
                "SELECT id FROM users WHERE username = ?",
                (user_data.get("username", "Unknown"),),
            )

            if existing_user:
                return existing_user[0]["id"]

            # Create a new user for sync (using minimal required fields)
            user_id = self.db_manager.execute_insert(
                """
                INSERT INTO users (username, password_hash, email, avatar_path, bio, avatar, ai_consent_given)
                VALUES (?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    user_data.get("username", "Unknown"),
                    "synced_user:no_password",  # Placeholder password hash for synced users
                    None,  # No email for synced users
                    ":/images/profilePicture.png",  # Default avatar path
                    f"Synced user from export",  # Bio indicating this is a synced user
                    user_data.get("avatar", None),  # Avatar blob if available
                    1,  # AI consent given
                ),
            )

            logging.info(
                f"Created synced user: {user_data.get('username', 'Unknown')} (ID: {user_id})"
            )
            return user_id

        except Exception as e:
            logging.error(f"Error ensuring user exists: {e}")
            # Return None to indicate failure
            return None

    def _get_current_user_id(self):
        """
        Get the current user's ID.

        Returns:
            int: Current user ID or None if not logged in
        """
        try:
            current_user = self.db_manager.execute_query(
                "SELECT id FROM users WHERE is_logged_in = 1 LIMIT 1"
            )
            return current_user[0]["id"] if current_user else None
        except Exception as e:
            logging.error(f"Error getting current user ID: {e}")
            return None

    def export_data(self):
        """
        Export wall posts and comments to a JSON file for sharing.

        Returns:
            str: Path to the exported file
        """
        try:
            # Get all posts with user information
            posts = self.db_manager.execute_query(
                """
                SELECT w.*,
                       CASE
                           WHEN w.is_anonymous = 1 THEN 'Anonymous'
                           ELSE u.username
                       END as display_name,
                       u.username,
                       u.avatar
                FROM kindness_wall w
                LEFT JOIN users u ON w.user_id = u.id
                ORDER BY w.created_at DESC
                """
            )

            # Get all comments with user information
            comments = self.db_manager.execute_query(
                """
                SELECT c.*,
                       CASE
                           WHEN c.is_anonymous = 1 THEN 'Anonymous'
                           ELSE u.username
                       END as display_name,
                       u.username,
                       u.avatar
                FROM wall_comments c
                LEFT JOIN users u ON c.user_id = u.id
                ORDER BY c.created_at ASC
                """
            )

            # Add hash to each post and include user info
            for post in posts:
                post["hash"] = self._calculate_post_hash(post)
                # Include user information for proper sync
                post["user_info"] = {
                    "username": post.get("username", "Unknown"),
                    "avatar": post.get("avatar", ""),
                    "display_name": post.get("display_name", "Unknown"),
                }

            # Add hash to each comment and include user info
            for comment in comments:
                comment["hash"] = self._calculate_comment_hash(comment)
                # Include user information for proper sync
                comment["user_info"] = {
                    "username": comment.get("username", "Unknown"),
                    "avatar": comment.get("avatar", ""),
                    "display_name": comment.get("display_name", "Unknown"),
                }

            # Create export data
            export_data = {
                "version": self.version,
                "export_date": datetime.now().isoformat(),
                "posts": posts,
                "comments": comments,
                "metadata": {
                    "total_posts": len(posts),
                    "total_comments": len(comments),
                    "last_modified": datetime.now().isoformat(),
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
            }

            # Import posts
            for post in import_data["posts"]:
                try:
                    # Check if post already exists
                    existing = self.db_manager.execute_query(
                        "SELECT id, content, image_data, created_at FROM kindness_wall WHERE id = ?",
                        (post["id"],),
                    )

                    if existing:
                        # Check for conflicts
                        existing_post = existing[0]
                        existing_hash = self._calculate_post_hash(existing_post)
                        new_hash = post.get("hash", self._calculate_post_hash(post))

                        if existing_hash != new_hash:
                            # Conflict detected - keep the newer version
                            existing_date = datetime.fromisoformat(
                                existing_post["created_at"]
                            )
                            new_date = datetime.fromisoformat(post["created_at"])

                            if new_date > existing_date:
                                # Get or create user for this post
                                if post.get("user_info"):
                                    target_user_id = self._ensure_user_exists(
                                        post["user_info"]
                                    )
                                    if target_user_id is None:
                                        logging.error(
                                            f"Failed to create user for post {post['id']}"
                                        )
                                        stats["conflicts"] += 1
                                        continue
                                else:
                                    target_user_id = post["user_id"]

                                # Update existing post
                                self.db_manager.execute_update(
                                    """
                                    UPDATE kindness_wall
                                    SET content = ?, image_data = ?, created_at = ?, likes = ?, is_anonymous = ?, user_id = ?
                                    WHERE id = ?
                                    """,
                                    (
                                        post["content"],
                                        post.get("image_data"),
                                        post["created_at"],
                                        post.get("likes", 0),
                                        post.get("is_anonymous", 0),
                                        target_user_id,
                                        post["id"],
                                    ),
                                )
                                stats["imported"] += 1
                            else:
                                stats["conflicts"] += 1
                        else:
                            stats["skipped"] += 1
                    else:
                        # Handle user for new post
                        target_user_id = None

                        if post.get("user_info"):
                            # Try to create/find user from user_info
                            target_user_id = self._ensure_user_exists(post["user_info"])
                            if target_user_id and target_user_id != post.get("user_id"):
                                stats["users_created"] += 1

                        if target_user_id is None:
                            # Check if original user_id exists
                            existing_user = self.db_manager.execute_query(
                                "SELECT id FROM users WHERE id = ?", (post["user_id"],)
                            )

                            if existing_user:
                                target_user_id = post["user_id"]
                            else:
                                # Create anonymous post if user doesn't exist
                                if current_user_id:
                                    target_user_id = current_user_id
                                    # Mark as anonymous since original user doesn't exist
                                    post["is_anonymous"] = 1
                                else:
                                    logging.error(
                                        f"Cannot import post {post['id']}: no valid user found"
                                    )
                                    stats["conflicts"] += 1
                                    continue

                        # Insert new post
                        self.db_manager.execute_insert(
                            """
                            INSERT INTO kindness_wall
                            (id, user_id, content, image_data, created_at, likes, is_anonymous)
                            VALUES (?, ?, ?, ?, ?, ?, ?)
                            """,
                            (
                                post["id"],
                                target_user_id,
                                post["content"],
                                post.get("image_data"),
                                post["created_at"],
                                post.get("likes", 0),
                                post.get("is_anonymous", 0),
                            ),
                        )
                        stats["imported"] += 1

                        # Import likes (only if current user exists and likes > 0)
                        if current_user_id and post.get("likes", 0) > 0:
                            # Check if like already exists
                            existing_like = self.db_manager.execute_query(
                                "SELECT id FROM wall_likes WHERE wall_post_id = ? AND user_id = ?",
                                (post["id"], current_user_id),
                            )

                            if not existing_like:
                                self.db_manager.execute_insert(
                                    """
                                    INSERT INTO wall_likes (wall_post_id, user_id)
                                    VALUES (?, ?)
                                    """,
                                    (post["id"], current_user_id),
                                )

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
                        # Check if comment already exists
                        existing_comment = self.db_manager.execute_query(
                            "SELECT id, content, created_at FROM wall_comments WHERE id = ?",
                            (comment["id"],),
                        )

                        if existing_comment:
                            # Check for conflicts
                            existing_comment_data = existing_comment[0]
                            existing_hash = self._calculate_comment_hash(
                                existing_comment_data
                            )
                            new_hash = comment.get(
                                "hash", self._calculate_comment_hash(comment)
                            )

                            if existing_hash != new_hash:
                                # Conflict detected - keep the newer version
                                existing_date = datetime.fromisoformat(
                                    existing_comment_data["created_at"]
                                )
                                new_date = datetime.fromisoformat(comment["created_at"])

                                if new_date > existing_date:
                                    # Get or create user for this comment
                                    if comment.get("user_info"):
                                        target_user_id = self._ensure_user_exists(
                                            comment["user_info"]
                                        )
                                        if target_user_id is None:
                                            logging.error(
                                                f"Failed to create user for comment {comment['id']}"
                                            )
                                            stats["comments_conflicts"] += 1
                                            continue
                                    else:
                                        target_user_id = comment["user_id"]

                                    # Update existing comment
                                    self.db_manager.execute_update(
                                        """
                                        UPDATE wall_comments
                                        SET content = ?, created_at = ?, likes = ?, is_anonymous = ?, user_id = ?
                                        WHERE id = ?
                                        """,
                                        (
                                            comment["content"],
                                            comment["created_at"],
                                            comment.get("likes", 0),
                                            comment.get("is_anonymous", 0),
                                            target_user_id,
                                            comment["id"],
                                        ),
                                    )
                                    stats["comments_imported"] += 1
                                else:
                                    stats["comments_conflicts"] += 1
                            else:
                                stats["comments_skipped"] += 1
                        else:
                            # Check if the wall post exists for this comment
                            post_exists = self.db_manager.execute_query(
                                "SELECT id FROM kindness_wall WHERE id = ?",
                                (comment["wall_post_id"],),
                            )

                            if not post_exists:
                                logging.warning(
                                    f"Cannot import comment {comment['id']}: wall post {comment['wall_post_id']} does not exist"
                                )
                                stats["comments_conflicts"] += 1
                                continue

                            # Handle user for new comment
                            target_user_id = None

                            if comment.get("user_info"):
                                # Try to create/find user from user_info
                                target_user_id = self._ensure_user_exists(
                                    comment["user_info"]
                                )
                                if target_user_id and target_user_id != comment.get(
                                    "user_id"
                                ):
                                    stats["users_created"] += 1

                            if target_user_id is None:
                                # Check if original user_id exists
                                existing_user = self.db_manager.execute_query(
                                    "SELECT id FROM users WHERE id = ?",
                                    (comment["user_id"],),
                                )

                                if existing_user:
                                    target_user_id = comment["user_id"]
                                else:
                                    # Create anonymous comment if user doesn't exist
                                    if current_user_id:
                                        target_user_id = current_user_id
                                        # Mark as anonymous since original user doesn't exist
                                        comment["is_anonymous"] = 1
                                    else:
                                        logging.error(
                                            f"Cannot import comment {comment['id']}: no valid user found"
                                        )
                                        stats["comments_conflicts"] += 1
                                        continue

                            # Insert new comment
                            self.db_manager.execute_insert(
                                """
                                INSERT INTO wall_comments
                                (id, wall_post_id, user_id, content, created_at, likes, is_anonymous)
                                VALUES (?, ?, ?, ?, ?, ?, ?)
                                """,
                                (
                                    comment["id"],
                                    comment["wall_post_id"],
                                    target_user_id,
                                    comment["content"],
                                    comment["created_at"],
                                    comment.get("likes", 0),
                                    comment.get("is_anonymous", 0),
                                ),
                            )
                            stats["comments_imported"] += 1

                            # Import comment likes (only if current user exists and likes > 0)
                            if current_user_id and comment.get("likes", 0) > 0:
                                # Check if like already exists
                                existing_like = self.db_manager.execute_query(
                                    "SELECT id FROM comment_likes WHERE comment_id = ? AND user_id = ?",
                                    (comment["id"], current_user_id),
                                )

                                if not existing_like:
                                    self.db_manager.execute_insert(
                                        """
                                        INSERT INTO comment_likes (comment_id, user_id)
                                        VALUES (?, ?)
                                        """,
                                        (comment["id"], current_user_id),
                                    )

                    except Exception as comment_error:
                        logging.error(
                            f"Error importing comment {comment.get('id', 'unknown')}: {comment_error}"
                        )
                        stats["comments_conflicts"] += 1
                        continue

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

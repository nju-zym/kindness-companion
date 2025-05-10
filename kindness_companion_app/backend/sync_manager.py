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
        self.version = "1.1"  # Current version of sync format

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

    def export_data(self):
        """
        Export wall posts to a JSON file for sharing.

        Returns:
            str: Path to the exported file
        """
        try:
            # Get all posts
            posts = self.db_manager.execute_query(
                """
                SELECT w.*, 
                       CASE 
                           WHEN w.is_anonymous = 1 THEN 'Anonymous'
                           ELSE u.username 
                       END as display_name,
                       u.avatar
                FROM kindness_wall w
                LEFT JOIN users u ON w.user_id = u.id
                ORDER BY w.created_at DESC
                """
            )

            # Add hash to each post
            for post in posts:
                post["hash"] = self._calculate_post_hash(post)

            # Create export data
            export_data = {
                "version": self.version,
                "export_date": datetime.now().isoformat(),
                "posts": posts,
                "metadata": {
                    "total_posts": len(posts),
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

            stats = {
                "total": len(import_data["posts"]),
                "imported": 0,
                "skipped": 0,
                "conflicts": 0,
            }

            # Import posts
            for post in import_data["posts"]:
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
                            # Update existing post
                            self.db_manager.execute_update(
                                """
                                UPDATE kindness_wall 
                                SET content = ?, image_data = ?, created_at = ?, likes = ?, is_anonymous = ?
                                WHERE id = ?
                                """,
                                (
                                    post["content"],
                                    post.get("image_data"),
                                    post["created_at"],
                                    post.get("likes", 0),
                                    post.get("is_anonymous", 0),
                                    post["id"],
                                ),
                            )
                            stats["imported"] += 1
                        else:
                            stats["conflicts"] += 1
                    else:
                        stats["skipped"] += 1
                else:
                    # Insert new post
                    self.db_manager.execute_insert(
                        """
                        INSERT INTO kindness_wall 
                        (id, user_id, content, image_data, created_at, likes, is_anonymous)
                        VALUES (?, ?, ?, ?, ?, ?, ?)
                        """,
                        (
                            post["id"],
                            post["user_id"],
                            post["content"],
                            post.get("image_data"),
                            post["created_at"],
                            post.get("likes", 0),
                            post.get("is_anonymous", 0),
                        ),
                    )
                    stats["imported"] += 1

                    # Import likes
                    if "likes" in post and post["likes"] > 0:
                        self.db_manager.execute_insert(
                            """
                            INSERT INTO wall_likes (wall_post_id, user_id)
                            VALUES (?, ?)
                            """,
                            (post["id"], post["user_id"]),
                        )

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

            latest_post = self.db_manager.execute_query(
                "SELECT created_at FROM kindness_wall ORDER BY created_at DESC LIMIT 1"
            )

            return {
                "total_posts": total_posts,
                "total_likes": total_likes,
                "latest_post": latest_post[0]["created_at"] if latest_post else None,
            }
        except Exception as e:
            logging.error(f"Error getting sync stats: {e}")
            return None

import datetime
from PIL import Image
import io
from .database_manager import DatabaseManager


class WallManager:
    """
    Manages the kindness wall functionality.
    """

    def __init__(self, db_manager=None):
        """
        Initialize the wall manager.

        Args:
            db_manager (DatabaseManager, optional): Database manager instance.
                If None, a new instance will be created.
        """
        self.db_manager = db_manager or DatabaseManager()
        self._initialize_tables()

    def _initialize_tables(self):
        """Initialize the database tables for the kindness wall."""
        try:
            # Create kindness_wall table
            self.db_manager.execute_query(
                """
                CREATE TABLE IF NOT EXISTS kindness_wall (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER NOT NULL,
                    content TEXT NOT NULL,
                    image_data BLOB,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    likes INTEGER DEFAULT 0,
                    is_anonymous BOOLEAN DEFAULT 0,
                    FOREIGN KEY (user_id) REFERENCES users (id)
                )
            """
            )

            # Create wall_likes table
            self.db_manager.execute_query(
                """
                CREATE TABLE IF NOT EXISTS wall_likes (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    wall_post_id INTEGER NOT NULL,
                    user_id INTEGER NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (wall_post_id) REFERENCES kindness_wall (id),
                    FOREIGN KEY (user_id) REFERENCES users (id),
                    UNIQUE (wall_post_id, user_id)
                )
            """
            )

            # Create wall_comments table
            self.db_manager.execute_query(
                """
                CREATE TABLE IF NOT EXISTS wall_comments (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    wall_post_id INTEGER NOT NULL,
                    user_id INTEGER NOT NULL,
                    content TEXT NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    likes INTEGER DEFAULT 0,
                    is_anonymous BOOLEAN DEFAULT 0,
                    FOREIGN KEY (wall_post_id) REFERENCES kindness_wall (id) ON DELETE CASCADE,
                    FOREIGN KEY (user_id) REFERENCES users (id)
                )
            """
            )

            # Create comment_likes table
            self.db_manager.execute_query(
                """
                CREATE TABLE IF NOT EXISTS comment_likes (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    comment_id INTEGER NOT NULL,
                    user_id INTEGER NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (comment_id) REFERENCES wall_comments (id) ON DELETE CASCADE,
                    FOREIGN KEY (user_id) REFERENCES users (id),
                    UNIQUE (comment_id, user_id)
                )
            """
            )
        except Exception as e:
            print(f"Error initializing wall tables: {e}")

    def _compress_image(self, image_data, max_size=(800, 800), quality=85):
        """
        Compress an image to reduce its size.

        Args:
            image_data (bytes): The original image data
            max_size (tuple): Maximum width and height
            quality (int): JPEG quality (1-100)

        Returns:
            bytes: Compressed image data
        """
        try:
            img = Image.open(io.BytesIO(image_data))
            img.thumbnail(max_size, Image.Resampling.LANCZOS)
            output = io.BytesIO()
            img.save(output, format="JPEG", quality=quality)
            return output.getvalue()
        except Exception as e:
            print(f"Error compressing image: {e}")
            return image_data

    def create_post(self, user_id, content, image_data=None, is_anonymous=False):
        """
        Create a new post on the kindness wall.

        Args:
            user_id (int): User ID
            content (str): Post content
            image_data (bytes, optional): Image data
            is_anonymous (bool): Whether to post anonymously

        Returns:
            int: ID of the created post, or None if creation failed
        """
        try:
            # Compress image if provided
            if image_data:
                image_data = self._compress_image(image_data)

            return self.db_manager.execute_insert(
                """
                INSERT INTO kindness_wall (user_id, content, image_data, is_anonymous)
                VALUES (?, ?, ?, ?)
                """,
                (user_id, content, image_data, 1 if is_anonymous else 0),
            )
        except Exception as e:
            print(f"Error creating wall post: {e}")
            return None

    def get_posts(self, limit=20, offset=0):
        """
        Get posts from the kindness wall.

        Args:
            limit (int): Maximum number of posts to return
            offset (int): Number of posts to skip

        Returns:
            list: List of post dictionaries
        """
        return self.db_manager.execute_query(
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
            LIMIT ? OFFSET ?
            """,
            (limit, offset),
        )

    def get_user_posts(self, user_id, limit=20, offset=0):
        """
        Get posts from a specific user.

        Args:
            user_id (int): User ID
            limit (int): Maximum number of posts to return
            offset (int): Number of posts to skip

        Returns:
            list: List of post dictionaries
        """
        return self.db_manager.execute_query(
            """
            SELECT w.*,
                   CASE
                       WHEN w.is_anonymous = 1 THEN 'Anonymous'
                       ELSE u.username
                   END as display_name,
                   u.avatar
            FROM kindness_wall w
            LEFT JOIN users u ON w.user_id = u.id
            WHERE w.user_id = ?
            ORDER BY w.created_at DESC
            LIMIT ? OFFSET ?
            """,
            (user_id, limit, offset),
        )

    def like_post(self, post_id, user_id):
        """
        Like a post.

        Args:
            post_id (int): Post ID
            user_id (int): User ID

        Returns:
            bool: True if successful, False otherwise
        """
        try:
            # First check if already liked
            existing_like = self.db_manager.execute_query(
                "SELECT id FROM wall_likes WHERE wall_post_id = ? AND user_id = ?",
                (post_id, user_id),
            )

            if existing_like:
                return False  # Already liked

            # Add like record
            self.db_manager.execute_insert(
                "INSERT INTO wall_likes (wall_post_id, user_id) VALUES (?, ?)",
                (post_id, user_id),
            )

            # Update post likes count
            self.db_manager.execute_update(
                "UPDATE kindness_wall SET likes = likes + 1 WHERE id = ?", (post_id,)
            )

            return True
        except Exception as e:
            print(f"Error liking post: {e}")
            return False

    def unlike_post(self, post_id, user_id):
        """
        Unlike a post.

        Args:
            post_id (int): Post ID
            user_id (int): User ID

        Returns:
            bool: True if successful, False otherwise
        """
        try:
            # Remove like record
            affected_rows = self.db_manager.execute_update(
                "DELETE FROM wall_likes WHERE wall_post_id = ? AND user_id = ?",
                (post_id, user_id),
            )

            if affected_rows > 0:
                # Update post likes count
                self.db_manager.execute_update(
                    "UPDATE kindness_wall SET likes = likes - 1 WHERE id = ?",
                    (post_id,),
                )
                return True

            return False
        except Exception as e:
            print(f"Error unliking post: {e}")
            return False

    def delete_post(self, post_id, user_id):
        """
        Delete a post.

        Args:
            post_id (int): Post ID
            user_id (int): User ID (must be the post owner)

        Returns:
            bool: True if successful, False otherwise
        """
        try:
            # First verify ownership
            post = self.db_manager.execute_query(
                "SELECT user_id FROM kindness_wall WHERE id = ?", (post_id,)
            )

            if not post or post[0]["user_id"] != user_id:
                return False

            # Delete all likes for this post
            self.db_manager.execute_update(
                "DELETE FROM wall_likes WHERE wall_post_id = ?", (post_id,)
            )

            # Delete the post
            affected_rows = self.db_manager.execute_update(
                "DELETE FROM kindness_wall WHERE id = ?", (post_id,)
            )

            return affected_rows > 0
        except Exception as e:
            print(f"Error deleting post: {e}")
            return False

    # ================== Comment Management Methods ==================

    def create_comment(self, post_id, user_id, content, is_anonymous=False):
        """
        Create a new comment on a wall post.

        Args:
            post_id (int): Wall post ID
            user_id (int): User ID
            content (str): Comment content
            is_anonymous (bool): Whether to comment anonymously

        Returns:
            int: ID of the created comment, or None if creation failed
        """
        try:
            # Verify the post exists
            post = self.db_manager.execute_query(
                "SELECT id FROM kindness_wall WHERE id = ?", (post_id,)
            )

            if not post:
                print(f"Post with ID {post_id} does not exist")
                return None

            # Create the comment
            comment_id = self.db_manager.execute_insert(
                """
                INSERT INTO wall_comments (wall_post_id, user_id, content, is_anonymous)
                VALUES (?, ?, ?, ?)
                """,
                (post_id, user_id, content, 1 if is_anonymous else 0),
            )

            return comment_id
        except Exception as e:
            print(f"Error creating comment: {e}")
            return None

    def get_comments(self, post_id, limit=50, offset=0):
        """
        Get comments for a specific wall post.

        Args:
            post_id (int): Wall post ID
            limit (int): Maximum number of comments to return
            offset (int): Number of comments to skip

        Returns:
            list: List of comment dictionaries
        """
        try:
            return self.db_manager.execute_query(
                """
                SELECT c.*,
                       CASE
                           WHEN c.is_anonymous = 1 THEN 'Anonymous'
                           ELSE u.username
                       END as display_name,
                       u.avatar
                FROM wall_comments c
                LEFT JOIN users u ON c.user_id = u.id
                WHERE c.wall_post_id = ?
                ORDER BY c.created_at ASC
                LIMIT ? OFFSET ?
                """,
                (post_id, limit, offset),
            )
        except Exception as e:
            print(f"Error getting comments: {e}")
            return []

    def get_comment_count(self, post_id):
        """
        Get the total number of comments for a post.

        Args:
            post_id (int): Wall post ID

        Returns:
            int: Number of comments
        """
        try:
            result = self.db_manager.execute_query(
                "SELECT COUNT(*) as count FROM wall_comments WHERE wall_post_id = ?",
                (post_id,),
            )
            return result[0]["count"] if result else 0
        except Exception as e:
            print(f"Error getting comment count: {e}")
            return 0

    def delete_comment(self, comment_id, user_id):
        """
        Delete a comment.

        Args:
            comment_id (int): Comment ID
            user_id (int): User ID (must be the comment author)

        Returns:
            bool: True if successful, False otherwise
        """
        try:
            # First verify ownership
            comment = self.db_manager.execute_query(
                "SELECT user_id FROM wall_comments WHERE id = ?", (comment_id,)
            )

            if not comment or comment[0]["user_id"] != user_id:
                return False

            # Delete all likes for this comment
            self.db_manager.execute_update(
                "DELETE FROM comment_likes WHERE comment_id = ?", (comment_id,)
            )

            # Delete the comment
            affected_rows = self.db_manager.execute_update(
                "DELETE FROM wall_comments WHERE id = ?", (comment_id,)
            )

            return affected_rows > 0
        except Exception as e:
            print(f"Error deleting comment: {e}")
            return False

    def like_comment(self, comment_id, user_id):
        """
        Like a comment.

        Args:
            comment_id (int): Comment ID
            user_id (int): User ID

        Returns:
            bool: True if successful, False otherwise
        """
        try:
            # First check if already liked
            existing_like = self.db_manager.execute_query(
                "SELECT id FROM comment_likes WHERE comment_id = ? AND user_id = ?",
                (comment_id, user_id),
            )

            if existing_like:
                return False  # Already liked

            # Add like record
            self.db_manager.execute_insert(
                "INSERT INTO comment_likes (comment_id, user_id) VALUES (?, ?)",
                (comment_id, user_id),
            )

            # Update comment likes count
            self.db_manager.execute_update(
                "UPDATE wall_comments SET likes = likes + 1 WHERE id = ?", (comment_id,)
            )

            return True
        except Exception as e:
            print(f"Error liking comment: {e}")
            return False

    def unlike_comment(self, comment_id, user_id):
        """
        Unlike a comment.

        Args:
            comment_id (int): Comment ID
            user_id (int): User ID

        Returns:
            bool: True if successful, False otherwise
        """
        try:
            # Remove like record
            affected_rows = self.db_manager.execute_update(
                "DELETE FROM comment_likes WHERE comment_id = ? AND user_id = ?",
                (comment_id, user_id),
            )

            if affected_rows > 0:
                # Update comment likes count
                self.db_manager.execute_update(
                    "UPDATE wall_comments SET likes = likes - 1 WHERE id = ?",
                    (comment_id,),
                )
                return True

            return False
        except Exception as e:
            print(f"Error unliking comment: {e}")
            return False

    def get_user_comments(self, user_id, limit=20, offset=0):
        """
        Get comments from a specific user.

        Args:
            user_id (int): User ID
            limit (int): Maximum number of comments to return
            offset (int): Number of comments to skip

        Returns:
            list: List of comment dictionaries with post information
        """
        try:
            return self.db_manager.execute_query(
                """
                SELECT c.*,
                       CASE
                           WHEN c.is_anonymous = 1 THEN 'Anonymous'
                           ELSE u.username
                       END as display_name,
                       u.avatar,
                       w.content as post_content,
                       w.id as post_id
                FROM wall_comments c
                LEFT JOIN users u ON c.user_id = u.id
                LEFT JOIN kindness_wall w ON c.wall_post_id = w.id
                WHERE c.user_id = ?
                ORDER BY c.created_at DESC
                LIMIT ? OFFSET ?
                """,
                (user_id, limit, offset),
            )
        except Exception as e:
            print(f"Error getting user comments: {e}")
            return []

    def check_user_liked_comment(self, comment_id, user_id):
        """
        Check if a user has liked a specific comment.

        Args:
            comment_id (int): Comment ID
            user_id (int): User ID

        Returns:
            bool: True if user has liked the comment, False otherwise
        """
        try:
            result = self.db_manager.execute_query(
                "SELECT id FROM comment_likes WHERE comment_id = ? AND user_id = ?",
                (comment_id, user_id),
            )
            return len(result) > 0
        except Exception as e:
            print(f"Error checking comment like status: {e}")
            return False

    def get_posts_with_comment_counts(self, limit=20, offset=0):
        """
        Get posts with their comment counts.

        Args:
            limit (int): Maximum number of posts to return
            offset (int): Number of posts to skip

        Returns:
            list: List of post dictionaries with comment counts
        """
        try:
            return self.db_manager.execute_query(
                """
                SELECT w.*,
                       CASE
                           WHEN w.is_anonymous = 1 THEN 'Anonymous'
                           ELSE u.username
                       END as display_name,
                       u.avatar,
                       COUNT(c.id) as comment_count
                FROM kindness_wall w
                LEFT JOIN users u ON w.user_id = u.id
                LEFT JOIN wall_comments c ON w.id = c.wall_post_id
                GROUP BY w.id
                ORDER BY w.created_at DESC
                LIMIT ? OFFSET ?
                """,
                (limit, offset),
            )
        except Exception as e:
            print(f"Error getting posts with comment counts: {e}")
            return []

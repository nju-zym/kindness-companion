import pytest
import os
import tempfile
import json
from unittest.mock import Mock, patch
from kindness_companion_app.backend.database_manager import DatabaseManager
from kindness_companion_app.backend.sync_manager import SyncManager
from kindness_companion_app.backend.user_manager import UserManager


class TestSyncManager:
    """Test cases for SyncManager multi-user functionality."""

    @pytest.fixture
    def temp_db(self):
        """Create a temporary database for testing."""
        fd, path = tempfile.mkstemp(suffix=".db")
        os.close(fd)
        yield path
        try:
            os.unlink(path)
        except FileNotFoundError:
            pass

    @pytest.fixture
    def db_manager(self, temp_db):
        """Create a database manager with temporary database."""
        db_manager = DatabaseManager(db_path=temp_db)

        # Ensure all necessary tables exist for sync manager testing
        # Create wall tables
        db_manager.execute_query(
            """
            CREATE TABLE IF NOT EXISTS kindness_wall (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                content TEXT NOT NULL,
                image_data BLOB,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                likes INTEGER DEFAULT 0,
                is_anonymous INTEGER DEFAULT 0,
                FOREIGN KEY (user_id) REFERENCES users (id)
            )
        """
        )

        db_manager.execute_query(
            """
            CREATE TABLE IF NOT EXISTS wall_comments (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                wall_post_id INTEGER NOT NULL,
                user_id INTEGER NOT NULL,
                content TEXT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                likes INTEGER DEFAULT 0,
                is_anonymous INTEGER DEFAULT 0,
                FOREIGN KEY (wall_post_id) REFERENCES kindness_wall (id),
                FOREIGN KEY (user_id) REFERENCES users (id)
            )
        """
        )

        db_manager.execute_query(
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

        db_manager.execute_query(
            """
            CREATE TABLE IF NOT EXISTS comment_likes (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                comment_id INTEGER NOT NULL,
                user_id INTEGER NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (comment_id) REFERENCES wall_comments (id),
                FOREIGN KEY (user_id) REFERENCES users (id),
                UNIQUE (comment_id, user_id)
            )
        """
        )

        return db_manager

    @pytest.fixture
    def sync_manager(self, db_manager):
        """Create a sync manager instance."""
        return SyncManager(db_manager)

    @pytest.fixture
    def user_manager(self, db_manager):
        """Create a user manager instance."""
        return UserManager(db_manager)

    def test_multi_user_sync_creation(self, sync_manager, user_manager):
        """Test that sync manager can handle multiple users correctly."""
        # Create two test users
        user1_data = user_manager.register_user(
            "user1", "password123", "user1@test.com"
        )
        user2_data = user_manager.register_user(
            "user2", "password123", "user2@test.com"
        )

        assert user1_data is not None
        assert user2_data is not None

        user1_id = user1_data["id"]
        user2_id = user2_data["id"]

        # Initialize sync for both users
        sync1 = sync_manager.initialize_sync_for_user(user1_id)
        sync2 = sync_manager.initialize_sync_for_user(user2_id)

        assert sync1 is not None
        assert sync2 is not None
        assert sync1 != sync2  # Should have different sync UUIDs

    def test_user_creation_from_import_data(self, sync_manager):
        """Test that sync manager can create users from import data."""
        # Test user info data as would come from export
        user_info = {
            "username": "test_user",
            "original_username": "test_user",
            "bio": "Test user bio",
            "sync_uuid": "test-uuid-123",
            "device_name": "Test Device",
            "avatar": None,
        }

        # This should create a new user
        user_id = sync_manager._ensure_user_exists(user_info)
        assert user_id is not None

        # Verify user was created with correct info
        user_sync_info = sync_manager.get_user_sync_info(user_id)
        assert user_sync_info is not None
        assert user_sync_info["sync_uuid"] == "test-uuid-123"
        assert user_sync_info["original_username"] == "test_user"

    def test_placeholder_user_creation(self, sync_manager):
        """Test that placeholder users are created for posts without user_info."""
        # Simulate import data without complete user_info
        user_info = {
            "username": "user_42",
            "original_username": "user_42",
            "bio": "同步用户（原用户信息不完整）",
            "sync_uuid": None,
            "device_name": "Unknown",
            "avatar": None,
        }

        user_id = sync_manager._ensure_user_exists(user_info)
        assert user_id is not None

        # Check that user was created
        users = sync_manager.db_manager.execute_query(
            "SELECT username, bio FROM users WHERE id = ?", (user_id,)
        )
        assert len(users) == 1
        assert users[0]["username"] == "user_42"
        assert "原用户信息不完整" in users[0]["bio"]

    def test_sync_status_summary(self, sync_manager, user_manager):
        """Test sync status summary functionality."""
        # Create a user and check status
        user_data = user_manager.register_user("test_user", "password", "test@test.com")
        user_id = user_data["id"]

        # Before initializing sync
        status = sync_manager.get_sync_status_summary()
        assert status["total_users"] == 1
        assert status["users_with_sync"] == 0
        assert status["sync_ready"] == False

        # After initializing sync
        sync_manager.initialize_sync_for_user(user_id)
        status = sync_manager.get_sync_status_summary()
        assert status["users_with_sync"] == 1
        assert status["sync_ready"] == True

    @patch("os.uname")
    def test_export_includes_all_users(self, mock_uname, sync_manager, user_manager):
        """Test that export includes posts from all users, not just current user."""
        mock_uname.return_value = Mock(nodename="test-device")

        # Create multiple users
        user1_data = user_manager.register_user("user1", "pass1", "user1@test.com")
        user2_data = user_manager.register_user("user2", "pass2", "user2@test.com")

        user1_id = user1_data["id"]
        user2_id = user2_data["id"]

        # Initialize sync for both
        sync_manager.initialize_sync_for_user(user1_id)
        sync_manager.initialize_sync_for_user(user2_id)

        # Create posts for both users
        from kindness_companion_app.backend.wall_manager import WallManager

        wall_manager = WallManager(sync_manager.db_manager)

        post1_id = wall_manager.create_post(user1_id, "Post by user1", None, False)
        post2_id = wall_manager.create_post(user2_id, "Post by user2", None, False)

        assert post1_id is not None
        assert post2_id is not None

        # Export data
        export_file = sync_manager.export_data()
        assert export_file is not None
        assert os.path.exists(export_file)

        # Read and verify export contains both users' posts
        with open(export_file, "r", encoding="utf-8") as f:
            export_data = json.load(f)

        assert len(export_data["posts"]) == 2
        post_contents = [post["content"] for post in export_data["posts"]]
        assert "Post by user1" in post_contents
        assert "Post by user2" in post_contents

        # Clean up
        os.unlink(export_file)


if __name__ == "__main__":
    pytest.main([__file__])

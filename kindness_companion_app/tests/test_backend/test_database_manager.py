import unittest
import os
import tempfile
import sqlite3
import sys
from pathlib import Path

# Add the parent directory to sys.path to allow importing the modules
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

from backend.database_manager import DatabaseManager

class TestDatabaseManager(unittest.TestCase):
    """Test cases for the DatabaseManager class."""

    def setUp(self):
        """Set up a temporary database for testing."""
        # Create a temporary file for the test database
        self.temp_db_file = tempfile.NamedTemporaryFile(suffix='.db', delete=False)
        self.temp_db_file.close()
        
        # Create a DatabaseManager instance with the temporary database
        self.db_manager = DatabaseManager(self.temp_db_file.name)
    
    def tearDown(self):
        """Clean up after tests."""
        # Disconnect from the database
        if self.db_manager.connection:
            self.db_manager.disconnect()
        
        # Remove the temporary database file
        if os.path.exists(self.temp_db_file.name):
            os.unlink(self.temp_db_file.name)
    
    def test_connect_disconnect(self):
        """Test connecting to and disconnecting from the database."""
        # Connect to the database
        connection = self.db_manager.connect()
        
        # Check that the connection is established
        self.assertIsNotNone(connection)
        self.assertIsNotNone(self.db_manager.cursor)
        
        # Disconnect from the database
        self.db_manager.disconnect()
        
        # Check that the connection is closed
        self.assertIsNone(self.db_manager.connection)
        self.assertIsNone(self.db_manager.cursor)
    
    def test_execute_query(self):
        """Test executing a query and returning results."""
        # Insert a test user
        self.db_manager.execute_insert(
            "INSERT INTO users (username, password_hash, email) VALUES (?, ?, ?)",
            ("test_user", "test_hash:test_salt", "test@example.com")
        )
        
        # Query the test user
        result = self.db_manager.execute_query(
            "SELECT * FROM users WHERE username = ?",
            ("test_user",)
        )
        
        # Check that the query returned the expected result
        self.assertEqual(len(result), 1)
        self.assertEqual(result[0]["username"], "test_user")
        self.assertEqual(result[0]["email"], "test@example.com")
    
    def test_execute_insert(self):
        """Test inserting a row and returning the ID."""
        # Insert a test user
        user_id = self.db_manager.execute_insert(
            "INSERT INTO users (username, password_hash, email) VALUES (?, ?, ?)",
            ("test_user", "test_hash:test_salt", "test@example.com")
        )
        
        # Check that the insert returned a valid ID
        self.assertIsNotNone(user_id)
        self.assertGreater(user_id, 0)
        
        # Query the inserted user to verify
        result = self.db_manager.execute_query(
            "SELECT * FROM users WHERE id = ?",
            (user_id,)
        )
        
        # Check that the query returned the expected result
        self.assertEqual(len(result), 1)
        self.assertEqual(result[0]["id"], user_id)
        self.assertEqual(result[0]["username"], "test_user")
    
    def test_execute_update(self):
        """Test updating a row and returning the number of affected rows."""
        # Insert a test user
        user_id = self.db_manager.execute_insert(
            "INSERT INTO users (username, password_hash, email) VALUES (?, ?, ?)",
            ("test_user", "test_hash:test_salt", "test@example.com")
        )
        
        # Update the test user
        affected_rows = self.db_manager.execute_update(
            "UPDATE users SET email = ? WHERE id = ?",
            ("updated@example.com", user_id)
        )
        
        # Check that the update affected one row
        self.assertEqual(affected_rows, 1)
        
        # Query the updated user to verify
        result = self.db_manager.execute_query(
            "SELECT * FROM users WHERE id = ?",
            (user_id,)
        )
        
        # Check that the query returned the expected result
        self.assertEqual(len(result), 1)
        self.assertEqual(result[0]["email"], "updated@example.com")
    
    def test_initialize_db(self):
        """Test that the database is initialized with the expected tables."""
        # Connect to the database
        self.db_manager.connect()
        
        # Query the sqlite_master table to get a list of tables
        self.db_manager.cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
        tables = [row[0] for row in self.db_manager.cursor.fetchall()]
        
        # Check that the expected tables exist
        expected_tables = ['users', 'challenges', 'user_challenges', 'progress', 'reminders']
        for table in expected_tables:
            self.assertIn(table, tables)
        
        # Disconnect from the database
        self.db_manager.disconnect()
    
    def test_default_challenges(self):
        """Test that default challenges are inserted during initialization."""
        # Query the challenges table
        result = self.db_manager.execute_query("SELECT * FROM challenges")
        
        # Check that there are default challenges
        self.assertGreater(len(result), 0)
        
        # Check that the challenges have the expected structure
        for challenge in result:
            self.assertIn("id", challenge)
            self.assertIn("title", challenge)
            self.assertIn("description", challenge)
            self.assertIn("category", challenge)
            self.assertIn("difficulty", challenge)

if __name__ == '__main__':
    unittest.main()

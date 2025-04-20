import sqlite3
import os
from pathlib import Path


class DatabaseManager:
    """
    Manages SQLite database connections and provides CRUD operations.
    """
    
    def __init__(self, db_path=None):
        """
        Initialize the database manager.
        
        Args:
            db_path (str, optional): Path to the SQLite database file.
                If None, a default path will be used.
        """
        if db_path is None:
            # Create a data directory in the user's home directory
            data_dir = Path.home() / ".kindness_challenge"
            data_dir.mkdir(exist_ok=True)
            db_path = data_dir / "kindness_challenge.db"
        
        self.db_path = str(db_path)
        self.connection = None
        self.cursor = None
        
        # Initialize the database
        self._initialize_db()
    
    def connect(self):
        """Establish a connection to the database."""
        self.connection = sqlite3.connect(self.db_path)
        self.connection.row_factory = sqlite3.Row  # Return rows as dictionaries
        self.cursor = self.connection.cursor()
        return self.connection
    
    def disconnect(self):
        """Close the database connection."""
        if self.connection:
            self.connection.close()
            self.connection = None
            self.cursor = None
    
    def _initialize_db(self):
        """Create database tables if they don't exist."""
        self.connect()
        
        # Create users table
        self.cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            password_hash TEXT NOT NULL,
            email TEXT UNIQUE,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            last_login TIMESTAMP
        )
        ''')
        
        # Create challenges table
        self.cursor.execute('''
        CREATE TABLE IF NOT EXISTS challenges (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT NOT NULL,
            description TEXT,
            category TEXT,
            difficulty INTEGER,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        ''')
        
        # Create user_challenges table (for subscriptions)
        self.cursor.execute('''
        CREATE TABLE IF NOT EXISTS user_challenges (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            challenge_id INTEGER,
            subscribed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users (id),
            FOREIGN KEY (challenge_id) REFERENCES challenges (id),
            UNIQUE (user_id, challenge_id)
        )
        ''')
        
        # Create progress table (for check-ins)
        self.cursor.execute('''
        CREATE TABLE IF NOT EXISTS progress (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            challenge_id INTEGER,
            check_in_date DATE,
            notes TEXT,
            FOREIGN KEY (user_id) REFERENCES users (id),
            FOREIGN KEY (challenge_id) REFERENCES challenges (id),
            UNIQUE (user_id, challenge_id, check_in_date)
        )
        ''')
        
        # Create reminders table
        self.cursor.execute('''
        CREATE TABLE IF NOT EXISTS reminders (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            challenge_id INTEGER,
            time TEXT,
            days TEXT,  -- Comma-separated days of week (0-6, where 0 is Monday)
            enabled BOOLEAN DEFAULT 1,
            FOREIGN KEY (user_id) REFERENCES users (id),
            FOREIGN KEY (challenge_id) REFERENCES challenges (id)
        )
        ''')
        
        # Insert some default challenges
        self.cursor.execute('''
        INSERT OR IGNORE INTO challenges (id, title, description, category, difficulty)
        VALUES 
            (1, '每日微笑', '对遇到的每个人微笑，传递善意', '日常行为', 1),
            (2, '扶老助残', '帮助老人或残障人士完成一项任务', '社区服务', 2),
            (3, '环保行动', '捡起路边垃圾并正确分类处理', '环保', 2),
            (4, '匿名善举', '做一件好事但不求回报或认可', '精神成长', 3),
            (5, '感恩日记', '每天写下3件你感恩的事情', '自我提升', 1)
        ''')
        
        self.connection.commit()
        self.disconnect()
    
    def execute_query(self, query, params=None):
        """
        Execute a query and return the results.
        
        Args:
            query (str): SQL query to execute
            params (tuple, optional): Parameters for the query
            
        Returns:
            list: Query results as a list of dictionaries
        """
        try:
            self.connect()
            if params:
                self.cursor.execute(query, params)
            else:
                self.cursor.execute(query)
            
            results = self.cursor.fetchall()
            self.connection.commit()
            return [dict(row) for row in results]
        finally:
            self.disconnect()
    
    def execute_insert(self, query, params=None):
        """
        Execute an insert query and return the ID of the inserted row.
        
        Args:
            query (str): SQL query to execute
            params (tuple, optional): Parameters for the query
            
        Returns:
            int: ID of the last inserted row
        """
        try:
            self.connect()
            if params:
                self.cursor.execute(query, params)
            else:
                self.cursor.execute(query)
            
            last_id = self.cursor.lastrowid
            self.connection.commit()
            return last_id
        finally:
            self.disconnect()
    
    def execute_update(self, query, params=None):
        """
        Execute an update query and return the number of affected rows.
        
        Args:
            query (str): SQL query to execute
            params (tuple, optional): Parameters for the query
            
        Returns:
            int: Number of affected rows
        """
        try:
            self.connect()
            if params:
                self.cursor.execute(query, params)
            else:
                self.cursor.execute(query)
            
            affected_rows = self.cursor.rowcount
            self.connection.commit()
            return affected_rows
        finally:
            self.disconnect()

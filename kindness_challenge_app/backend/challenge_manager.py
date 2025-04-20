from .database_manager import DatabaseManager


class ChallengeManager:
    """
    Manages challenge data and subscription operations.
    """
    
    def __init__(self, db_manager=None):
        """
        Initialize the challenge manager.
        
        Args:
            db_manager (DatabaseManager, optional): Database manager instance.
                If None, a new instance will be created.
        """
        self.db_manager = db_manager or DatabaseManager()
    
    def get_all_challenges(self):
        """
        Get all available challenges.
        
        Returns:
            list: List of challenge dictionaries
        """
        return self.db_manager.execute_query("SELECT * FROM challenges ORDER BY difficulty")
    
    def get_challenge_by_id(self, challenge_id):
        """
        Get a challenge by its ID.
        
        Args:
            challenge_id (int): Challenge ID
            
        Returns:
            dict: Challenge information, or None if not found
        """
        result = self.db_manager.execute_query(
            "SELECT * FROM challenges WHERE id = ?", 
            (challenge_id,)
        )
        
        return result[0] if result else None
    
    def get_challenges_by_category(self, category):
        """
        Get challenges by category.
        
        Args:
            category (str): Challenge category
            
        Returns:
            list: List of challenge dictionaries
        """
        return self.db_manager.execute_query(
            "SELECT * FROM challenges WHERE category = ? ORDER BY difficulty",
            (category,)
        )
    
    def get_challenges_by_difficulty(self, difficulty):
        """
        Get challenges by difficulty level.
        
        Args:
            difficulty (int): Difficulty level (1-5)
            
        Returns:
            list: List of challenge dictionaries
        """
        return self.db_manager.execute_query(
            "SELECT * FROM challenges WHERE difficulty = ? ORDER BY title",
            (difficulty,)
        )
    
    def subscribe_to_challenge(self, user_id, challenge_id):
        """
        Subscribe a user to a challenge.
        
        Args:
            user_id (int): User ID
            challenge_id (int): Challenge ID
            
        Returns:
            bool: True if subscription is successful, False otherwise
        """
        try:
            self.db_manager.execute_insert(
                "INSERT INTO user_challenges (user_id, challenge_id) VALUES (?, ?)",
                (user_id, challenge_id)
            )
            return True
        except Exception:
            return False  # Subscription failed (possibly already subscribed)
    
    def unsubscribe_from_challenge(self, user_id, challenge_id):
        """
        Unsubscribe a user from a challenge.
        
        Args:
            user_id (int): User ID
            challenge_id (int): Challenge ID
            
        Returns:
            bool: True if unsubscription is successful, False otherwise
        """
        affected_rows = self.db_manager.execute_update(
            "DELETE FROM user_challenges WHERE user_id = ? AND challenge_id = ?",
            (user_id, challenge_id)
        )
        
        return affected_rows > 0
    
    def get_user_challenges(self, user_id):
        """
        Get all challenges subscribed by a user.
        
        Args:
            user_id (int): User ID
            
        Returns:
            list: List of challenge dictionaries
        """
        return self.db_manager.execute_query(
            """
            SELECT c.* 
            FROM challenges c
            JOIN user_challenges uc ON c.id = uc.challenge_id
            WHERE uc.user_id = ?
            ORDER BY c.difficulty
            """,
            (user_id,)
        )
    
    def is_subscribed(self, user_id, challenge_id):
        """
        Check if a user is subscribed to a challenge.
        
        Args:
            user_id (int): User ID
            challenge_id (int): Challenge ID
            
        Returns:
            bool: True if subscribed, False otherwise
        """
        result = self.db_manager.execute_query(
            "SELECT * FROM user_challenges WHERE user_id = ? AND challenge_id = ?",
            (user_id, challenge_id)
        )
        
        return len(result) > 0
    
    def create_challenge(self, title, description, category, difficulty):
        """
        Create a new challenge.
        
        Args:
            title (str): Challenge title
            description (str): Challenge description
            category (str): Challenge category
            difficulty (int): Difficulty level (1-5)
            
        Returns:
            int: ID of the created challenge, or None if creation failed
        """
        return self.db_manager.execute_insert(
            """
            INSERT INTO challenges (title, description, category, difficulty)
            VALUES (?, ?, ?, ?)
            """,
            (title, description, category, difficulty)
        )

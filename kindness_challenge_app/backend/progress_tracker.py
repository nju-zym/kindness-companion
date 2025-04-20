import datetime
from .database_manager import DatabaseManager


class ProgressTracker:
    """
    Manages user progress tracking and check-ins.
    """
    
    def __init__(self, db_manager=None):
        """
        Initialize the progress tracker.
        
        Args:
            db_manager (DatabaseManager, optional): Database manager instance.
                If None, a new instance will be created.
        """
        self.db_manager = db_manager or DatabaseManager()
    
    def check_in(self, user_id, challenge_id, date=None, notes=None):
        """
        Record a check-in for a challenge.
        
        Args:
            user_id (int): User ID
            challenge_id (int): Challenge ID
            date (str, optional): Check-in date in YYYY-MM-DD format.
                If None, current date will be used.
            notes (str, optional): Additional notes for the check-in
            
        Returns:
            bool: True if check-in is successful, False otherwise
        """
        if date is None:
            date = datetime.date.today().isoformat()
        
        try:
            self.db_manager.execute_insert(
                """
                INSERT INTO progress (user_id, challenge_id, check_in_date, notes)
                VALUES (?, ?, ?, ?)
                """,
                (user_id, challenge_id, date, notes)
            )
            return True
        except Exception:
            return False  # Check-in failed (possibly already checked in for this date)
    
    def undo_check_in(self, user_id, challenge_id, date=None):
        """
        Remove a check-in record.
        
        Args:
            user_id (int): User ID
            challenge_id (int): Challenge ID
            date (str, optional): Check-in date in YYYY-MM-DD format.
                If None, current date will be used.
            
        Returns:
            bool: True if removal is successful, False otherwise
        """
        if date is None:
            date = datetime.date.today().isoformat()
        
        affected_rows = self.db_manager.execute_update(
            """
            DELETE FROM progress 
            WHERE user_id = ? AND challenge_id = ? AND check_in_date = ?
            """,
            (user_id, challenge_id, date)
        )
        
        return affected_rows > 0
    
    def get_check_ins(self, user_id, challenge_id, start_date=None, end_date=None):
        """
        Get check-in records for a specific challenge.
        
        Args:
            user_id (int): User ID
            challenge_id (int): Challenge ID
            start_date (str, optional): Start date in YYYY-MM-DD format
            end_date (str, optional): End date in YYYY-MM-DD format
            
        Returns:
            list: List of check-in dictionaries
        """
        query = """
        SELECT * FROM progress 
        WHERE user_id = ? AND challenge_id = ?
        """
        params = [user_id, challenge_id]
        
        if start_date:
            query += " AND check_in_date >= ?"
            params.append(start_date)
        
        if end_date:
            query += " AND check_in_date <= ?"
            params.append(end_date)
        
        query += " ORDER BY check_in_date DESC"
        
        return self.db_manager.execute_query(query, tuple(params))
    
    def get_all_user_check_ins(self, user_id, start_date=None, end_date=None):
        """
        Get all check-in records for a user across all challenges.
        
        Args:
            user_id (int): User ID
            start_date (str, optional): Start date in YYYY-MM-DD format
            end_date (str, optional): End date in YYYY-MM-DD format
            
        Returns:
            list: List of check-in dictionaries with challenge information
        """
        query = """
        SELECT p.*, c.title as challenge_title, c.category, c.difficulty
        FROM progress p
        JOIN challenges c ON p.challenge_id = c.id
        WHERE p.user_id = ?
        """
        params = [user_id]
        
        if start_date:
            query += " AND p.check_in_date >= ?"
            params.append(start_date)
        
        if end_date:
            query += " AND p.check_in_date <= ?"
            params.append(end_date)
        
        query += " ORDER BY p.check_in_date DESC, c.title"
        
        return self.db_manager.execute_query(query, tuple(params))
    
    def get_streak(self, user_id, challenge_id):
        """
        Calculate the current streak for a challenge.
        
        Args:
            user_id (int): User ID
            challenge_id (int): Challenge ID
            
        Returns:
            int: Current streak (consecutive days)
        """
        check_ins = self.db_manager.execute_query(
            """
            SELECT check_in_date FROM progress 
            WHERE user_id = ? AND challenge_id = ?
            ORDER BY check_in_date DESC
            """,
            (user_id, challenge_id)
        )
        
        if not check_ins:
            return 0
        
        # Convert string dates to datetime objects
        dates = [datetime.date.fromisoformat(ci["check_in_date"]) for ci in check_ins]
        
        # Check if the most recent check-in is today or yesterday
        today = datetime.date.today()
        if dates[0] < today - datetime.timedelta(days=1):
            return 0  # Streak broken
        
        # Count consecutive days
        streak = 1
        for i in range(len(dates) - 1):
            if dates[i] - dates[i + 1] == datetime.timedelta(days=1):
                streak += 1
            else:
                break
        
        return streak
    
    def get_completion_rate(self, user_id, challenge_id, days=30):
        """
        Calculate the completion rate for a challenge.
        
        Args:
            user_id (int): User ID
            challenge_id (int): Challenge ID
            days (int, optional): Number of days to consider
            
        Returns:
            float: Completion rate (0.0 to 1.0)
        """
        end_date = datetime.date.today()
        start_date = end_date - datetime.timedelta(days=days-1)
        
        check_ins = self.get_check_ins(
            user_id, 
            challenge_id, 
            start_date.isoformat(), 
            end_date.isoformat()
        )
        
        # Count unique dates
        unique_dates = set(ci["check_in_date"] for ci in check_ins)
        
        return len(unique_dates) / days

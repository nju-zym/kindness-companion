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
        Get all available challenges with data validation.

        Returns:
            list: List of complete challenge dictionaries (excluding incomplete records)
        """
        challenges = self.db_manager.execute_query(
            "SELECT * FROM challenges ORDER BY difficulty, title"
        )
        # Filter out challenges with incomplete data
        return [
            challenge
            for challenge in challenges
            if self._is_challenge_complete(challenge)
        ]

    def get_challenge_by_id(self, challenge_id):
        """
        Get a challenge by its ID.

        Args:
            challenge_id (int): Challenge ID

        Returns:
            dict: Challenge information, or None if not found
        """
        if not challenge_id:
            return None

        result = self.db_manager.execute_query(
            "SELECT * FROM challenges WHERE id = ?", (challenge_id,)
        )

        if result and len(result) > 0:
            challenge = result[0]
            return challenge if self._is_challenge_complete(challenge) else None
        return None

    def get_challenges_by_category(self, category):
        """
        Get challenges by category with data validation.

        Args:
            category (str): Challenge category

        Returns:
            list: List of complete challenge dictionaries
        """
        if not category:
            return []

        challenges = self.db_manager.execute_query(
            "SELECT * FROM challenges WHERE category = ? ORDER BY difficulty, title",
            (category,),
        )
        # Filter out challenges with incomplete data
        return [
            challenge
            for challenge in challenges
            if self._is_challenge_complete(challenge)
        ]

    def get_challenges_by_difficulty(self, difficulty):
        """
        Get challenges by difficulty level with data validation.

        Args:
            difficulty (int): Difficulty level (1-5)

        Returns:
            list: List of complete challenge dictionaries
        """
        if not isinstance(difficulty, int) or difficulty < 1 or difficulty > 5:
            return []

        challenges = self.db_manager.execute_query(
            "SELECT * FROM challenges WHERE difficulty = ? ORDER BY category, title",
            (difficulty,),
        )
        # Filter out challenges with incomplete data
        return [
            challenge
            for challenge in challenges
            if self._is_challenge_complete(challenge)
        ]

    def get_unique_categories(self):
        """
        Get all unique challenge categories.

        Returns:
            list: List of unique category names, sorted alphabetically
        """
        result = self.db_manager.execute_query(
            "SELECT DISTINCT category FROM challenges WHERE category IS NOT NULL AND category != '' ORDER BY category"
        )
        return [row["category"] for row in result if row["category"]]

    def get_challenges_summary(self):
        """
        Get a summary of challenges by category and difficulty.

        Returns:
            dict: Summary containing category counts and difficulty distribution
        """
        challenges = self.get_all_challenges()

        summary = {
            "total_challenges": len(challenges),
            "by_category": {},
            "by_difficulty": {1: 0, 2: 0, 3: 0, 4: 0, 5: 0},
        }

        for challenge in challenges:
            # Count by category
            category = challenge.get("category", "未分类")
            summary["by_category"][category] = (
                summary["by_category"].get(category, 0) + 1
            )

            # Count by difficulty
            difficulty = challenge.get("difficulty", 1)
            if 1 <= difficulty <= 5:
                summary["by_difficulty"][difficulty] += 1

        return summary

    def _is_challenge_complete(self, challenge):
        """
        Check if a challenge has all required fields and valid data.

        Args:
            challenge (dict): Challenge dictionary to validate

        Returns:
            bool: True if challenge is complete and valid, False otherwise
        """
        if not challenge:
            return False

        # Check required fields
        required_fields = ["id", "title", "description", "category", "difficulty"]
        for field in required_fields:
            if field not in challenge or challenge[field] is None:
                return False

            # Check for empty strings
            if isinstance(challenge[field], str) and challenge[field].strip() == "":
                return False

        # Validate difficulty range
        try:
            difficulty = int(challenge["difficulty"])
            if difficulty < 1 or difficulty > 5:
                return False
        except (ValueError, TypeError):
            return False

        # Validate ID is positive
        try:
            challenge_id = int(challenge["id"])
            if challenge_id <= 0:
                return False
        except (ValueError, TypeError):
            return False

        return True

    def subscribe_to_challenge(self, user_id, challenge_id):
        """
        Subscribe a user to a challenge with validation.

        Args:
            user_id (int): User ID
            challenge_id (int): Challenge ID

        Returns:
            bool: True if subscription is successful, False otherwise
        """
        if not user_id or not challenge_id:
            return False

        # Check if challenge exists and is valid
        challenge = self.get_challenge_by_id(challenge_id)
        if not challenge:
            return False

        # Check if already subscribed
        if self.is_subscribed(user_id, challenge_id):
            return False

        try:
            result = self.db_manager.execute_insert(
                "INSERT INTO user_challenges (user_id, challenge_id) VALUES (?, ?)",
                (user_id, challenge_id),
            )
            return result > 0
        except Exception as e:
            print(f"Error subscribing to challenge: {e}")
            return False

    def unsubscribe_from_challenge(self, user_id, challenge_id):
        """
        Unsubscribe a user from a challenge with validation.

        Args:
            user_id (int): User ID
            challenge_id (int): Challenge ID

        Returns:
            bool: True if unsubscription is successful, False otherwise
        """
        if not user_id or not challenge_id:
            return False

        affected_rows = self.db_manager.execute_update(
            "DELETE FROM user_challenges WHERE user_id = ? AND challenge_id = ?",
            (user_id, challenge_id),
        )

        return affected_rows > 0

    def get_user_challenges(self, user_id):
        """
        Get all challenges subscribed by a user with data validation.

        Args:
            user_id (int): User ID

        Returns:
            list: List of complete challenge dictionaries
        """
        if not user_id:
            return []

        challenges = self.db_manager.execute_query(
            """
            SELECT c.*
            FROM challenges c
            JOIN user_challenges uc ON c.id = uc.challenge_id
            WHERE uc.user_id = ?
            ORDER BY c.difficulty, c.title
            """,
            (user_id,),
        )

        # Filter out challenges with incomplete data
        return [
            challenge
            for challenge in challenges
            if self._is_challenge_complete(challenge)
        ]

    def is_subscribed(self, user_id, challenge_id):
        """
        Check if a user is subscribed to a challenge with validation.

        Args:
            user_id (int): User ID
            challenge_id (int): Challenge ID

        Returns:
            bool: True if subscribed, False otherwise
        """
        if not user_id or not challenge_id:
            return False

        result = self.db_manager.execute_query(
            "SELECT COUNT(*) as count FROM user_challenges WHERE user_id = ? AND challenge_id = ?",
            (user_id, challenge_id),
        )

        return result and result[0]["count"] > 0

    def create_challenge(self, title, description, category, difficulty):
        """
        Create a new challenge with validation.

        Args:
            title (str): Challenge title
            description (str): Challenge description
            category (str): Challenge category
            difficulty (int): Difficulty level (1-5)

        Returns:
            int: ID of the created challenge, or None if creation failed
        """
        # Validate input data
        if not title or not title.strip():
            return None
        if not description or not description.strip():
            return None
        if not category or not category.strip():
            return None

        try:
            difficulty = int(difficulty)
            if difficulty < 1 or difficulty > 5:
                return None
        except (ValueError, TypeError):
            return None

        return self.db_manager.execute_insert(
            """
            INSERT INTO challenges (title, description, category, difficulty)
            VALUES (?, ?, ?, ?)
            """,
            (title.strip(), description.strip(), category.strip(), difficulty),
        )

    def verify_data_integrity(self):
        """
        Verify data integrity and return a report of any issues found.

        Returns:
            dict: Report containing information about data integrity issues
        """
        report = {
            "total_challenges": 0,
            "valid_challenges": 0,
            "invalid_challenges": [],
            "issues_found": [],
        }

        # Get all challenges from database (without filtering)
        all_challenges = self.db_manager.execute_query(
            "SELECT * FROM challenges ORDER BY id"
        )
        report["total_challenges"] = len(all_challenges)

        for challenge in all_challenges:
            if self._is_challenge_complete(challenge):
                report["valid_challenges"] += 1
            else:
                report["invalid_challenges"].append(challenge)

                # Identify specific issues
                issues = []
                if not challenge.get("id"):
                    issues.append("Missing ID")
                if not challenge.get("title") or (
                    isinstance(challenge.get("title"), str)
                    and not challenge["title"].strip()
                ):
                    issues.append("Missing or empty title")
                if not challenge.get("description") or (
                    isinstance(challenge.get("description"), str)
                    and not challenge["description"].strip()
                ):
                    issues.append("Missing or empty description")
                if not challenge.get("category") or (
                    isinstance(challenge.get("category"), str)
                    and not challenge["category"].strip()
                ):
                    issues.append("Missing or empty category")

                difficulty = challenge.get("difficulty")
                if difficulty is None:
                    issues.append("Missing difficulty")
                elif (
                    not isinstance(difficulty, int) or difficulty < 1 or difficulty > 5
                ):
                    issues.append(f"Invalid difficulty: {difficulty}")

                report["issues_found"].append(
                    {
                        "challenge_id": challenge.get("id", "Unknown"),
                        "title": challenge.get("title", "Unknown"),
                        "issues": issues,
                    }
                )

        return report

    def clean_invalid_challenges(self, dry_run=True):
        """
        Clean up invalid challenge records from the database.

        Args:
            dry_run (bool): If True, only report what would be cleaned without making changes

        Returns:
            dict: Report of cleanup actions taken or planned
        """
        report = self.verify_data_integrity()
        cleanup_report = {
            "dry_run": dry_run,
            "challenges_to_clean": len(report["invalid_challenges"]),
            "cleaned_ids": [],
            "errors": [],
        }

        if not dry_run and report["invalid_challenges"]:
            for invalid_challenge in report["invalid_challenges"]:
                challenge_id = invalid_challenge.get("id")
                if challenge_id:
                    try:
                        # Remove from user subscriptions first
                        self.db_manager.execute_update(
                            "DELETE FROM user_challenges WHERE challenge_id = ?",
                            (challenge_id,),
                        )

                        # Remove from progress records
                        self.db_manager.execute_update(
                            "DELETE FROM progress WHERE challenge_id = ?",
                            (challenge_id,),
                        )

                        # Remove the challenge itself
                        self.db_manager.execute_update(
                            "DELETE FROM challenges WHERE id = ?", (challenge_id,)
                        )

                        cleanup_report["cleaned_ids"].append(challenge_id)
                    except Exception as e:
                        cleanup_report["errors"].append(
                            f"Error cleaning challenge {challenge_id}: {e}"
                        )

        return cleanup_report

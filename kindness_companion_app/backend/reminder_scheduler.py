import datetime
import threading
import time
from apscheduler.schedulers.background import BackgroundScheduler
from .database_manager import DatabaseManager


class ReminderScheduler:
    """
    Manages scheduling and triggering of reminders.
    """

    def __init__(self, db_manager=None, callback=None):
        """
        Initialize the reminder scheduler.

        Args:
            db_manager (DatabaseManager, optional): Database manager instance.
                If None, a new instance will be created.
            callback (callable, optional): Function to call when a reminder is triggered.
                The function should accept a reminder dictionary as its argument.
        """
        self.db_manager = db_manager or DatabaseManager()
        self.callback = callback
        self.scheduler = BackgroundScheduler()
        self.scheduler.start()
        self.jobs = {}  # Dictionary to store job IDs

    def set_callback(self, callback):
        """
        Set the callback function for reminders.

        Args:
            callback (callable): Function to call when a reminder is triggered.
                The function should accept a reminder dictionary as its argument.
        """
        self.callback = callback

    def _trigger_reminder(self, reminder_id, user_id, challenge_id, challenge_title):
        """
        Trigger a reminder.

        Args:
            reminder_id (int): Reminder ID
            user_id (int): User ID
            challenge_id (int): Challenge ID
            challenge_title (str): Challenge title
        """
        if self.callback:
            reminder = {
                "id": reminder_id,
                "user_id": user_id,
                "challenge_id": challenge_id,
                "challenge_title": challenge_title,
                "timestamp": datetime.datetime.now().isoformat()
            }
            self.callback(reminder)

    def create_reminder(self, user_id, challenge_id, time_str, days_of_week=None):
        """
        Create a new reminder.

        Args:
            user_id (int): User ID
            challenge_id (int): Challenge ID
            time_str (str): Time in HH:MM format (24-hour)
            days_of_week (list, optional): List of days (0-6, where 0 is Monday).
                If None, reminder will be set for all days.

        Returns:
            int: ID of the created reminder, or None if creation failed
        """
        if days_of_week is None:
            days_of_week = list(range(7))  # All days

        # Convert list to comma-separated string
        days_str = ",".join(map(str, days_of_week))

        # Get challenge title for the reminder
        challenge = self.db_manager.execute_query(
            "SELECT title FROM challenges WHERE id = ?",
            (challenge_id,)
        )

        if not challenge:
            return None  # Challenge not found

        challenge_title = challenge[0]["title"]

        reminder_id = self.db_manager.execute_insert(
            """
            INSERT INTO reminders (user_id, challenge_id, time, days)
            VALUES (?, ?, ?, ?)
            """,
            (user_id, challenge_id, time_str, days_str)
        )

        if reminder_id:
            self._schedule_reminder(reminder_id, user_id, challenge_id, challenge_title, time_str, days_of_week)

        return reminder_id

    def update_reminder(self, reminder_id, time_str=None, days_of_week=None, enabled=None):
        """
        Update an existing reminder.

        Args:
            reminder_id (int): Reminder ID
            time_str (str, optional): New time in HH:MM format (24-hour)
            days_of_week (list, optional): New list of days (0-6, where 0 is Monday)
            enabled (bool, optional): Whether the reminder is enabled

        Returns:
            bool: True if update is successful, False otherwise
        """
        # Get current reminder data
        reminder = self.db_manager.execute_query(
            """
            SELECT r.*, c.title as challenge_title
            FROM reminders r
            JOIN challenges c ON r.challenge_id = c.id
            WHERE r.id = ?
            """,
            (reminder_id,)
        )

        if not reminder:
            return False  # Reminder not found

        reminder = reminder[0]

        # Prepare update query
        updates = []
        params = []

        if time_str is not None:
            updates.append("time = ?")
            params.append(time_str)
        else:
            time_str = reminder["time"]

        if days_of_week is not None:
            days_str = ",".join(map(str, days_of_week))
            updates.append("days = ?")
            params.append(days_str)
        else:
            days_of_week = [int(d) for d in reminder["days"].split(",")]

        if enabled is not None:
            updates.append("enabled = ?")
            params.append(1 if enabled else 0)

        if not updates:
            return False  # Nothing to update

        # Add reminder_id to params
        params.append(reminder_id)

        query = f"UPDATE reminders SET {', '.join(updates)} WHERE id = ?"

        affected_rows = self.db_manager.execute_update(query, tuple(params))

        if affected_rows > 0:
            # Reschedule the reminder
            self._unschedule_reminder(reminder_id)

            if enabled is None or enabled:
                self._schedule_reminder(
                    reminder_id,
                    reminder["user_id"],
                    reminder["challenge_id"],
                    reminder["challenge_title"],
                    time_str,
                    days_of_week
                )

            return True

        return False

    def delete_reminder(self, reminder_id):
        """
        Delete a reminder from the scheduler and the database.

        Args:
            reminder_id (int): Reminder ID

        Returns:
            bool: True if deletion is successful, False otherwise
        """
        print(f"Attempting to delete reminder ID: {reminder_id}")
        try:
            reminder_id = int(reminder_id)
        except (ValueError, TypeError):
            print(f"Error: Invalid reminder ID format: {reminder_id}")
            return False

        # 1. Unschedule the job first
        unscheduled = False
        try:
            self._unschedule_reminder(reminder_id)
            print(f"Successfully processed unscheduling for reminder ID: {reminder_id}")
            unscheduled = True  # Mark as processed, even if job wasn't found in scheduler
        except Exception as e:
            print(f"Error during unscheduling job for reminder ID {reminder_id}: {e}")
            # Depending on requirements, you might return False here if unscheduling MUST succeed first.
            # Let's assume for now that DB deletion is the primary goal.

        # 2. Delete from the database using the standard manager method
        db_success = False
        try:
            affected_rows = self.db_manager.execute_update(
                "DELETE FROM reminders WHERE id = ?",
                (reminder_id,)
            )
            print(f"Database delete query executed for reminder ID: {reminder_id}. Affected rows: {affected_rows}")

            if affected_rows > 0:
                print(f"Successfully deleted reminder ID: {reminder_id} from database.")
                db_success = True
            else:
                # If unscheduling seemed ok but DB row not found, maybe it was already deleted.
                print(f"Warning: Reminder ID {reminder_id} not found in database for deletion (or already deleted). execute_update returned 0 affected rows.")
                # Consider if this case should return True or False based on desired behavior.
                # Returning False as the record wasn't actively deleted *now*.
                db_success = False
        except Exception as e:
            print(f"Error executing database delete for reminder ID {reminder_id}: {e}")
            db_success = False

        # Return the status of the database operation
        return db_success

    def get_user_reminders(self, user_id):
        """
        Get all reminders for a user.

        Args:
            user_id (int): User ID

        Returns:
            list: List of reminder dictionaries with challenge information
        """
        return self.db_manager.execute_query(
            """
            SELECT r.*, c.title as challenge_title
            FROM reminders r
            JOIN challenges c ON r.challenge_id = c.id
            WHERE r.user_id = ?
            ORDER BY r.time
            """,
            (user_id,)
        )

    def _schedule_reminder(self, reminder_id, user_id, challenge_id, challenge_title, time_str, days_of_week):
        """
        Schedule a reminder using APScheduler.

        Args:
            reminder_id (int): Reminder ID
            user_id (int): User ID
            challenge_id (int): Challenge ID
            challenge_title (str): Challenge title
            time_str (str): Time in HH:MM format (24-hour)
            days_of_week (list): List of days (0-6, where 0 is Monday)
        """
        hour, minute = map(int, time_str.split(":"))

        job = self.scheduler.add_job(
            self._trigger_reminder,
            'cron',
            hour=hour,
            minute=minute,
            day_of_week=",".join(map(str, days_of_week)),
            args=[reminder_id, user_id, challenge_id, challenge_title]
        )

        self.jobs[reminder_id] = job.id

    def _unschedule_reminder(self, reminder_id):
        """
        Unschedule a reminder.

        Args:
            reminder_id (int): Reminder ID
        """
        # Ensure reminder_id is treated as int for dictionary lookup
        try:
            reminder_id = int(reminder_id)
        except (ValueError, TypeError):
            print(f"Error: Invalid reminder ID format for unscheduling: {reminder_id}")
            raise ValueError(f"Invalid reminder ID format: {reminder_id}")

        if reminder_id in self.jobs:
            job_id = self.jobs[reminder_id]
            try:
                self.scheduler.remove_job(job_id)
                print(f"Successfully removed job {job_id} from APScheduler.")
            except Exception as e:
                print(f"Error removing job {job_id} from APScheduler: {e}. Might already be removed or scheduler stopped.")
            finally:
                del self.jobs[reminder_id]
                print(f"Removed reminder ID {reminder_id} from internal jobs dictionary.")
        else:
            print(f"Reminder ID {reminder_id} not found in scheduled jobs dictionary (might be already unscheduled or never scheduled).")

    def load_all_reminders(self):
        """
        Load and schedule all active reminders from the database.
        """
        reminders = self.db_manager.execute_query(
            """
            SELECT r.*, c.title as challenge_title
            FROM reminders r
            JOIN challenges c ON r.challenge_id = c.id
            WHERE r.enabled = 1
            """
        )

        for reminder in reminders:
            days_of_week = [int(d) for d in reminder["days"].split(",")]
            self._schedule_reminder(
                reminder["id"],
                reminder["user_id"],
                reminder["challenge_id"],
                reminder["challenge_title"],
                reminder["time"],
                days_of_week
            )

    def shutdown(self):
        """Shut down the scheduler."""
        self.scheduler.shutdown()

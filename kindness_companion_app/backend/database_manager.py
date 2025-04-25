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
            avatar_path TEXT,  -- Keep for potential fallback or future use
            bio TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            last_login TIMESTAMP,
            avatar BLOB        -- Add avatar blob column
        )
        ''')

        # --- Check and add the avatar column if it doesn't exist ---
        try:
            self.cursor.execute("PRAGMA table_info(users)")
            columns = [column[1] for column in self.cursor.fetchall()]
            if 'avatar' not in columns:
                self.cursor.execute("ALTER TABLE users ADD COLUMN avatar BLOB")
                self.connection.commit()
                print("Added 'avatar' BLOB column to 'users' table.")
            # --- Add check for bio column --- Start
            if 'bio' not in columns:
                self.cursor.execute("ALTER TABLE users ADD COLUMN bio TEXT")
                self.connection.commit()
                print("Added 'bio' TEXT column to 'users' table.")
            # --- Add check for bio column --- End
        except sqlite3.Error as e:
            print(f"Error checking/adding columns: {e}")
        # --- End check ---

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
            (5, '感恩日记', '每天写下3件你感恩的事情', '自我提升', 1),
            (6, '赞美他人', '真诚地赞美一位同事或朋友', '人际关系', 1),
            (7, '节约用水', '有意识地减少洗漱或淋浴时的用水量', '环保', 1),
            (8, '主动问候', '主动向邻居或保安问好', '社区互动', 1),
            (9, '分享知识', '向他人分享一个有用的知识或技巧', '自我提升', 2),
            (10, '倾听烦恼', '耐心倾听朋友或家人的烦恼', '人际关系', 2),
            (11, '公共交通', '选择乘坐公共交通工具代替私家车', '环保', 2),
            (12, '志愿服务', '参与一次社区或组织的志愿服务活动', '社区服务', 4),
            (13, '学习新技能', '花30分钟学习一项新技能或知识', '自我提升', 3),
            (14, '整理旧物', '整理不再需要的物品并捐赠或回收', '环保', 3),
            (15, '表达感谢', '向服务人员（如快递员、服务员）表达感谢', '日常行为', 1),
            (16, '给陌生人一个微笑', '在街上或商店里给一个陌生人一个真诚的微笑', '日常行为', 1),
            (17, '写感谢信', '写一封感谢信给曾经帮助过你的人', '人际关系', 2),
            (18, '捐赠物品', '为慈善机构或需要帮助的人捐赠衣物、书籍或食物', '社区服务', 3),
            (19, '学习手语', '学习一句简单的手语，如“谢谢”或“你好”', '自我提升', 2),
            (20, '关爱植物', '给家里的或办公室的植物浇水', '日常行为', 1),
            (21, '分享正能量', '在社交媒体上分享一条积极的新闻或引语', '精神成长', 1),
            (22, '支持本地商家', '光顾一家本地小商店或餐馆', '社区互动', 2),
            (23, '无抱怨日', '尝试一整天不抱怨任何事情', '自我提升', 3),
            (24, '留下鼓励便条', '在公共场所（如图书馆的书里）留下一张鼓励的小便条', '精神成长', 2),
            (25, '旧物改造', '将一件旧物品改造成有用的新东西', '环保', 3),
            (26, '保持耐心', '在排队或遇到延误时保持耐心和礼貌', '日常行为', 2),
            (27, '提供帮助', '主动询问身边的人是否需要帮助', '人际关系', 2),
            (28, '减少塑料使用', '购物时自带购物袋，拒绝一次性塑料制品', '环保', 2),
            (29, '参与社区清洁', '参加或组织一次社区清洁活动', '社区服务', 3),
            (30, '冥想或正念练习', '进行10分钟的冥想或正念呼吸练习', '自我提升', 1),
            (31, '鼓励他人', '给正在经历困难的朋友或家人发送鼓励信息', '人际关系', 2),
            (32, '节约用电', '离开房间时随手关灯，拔掉不用的电器插头', '环保', 1),
            (33, '阅读有益书籍', '阅读至少15分钟关于个人成长或积极心理学的书籍', '自我提升', 2),
            (34, '帮助邻居', '帮助邻居做一些小事，如取快递、照看宠物', '社区互动', 2),
            (35, '反思与记录', '花5分钟反思今天的善行和感受', '精神成长', 1)
        ''')

        self.connection.commit() # Commit changes if ALTER TABLE was executed
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

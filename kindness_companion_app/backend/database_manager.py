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
        if not self.connection:
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

    def ensure_connected(self):
        """确保数据库连接已建立"""
        if not self.connection or not self.cursor:
            self.connect()

    def _initialize_db(self):
        """Create database tables if they don't exist."""
        try:
            self.ensure_connected()
            if not self.cursor or not self.connection:
                print("Failed to establish database connection")
                return

            # Create users table
            self.cursor.execute(
                """
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT UNIQUE NOT NULL,
                password_hash TEXT NOT NULL,
                email TEXT UNIQUE,
                avatar_path TEXT,
                bio TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                last_login TIMESTAMP,
                avatar BLOB,
                ai_consent_given INTEGER
            )
            """
            )

            # Create conversation_history table
            self.cursor.execute(
                """
            CREATE TABLE IF NOT EXISTS conversation_history (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                message TEXT NOT NULL,
                is_user BOOLEAN NOT NULL,
                timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                context_id TEXT,
                topic TEXT,
                emotion_score FLOAT,
                FOREIGN KEY (user_id) REFERENCES users (id)
            )
            """
            )

            # Check and add columns if they don't exist
            try:
                self.cursor.execute("PRAGMA table_info(users)")
                columns = [column[1] for column in self.cursor.fetchall()]

                columns_to_add = {
                    "avatar": "BLOB",
                    "avatar_path": "TEXT",
                    "bio": "TEXT",
                    "ai_consent_given": "INTEGER",
                }

                for col_name, col_type in columns_to_add.items():
                    if col_name not in columns:
                        self.cursor.execute(
                            f"ALTER TABLE users ADD COLUMN {col_name} {col_type}"
                        )
                        self.connection.commit()
                        print(f"Added '{col_name}' {col_type} column to 'users' table.")

            except sqlite3.Error as e:
                print(f"Error checking/adding columns: {e}")

            # Create other tables and insert default data
            tables = [
                (
                    """
                CREATE TABLE IF NOT EXISTS challenges (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    title TEXT NOT NULL,
                    description TEXT,
                    category TEXT,
                    difficulty INTEGER,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
                """,
                    "challenges",
                ),
                (
                    """
                CREATE TABLE IF NOT EXISTS user_challenges (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER,
                    challenge_id INTEGER,
                    subscribed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (user_id) REFERENCES users (id),
                    FOREIGN KEY (challenge_id) REFERENCES challenges (id),
                    UNIQUE (user_id, challenge_id)
                )
                """,
                    "user_challenges",
                ),
                (
                    """
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
                """,
                    "progress",
                ),
                (
                    """
                CREATE TABLE IF NOT EXISTS reminders (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER,
                    challenge_id INTEGER,
                    time TEXT,
                    days TEXT,
                    enabled BOOLEAN DEFAULT 1,
                    FOREIGN KEY (user_id) REFERENCES users (id),
                    FOREIGN KEY (challenge_id) REFERENCES challenges (id)
                )
                """,
                    "reminders",
                ),
                (
                    """
                CREATE TABLE IF NOT EXISTS weekly_reports (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER NOT NULL,
                    report_text TEXT NOT NULL,
                    start_date DATE NOT NULL,
                    end_date DATE NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (user_id) REFERENCES users (id),
                    UNIQUE (user_id, start_date, end_date)
                )
                """,
                    "weekly_reports",
                ),
            ]

            for create_sql, table_name in tables:
                try:
                    self.cursor.execute(create_sql)
                    print(f"Created or verified table: {table_name}")
                except sqlite3.Error as e:
                    print(f"Error creating table {table_name}: {e}")

            # Insert default challenges
            try:
                self.cursor.execute(
                    """
                INSERT OR IGNORE INTO challenges (id, title, description, category, difficulty)
                VALUES
                    -- 日常行为类
                    (1, '每日微笑', '对遇到的每个人微笑，传递善意', '日常行为', 1),
                    (2, '主动问候', '主动向身边的人问好，传递温暖', '日常行为', 1),
                    (3, '让座行动', '在公共交通上主动为需要的人让座', '日常行为', 1),
                    (4, '随手关门', '进出公共场所时，注意为后面的人扶门', '日常行为', 1),
                    (25, '电梯礼仪', '在电梯里主动为他人按楼层，让行', '日常行为', 1),
                    (26, '礼貌用语', '使用"请"、"谢谢"等礼貌用语', '日常行为', 1),
                    (27, '轻声细语', '在公共场合保持适当的音量', '日常行为', 1),
                    (28, '排队守序', '遵守排队秩序，不插队', '日常行为', 1),
                    
                    -- 社区服务类
                    (5, '扶老助残', '帮助老人或残障人士完成一项任务', '社区服务', 2),
                    (6, '社区清洁', '参与社区环境清洁活动', '社区服务', 2),
                    (7, '义务教学', '为社区儿童提供免费辅导', '社区服务', 3),
                    (8, '爱心捐赠', '整理并捐赠闲置物品给需要的人', '社区服务', 2),
                    (29, '社区巡逻', '参与社区安全巡逻活动', '社区服务', 2),
                    (30, '邻里互助', '帮助邻居解决生活困难', '社区服务', 2),
                    (31, '志愿服务', '参与社区志愿服务活动', '社区服务', 2),
                    (32, '文化传承', '参与传统文化传承活动', '社区服务', 3),
                    
                    -- 环保类
                    (9, '垃圾分类', '坚持正确进行垃圾分类', '环保', 1),
                    (10, '节约用水', '注意节约用水，及时关闭水龙头', '环保', 1),
                    (11, '绿色出行', '选择步行、骑行或公共交通出行', '环保', 2),
                    (12, '减少塑料', '减少使用一次性塑料制品', '环保', 2),
                    (33, '节约用电', '及时关闭不需要的电器', '环保', 1),
                    (34, '植树护绿', '参与植树或绿化活动', '环保', 2),
                    (35, '旧物改造', '将废旧物品改造成有用物品', '环保', 3),
                    (36, '环保宣传', '向他人宣传环保知识', '环保', 2),
                    
                    -- 精神成长类
                    (13, '每日感恩', '记录三件值得感恩的事', '精神成长', 1),
                    (14, '正念冥想', '每天进行10分钟的正念冥想', '精神成长', 2),
                    (15, '阅读分享', '阅读一本好书并分享感悟', '精神成长', 2),
                    (16, '情绪觉察', '觉察并记录自己的情绪变化', '精神成长', 2),
                    (37, '自我反思', '每天进行自我反思和总结', '精神成长', 2),
                    (38, '目标设定', '设定并执行个人成长目标', '精神成长', 2),
                    (39, '心灵对话', '与信任的人分享内心想法', '精神成长', 2),
                    (40, '静心时刻', '每天留出独处的时间', '精神成长', 1),
                    
                    -- 自我提升类
                    (17, '早起锻炼', '坚持早起进行适度运动', '自我提升', 2),
                    (18, '学习新技能', '学习一项新的技能或知识', '自我提升', 3),
                    (19, '时间管理', '制定并执行每日计划', '自我提升', 2),
                    (20, '健康饮食', '注意均衡饮食，减少垃圾食品', '自我提升', 2),
                    (41, '作息规律', '保持规律的作息时间', '自我提升', 2),
                    (42, '专注力训练', '进行专注力训练活动', '自我提升', 2),
                    (43, '压力管理', '学习并实践压力管理技巧', '自我提升', 2),
                    (44, '习惯养成', '培养一个积极的新习惯', '自我提升', 3),
                    
                    -- 人际关系类
                    (21, '倾听他人', '认真倾听他人的想法和感受', '人际关系', 2),
                    (22, '表达感谢', '向帮助过你的人表达感谢', '人际关系', 1),
                    (23, '化解矛盾', '主动化解与他人的小矛盾', '人际关系', 3),
                    (24, '分享快乐', '与他人分享你的快乐时刻', '人际关系', 1),
                    (45, '主动关心', '主动关心身边的人', '人际关系', 1),
                    (46, '真诚道歉', '为自己的错误真诚道歉', '人际关系', 2),
                    (47, '赞美他人', '真诚地赞美他人的优点', '人际关系', 1),
                    (48, '团队合作', '积极参与团队活动', '人际关系', 2),
                    
                    -- 家庭关系类
                    (49, '陪伴家人', '每天抽出时间陪伴家人', '家庭关系', 1),
                    (50, '分担家务', '主动分担家务劳动', '家庭关系', 1),
                    (51, '家庭活动', '组织一次家庭活动', '家庭关系', 2),
                    (52, '表达爱意', '向家人表达爱意和关心', '家庭关系', 1),
                    (53, '倾听父母', '认真倾听父母的想法', '家庭关系', 2),
                    (54, '照顾长辈', '关心照顾家中长辈', '家庭关系', 2),
                    (55, '教育子女', '耐心教育引导子女', '家庭关系', 3),
                    (56, '家庭沟通', '促进家庭成员间的沟通', '家庭关系', 2),
                    
                    -- 职场发展类
                    (57, '工作创新', '提出工作改进建议', '职场发展', 2),
                    (58, '团队协作', '主动帮助同事', '职场发展', 2),
                    (59, '学习成长', '参加职业培训或学习', '职场发展', 2),
                    (60, '时间效率', '提高工作效率', '职场发展', 2),
                    (61, '领导力', '培养领导能力', '职场发展', 3),
                    (62, '沟通技巧', '提升职场沟通能力', '职场发展', 2),
                    (63, '压力管理', '学会处理工作压力', '职场发展', 2),
                    (64, '职业规划', '制定职业发展规划', '职场发展', 3)
                """
                )
                print("Inserted default challenges")
            except sqlite3.Error as e:
                print(f"Error inserting default challenges: {e}")

            self.connection.commit()
            print("Database initialization completed successfully")

        except sqlite3.Error as e:
            print(f"Database initialization error: {e}")
            if self.connection:
                self.connection.rollback()
        finally:
            self.disconnect()

    def execute_query(self, query: str, params=None) -> list:
        """
        Execute a query and return the results.

        Args:
            query (str): SQL query to execute
            params (tuple, optional): Parameters for the query

        Returns:
            list: Query results as a list of dictionaries
        """
        try:
            self.ensure_connected()
            if not self.cursor:
                return []

            if params:
                self.cursor.execute(query, params)
            else:
                self.cursor.execute(query)

            results = self.cursor.fetchall()
            if self.connection:
                self.connection.commit()
            return [dict(row) for row in results]
        except sqlite3.Error as e:
            print(f"Database error: {e}")
            return []
        finally:
            self.disconnect()

    def execute_insert(self, query: str, params=None) -> int:
        """
        Execute an insert query and return the ID of the inserted row.
        If the operation fails, returns 0.

        Args:
            query (str): SQL query to execute
            params (tuple, optional): Parameters for the query

        Returns:
            int: ID of the last inserted row, or 0 if operation fails
        """
        try:
            self.ensure_connected()
            if not self.cursor:
                return 0

            if params:
                self.cursor.execute(query, params)
            else:
                self.cursor.execute(query)

            last_id = self.cursor.lastrowid if self.cursor else 0
            if self.connection:
                self.connection.commit()
            return last_id or 0  # 确保返回整数
        except sqlite3.Error as e:
            print(f"Database error: {e}")
            return 0
        finally:
            self.disconnect()

    def execute_update(self, query: str, params=None) -> int:
        """
        Execute an update query and return the number of affected rows.

        Args:
            query (str): SQL query to execute
            params (tuple, optional): Parameters for the query

        Returns:
            int: Number of affected rows
        """
        try:
            self.ensure_connected()
            if not self.cursor:
                return 0

            print(f"Executing SQL update: {query}")
            print(f"With parameters: {params}")

            try:
                if params:
                    self.cursor.execute(query, params)
                else:
                    self.cursor.execute(query)

                affected_rows = self.cursor.rowcount if self.cursor else 0
                print(f"SQL update affected {affected_rows} rows")

                if self.connection:
                    self.connection.commit()
                    print("Changes committed to database")

                return affected_rows
            except Exception as e:
                print(f"SQL error: {e}")
                if self.connection:
                    self.connection.rollback()
                    print("Transaction rolled back due to error")
                return 0
        finally:
            self.disconnect()
            print("Database connection closed")

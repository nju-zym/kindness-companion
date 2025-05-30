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
                    (64, '职业规划', '制定职业发展规划', '职场发展', 3),

                    -- 碎片时间类 (专注于分钟级的快速善行)
                    (65, '1分钟深呼吸', '在等待时进行1分钟深呼吸，放松身心', '碎片时间', 1),
                    (66, '手机整理', '利用等车时间整理手机照片或联系人', '碎片时间', 1),
                    (67, '快速冥想', '在电梯或等待时进行30秒正念冥想', '碎片时间', 1),
                    (68, '感恩一刻', '在排队时心中感恩身边的一件事物', '碎片时间', 1),
                    (69, '眼睛保健', '看屏幕间隙眺望远方20秒护眼', '碎片时间', 1),
                    (70, '微笑练习', '对着镜子练习自然的微笑1分钟', '碎片时间', 1),
                    (71, '伸展运动', '利用工作间隙做简单的颈肩伸展', '碎片时间', 1),
                    (72, '记忆回顾', '在等待时回想今天的三个美好瞬间', '碎片时间', 1),

                    -- 即时行动类 (可立即完成的善行)
                    (73, '垃圾捡拾', '随手捡起身边的一个垃圾扔进垃圾桶', '即时行动', 1),
                    (74, '问候员工', '对服务员、保安、清洁工说声"谢谢"', '即时行动', 1),
                    (75, '让路他人', '主动为后面的人让出通道', '即时行动', 1),
                    (76, '收纳整理', '随手整理桌面或身边的物品', '即时行动', 1),
                    (77, '节能小事', '离开房间时随手关灯', '即时行动', 1),
                    (78, '善意提醒', '提醒他人掉落的物品或注意安全', '即时行动', 1),
                    (79, '分享信息', '向询问路线的人提供帮助', '即时行动', 1),
                    (80, '车厢礼仪', '在地铁公交上往里走，方便他人上车', '即时行动', 1),

                    -- 数字时代类 (利用数字工具的微善行)
                    (81, '发送祝福', '给朋友发送一条关心或祝福信息', '数字时代', 1),
                    (82, '点赞鼓励', '为朋友的积极动态点赞或留言鼓励', '数字时代', 1),
                    (83, '分享正能量', '转发一条有意义的正能量内容', '数字时代', 1),
                    (84, '线上学习', '观看一个3分钟的知识或技能短视频', '数字时代', 1),
                    (85, '网络礼仪', '在网络交流中保持礼貌和尊重', '数字时代', 1),
                    (86, '数字断舍离', '删除手机中不需要的应用或文件', '数字时代', 1),
                    (87, '信息核实', '分享信息前核实真实性，避免传播谣言', '数字时代', 2),
                    (88, '在线反馈', '为优质的服务或产品留下正面评价', '数字时代', 1),

                    -- 通勤时光类 (专为上下班路上设计)
                    (89, '播客学习', '在通勤途中听3分钟教育或励志播客', '通勤时光', 1),
                    (90, '观察练习', '观察路上的美好事物并心存感激', '通勤时光', 1),
                    (91, '步行计数', '走路时计算步数，关注身体健康', '通勤时光', 1),
                    (92, '车窗风景', '欣赏车窗外的风景，寻找美的瞬间', '通勤时光', 1),
                    (93, '默读诗词', '在脑海中背诵一首喜欢的诗或词', '通勤时光', 1),
                    (94, '规划思考', '用5分钟规划今天的重要任务', '通勤时光', 1),
                    (95, '音乐放松', '听一首舒缓的音乐，调节心情', '通勤时光', 1),
                    (96, '语言练习', '默念几个外语单词或短语', '通勤时光', 1),

                    -- 等待时刻类 (排队、候车时的微行动)
                    (97, '姿态调整', '检查并调整自己的站姿或坐姿', '等待时刻', 1),
                    (98, '呼吸调节', '进行4-7-8呼吸法调节状态', '等待时刻', 1),
                    (99, '心理暗示', '给自己积极的心理暗示或鼓励', '等待时刻', 1),
                    (100, '环境观察', '观察周围环境，培养观察力', '等待时刻', 1),
                    (101, '微表情练习', '练习放松面部肌肉，保持平和表情', '等待时刻', 1),
                    (102, '联想游戏', '看到物品联想积极正面的词汇', '等待时刻', 1),
                    (103, '时间感知', '估算等待时间，训练时间感知力', '等待时刻', 1),
                    (104, '优先级思考', '思考今天最重要的三件事', '等待时刻', 1),

                    -- 工作间隙类 (办公室或工作场所的快速行动)
                    (105, '桌面清洁', '用湿巾擦拭办公桌面，保持整洁', '工作间隙', 1),
                    (106, '同事关怀', '询问同事是否需要帮助', '工作间隙', 1),
                    (107, '饮水提醒', '提醒自己和同事适时补充水分', '工作间隙', 1),
                    (108, '邮件整理', '花2分钟整理邮箱，删除无用邮件', '工作间隙', 1),
                    (109, '笔记记录', '记录一个工作心得或改进想法', '工作间隙', 1),
                    (110, '座椅调整', '调整座椅高度，保护腰椎健康', '工作间隙', 1),
                    (111, '文具整理', '整理桌上的文具，分类摆放', '工作间隙', 1),
                    (112, '进度检查', '快速检查工作进度，调整节奏', '工作间隙', 1),

                    -- 生活细节类 (日常生活中的微小改变)
                    (113, '餐具清洗', '用餐后立即清洗餐具，保持厨房整洁', '生活细节', 1),
                    (114, '鞋子摆放', '进门后整齐摆放鞋子', '生活细节', 1),
                    (115, '毛巾整理', '使用后整理毛巾，保持浴室整洁', '生活细节', 1),
                    (116, '床铺整理', '起床后简单整理床铺', '生活细节', 1),
                    (117, '开窗通风', '定时开窗通风，保持空气新鲜', '生活细节', 1),
                    (118, '植物浇水', '给家中的植物浇适量的水', '生活细节', 1),
                    (119, '冰箱检查', '检查冰箱食材，避免浪费', '生活细节', 1),
                    (120, '钥匙定位', '进门后将钥匙放在固定位置', '生活细节', 1),

                    -- 自我关怀类 (关注自身健康和成长的小行动)
                    (121, '保湿护肤', '为手部或面部涂抹保湿产品', '自我关怀', 1),
                    (122, '护眼操练', '做简单的眼保健操缓解眼疲劳', '自我关怀', 1),
                    (123, '肩颈舒缓', '转动肩膀和脖子，缓解僵硬', '自我关怀', 1),
                    (124, '心情记录', '用一个词记录当前的心情状态', '自我关怀', 1),
                    (125, '补充营养', '吃一个水果或喝一杯温水', '自我关怀', 1),
                    (126, '口腔护理', '使用漱口水或清洁牙缝', '自我关怀', 1),
                    (127, '足部护理', '脱鞋活动脚趾，促进血液循环', '自我关怀', 1),
                    (128, '正念片刻', '专注感受当下的身体感觉', '自我关怀', 1),

                    -- 快闪善行类 (超短时间的即时善行)
                    (129, '拾起垃圾', '看到垃圾随手捡起丢进垃圾桶', '快闪善行', 1),
                    (130, '电梯按钮', '在电梯里主动询问并帮忙按楼层', '快闪善行', 1),
                    (131, '物品递送', '帮忙递送掉落或够不到的物品', '快闪善行', 1),
                    (132, '路况提醒', '提醒他人注意脚下湿滑或障碍物', '快闪善行', 1),
                    (133, '善意指路', '为问路的人提供准确的方向指引', '快闪善行', 1),
                    (134, '共享空间', '主动让出公共座位给更需要的人', '快闪善行', 1),
                    (135, '耐心等待', '为老人孕妇放慢脚步，耐心等待', '快闪善行', 1),
                    (136, '温馨提醒', '提醒他人带好随身物品或关好车门', '快闪善行', 1)
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

# Kindness Companion 技术上下文

## 技术栈详解

### 1. 前端技术

#### PySide6
- 版本：6.5.0+
- 用途：GUI 界面开发
- 特性：
  - 信号槽机制
  - 样式表支持
  - 动画系统
  - 主题切换

#### QSS 样式
- 自定义主题
- 响应式设计
- 动画效果
- 深色模式支持

#### Lottie 动画
- 用于 UI 动画
- 支持 JSON 格式
- 轻量级实现
- 流畅的动画效果

### 2. 后端技术

#### SQLite3
- 本地数据存储
- 表结构：
  ```sql
  -- 用户表
  CREATE TABLE users (
      id INTEGER PRIMARY KEY,
      username TEXT UNIQUE,
      password_hash TEXT,
      ai_consent_given BOOLEAN
  );

  -- 挑战表
  CREATE TABLE challenges (
      id INTEGER PRIMARY KEY,
      title TEXT,
      description TEXT,
      category TEXT
  );

  -- 用户挑战表
  CREATE TABLE user_challenges (
      user_id INTEGER,
      challenge_id INTEGER,
      status TEXT,
      FOREIGN KEY (user_id) REFERENCES users(id),
      FOREIGN KEY (challenge_id) REFERENCES challenges(id)
  );

  -- 打卡记录表
  CREATE TABLE checkins (
      id INTEGER PRIMARY KEY,
      user_id INTEGER,
      challenge_id INTEGER,
      date TEXT,
      reflection TEXT,
      FOREIGN KEY (user_id) REFERENCES users(id),
      FOREIGN KEY (challenge_id) REFERENCES challenges(id)
  );
  ```

#### APScheduler
- 任务调度
- 提醒功能
- 定时任务
- 后台执行

### 3. AI 技术

#### ZhipuAI API
- 对话生成
- 情感分析
- 报告生成
- API 集成

#### API 客户端
```python
class ZhipuAIClient:
    def __init__(self, api_key):
        self.api_key = api_key
        self.base_url = "https://api.zhipuai.cn"

    async def generate_dialogue(self, prompt):
        # 实现对话生成
        pass

    async def analyze_emotion(self, text):
        # 实现情感分析
        pass

    async def generate_report(self, data):
        # 实现报告生成
        pass
```

### 4. 测试技术

#### pytest
- 单元测试
- 集成测试
- 参数化测试
- 测试夹具

#### pytest-qt
- UI 测试
- 事件模拟
- 状态验证
- 异步测试

## 实现方案

### 1. 数据流实现

```python
class DataFlow:
    def __init__(self):
        self.db = DatabaseManager.get_instance()
        self.ai_client = ZhipuAIClient(API_KEY)

    async def process_user_input(self, user_id, input_data):
        # 1. 保存用户输入
        self.db.save_input(user_id, input_data)

        # 2. 分析情感
        emotion = await self.ai_client.analyze_emotion(input_data)

        # 3. 生成响应
        response = await self.ai_client.generate_dialogue(
            self._build_prompt(input_data, emotion)
        )

        # 4. 更新状态
        self.db.update_user_state(user_id, emotion)

        return response
```

### 2. 错误处理实现

```python
class ErrorHandler:
    @staticmethod
    def handle_api_error(error):
        if isinstance(error, APIError):
            logger.error(f"API Error: {error}")
            return "抱歉，AI 服务暂时不可用，请稍后再试。"
        elif isinstance(error, ValidationError):
            logger.warning(f"Validation Error: {error}")
            return "输入数据格式不正确，请检查后重试。"
        else:
            logger.error(f"Unexpected Error: {error}")
            return "发生未知错误，请稍后重试。"
```

### 3. 安全实现

```python
class SecurityManager:
    def __init__(self):
        self.encryption_key = self._load_encryption_key()

    def encrypt_data(self, data):
        # 实现数据加密
        pass

    def decrypt_data(self, encrypted_data):
        # 实现数据解密
        pass

    def validate_user(self, username, password):
        # 实现用户验证
        pass
```

### 4. 性能优化

1. **数据库优化**
   - 索引优化
   - 查询优化
   - 连接池管理
   - 缓存策略

2. **API 调用优化**
   - 请求合并
   - 响应缓存
   - 错误重试
   - 超时控制

3. **UI 性能优化**
   - 延迟加载
   - 资源缓存
   - 渲染优化
   - 事件节流

## 部署方案

### 1. 打包配置

```python
# KindnessCompanion.spec
a = Analysis(
    ['main.py'],
    pathex=['/path/to/project'],
    binaries=[],
    datas=[
        ('resources', 'resources'),
        ('config.py', '.'),
    ],
    hiddenimports=[
        'PySide6.QtCore',
        'PySide6.QtGui',
        'PySide6.QtWidgets',
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    noarchive=False,
)
```

### 2. 环境配置

```bash
# requirements.txt
PySide6>=6.5.0
APScheduler>=3.9.1
requests>=2.28.2
pytest>=7.3.1
pytest-qt>=4.2.0
```

### 3. 启动脚本

```python
# main.py
def main():
    # 1. 初始化配置
    config = load_config()

    # 2. 初始化数据库
    db = DatabaseManager.get_instance()
    db.initialize()

    # 3. 创建应用
    app = QApplication(sys.argv)
    
    # 4. 设置主题
    theme_manager = ThemeManager()
    theme_manager.apply_theme()

    # 5. 创建主窗口
    window = MainWindow()
    window.show()

    # 6. 运行应用
    sys.exit(app.exec())
```

## 监控与日志

### 1. 日志配置

```python
# logging_config.py
LOGGING_CONFIG = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'standard': {
            'format': '%(asctime)s [%(levelname)s] %(name)s: %(message)s'
        },
    },
    'handlers': {
        'default': {
            'level': 'INFO',
            'formatter': 'standard',
            'class': 'logging.StreamHandler',
        },
        'file': {
            'level': 'DEBUG',
            'formatter': 'standard',
            'class': 'logging.FileHandler',
            'filename': 'app.log',
        },
    },
    'loggers': {
        '': {
            'handlers': ['default', 'file'],
            'level': 'INFO',
            'propagate': True
        }
    }
}
```

### 2. 性能监控

```python
class PerformanceMonitor:
    def __init__(self):
        self.metrics = {}

    def start_operation(self, operation_name):
        self.metrics[operation_name] = {
            'start_time': time.time(),
            'end_time': None,
            'duration': None
        }

    def end_operation(self, operation_name):
        if operation_name in self.metrics:
            self.metrics[operation_name]['end_time'] = time.time()
            self.metrics[operation_name]['duration'] = (
                self.metrics[operation_name]['end_time'] -
                self.metrics[operation_name]['start_time']
            )
``` 
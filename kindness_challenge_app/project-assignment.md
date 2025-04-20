# 善行挑战 (Kindness Challenge) 应用

## 项目框架

```
kindness_challenge_app/
├── frontend/                  # 前端模块（GUI）
│   ├── __init__.py
│   ├── main_window.py         # 主应用程序窗口框架
│   ├── user_auth.py           # 用户注册/登录界面
│   ├── challenge_ui.py        # 挑战列表与订阅界面
│   ├── progress_ui.py         # 打卡界面
│   ├── reminder_ui.py         # 提醒设置界面
│   ├── profile_ui.py          # 用户个人信息界面
│   └── widgets/               # 可重用控件库
│       └── ...
├── backend/                   # 后端模块（业务逻辑 & 数据）
│   ├── __init__.py
│   ├── database_manager.py    # SQLite 连接与 CRUD 接口
│   ├── user_manager.py        # 用户认证与管理逻辑
│   ├── challenge_manager.py   # 挑战创建与订阅逻辑
│   ├── progress_tracker.py    # 打卡记录与进度统计
│   ├── reminder_scheduler.py  # 善意提醒调度模块
│   └── utils.py               # 公共工具函数
├── resources/                 # 应用资源（图标、图片、样式等）
│   └── icons/
│       └── ...
├── tests/                     # 单元测试目录 (pytest)
│   ├── test_user_manager.py
│   ├── test_challenge_manager.py
│   └── ...
├── main.py                    # 应用启动入口
├── requirements.txt           # Python 依赖列表
└── project-assignment.md                  # 项目说明文档 (当前文件)
.gitignore
README.md
```

---

## README 文档说明

本 `project-assignment.md` 用于团队成员之间统一任务分工和模块参考。

### 技术栈

- **语言**：Python 3.10+
- **GUI**：PySide6 (Qt for Python)
- **数据库**：SQLite3 (内置模块)
- **任务调度**：APScheduler 或 Python 内置 `sched` 库
- **版本控制**：Git + GitHub/GitLab
- **测试框架**：pytest

---

## 模块与任务分工

### 前端（开发者 A：GUI 与用户交互）

| 模块文件          | 功能描述                         | 负责人 |
| ----------------- | -------------------------------- | ------ |
| `main_window.py`  | 主应用程序框架，导航栏与容器布局 | A      |
| `user_auth.py`    | 注册/登录界面、表单验证与反馈    | A      |
| `challenge_ui.py` | 展示挑战列表及订阅/取消按钮      | A      |
| `progress_ui.py`  | 每日打卡按钮及历史记录展示       | A      |
| `reminder_ui.py`  | 提醒设置界面（时间、频率、类型） | A      |
| `profile_ui.py`   | 用户个人信息与成就进度页面       | A      |
| `widgets/`        | 通用自定义控件库                 | A      |

### 后端（开发者 B：业务逻辑与数据持久化）

| 模块文件                | 功能描述                             | 负责人 |
| ----------------------- | ------------------------------------ | ------ |
| `database_manager.py`   | 管理 SQLite 连接、表结构及 CRUD 接口 | B      |
| `user_manager.py`       | 用户注册、登录、密码哈希、安全校验   | B      |
| `challenge_manager.py`  | 挑战数据模型、订阅/取消逻辑          | B      |
| `progress_tracker.py`   | 打卡记录存储、进度统计及校验         | B      |
| `reminder_scheduler.py` | 善意提醒的调度与触发逻辑             | B      |
| `utils.py`              | 通用工具函数（日期处理、日志封装等） | B      |

### 测试（开发者 A & B 协同）

| 测试脚本                           | 测试内容             | 负责人 |
| ---------------------------------- | -------------------- | ------ |
| `tests/test_user_manager.py`       | 用户管理模块单元测试 | A & B  |
| `tests/test_challenge_manager.py`  | 挑战管理模块单元测试 | A & B  |
| `tests/test_progress_tracker.py`   | 打卡模块单元测试     | A & B  |
| `tests/test_reminder_scheduler.py` | 提醒调度模块单元测试 | A & B  |

### 根目录文件

| 文件               | 说明                            | 负责人 |
| ------------------ | ------------------------------- | ------ |
| `main.py`          | 应用程序入口，初始化 GUI 与后端 | A & B  |
| `requirements.txt` | 依赖列表 (版本锁定)             | A & B  |
| `README.md`        | 项目说明与分工参考              | —      |

---

## 开发流程与时间管理

1. **Sprint 1（第1周）**：环境搭建、数据库设计、主框架初始化
2. **Sprint 2（第2周）**：核心模块开发（注册/登录、挑战订阅、打卡、提醒设置）
3. **Sprint 3（第3周）**：模块集成、界面美化、测试覆盖及打包发布

**日常机制**：每日站会（15 分钟）→ 持续集成 (CI) → 代码评审 (PR)

---

## 环境配置

### Conda 环境配置

#### macOS 平台

```bash
# 安装 Miniconda（如果尚未安装）
bash <(curl -L https://repo.anaconda.com/miniconda/Miniconda3-latest-MacOSX-x86_64.sh) -b -p $HOME/miniconda

# 初始化 Conda
$HOME/miniconda/bin/conda init zsh  # 如果使用 zsh 终端
# 或者
$HOME/miniconda/bin/conda init bash  # 如果使用 bash 终端

# 重启终端或执行以下命令使配置生效
source ~/.zshrc  # 如果使用 zsh 终端
# 或者
source ~/.bashrc  # 如果使用 bash 终端

# 创建项目环境
conda create -n kindness_challenge python=3.10

# 激活环境
conda activate kindness_challenge

# 安装依赖
pip install -r requirements.txt
```

#### Windows 平台

```bash
# 安装 Miniconda（需要先下载安装程序）
# 从 https://docs.conda.io/en/latest/miniconda.html 下载 Windows 安装程序并运行

# 打开 Anaconda Prompt（从开始菜单搜索）

# 创建项目环境
conda create -n kindness_challenge python=3.10

# 激活环境
conda activate kindness_challenge

# 安装依赖
pip install -r requirements.txt
```

---

## 备注

- 所有任务请严格依据分工协同推进，完成后在对应分支提交 PR 并标注关联 Issue。
- 如需调整任务优先级或模块负责人，请在第一时间通过团队沟通工具（如 Slack、微信）协商。
- 内置用户 “zym” 密码为 “1”，用于测试登录。

# 善行挑战 (Kindness Challenge) 应用

一个鼓励用户进行善行的桌面应用程序，帮助用户养成良好习惯，传递社会正能量。

## 功能特点

- **用户管理**：注册、登录、个人信息管理
- **挑战订阅**：浏览、订阅和取消订阅各种善行挑战
- **打卡记录**：记录每日完成的善行挑战
- **提醒设置**：自定义提醒时间和频率
- **成就系统**：跟踪进度和获得成就

## 技术栈

- **语言**：Python 3.10+
- **GUI**：PySide6 (Qt for Python)
- **数据库**：SQLite3 (内置模块)
- **任务调度**：APScheduler
- **测试框架**：pytest

## 安装与运行

1. 克隆仓库：

```bash
git clone https://github.com/yourusername/kindness_challenge_app.git
cd kindness_challenge_app
```

2. 创建并激活虚拟环境：

```bash
python -m venv venv
source venv/bin/activate  # Linux/Mac
venv\Scripts\activate  # Windows
```

3. 安装依赖：

```bash
pip install -r kindness_challenge_app/requirements.txt
```

4. 运行应用：

```bash
python kindness_challenge_app/main.py
```

## 项目结构

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
└── README.md                  # 项目说明文档 (当前文件)
```

## 测试

运行测试：

```bash
cd kindness_challenge_app
pytest
```

## 贡献

欢迎贡献代码、报告问题或提出改进建议。请遵循以下步骤：

1. Fork 仓库
2. 创建功能分支 (`git checkout -b feature/amazing-feature`)
3. 提交更改 (`git commit -m 'Add some amazing feature'`)
4. 推送到分支 (`git push origin feature/amazing-feature`)
5. 创建 Pull Request

## 许可证

本项目采用 MIT 许可证 - 详情请参阅 [LICENSE](LICENSE) 文件。

## 联系方式

如有任何问题或建议，请联系项目维护者：

- 电子邮件：241880200@smail.nju.edu.cn
- GitHub：[nju-zym](https://github.com/nju-zym)

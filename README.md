
# **Kindness Companion (善意伴侣) 应用**

一个旨在通过技术传递善意、鼓励用户实践并反思日常善行的桌面应用程序。本项目旨在参与“代码有温度 ——用软件守护每一份善意”竞赛。

## **✨ 核心特性 (MVP)**

* **💖 情感化设计:** 温暖的视觉风格、流畅的交互体验，营造积极氛围。
* **🎯 善行挑战:** 浏览、订阅和追踪多样化的善行挑战。
* **✍️ 每日打卡与反思:** 记录善行完成情况，并进行简短的个人反思（本地存储）。
* **🏆 进度与成就:** 可视化追踪您的善行旅程，解锁基础成就徽章。
* **⏰ 基础提醒:** 设置每日提醒，帮助养成善行习惯。
* **🔒 本地优先与隐私:** 核心数据存储在本地 SQLite 数据库，尊重用户隐私。
* **🤖 AI 电子宠物:** 提供情感陪伴，根据用户情绪和善举进行互动和激励（如治愈犬、智慧猫）。
* **📊 AI 善举报告:** 生成个性化的图文报告（日/周/年）和数据洞察，可视化善举历程。
* **🎯 AI 个性化推荐:** 基于用户行为和偏好，利用协同过滤与强化学习动态推荐合适的善行挑战。
* **🎮 AI 优化激励:** 利用 AI 优化游戏化元素（如勋章解锁顺序、动态积分），提升用户参与度和留存。

## **🚀 可选特性 (未来增强)**

* **🤝 匿名善意墙:** \[可选] 查看社区分享的匿名善意故事，感受集体温暖 (只读)。
* **💌 匿名分享:** \[可选] 选择性地将您的匿名善行感想分享到善意墙。
* **🔔 高级提醒:** \[可选] 更灵活的提醒设置选项。

## **🛠️ 技术栈**

* **语言:** Python 3.10+
* **GUI:** PySide6
* **本地数据库:** SQLite3
* **任务调度:** APScheduler / sched
* **后端 API (可选):** Flask / FastAPI
* **AI 服务:** Hugging Face Transformers, OpenAI API, Stability AI 等 (根据具体功能选择)
* **数据处理/分析 (AI 相关):** PySpark, Pandas, Scikit-learn, Surprise
* **测试:** pytest

## **🔧 环境配置与运行**

```bash
# 1. 创建并激活 Conda 环境
conda create -n kindness_companion python=3.10
conda activate kindness_companion

# 2. 安装依赖
pip install -r requirements.txt

# 3. [可选] 配置 API 密钥
# - 如果使用 AI 或社区功能，请按照 config.py 中的说明安全配置 API 密钥。
# - 切勿将密钥直接写入代码或提交到版本控制！

# 4. 运行应用
python main.py
```

## 📂 项目结构

```
kindness_companion_app/
├── frontend/                  # 前端模块 (PySide6 GUI 或 Flutter)
│   ├── __init__.py
│   ├── main_window.py         # 主应用窗口框架与导航
│   ├── user_auth.py           # 用户注册/登录界面
│   ├── challenge_ui.py        # 挑战浏览、订阅、详情、推荐界面
│   ├── checkin_ui.py          # 每日打卡、反思记录、AI引导界面
│   ├── progress_ui.py         # 个人进度、成就(徽章)、AI报告展示界面
│   ├── reminder_ui.py         # 提醒设置界面
│   ├── pet_ui.py              # AI电子宠物交互界面 (Lottie/Unity渲染)
│   ├── profile_ui.py          # 用户设置界面 (未来可扩展)
│   ├── community_ui.py        # [可选] 社区善意墙展示界面
│   └── widgets/               # 可重用自定义控件
│       └──...
├── backend/                   # 本地后端逻辑
│   ├── __init__.py
│   ├── database_manager.py    # SQLite/Firebase 管理 (表结构, CRUD)
│   ├── user_manager.py        # 本地用户认证、会话管理
│   ├── challenge_manager.py   # 挑战数据管理、订阅逻辑
│   ├── progress_tracker.py    # 打卡记录、基础成就解锁逻辑
│   ├── reminder_scheduler.py  # 本地提醒调度
│   └── utils.py               # 本地工具函数 (日期, 日志等)
├── ai_core/                   # AI核心功能模块
│   ├── __init__.py
│   ├── emotion_analyzer.py    # 情绪识别 (RoBERTa)
│   ├── dialogue_generator.py  # 对话生成 (GPT)
│   ├── report_generator.py    # 善举报告生成 (GPT-4, Stable Diffusion, K-Means)
│   ├── recommendation_engine.py # 推荐系统 (Surprise, DQN, TF-IDF)
│   ├── gamification_optimizer.py # 激励机制优化 (BPR, Isolation Forest)
│   └── models/                # 预训练模型或配置文件
├── api/                       # [可选] 轻量级后端 API (Flask/FastAPI)
│   ├── __init__.py
│   ├── app.py                 # API 应用实例与路由
│   ├── community_handler.py   # [可选] 处理匿名分享、获取善意墙数据
│   ├── ai_handler.py          # 代理对外部 AI API 的调用或调用 ai_core 模块
│   └── api_utils.py           # API 相关工具函数
├── resources/                 # 应用资源 (图标, 图片, 样式表, Lottie动画)
│   ├── icons/
│   ├── images/
│   ├── styles/
│   └── animations/
├── tests/                     # 单元测试与集成测试
│   ├── test_backend/
│   ├── test_ai_core/
│   └── test_api/              # [可选] API 测试
├── main.py                    # 应用启动入口
├── requirements.txt           # Python 依赖列表
├── config.py                  # 配置文件 (如 API Keys 的安全处理方式)
└── README.md                  # 项目说明文档 (本文件)
.gitignore
```

## 🤝 贡献指南

欢迎贡献代码、报告问题或提出改进建议。请遵循以下步骤：

1.  Fork 仓库
2.  创建功能分支 (`git checkout -b feature/amazing-feature`)
3.  提交更改 (`git commit -m 'Add some amazing feature'`)
4.  推送到分支 (`git push origin feature/amazing-feature`)
5.  创建 Pull Request

## 📜 开源许可

本项目采用 LGPLv3 许可证。详情请见(LICENSE) 文件。PySide6 本身也使用 LGPLv3 等许可。

## ⚠️ 伦理与隐私声明

  * **数据本地优先/云端存储说明:** 核心用户数据默认存储在本地设备，部分 AI 功能可能需要云端处理和存储（如 Firebase），将明确告知。
  * **知情同意:** 对于所有 AI 功能（特别是情绪分析、个性化推荐），应用将在使用前明确告知用户数据用途、分析范围，并获取用户授权。
  * **数据加密:** 采用强加密措施（如 AES-256）保护本地和传输中的用户数据。
  * **AI 使用透明:** 明确告知用户 AI 在各功能中的参与程度及其局限性，避免过度承诺。
  * **匿名化处理:** 对于可选的社区分享功能，将采取匿名化措施保护用户身份。用户对是否分享拥有完全控制权。
  * **数据安全:** 尽力采取合理的安全措施保护本地数据和 API 通信。对于敏感的心理健康相关数据处理，需格外谨慎，遵循相关法规。
  * **防作弊机制:** 部署机制检测和处理异常行为，确保激励系统的公平性。

## 联系方式

如有任何问题或建议，请联系项目维护者：

  * 电子邮件：241880200@smail.nju.edu.cn
  * GitHub：[nju-zym](https://www.google.com/search?q=https://github.com/nju-zym)


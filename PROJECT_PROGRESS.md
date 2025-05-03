# Kindness Companion (善意伴侣) v3.0 项目进展与计划

**最后更新:** 2025-05-03

## 1. 项目概述

本应用旨在通过技术传递善意，鼓励用户实践并反思日常善行。v3.0 版本采用 "API 优先" 策略，将 AI 功能通过调用云端 API 实现，以提高可移植性和简化打包。

核心理念包括鼓励实践、促进反思、提供 AI 陪伴、可视化进步和尊重隐私。

## 2. 当前进展 (已完成 / 基本完成)

*   **✅ 基础框架:**
    *   项目结构已按 `README.md` (API 优先版) 搭建，包含 `frontend`, `backend`, `ai_core`, `api`, `resources`, `tests` 等目录。
    *   使用 Python 3.10+ 和 PySide6 构建。
*   **✅ 核心本地功能 (Backend):**
    *   `backend/database_manager.py`: SQLite 数据库连接和基本操作封装。
    *   `backend/user_manager.py`: 用户注册、登录、密码管理。
    *   `backend/challenge_manager.py`: 预设挑战的加载、用户订阅管理。
    *   `backend/progress_tracker.py`: 基础的打卡记录、数据查询（总次数、分类次数、连胜等）逻辑。
    *   `backend/reminder_scheduler.py`: 使用 APScheduler 实现本地提醒的基础框架。
*   **✅ 前端 UI (Frontend):**
    *   `frontend/main_window.py`: 应用主窗口框架。
    *   各子界面 (`challenge_ui.py`, `checkin_ui.py`, `profile_ui.py`, `progress_ui.py`, `reminder_ui.py`, `user_auth.py`) 的基本 UI 文件已创建。
    *   `frontend/progress_ui.py`: 实现了进度统计、日历高亮、打卡记录表格、成就徽章的加载和展示逻辑。
    *   `frontend/widgets/`: 包含一些自定义控件，如 `AnimatedMessageBox`。
*   **✅ 应用配置与资源:**
    *   `main.py`: 应用入口，包含字体加载 (`load_fonts`)、主题管理 (`ThemeManager` 支持浅色/深色模式切换)、基础组件初始化。
    *   `resources/`: 包含图标、字体、样式表 (QSS)、动画等资源。
    *   `resources.qrc` 和 `resources_rc.py`: 用于将资源编译进应用。
*   **✅ 打包与分发:**
    *   `README.md` 提供了详细的 macOS PyInstaller 打包指南，包括 `.spec` 文件配置示例。

## 3. 进行中 / 待办事项 (TODO)

### 3.1 MVP (最小可行产品)

*   **🤖 AI 核心 API 集成 (`ai_core/`):**
    *   `dialogue_generator.py`: **TODO:** 实现调用云端对话 API (如 GPT, Gemini) 的逻辑。
    *   `emotion_analyzer.py`: **TODO:** 实现调用云端情感分析 API 的逻辑。
    *   `pet_handler.py`: **TODO:** 实现核心宠物交互逻辑，集成 `dialogue_generator` 和 `emotion_analyzer` 的 API 调用。
    *   `report_generator.py`: **TODO:** 实现调用云端文本生成 API 生成善举报告的逻辑。
    *   `api_client.py`: (可能需要完善) 封装通用的 API 请求逻辑，包括认证、错误处理、重试。
*   **🎨 前端 AI 功能集成 (`frontend/`):**
    *   `pet_ui.py`: **TODO:** 实现 AI 电子宠物交互界面逻辑，连接 `ai_core.pet_handler`，处理用户输入，展示宠物动画和对话。
    *   (待定) 在 `progress_ui.py` 或新界面中展示由 `report_generator` 生成的 AI 报告。
*   **🔒 隐私与安全:**
    *   **TODO:** 实现明确的用户同意 (Opt-in) 流程，让用户在首次使用 AI 功能前知晓数据将被发送至第三方 API 并同意。(#README.md:194, #README.md:34)
    *   **TODO:** 提供设置选项，允许用户禁用 AI 功能或撤销同意。(#README.md:194)
    *   **TODO:** 确保 `config.py` 中的 API Key 安全管理（遵循 README 建议，如使用环境变量）。(#README.md:90, #README.md:108, #README.md:198)
*   **🧪 测试:**
    *   `tests/test_ai_core/`: **TODO:** 为 `ai_core` 中的模块添加单元测试，特别是 API 请求的构建和响应的处理逻辑 (使用 mock)。(#README.md:158)

### 3.2 未来增强特性 (Post-MVP)

*   **🎯 AI 个性化推荐 (`ai_core/` & `frontend/`):**
    *   `recommendation_engine.py`: **TODO:** 实现调用推荐系统 API 或文本分析/向量数据库 API 的逻辑。(#README.md:58)
    *   `frontend/`: **TODO:** 在挑战浏览等界面集成推荐结果。
*   **🎮 AI 优化激励机制 (`ai_core/`):**
    *   `gamification_optimizer.py`: **TODO:** 实现调用机器学习/分析 API 的逻辑，为调整游戏化元素提供建议。(#README.md:65)
*   **🤝 匿名善意墙 (`api/` & `frontend/`):**
    *   `api/community_handler.py`: **TODO:** 实现自建后端 API (Flask/FastAPI) 的端点，用于发布和获取匿名分享 (需要配合云数据库)。(#README.md:70)
    *   `frontend/community_ui.py`: **TODO:** 实现展示匿名善意墙的前端界面。
    *   `api/app.py`: **TODO:** 注册 `community_handler` 蓝图。
*   **📦 打包与分发:**
    *   **TODO:** 完善 macOS 的代码签名和公证流程。(#README.md:328)
    *   **TODO:** (可选) 研究其他平台 (Windows, Linux) 的打包。

## 4. 下一步计划 (优先级)

1.  **完成 MVP AI 功能集成:**
    *   配置好 `config.py` 并确保在 `.gitignore` 中。
    *   实现 `ai_core` 中各模块的 API 调用逻辑 (`dialogue_generator`, `emotion_analyzer`, `report_generator`)。
    *   实现 `ai_core.pet_handler` 的核心逻辑。
    *   在 `frontend.pet_ui` 中实现完整的宠物交互流程。
2.  **实现用户同意与隐私控制:**
    *   添加首次使用 AI 功能时的提示和同意对话框。
    *   在设置界面添加 AI 功能开关。
3.  **编写 AI 核心单元测试:**
    *   为 `ai_core` 模块编写测试用例，mock API 调用。
4.  **集成 AI 报告功能:**
    *   确定报告展示方式 (新界面或集成到 `progress_ui`) 并实现。
5.  **完善 MVP 测试:**
    *   进行 GUI 测试和手动集成测试。
6.  **探索未来增强功能:**
    *   根据优先级逐步实现个性化推荐、游戏化优化或匿名墙功能。

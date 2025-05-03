# Kindness Companion (善意伴侣) v3.0 项目进展与计划

**最后更新:** 2025-05-05

## 1. 项目概述

本应用旨在通过技术传递善意，鼓励用户实践并反思日常善行。v3.0 版本采用 "API 优先" 策略，将 AI 功能通过调用云端 API 实现，以提高可移植性和简化打包。

核心理念包括鼓励实践、促进反思、提供 AI 陪伴、可视化进步和尊重隐私。

## 2. 当前进展 (已完成 / 基本完成)

*   **✅ 基础框架:**
    *   项目结构已按 `README.md` (API 优先版) 搭建，包含 `frontend`, `backend`, `ai_core`, `api`, `resources`, `tests` 等目录。
    *   使用 Python 3.10+ 和 PySide6 构建。
*   **✅ 核心本地功能 (Backend):**
    *   `backend/database_manager.py`: SQLite 数据库连接和基本操作封装。**已添加 AI 同意字段 (`ai_consent_given`)。**
    *   `backend/user_manager.py`: 用户注册、登录、密码管理。**已添加 AI 同意状态管理方法 (`get_ai_consent`, `set_ai_consent`)。**
    *   `backend/challenge_manager.py`: 预设挑战的加载、用户订阅管理。
    *   `backend/progress_tracker.py`: 基础的打卡记录、数据查询（总次数、分类次数、连胜等）逻辑。
    *   `backend/reminder_scheduler.py`: 使用 APScheduler 实现本地提醒的基础框架。
*   **✅ 前端 UI (Frontend):**
    *   `frontend/main_window.py`: 应用主窗口框架。**已集成 `PetWidget` 并连接用户状态信号。**
    *   各子界面 (`challenge_ui.py`, `checkin_ui.py`, `profile_ui.py`, `progress_ui.py`, `reminder_ui.py`, `user_auth.py`) 的基本 UI 文件已创建。
    *   `frontend/progress_ui.py`: 实现了进度统计、日历高亮、打卡记录表格、成就徽章的加载和展示逻辑。
    *   `frontend/widgets/`: 包含一些自定义控件，如 `AnimatedMessageBox`, `BaseDialog`。
    *   `frontend/widgets/ai_consent_dialog.py`: ✅ 已创建 AI 同意对话框 UI。
    *   `frontend/pet_ui.py`: ✅ 已实现 AI 电子宠物交互界面逻辑，连接 `ai_core.pet_handler`。**已集成 AI 同意检查和对话框弹出逻辑。** **已实现 GIF 动画圆形遮罩和透明背景。**
    *   `frontend/user_auth.py`: ✅ 实现了登录和注册界面。**已集成 `PetWidget` 以在登录界面显示动画，并修复了动画不显示的 Bug。**
*   **✅ 应用配置与资源:**
    *   `main.py`: 应用入口，包含字体加载 (`load_fonts`)、主题管理 (`ThemeManager` 支持浅色/深色模式切换)、基础组件初始化。
    *   `resources/`: 包含图标、字体、样式表 (QSS)、动画等资源。
    *   `resources.qrc` 和 `resources_rc.py`: 用于将资源编译进应用。
*   **✅ 打包与分发:**
    *   `README.md` 提供了详细的 macOS PyInstaller 打包指南，包括 `.spec` 文件配置示例。
*   **✅ AI 核心 API 集成 (`ai_core/`):**
    *   `api_client.py`: ✅ 封装了通用的 API 请求逻辑。
    *   `dialogue_generator.py`: ✅ 已实现调用 ZhipuAI API 生成对话。
    *   `emotion_analyzer.py`: ✅ 已实现调用 ZhipuAI API 分析情感。
    *   `pet_handler.py`: ✅ 已实现核心宠物交互逻辑，集成对话和情感分析。
    *   `report_generator.py`: ✅ 已实现调用 ZhipuAI API 生成个性化周报，包含丰富的上下文信息和数据比较。
*   **✅ 隐私与安全:**
    *   **✅** 实现明确的用户同意 (Opt-in) 流程：在 `frontend/pet_ui.py` 中首次调用 AI 功能前检查同意状态 (`user_manager.get_ai_consent`)，如果未同意则显示 `AIConsentDialog`，并根据结果更新数据库 (`user_manager.set_ai_consent`)。**已修复同意对话框在每次登录时都弹出的 Bug。**
    *   **✅** 确保 `config.py` 中的 API Key 安全管理（已添加到 `.gitignore`）。

## 3. 进行中 / 待办事项 (TODO)

### 3.1 MVP (最小可行产品)

*   **🤖 AI 核心 API 集成 (`ai_core/`):**
    *   ✅ `report_generator.py`: 已实现调用云端文本生成 API 生成善举报告的逻辑，包含丰富的上下文信息和数据比较。
*   **🎨 前端 AI 功能集成 (`frontend/`):**
    *   ✅ 已在 `progress_ui.py` 中实现 AI 报告展示功能，包括报告生成按钮、报告显示区域、加载状态显示和错误处理。报告生成前会检查用户是否已同意 AI 功能。
*   **🔒 隐私与安全:**
    *   ✅ 已在 `profile_ui.py` 中实现 AI 功能设置开关，允许用户通过复选框启用/禁用 AI 功能，并更新 `ai_consent_given` 状态。设置更改后会显示确认消息，并通过信号通知应用的其他部分。
*   **🧪 测试:**
    *   `tests/test_ai_core/`: ✅ 已为 `report_generator.py` 添加全面的单元测试，包括 API 请求的构建和响应的处理逻辑 (使用 mock)。
    *   **TODO:** 继续为其他 `ai_core` 模块添加单元测试。(#README.md:158)

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

1.  **✅ 实现 AI 功能设置开关:**
    *   ✅ 已在 `profile_ui.py` 中实现 AI 功能设置开关，允许用户通过复选框启用/禁用 AI 功能，并更新 `ai_consent_given` 状态。
2.  **✅ 在前端展示 AI 报告:**
    *   ✅ 已完成 `ai_core.report_generator` 的实现和测试。
    *   ✅ 已确认 `progress_ui.py` 中的报告展示功能正常工作，包括报告生成按钮、报告显示区域、加载状态显示和错误处理。
3.  **继续编写 AI 核心单元测试:**
    *   为其他 `ai_core` 模块编写测试用例，mock API 调用。
4.  **完善 MVP 测试:**
    *   进行 GUI 测试和手动集成测试。
5.  **探索未来增强功能:**
    *   根据优先级逐步实现个性化推荐、游戏化优化或匿名墙功能。

# 善行伴侣 (Kindness Companion) 测试文档

本文档提供了善行伴侣应用的测试框架和测试执行指南。

## 测试框架概述

测试框架包含以下几个主要部分：

1. **后端测试** (`test_backend/`): 使用 unittest 测试后端组件
2. **前端测试** (`test_frontend/`): 使用 pytest-qt 测试前端组件
3. **AI 核心测试** (`test_ai_core/`): 使用 unittest 测试 AI 功能
4. **API 测试** (`test_api/`): 使用 unittest 测试 API 功能
5. **综合测试运行器** (`run_comprehensive_tests.py`): 运行所有测试并生成报告

## 测试环境设置

### 安装测试依赖

```bash
# 安装测试依赖
pip install -r tests/requirements-test.txt
```

### 测试环境要求

- Python 3.10+
- PySide6
- 测试依赖项（见 `requirements-test.txt`）
- 对于前端测试，需要一个图形环境（或虚拟显示器如 Xvfb）

## 运行测试

### 运行所有测试

```bash
# 从项目根目录运行
python -m kindness_companion_app.tests.run_comprehensive_tests

# 生成 HTML 报告
python -m kindness_companion_app.tests.run_comprehensive_tests --html-report

# 显示详细输出
python -m kindness_companion_app.tests.run_comprehensive_tests --verbose
```

### 运行特定类别的测试

```bash
# 运行后端测试
python -m kindness_companion_app.tests.run_tests --backend

# 运行前端测试
python -m kindness_companion_app.tests.run_tests --frontend

# 运行 AI 核心测试
python -m kindness_companion_app.tests.run_tests --ai

# 运行 API 测试
python -m kindness_companion_app.tests.run_tests --api
```

### 运行单个测试文件

```bash
# 运行单个后端测试文件
python -m unittest kindness_companion_app.tests.test_backend.test_database_manager

# 运行单个前端测试文件
python -m pytest kindness_companion_app/tests/test_frontend/test_main_window.py
```

## 测试报告

当使用 `--html-report` 选项运行测试时，测试报告将生成在 `test_reports/` 目录下：

- `test_reports/backend/`: 后端测试报告
- `test_reports/frontend/`: 前端测试报告
- `test_reports/ai_core/`: AI 核心测试报告
- `test_reports/api/`: API 测试报告
- `test_reports/summary.html`: 综合测试摘要报告

## 测试覆盖率

要生成测试覆盖率报告，可以使用 `coverage` 工具：

```bash
# 安装 coverage
pip install coverage

# 运行测试并收集覆盖率数据
coverage run -m kindness_companion_app.tests.run_comprehensive_tests

# 生成覆盖率报告
coverage report

# 生成 HTML 覆盖率报告
coverage html
```

HTML 覆盖率报告将生成在 `htmlcov/` 目录下。

## 测试结构

### 后端测试

后端测试位于 `test_backend/` 目录，使用 unittest 框架。主要测试以下组件：

- `test_database_manager.py`: 测试数据库连接和操作
- `test_user_manager.py`: 测试用户管理功能
- `test_challenge_manager.py`: 测试挑战管理功能
- `test_progress_tracker.py`: 测试进度跟踪功能
- `test_reminder_scheduler.py`: 测试提醒调度功能

### 前端测试

前端测试位于 `test_frontend/` 目录，使用 pytest-qt 框架。主要测试以下组件：

- `test_main_window.py`: 测试主窗口功能
- `test_pet_ui.py`: 测试宠物界面功能
- `test_progress_ui.py`: 测试进度界面功能
- `test_challenge_ui.py`: 测试挑战界面功能
- `test_checkin_ui.py`: 测试打卡界面功能

### AI 核心测试

AI 核心测试位于 `test_ai_core/` 目录，使用 unittest 框架。主要测试以下组件：

- `test_pet_handler.py`: 测试宠物交互处理功能
- `test_report_generator.py`: 测试报告生成功能
- `test_dialogue_generator.py`: 测试对话生成功能
- `test_emotion_analyzer.py`: 测试情感分析功能
- `test_enhanced_dialogue_generator.py`: 测试增强对话生成功能

### API 测试

API 测试位于 `test_api/` 目录，使用 unittest 框架。主要测试以下组件：

- `test_api_client.py`: 测试 API 客户端功能
- `test_community_api.py`: 测试社区 API 功能

## 编写新测试

### 后端测试

```python
import unittest
from unittest.mock import MagicMock
from backend.your_module import YourClass

class TestYourClass(unittest.TestCase):
    def setUp(self):
        # 设置测试环境
        self.mock_dependency = MagicMock()
        self.your_class = YourClass(self.mock_dependency)
    
    def test_your_method(self):
        # 配置 mock
        self.mock_dependency.some_method.return_value = "expected_value"
        
        # 调用被测试的方法
        result = self.your_class.your_method()
        
        # 验证结果
        self.assertEqual(result, "expected_value")
        
        # 验证 mock 被正确调用
        self.mock_dependency.some_method.assert_called_once()
```

### 前端测试

```python
import pytest
from PySide6.QtCore import Qt
from frontend.your_widget import YourWidget

def test_your_widget(qtbot):
    # 创建部件
    widget = YourWidget()
    
    # 添加部件到 qtbot
    qtbot.addWidget(widget)
    
    # 与部件交互
    qtbot.mouseClick(widget.button, Qt.LeftButton)
    
    # 验证结果
    assert widget.label.text() == "expected_text"
```

## 持续集成

本测试框架设计为可以在持续集成环境中运行。在 CI 环境中，可以使用以下命令运行测试：

```bash
# 安装依赖
pip install -r requirements.txt
pip install -r tests/requirements-test.txt

# 运行测试并生成报告
python -m kindness_companion_app.tests.run_comprehensive_tests --html-report
```

## 故障排除

### 前端测试问题

- **问题**: 在无头环境（如 CI 服务器）中运行前端测试失败
- **解决方案**: 安装并使用 Xvfb 虚拟显示服务器
  ```bash
  sudo apt-get install xvfb
  xvfb-run python -m kindness_companion_app.tests.run_tests --frontend
  ```

### 测试数据库问题

- **问题**: 测试修改了实际的数据库
- **解决方案**: 确保测试使用临时数据库或 mock 数据库管理器

### AI API 测试问题

- **问题**: AI API 测试需要真实的 API 密钥
- **解决方案**: 使用 mock 对象模拟 API 响应，避免实际调用 API

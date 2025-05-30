# 资源文件管理说明

## 背景

本项目使用Qt资源系统来管理图标、图片、字体和样式文件。编译后的资源文件（`resources_rc.py`）可能非常大（>600MB），因此被排除在git版本控制之外。

## 文件说明

- `kindness_companion_app/resources/resources.qrc` - Qt资源配置文件（包含在git中）
- `kindness_companion_app/resources/resources_rc.py` - 编译后的资源文件（被gitignore，需要本地生成）
- `generate_resources.py` - 资源文件生成脚本

## 使用方法

### 首次设置或克隆项目后

1. 确保已安装PySide6：
   ```bash
   pip install PySide6
   ```

2. 运行资源生成脚本：
   ```bash
   python generate_resources.py
   ```

### 修改资源后

如果您修改了`resources.qrc`文件或添加了新的资源文件，需要重新生成：

```bash
python generate_resources.py
```

## 重要提示

- **不要**将`resources_rc.py`文件提交到git
- **不要**将`resources.py`文件提交到git（如果存在）
- 这些文件已被添加到`.gitignore`中
- 每次修改资源后都需要重新运行生成脚本

## 故障排除

### 问题：找不到pyside6-rcc命令
**解决方案：** 确保已正确安装PySide6
```bash
pip install PySide6
```

### 问题：生成的文件过大
这是正常的，因为资源文件包含了所有的图标、图片、字体等二进制数据。这就是为什么我们不将其包含在git中的原因。

### 问题：应用程序运行时找不到资源
确保已运行`python generate_resources.py`来生成`resources_rc.py`文件。

## Git提交最佳实践

1. 修改`.qrc`文件后，先运行生成脚本测试
2. 只提交`.qrc`文件和其他源代码文件
3. 不要提交生成的资源文件
4. 在README中说明新加入项目的开发者需要运行生成脚本
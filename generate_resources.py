#!/usr/bin/env python3
"""
Qt资源文件生成脚本
用于重新生成被gitignore的大型资源文件
"""

import os
import subprocess
import sys
from pathlib import Path


def generate_resources():
    """生成Qt资源文件"""
    # 获取项目根目录
    project_root = Path(__file__).parent
    resources_dir = project_root / "kindness_companion_app" / "resources"
    qrc_file = resources_dir / "resources.qrc"
    output_file = resources_dir / "resources_rc.py"

    # 检查qrc文件是否存在
    if not qrc_file.exists():
        print(f"错误: 找不到资源文件 {qrc_file}")
        return False

    # 检查pyside6-rcc命令是否可用
    try:
        subprocess.run(["pyside6-rcc", "--help"], capture_output=True, check=True)
    except (subprocess.CalledProcessError, FileNotFoundError):
        print("错误: 找不到pyside6-rcc命令")
        print("请确保已安装PySide6:")
        print("pip install PySide6")
        return False

    try:
        # 生成resources_rc.py文件
        print(f"正在生成 {output_file}...")
        cmd = ["pyside6-rcc", str(qrc_file), "-o", str(output_file)]

        result = subprocess.run(cmd, capture_output=True, text=True)

        if result.returncode == 0:
            print(f"✅ 成功生成 {output_file}")
            # 显示文件大小
            file_size = output_file.stat().st_size / (1024 * 1024)  # MB
            print(f"   文件大小: {file_size:.2f} MB")
            return True
        else:
            print(f"❌ 生成失败:")
            print(f"stdout: {result.stdout}")
            print(f"stderr: {result.stderr}")
            return False

    except Exception as e:
        print(f"❌ 生成过程中发生错误: {e}")
        return False


def main():
    """主函数"""
    print("Qt资源文件生成工具")
    print("=" * 50)

    if generate_resources():
        print("\n✅ 资源文件生成完成!")
        print("\n注意: 生成的resources_rc.py文件已被添加到.gitignore中")
        print("这样可以避免将大文件提交到git仓库")
        print("每次克隆项目后都需要运行此脚本来重新生成资源文件")
    else:
        print("\n❌ 资源文件生成失败!")
        sys.exit(1)


if __name__ == "__main__":
    main()

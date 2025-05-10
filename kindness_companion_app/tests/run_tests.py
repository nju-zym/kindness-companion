#!/usr/bin/env python3
"""
Comprehensive test runner for the Kindness Companion application.
This script can run all tests or specific test categories.

Usage:
    python run_tests.py [--backend] [--frontend] [--ai] [--all] [--verbose]

Options:
    --backend   Run backend tests only
    --frontend  Run frontend tests only
    --ai        Run AI core tests only
    --all       Run all tests (default)
    --verbose   Show verbose output
"""

import os
import sys
import argparse
import unittest
import pytest
import logging
from pathlib import Path

# Add the parent directory to the Python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[
        logging.FileHandler("test_results.log"),
        logging.StreamHandler(sys.stdout),
    ],
)
logger = logging.getLogger("test_runner")


def run_backend_tests(verbose=False):
    """Run backend tests using unittest."""
    logger.info("Running backend tests...")

    # Create a test suite for backend tests
    test_loader = unittest.TestLoader()
    backend_test_dir = os.path.join(os.path.dirname(__file__), "test_backend")
    backend_suite = test_loader.discover(backend_test_dir, pattern="test_*.py")

    # Run the tests
    runner = unittest.TextTestRunner(verbosity=2 if verbose else 1)
    result = runner.run(backend_suite)

    return result.wasSuccessful()


def run_ai_tests(verbose=False):
    """Run AI core tests using unittest."""
    logger.info("Running AI core tests...")

    # Create a test suite for AI core tests
    test_loader = unittest.TestLoader()
    ai_test_dir = os.path.join(os.path.dirname(__file__), "test_ai_core")
    ai_suite = test_loader.discover(ai_test_dir, pattern="test_*.py")

    # Run the tests
    runner = unittest.TextTestRunner(verbosity=2 if verbose else 1)
    result = runner.run(ai_suite)

    return result.wasSuccessful()


def run_frontend_tests(verbose=False):
    """Run frontend tests using pytest-qt."""
    logger.info("Running frontend tests...")

    # Use pytest for frontend tests (pytest-qt)
    frontend_test_dir = os.path.join(os.path.dirname(__file__), "test_frontend")
    args = [frontend_test_dir, "-v"] if verbose else [frontend_test_dir]

    # Run pytest
    result = pytest.main(args)

    return result == 0  # pytest.ExitCode.OK == 0


def run_all_tests(verbose=False):
    """Run all tests."""
    logger.info("Running all tests...")

    # Run each test category
    backend_success = run_backend_tests(verbose)
    ai_success = run_ai_tests(verbose)
    frontend_success = run_frontend_tests(verbose)

    # Return overall success
    return backend_success and ai_success and frontend_success


def run_tests():
    """运行所有测试"""
    try:
        # 获取测试目录
        test_dir = os.path.dirname(os.path.abspath(__file__))

        # 运行测试
        logger.info("开始运行测试...")
        result = pytest.main(
            [
                test_dir,
                "-v",  # 详细输出
                "--tb=short",  # 简短的错误回溯
                "--cov=kindness_companion_app",  # 代码覆盖率报告
                "--cov-report=term-missing",  # 显示未覆盖的代码行
                "--cov-report=html",  # 生成HTML覆盖率报告
            ]
        )

        # 检查测试结果
        if result == 0:
            logger.info("所有测试通过！")
        else:
            logger.error(f"测试失败，退出代码: {result}")

        return result

    except Exception as e:
        logger.error(f"运行测试时发生错误: {str(e)}")
        return 1


def main():
    """Parse arguments and run tests."""
    parser = argparse.ArgumentParser(
        description="Run tests for Kindness Companion application."
    )
    parser.add_argument("--backend", action="store_true", help="Run backend tests only")
    parser.add_argument(
        "--frontend", action="store_true", help="Run frontend tests only"
    )
    parser.add_argument("--ai", action="store_true", help="Run AI core tests only")
    parser.add_argument("--all", action="store_true", help="Run all tests (default)")
    parser.add_argument("--verbose", action="store_true", help="Show verbose output")

    args = parser.parse_args()

    # If no specific test category is specified, run all tests
    if not (args.backend or args.frontend or args.ai or args.all):
        args.all = True

    # Run the specified tests
    success = True
    if args.backend:
        success = success and run_backend_tests(args.verbose)
    if args.frontend:
        success = success and run_frontend_tests(args.verbose)
    if args.ai:
        success = success and run_ai_tests(args.verbose)
    if args.all:
        success = run_all_tests(args.verbose)

    # Return exit code
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    sys.exit(run_tests())

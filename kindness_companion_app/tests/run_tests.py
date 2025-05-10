#!/usr/bin/env python3
"""
Test runner for the Kindness Companion application.
This script discovers and runs all tests in the tests directory.
"""

import unittest
import sys
import os
import coverage
import argparse
from datetime import datetime


def run_tests(verbose=False, coverage_report=False):
    """Run all tests in the tests directory."""
    # Start coverage if requested
    if coverage_report:
        cov = coverage.Coverage()
        cov.start()

    # Discover and run tests
    loader = unittest.TestLoader()
    start_dir = os.path.dirname(os.path.abspath(__file__))
    suite = loader.discover(start_dir, pattern="test_*.py")

    # Run tests
    runner = unittest.TextTestRunner(verbosity=2 if verbose else 1)
    result = runner.run(suite)

    # Generate coverage report if requested
    if coverage_report:
        cov.stop()
        cov.save()

        # Generate HTML report
        report_dir = os.path.join(start_dir, "coverage_report")
        os.makedirs(report_dir, exist_ok=True)
        cov.html_report(directory=report_dir)

        # Print coverage summary
        print("\nCoverage Summary:")
        cov.report()

    return result.wasSuccessful()


def main():
    """Main entry point for the test runner."""
    parser = argparse.ArgumentParser(description="Run Kindness Companion tests")
    parser.add_argument(
        "-v", "--verbose", action="store_true", help="Run tests in verbose mode"
    )
    parser.add_argument(
        "-c", "--coverage", action="store_true", help="Generate coverage report"
    )
    args = parser.parse_args()

    # Add the parent directory to sys.path
    sys.path.insert(
        0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../.."))
    )

    # Run tests
    print(f"\nRunning tests at {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    success = run_tests(args.verbose, args.coverage)

    # Exit with appropriate status code
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()

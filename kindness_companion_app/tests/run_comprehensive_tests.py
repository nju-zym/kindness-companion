#!/usr/bin/env python3
"""
Comprehensive test suite for the Kindness Companion application.
This script runs all tests and generates a detailed report.

Usage:
    python run_comprehensive_tests.py [--html-report] [--verbose]

Options:
    --html-report  Generate an HTML report
    --verbose      Show verbose output
"""

import os
import sys
import argparse
import unittest
import pytest
import logging
import time
from pathlib import Path
from datetime import datetime

# Add the parent directory to the Python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("comprehensive_test_runner")

def run_backend_tests(verbose=False, html_report=False):
    """Run backend tests using unittest."""
    logger.info("Running backend tests...")
    start_time = time.time()
    
    # Create a test suite for backend tests
    test_loader = unittest.TestLoader()
    backend_test_dir = os.path.join(os.path.dirname(__file__), 'test_backend')
    backend_suite = test_loader.discover(backend_test_dir, pattern='test_*.py')
    
    # Run the tests
    if html_report:
        import HtmlTestRunner
        runner = HtmlTestRunner.HTMLTestRunner(
            output='test_reports/backend',
            report_name="backend_test_report",
            combine_reports=True,
            verbosity=2 if verbose else 1
        )
    else:
        runner = unittest.TextTestRunner(verbosity=2 if verbose else 1)
    
    result = runner.run(backend_suite)
    
    elapsed_time = time.time() - start_time
    logger.info(f"Backend tests completed in {elapsed_time:.2f} seconds")
    
    return result.wasSuccessful()

def run_ai_tests(verbose=False, html_report=False):
    """Run AI core tests using unittest."""
    logger.info("Running AI core tests...")
    start_time = time.time()
    
    # Create a test suite for AI core tests
    test_loader = unittest.TestLoader()
    ai_test_dir = os.path.join(os.path.dirname(__file__), 'test_ai_core')
    ai_suite = test_loader.discover(ai_test_dir, pattern='test_*.py')
    
    # Run the tests
    if html_report:
        import HtmlTestRunner
        runner = HtmlTestRunner.HTMLTestRunner(
            output='test_reports/ai_core',
            report_name="ai_core_test_report",
            combine_reports=True,
            verbosity=2 if verbose else 1
        )
    else:
        runner = unittest.TextTestRunner(verbosity=2 if verbose else 1)
    
    result = runner.run(ai_suite)
    
    elapsed_time = time.time() - start_time
    logger.info(f"AI core tests completed in {elapsed_time:.2f} seconds")
    
    return result.wasSuccessful()

def run_frontend_tests(verbose=False, html_report=False):
    """Run frontend tests using pytest-qt."""
    logger.info("Running frontend tests...")
    start_time = time.time()
    
    # Use pytest for frontend tests (pytest-qt)
    frontend_test_dir = os.path.join(os.path.dirname(__file__), 'test_frontend')
    
    # Prepare pytest arguments
    args = [frontend_test_dir]
    if verbose:
        args.append('-v')
    
    if html_report:
        # Create the report directory if it doesn't exist
        report_dir = Path('test_reports/frontend')
        report_dir.mkdir(parents=True, exist_ok=True)
        
        # Add HTML report arguments
        report_path = report_dir / f"frontend_test_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.html"
        args.extend(['--html', str(report_path), '--self-contained-html'])
    
    # Run pytest
    result = pytest.main(args)
    
    elapsed_time = time.time() - start_time
    logger.info(f"Frontend tests completed in {elapsed_time:.2f} seconds")
    
    return result == 0  # pytest.ExitCode.OK == 0

def run_api_tests(verbose=False, html_report=False):
    """Run API tests using unittest."""
    logger.info("Running API tests...")
    start_time = time.time()
    
    # Create a test suite for API tests
    test_loader = unittest.TestLoader()
    api_test_dir = os.path.join(os.path.dirname(__file__), 'test_api')
    api_suite = test_loader.discover(api_test_dir, pattern='test_*.py')
    
    # Run the tests
    if html_report:
        import HtmlTestRunner
        runner = HtmlTestRunner.HTMLTestRunner(
            output='test_reports/api',
            report_name="api_test_report",
            combine_reports=True,
            verbosity=2 if verbose else 1
        )
    else:
        runner = unittest.TextTestRunner(verbosity=2 if verbose else 1)
    
    result = runner.run(api_suite)
    
    elapsed_time = time.time() - start_time
    logger.info(f"API tests completed in {elapsed_time:.2f} seconds")
    
    return result.wasSuccessful()

def run_all_tests(verbose=False, html_report=False):
    """Run all tests and generate a summary report."""
    logger.info("Running all tests...")
    start_time = time.time()
    
    # Create the report directory if it doesn't exist
    if html_report:
        report_dir = Path('test_reports')
        report_dir.mkdir(parents=True, exist_ok=True)
    
    # Run each test category
    backend_success = run_backend_tests(verbose, html_report)
    ai_success = run_ai_tests(verbose, html_report)
    frontend_success = run_frontend_tests(verbose, html_report)
    api_success = run_api_tests(verbose, html_report)
    
    # Generate a summary report
    elapsed_time = time.time() - start_time
    logger.info(f"All tests completed in {elapsed_time:.2f} seconds")
    
    # Print a summary
    logger.info("Test Summary:")
    logger.info(f"  Backend tests: {'PASSED' if backend_success else 'FAILED'}")
    logger.info(f"  AI core tests: {'PASSED' if ai_success else 'FAILED'}")
    logger.info(f"  Frontend tests: {'PASSED' if frontend_success else 'FAILED'}")
    logger.info(f"  API tests: {'PASSED' if api_success else 'FAILED'}")
    logger.info(f"  Overall: {'PASSED' if (backend_success and ai_success and frontend_success and api_success) else 'FAILED'}")
    
    # Generate a summary HTML report if requested
    if html_report:
        with open('test_reports/summary.html', 'w') as f:
            f.write(f"""
            <html>
            <head>
                <title>Kindness Companion Test Summary</title>
                <style>
                    body {{ font-family: Arial, sans-serif; margin: 20px; }}
                    h1 {{ color: #333; }}
                    .summary {{ margin-bottom: 20px; }}
                    .passed {{ color: green; }}
                    .failed {{ color: red; }}
                    table {{ border-collapse: collapse; width: 100%; }}
                    th, td {{ border: 1px solid #ddd; padding: 8px; text-align: left; }}
                    th {{ background-color: #f2f2f2; }}
                </style>
            </head>
            <body>
                <h1>Kindness Companion Test Summary</h1>
                <div class="summary">
                    <p>Test run completed at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>
                    <p>Total time: {elapsed_time:.2f} seconds</p>
                </div>
                <table>
                    <tr>
                        <th>Test Category</th>
                        <th>Result</th>
                        <th>Report</th>
                    </tr>
                    <tr>
                        <td>Backend Tests</td>
                        <td class="{'passed' if backend_success else 'failed'}">{'PASSED' if backend_success else 'FAILED'}</td>
                        <td><a href="backend/backend_test_report.html">View Report</a></td>
                    </tr>
                    <tr>
                        <td>AI Core Tests</td>
                        <td class="{'passed' if ai_success else 'failed'}">{'PASSED' if ai_success else 'FAILED'}</td>
                        <td><a href="ai_core/ai_core_test_report.html">View Report</a></td>
                    </tr>
                    <tr>
                        <td>Frontend Tests</td>
                        <td class="{'passed' if frontend_success else 'failed'}">{'PASSED' if frontend_success else 'FAILED'}</td>
                        <td><a href="frontend/">View Reports</a></td>
                    </tr>
                    <tr>
                        <td>API Tests</td>
                        <td class="{'passed' if api_success else 'failed'}">{'PASSED' if api_success else 'FAILED'}</td>
                        <td><a href="api/api_test_report.html">View Report</a></td>
                    </tr>
                </table>
                <h2>Overall Result: <span class="{'passed' if (backend_success and ai_success and frontend_success and api_success) else 'failed'}">{'PASSED' if (backend_success and ai_success and frontend_success and api_success) else 'FAILED'}</span></h2>
            </body>
            </html>
            """)
    
    # Return overall success
    return backend_success and ai_success and frontend_success and api_success

def main():
    """Parse arguments and run tests."""
    parser = argparse.ArgumentParser(description='Run comprehensive tests for Kindness Companion application.')
    parser.add_argument('--html-report', action='store_true', help='Generate HTML reports')
    parser.add_argument('--verbose', action='store_true', help='Show verbose output')
    
    args = parser.parse_args()
    
    # Run all tests
    success = run_all_tests(args.verbose, args.html_report)
    
    # Return exit code
    sys.exit(0 if success else 1)

if __name__ == '__main__':
    main()

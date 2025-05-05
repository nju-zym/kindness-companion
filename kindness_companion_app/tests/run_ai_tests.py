"""
Script to run AI-related tests.
"""

import unittest
import os
import sys

# Add the parent directory to the Python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# Import test modules
from test_ai_core.test_conversation_analyzer import TestConversationAnalyzer
from test_ai_core.test_enhanced_dialogue_generator import TestEnhancedDialogueGenerator

if __name__ == '__main__':
    # Create a test suite
    test_suite = unittest.TestSuite()
    
    # Add test cases
    test_suite.addTest(unittest.makeSuite(TestConversationAnalyzer))
    test_suite.addTest(unittest.makeSuite(TestEnhancedDialogueGenerator))
    
    # Run the tests
    runner = unittest.TextTestRunner(verbosity=2)
    runner.run(test_suite)

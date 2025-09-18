#!/usr/bin/env python3
"""
Test runner for backend modules.
Run this from the project root directory with: PYTHONPATH=. python3 backend/run_tests.py
"""

import sys
import os
import unittest

# Add current directory to path
sys.path.insert(0, os.path.dirname(__file__))

if __name__ == '__main__':
    # Discover and run all tests in the tests directory
    loader = unittest.TestLoader()
    start_dir = os.path.join(os.path.dirname(__file__), 'tests')
    suite = loader.discover(start_dir, pattern='test_*.py')
    
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    
    # Exit with error code if tests failed
    sys.exit(0 if result.wasSuccessful() else 1)
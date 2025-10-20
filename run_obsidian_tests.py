# run_obsidian_tests.py
"""
Test runner for Obsidian export feature.

This script runs all unit and integration tests for the Obsidian export functionality.
"""
import sys
import unittest
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))


def run_all_tests():
    """Run all Obsidian export tests."""
    loader = unittest.TestLoader()

    # Discover all tests in the tests directory
    test_suite = unittest.TestSuite()

    # Add unit tests
    test_suite.addTests(loader.discover('tests/adapters/obsidian', pattern='test_*.py'))
    test_suite.addTests(loader.discover('tests/core/services', pattern='test_obsidian*.py'))

    # Add integration tests
    test_suite.addTests(loader.discover('tests/integration', pattern='test_obsidian*.py'))

    # Run tests with detailed output
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(test_suite)

    # Return exit code based on success
    return 0 if result.wasSuccessful() else 1


def run_unit_tests_only():
    """Run only unit tests (faster)."""
    loader = unittest.TestLoader()
    test_suite = unittest.TestSuite()

    test_suite.addTests(loader.discover('tests/adapters/obsidian', pattern='test_*.py'))
    test_suite.addTests(loader.discover('tests/core/services', pattern='test_obsidian*.py'))

    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(test_suite)

    return 0 if result.wasSuccessful() else 1


def run_integration_tests_only():
    """Run only integration tests."""
    loader = unittest.TestLoader()
    test_suite = unittest.TestSuite()

    test_suite.addTests(loader.discover('tests/integration', pattern='test_obsidian*.py'))

    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(test_suite)

    return 0 if result.wasSuccessful() else 1


if __name__ == '__main__':
    import argparse

    parser = argparse.ArgumentParser(description='Run Obsidian export tests')
    parser.add_argument(
        '--type',
        choices=['all', 'unit', 'integration'],
        default='all',
        help='Type of tests to run (default: all)'
    )

    args = parser.parse_args()

    print("=" * 70)
    print("OBSIDIAN EXPORT FEATURE - TEST SUITE")
    print("=" * 70)
    print()

    if args.type == 'all':
        print("Running all tests (unit + integration)...")
        print()
        exit_code = run_all_tests()
    elif args.type == 'unit':
        print("Running unit tests only...")
        print()
        exit_code = run_unit_tests_only()
    else:
        print("Running integration tests only...")
        print()
        exit_code = run_integration_tests_only()

    print()
    print("=" * 70)
    if exit_code == 0:
        print("ALL TESTS PASSED")
    else:
        print("SOME TESTS FAILED")
    print("=" * 70)

    sys.exit(exit_code)

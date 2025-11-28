#!/usr/bin/env python3
"""
Test runner script for FastAPI GraphQL API.
Runs all tests with coverage reporting.
"""

import subprocess
import sys
import os
from pathlib import Path


def print_header(message: str):
    """Print a formatted header."""
    print("\n" + "=" * 70)
    print(f"  {message}")
    print("=" * 70 + "\n")


def run_command(command: str, description: str) -> bool:
    """Run a command and return success status."""
    print(f"→ {description}...")
    try:
        result = subprocess.run(
            command,
            shell=True,
            check=True,
            text=True
        )
        print(f"✓ {description} completed\n")
        return True
    except subprocess.CalledProcessError as e:
        print(f"✗ {description} failed\n")
        return False


def main():
    """Main test runner function."""
    print("\n╔" + "═" * 68 + "╗")
    print("║" + " " * 20 + "Test Runner" + " " * 37 + "║")
    print("╚" + "═" * 68 + "╝")
    
    try:
        import pytest  # noqa: F401
    except ImportError:
        print("✗ pytest is not installed")
        print("  Run: pip install pytest pytest-asyncio pytest-cov")
        sys.exit(1)
    try:
        import flake8  # noqa: F401
    except ImportError:
        print("⚠  flake8 is not installed")
        print("  Run: pip install flake8")
    
    # Run different test suites
    test_commands = [
        {
            "command": f"{sys.executable} -m pytest tests/ -v",
            "description": "Running all tests"
        },
        {
            "command": f"{sys.executable} -m pytest tests/ -v --cov=app --cov-report=term-missing",
            "description": "Running tests with coverage"
        },
        {
            "command": f"{sys.executable} -m pytest tests/ -v --cov=app --cov-report=html",
            "description": "Generating HTML coverage report"
        },
    ]
    
    print_header("Running Test Suite")
    
    # Ask user which tests to run
    print("Select test mode:")
    print("  1. Run all tests (quick)")
    print("  2. Run tests with coverage report")
    print("  3. Run tests with HTML coverage report")
    print("  4. Run mypy typecheck")
    print("  5. Run all of the above")
    print()
    
    choice = input("Enter choice (1-5) [default: 1]: ").strip() or "1"
    
    if choice == "1":
        run_command(test_commands[0]["command"], test_commands[0]["description"])
    elif choice == "2":
        run_command(test_commands[1]["command"], test_commands[1]["description"])
    elif choice == "3":
        run_command(test_commands[2]["command"], test_commands[2]["description"])
        print("\n→ HTML coverage report generated at: htmlcov/index.html")
    elif choice == "4":
        run_command(
            f"{sys.executable} -m mypy app --ignore-missing-imports", "Running mypy typecheck"
        )
    elif choice == "5":
        for cmd in test_commands:
            if not run_command(cmd["command"], cmd["description"]):
                print("\n⚠️  Some tests failed")
                break
        print("\n→ HTML coverage report generated at: htmlcov/index.html")
        run_command(
            f"{sys.executable} -m mypy app --ignore-missing-imports", "Running mypy typecheck"
        )
        run_command(f"{sys.executable} -m flake8 app --config=.flake8", "Running flake8 linting")
    else:
        print("Invalid choice")
        sys.exit(1)

    
    
    print_header("Test Run Complete")
    
    print("Additional test commands:")
    print(f"  • Run specific test file: {sys.executable} -m pytest tests/test_auth.py -v")
    print(f"  • Run with markers: {sys.executable} -m pytest -m unit")
    print(f"  • Run with verbose output: {sys.executable} -m pytest -vv")
    print(f"  • Run and stop on first failure: {sys.executable} -m pytest -x")
    print()
    print(f"  • Run typecheck: {sys.executable} -m mypy app --ignore-missing-imports")
    print(f"  • Run linting: {sys.executable} -m flake8 app --config=.flake8")


if __name__ == "__main__":
    main()

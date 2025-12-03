#!/usr/bin/env python3
"""
Test runner script for FastAPI GraphQL API.
Runs all tests with coverage reporting and code quality checks.
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


def run_command(command: str, description: str, check: bool = True) -> bool:
    """Run a command and return success status."""
    print(f"→ {description}...")
    try:
        result = subprocess.run(
            command,
            shell=True,
            check=check,
            text=True
        )
        if result.returncode == 0:
            print(f"✓ {description} passed\n")
            return True
        else:
            print(f"✗ {description} failed (exit code {result.returncode})\n")
            return False
    except subprocess.CalledProcessError as e:
        print(f"✗ {description} failed\n")
        return False
    except Exception as e:
        print(f"✗ {description} failed with error: {e}\n")
        return False


def check_dependencies():
    """Check if required dependencies are installed."""
    missing = []
    
    try:
        import pytest  # noqa: F401
    except ImportError:
        missing.append("pytest pytest-asyncio pytest-cov")
        
    try:
        import flake8  # noqa: F401
    except ImportError:
        missing.append("flake8")
        
    try:
        import isort  # noqa: F401
    except ImportError:
        missing.append("isort")
        
    try:
        import black  # noqa: F401
    except ImportError:
        missing.append("black")

    try:
        import mypy  # noqa: F401
    except ImportError:
        missing.append("mypy")
        
    if missing:
        print("⚠  Some dependencies are missing:")
        for dep in missing:
            print(f"  - {dep}")
        print(f"  Run: pip install {' '.join(missing)}")
        print("  Or install all dev dependencies: pip install -r requirements-dev.txt\n")


def run_quality_checks():
    """Run code quality checks."""
    print_header("Running Code Quality Checks")
    
    failed_checks = []
    
    # 1. Check imports sorting (isort)
    if not run_command("isort --check-only app", "Checking import sorting (isort)", check=False):
        failed_checks.append("isort")
        
    # 2. Check code formatting (black)
    if not run_command("black --check app", "Checking code formatting (black)", check=False):
        failed_checks.append("black")
        
    # 3. Check code style (flake8)
    if not run_command("flake8 app --config=.flake8", "Checking code style (flake8)", check=False):
        failed_checks.append("flake8")
        
    # 4. Check static types (mypy)
    if not run_command("mypy app --ignore-missing-imports", "Checking static types (mypy)", check=False):
        failed_checks.append("mypy")

    if failed_checks:
        print("❌ The following checks failed:")
        for check in failed_checks:
            print(f"   - {check}")
        print("\nRun the following to fix formatting issues:")
        print("   isort app")
        print("   black app")
        return False
    else:
        print("✅ All quality checks passed!")
        return True


def main():
    """Main test runner function."""
    print("\n╔" + "═" * 68 + "╗")
    print("║" + " " * 20 + "Test Runner" + " " * 37 + "║")
    print("╚" + "═" * 68 + "╝")
    
    check_dependencies()
    
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
    print("  4. Run code quality checks (isort, black, flake8, mypy)")
    print("  5. Run everything (tests + quality checks)")
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
        if not run_quality_checks():
            sys.exit(1)
    elif choice == "5":
        # Run tests
        for cmd in test_commands:
            if not run_command(cmd["command"], cmd["description"], check=False):
                print("\n⚠️  Some tests failed")
                break
        print("\n→ HTML coverage report generated at: htmlcov/index.html")
        
        # Run quality checks
        if not run_quality_checks():
            sys.exit(1)
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
    print(f"  • Run formatting fix: isort app && black app")
    print(f"  • Run typecheck: {sys.executable} -m mypy app --ignore-missing-imports")
    print(f"  • Run linting: {sys.executable} -m flake8 app --config=.flake8")


if __name__ == "__main__":
    main()

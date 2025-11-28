#!/usr/bin/env python3
"""
FastAPI GraphQL API - Installation and Setup Script
This script handles the complete installation and setup of the project.
"""

import subprocess
import sys
import os
import asyncio
from pathlib import Path


def print_header(message: str):
    """Print a formatted header."""
    print("\n" + "=" * 70)
    print(f"  {message}")
    print("=" * 70 + "\n")


def print_step(step: str, status: str = ""):
    """Print a step with optional status."""
    if status:
        print(f"  [{status}] {step}")
    else:
        print(f"  → {step}")


def run_command(command: str, description: str, check: bool = True) -> bool:
    """Run a shell command and return success status."""
    print_step(description, "...")
    try:
        result = subprocess.run(
            command,
            shell=True,
            check=check,
            capture_output=True,
            text=True
        )
        print_step(description, "✓")
        return True
    except subprocess.CalledProcessError as e:
        print_step(description, "✗")
        if e.stderr:
            print(f"    Error: {e.stderr}")
        return False


def check_python_version():
    """Check if Python version meets requirements."""
    print_header("Checking Python Version")
    version = sys.version_info
    print_step(f"Python {version.major}.{version.minor}.{version.micro} detected")
    
    if version < (3, 8):
        print_step("Python 3.8+ is required", "✗")
        return False
    
    print_step("Python version is compatible", "✓")
    return True


def install_dependencies():
    """Install project dependencies."""
    print_header("Installing Dependencies")
    
    # Upgrade pip
    if not run_command(
        f"{sys.executable} -m pip install --upgrade pip",
        "Upgrading pip"
    ):
        return False
    
    # Install requirements
    if not run_command(
        f"{sys.executable} -m pip install -r requirements.txt",
        "Installing project dependencies"
    ):
        return False
    
    return True


def create_directories():
    """Create necessary project directories."""
    print_header("Creating Project Directories")
    
    directories = [
        "logs",
        "data",
        "backups",
    ]
    
    for directory in directories:
        path = Path(directory)
        path.mkdir(exist_ok=True)
        print_step(f"Created directory: {directory}", "✓")
    
    return True


def setup_environment():
    """Set up environment configuration."""
    print_header("Setting Up Environment Configuration")
    
    env_file = Path(".env")
    
    if env_file.exists():
        print_step(".env file already exists", "✓")
        return True
    
    # Create default .env file
    default_env = """# FastAPI GraphQL API - Environment Configuration

# Application Settings
APP_NAME=FastAPI GraphQL API
DEBUG=True
HOST=0.0.0.0
PORT=8000

# Security Settings
SECRET_KEY=your-secret-key-change-this-in-production
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30
REFRESH_TOKEN_EXPIRE_MINUTES=10080

# Database Settings
MONGODB_URL=mongodb://localhost:27017
DATABASE_NAME=fastapi_graphql_db

# Authentication Settings
REQUIRE_AUTHENTICATION=False
MAX_LOGIN_ATTEMPTS=5
LOCKOUT_DURATION_MINUTES=30

# CORS Settings
ALLOWED_HOSTS=["*"]
"""
    
    env_file.write_text(default_env)
    print_step("Created .env file with default configuration", "✓")
    print_step("⚠️  Please update SECRET_KEY in .env file!", "!")
    
    return True


def setup_gitignore():
    """Set up .gitignore file."""
    print_header("Setting Up .gitignore")
    
    gitignore_file = Path(".gitignore")
    
    gitignore_content = """# Python
__pycache__/
*.py[cod]
*$py.class
*.so
.Python
build/
develop-eggs/
dist/
downloads/
eggs/
.eggs/
lib/
lib64/
parts/
sdist/
var/
wheels/
*.egg-info/
.installed.cfg
*.egg

# Virtual Environment
venv/
env/
ENV/
.venv

# IDE
.vscode/
.idea/
*.swp
*.swo
*~

# Testing
.pytest_cache/
.coverage
htmlcov/
.tox/
.mypy_cache/
.dmypy.json
dmypy.json

# Environment
.env
.env.local
.env.*.local

# Logs
logs/
*.log

# Database
data/
*.db
*.sqlite

# OS
.DS_Store
Thumbs.db

# Project specific
backups/
temp/
debug_*.py
debug_*.txt
test_*.log
*_output.txt
"""
    
    gitignore_file.write_text(gitignore_content)
    print_step("Created .gitignore file", "✓")
    
    return True


async def initialize_database():
    """Initialize the database with default data."""
    print_header("Initializing Database")
    
    print_step("Checking MongoDB connection...")
    
    try:
        # Import here to avoid issues if dependencies aren't installed yet
        sys.path.insert(0, os.getcwd())
        from app.core.motor_database import motor_db_manager
        
        await motor_db_manager.connect()
        print_step("Connected to MongoDB", "✓")
        
        # Run the database initialization script
        print_step("Setting up database schema and default data...")
        
        result = subprocess.run(
            f"{sys.executable} scripts/install_db.py",
            shell=True,
            capture_output=True,
            text=True
        )
        
        if result.returncode == 0:
            print_step("Database initialized successfully", "✓")
            print_step("Default admin user created:", "✓")
            print_step("  Email: admin@example.com")
            print_step("  Password: password123")
        else:
            print_step("Database initialization failed", "✗")
            if result.stderr:
                print(f"    Error: {result.stderr}")
            return False
        
        await motor_db_manager.disconnect()
        
    except Exception as e:
        print_step(f"Database initialization failed: {str(e)}", "✗")
        print_step("⚠️  You can run 'python scripts/install_db.py' manually later", "!")
        return False
    
    return True


def print_next_steps():
    """Print next steps for the user."""
    print_header("Installation Complete!")
    
    print("  Next Steps:")
    print()
    print("  1. Update your .env file with proper configuration")
    print("     - Change SECRET_KEY to a secure random string")
    print("     - Update MONGODB_URL if needed")
    print()
    print("  2. Make sure MongoDB is running:")
    print("     - Windows: Start MongoDB service")
    print("     - Linux/Mac: sudo systemctl start mongod")
    print()
    print("  3. Initialize the database (if not done automatically):")
    print("     python scripts/install_db.py")
    print()
    print("  4. Run tests to verify installation:")
    print("     pytest tests/ -v")
    print()
    print("  5. Start the development server:")
    print("     python run.py")
    print()
    print("  6. Access the application:")
    print("     - API: http://localhost:8000")
    print("     - GraphQL Playground: http://localhost:8000/api/graphql")
    print("     - API Docs: http://localhost:8000/docs")
    print()
    print("  Default Admin Credentials:")
    print("     Email: admin@example.com")
    print("     Password: password123")
    print()
    print("=" * 70 + "\n")


def main():
    """Main installation function."""
    print("\n")
    print("╔" + "═" * 68 + "╗")
    print("║" + " " * 15 + "FastAPI GraphQL API - Setup" + " " * 26 + "║")
    print("╚" + "═" * 68 + "╝")
    
    # Check Python version
    if not check_python_version():
        sys.exit(1)
    
    # Install dependencies
    if not install_dependencies():
        print("\n❌ Installation failed at dependency installation step")
        sys.exit(1)
    
    # Create directories
    if not create_directories():
        print("\n❌ Installation failed at directory creation step")
        sys.exit(1)
    
    # Setup environment
    if not setup_environment():
        print("\n❌ Installation failed at environment setup step")
        sys.exit(1)
    
    # Setup .gitignore
    if not setup_gitignore():
        print("\n❌ Installation failed at .gitignore setup step")
        sys.exit(1)
    
    # Ask user if they want to initialize database
    print_header("Database Initialization")
    print("  Do you want to initialize the database now?")
    print("  (Make sure MongoDB is running)")
    print()
    response = input("  Initialize database? (y/n): ").strip().lower()
    
    if response == 'y':
        try:
            asyncio.run(initialize_database())
        except Exception as e:
            print(f"\n⚠️  Database initialization failed: {e}")
            print("  You can run 'python scripts/install_db.py' manually later")
    else:
        print_step("Skipping database initialization", "!")
        print_step("Run 'python scripts/install_db.py' when ready", "!")
    
    # Print next steps
    print_next_steps()


if __name__ == "__main__":
    main()

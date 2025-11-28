# Contributing to FastAPI GraphQL API

Thank you for your interest in contributing to FastAPI GraphQL API! This document provides guidelines and instructions for contributing.

## Code of Conduct

By participating in this project, you agree to maintain a respectful and inclusive environment for everyone.

## How to Contribute

### Reporting Bugs

If you find a bug, please create an issue with:
- Clear description of the bug
- Steps to reproduce
- Expected vs actual behavior
- Environment details (OS, Python version, etc.)
- Any relevant logs or screenshots

### Suggesting Features

Feature suggestions are welcome! Please create an issue with:
- Clear description of the feature
- Use case and benefits
- Possible implementation approach (optional)

### Pull Requests

1. **Fork the repository**
   ```bash
   git clone https://github.com/n123al/fastapi-graphql-api.git
   cd fastapi-graphql-api
   ```

2. **Create a feature branch**
   ```bash
   git checkout -b feature/your-feature-name
   ```

3. **Set up development environment**
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   pip install -r requirements.txt
   pip install pytest pytest-asyncio pytest-cov black flake8 isort mypy
   ```

4. **Make your changes**
   - Write clean, readable code
   - Follow the existing code style
   - Add tests for new features
   - Update documentation as needed

5. **Run tests**
   ```bash
   pytest tests/ -v
   pytest tests/ --cov=app
   ```

6. **Run code quality checks**
   ```bash
   # Format code
   black app tests
   isort app tests
   
   # Lint code
   flake8 app tests
   
   # Type checking
   mypy app --ignore-missing-imports
   ```

7. **Commit your changes**
   ```bash
   git add .
   git commit -m "feat: add your feature description"
   ```
   
   Use conventional commit messages:
   - `feat:` for new features
   - `fix:` for bug fixes
   - `docs:` for documentation changes
   - `test:` for test additions/changes
   - `refactor:` for code refactoring
   - `style:` for formatting changes
   - `chore:` for maintenance tasks

8. **Push to your fork**
   ```bash
   git push origin feature/your-feature-name
   ```

9. **Create a Pull Request**
   - Go to the original repository
   - Click "New Pull Request"
   - Select your fork and branch
   - Fill in the PR template
   - Link any related issues

## Development Guidelines

### Code Style

- Follow PEP 8 guidelines
- Use type hints where possible
- Write docstrings for functions and classes
- Keep functions small and focused
- Use meaningful variable names

### Testing

- Write unit tests for new features
- Maintain or improve code coverage
- Test edge cases and error conditions
- Use fixtures for common test data
- Mock external dependencies

### Documentation

- Update README.md for user-facing changes
- Add docstrings to new functions/classes
- Update API documentation
- Include code examples where helpful

### Architecture

- Follow clean architecture principles
- Maintain separation of concerns
- Keep business logic in service layer
- Use repository pattern for data access
- Follow existing patterns and conventions

## Project Structure

```
app/
├── core/           # Core functionality (config, security, etc.)
├── data/           # Data layer (models, repositories)
├── services/       # Business logic layer
├── graphql/        # GraphQL schema and resolvers
└── main.py         # Application entry point

tests/
├── unit/           # Unit tests
├── integration/    # Integration tests
└── conftest.py     # Test fixtures

scripts/
└── *.py            # Utility scripts

docs/
└── *.md            # Documentation files
```

## Testing Checklist

Before submitting a PR, ensure:

- [ ] All tests pass
- [ ] Code coverage is maintained or improved
- [ ] Code is formatted with Black
- [ ] Imports are sorted with isort
- [ ] No linting errors from flake8
- [ ] Type hints are added where appropriate
- [ ] Documentation is updated
- [ ] Commit messages follow conventions
- [ ] PR description is clear and complete

## Getting Help

- Check existing issues and documentation
- Ask questions in issue discussions
- Join our community chat (if available)
- Tag maintainers for urgent issues

## Recognition

Contributors will be recognized in:
- README.md contributors section
- Release notes
- Project documentation

Thank you for contributing to FastAPI GraphQL API!

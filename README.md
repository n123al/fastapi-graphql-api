# FastAPI GraphQL API

[![CI](https://github.com/n123al/fastapi-graphql-api/actions/workflows/ci.yml/badge.svg)](https://github.com/n123al/fastapi-graphql-api/actions/workflows/ci.yml)
[![codecov](https://codecov.io/gh/n123al/fastapi-graphql-api/branch/main/graph/badge.svg)](https://codecov.io/gh/n123al/fastapi-graphql-api)
[![Python 3.8+](https://img.shields.io/badge/python-3.8+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Code style: black](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/psf/black)

A modern FastAPI application with Strawberry GraphQL, JWT auth, and clean architecture. Ready for local development and open-source contributions.

## 🏗️ Architecture Overview

This project follows **Clean Architecture** principles with clear separation of concerns across three main layers:

### Directory Structure
```
app/
├── core/           # Config, security, exceptions, database
├── data/           # Models & repositories
├── services/       # Business logic (auth, users)
├── graphql/        # Schema and resolvers
└── main.py         # Application entrypoint
```

## 🚀 Features

### Core Features
- **FastAPI** - Modern, fast web framework
- **GraphQL** - Query language for APIs using Strawberry
- **MongoDB** - NoSQL database with Beanie ODM
- **JWT Authentication** - Secure token-based authentication
- **Role-Based Authorization** - Granular permission system
- **User Management** - Complete user lifecycle management
- **Group Management** - Organize users into groups

### Security Features
- **Password Hashing** - Secure bcrypt password encryption
- **Rate Limiting** - API rate limiting to prevent abuse
- **Account Lockout** - Protection against brute force attacks
- **Email Verification** - User email verification system
- **Token Refresh** - Secure token refresh mechanism

### Architecture Features
- **Object-Oriented Design** - Clean, maintainable code architecture
- **Repository Pattern** - Data access abstraction
- **Service Layer** - Business logic separation
- **Strategy Pattern** - Pluggable authentication strategies
- **Factory Pattern** - Object creation abstraction
- **Observer Pattern** - Event-driven architecture

## 📋 Requirements

- Python 3.8+
- MongoDB 4.4+
- pip (Python package manager)

## 🛠️ Installation

### Quick Start

```bash
# Clone the repository
git clone https://github.com/n123al/fastapi-graphql-api.git
cd fastapi-graphql-api

# Create and activate a virtual environment
python -m venv venv
venv\Scripts\activate  # Windows
# source venv/bin/activate  # macOS/Linux

# Install dependencies
pip install -r requirements.txt

# Configure environment
copy .env.example .env  # Windows
# cp .env.example .env   # macOS/Linux

# Initialize the database (optional)
python scripts/install_db.py

# Start the server
python run.py
```

The API will be available at `http://localhost:8000`.

### Manual Installation

If you prefer manual setup:

#### 1. Clone the Repository
```bash
git clone https://github.com/n123al/fastapi-graphql-api.git
cd fastapi-graphql-api
```

#### 2. Create Virtual Environment
```bash
python -m venv venv

# On Linux/Mac
source venv/bin/activate

# On Windows
venv\Scripts\activate
```

#### 3. Install Dependencies
```bash
# Install production dependencies
pip install -r requirements.txt

# Install development dependencies (optional)
pip install -r requirements-dev.txt
```

#### 4. Configure Environment
```bash
# Copy example environment file
cp .env.example .env

# Edit .env file with your configuration
# IMPORTANT: Change SECRET_KEY in production!
```

#### 5. Start MongoDB
Make sure MongoDB is running on your system:

```bash
# On macOS with Homebrew
brew services start mongodb-community

# On Ubuntu/Debian
sudo systemctl start mongod

# On Windows
# Start MongoDB service from Services panel or:
net start MongoDB
```

#### 6. Initialize Database
```bash
# Run database initialization script
python scripts/install_db.py
```

This creates:
- Default permissions
- Default roles (superadmin, admin, user)
- Default groups (administrators, users)
- Admin user (email: admin@example.com, password: password123)

#### 7. Run the Application
```bash
# Using the run script
python run.py

# Or directly
python -m uvicorn app.main:app --reload
```

The API will be available at `http://localhost:8000`

### Docker

Basic runtime image example:

```dockerfile
FROM python:3.9-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY . .
CMD ["python", "run.py"]
```

## 📚 API Documentation

### GraphQL Playground
- URL: `http://localhost:8000/api/graphql`
- Interactive Strawberry GraphiQL interface

### REST API Documentation
- **Swagger UI**: `http://localhost:8000/docs`
- **ReDoc**: `http://localhost:8000/redoc`

### Health Check
- **Endpoint**: `http://localhost:8000/health`
- **Detailed Health**: `http://localhost:8000/health/detailed`

## 🔐 Authentication

### Login
```graphql
mutation {
  login(input: { identifier: "admin@example.com", password: "password123" }) {
    accessToken
    refreshToken
    tokenType
    expiresIn
  }
}
```

### Refresh Token
```graphql
mutation {
  refreshToken(refreshToken: "YOUR_REFRESH_TOKEN") {
    accessToken
    tokenType
    expiresIn
  }
}
```

After login, set the Playground "HTTP HEADERS":

```json
{
  "Authorization": "Bearer YOUR_ACCESS_TOKEN"
}
```

## 👥 User Management

### Get Current User (me)
Retrieve the currently authenticated user's profile.
```graphql
query {
  me {
    id
    username
    email
    fullName
    isActive
    isSuperuser
  }
}
```

### Get a User
By ID (requires `users:read` permission for other users):
```graphql
query {
  user(id: "USER_ID") {
    id
    username
    email
    fullName
    isActive
    isSuperuser
  }
}
```

### Get All Users
Retrieve a list of all users (active and inactive). Requires `users:read` permission.
```graphql
query {
  users(limit: 10) {
    id
    username
    email
    fullName
    isActive
  }
}
```

By email:
```graphql
query {
  userByEmail(email: "admin@example.com") {
    id
    username
    email
    fullName
  }
}
```

### Update User
Update user profile. Users can update their own profile; updating others requires `users:update` permission.
```graphql
mutation {
  updateUser(
    id: "USER_ID",
    input: {
      fullName: "John Doe"
      email: "newemail@example.com"
    }
  ) {
    id
    username
    email
    fullName
    isActive
  }
}
```

### Delete User
Soft delete a user (mark as deleted). Requires `users:delete` permission.
```graphql
mutation {
  deleteUser(id: "USER_ID")
}
```

## 🔑 Role & Permission Management

### Create Role
```graphql
mutation {
  createRole(input: {
    name: "editor",
    description: "Content editor role",
    permissionIds: ["permission-id-1", "permission-id-2"]
  }) {
    id
    name
    description
    permissions {
      name
      description
    }
  }
}
```

### Get All Roles
```graphql
query {
  roles {
    id
    name
    description
    permissions {
      name
      description
    }
    isSystemRole
  }
}
```

## 🏷️ Group Management

Groups help organize users and can be used for bulk permission management.

### Default Groups
- **administrators** - System administrators
- **moderators** - Content moderators  
- **users** - Regular users
- **guests** - Guest users with limited access

## 🏗️ Architecture Overview

### Project Structure
```
app/
├── core/
│   ├── config.py
│   ├── motor_database.py
│   ├── security.py
│   ├── auth_strategies.py
│   ├── exceptions.py
│   └── constants.py
├── data/
│   ├── models/
│   └── repositories.py
├── services/
│   ├── auth.py
│   └── user.py
├── graphql/
│   ├── schema.py
│   ├── context.py
│   ├── queries/
│   └── mutations/
└── main.py
```

### Design Patterns Used

1. **Repository Pattern** - Data access abstraction
2. **Service Layer Pattern** - Business logic separation
3. **Strategy Pattern** - Pluggable authentication methods
4. **Factory Pattern** - Object creation
5. **Observer Pattern** - Event handling
6. **Dependency Injection** - Loose coupling

### Authentication Strategies

The system supports multiple authentication strategies:

1. **Username/Password** - Traditional authentication
2. **Email/Magic Link** - Passwordless authentication
3. **JWT Token** - Token-based authentication

### Authorization System

- **Role-Based Access Control (RBAC)**
- **Permission-Based Authorization**
- **Group-Based Permissions**
- **Resource-Based Authorization**

## 🔧 Configuration

### Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `APP_NAME` | Application name | FastAPI GraphQL API |
| `DEBUG` | Debug mode | False |
| `HOST` | Server host | 0.0.0.0 |
| `PORT` | Server port | 8000 |
| `SECRET_KEY` | JWT secret key | (required) |
| `ALGORITHM` | JWT algorithm | HS256 |
| `ACCESS_TOKEN_EXPIRE_MINUTES` | Access token expiry (min) | 30 |
| `REFRESH_TOKEN_EXPIRE_MINUTES` | Refresh token expiry (min) | 10080 |
| `MONGODB_URL` | MongoDB connection URL | mongodb://localhost:27017 |
| `DATABASE_NAME` | Database name | fastapi_graphql_db |
| `ALLOWED_HOSTS` | CORS allowed origins | ["*"] |
| `REQUIRE_AUTHENTICATION` | Require auth for GraphQL | True |

### Security Settings

| Variable | Description | Default |
|----------|-------------|---------|
| `ACCESS_TOKEN_EXPIRE_MINUTES` | JWT access token expiry | 30 |
| `REFRESH_TOKEN_EXPIRE_MINUTES` | JWT refresh token expiry | 10080 (7 days) |
| `MAX_LOGIN_ATTEMPTS` | Max failed login attempts | 5 |
| `LOCKOUT_DURATION_MINUTES` | Account lockout duration | 30 |

## 🧪 Testing

### Quick Test Run

```bash
# Run all tests
python run_tests.py

# Or use pytest directly
pytest tests/ -v
```

### Test Options

```bash
# Run with coverage report
pytest tests/ -v --cov=app --cov-report=term-missing

# Generate HTML coverage report
pytest tests/ -v --cov=app --cov-report=html
# View report: open htmlcov/index.html

# Run specific test file
pytest tests/test_auth.py -v

# Run specific test class
pytest tests/test_auth.py::TestAuthentication -v

# Run specific test function
pytest tests/test_auth.py::TestAuthentication::test_login -v

# Run tests with markers
pytest -m unit  # Run only unit tests
pytest -m integration  # Run only integration tests

# Stop on first failure
pytest -x

# Show local variables in tracebacks
pytest -l

# Run tests in parallel (requires pytest-xdist)
pytest -n auto
```

### Test Structure

```
tests/
├── conftest.py              # Test fixtures and configuration
├── test_auth.py             # Authentication tests
├── test_models.py           # Data model tests
├── test_security.py         # Security function tests
├── test_config.py           # Configuration tests
├── test_exceptions.py       # Exception handling tests
├── test_constants.py        # Constants validation tests
├── test_utils.py            # Utility function tests
├── test_services.py         # Service layer tests
├── test_api_endpoints.py    # API endpoint tests
├── test_graphql_resolvers.py # GraphQL resolver tests
└── integration/
    └── test_auth_flow.py    # Integration tests
```

### Coverage Goals

- Minimum coverage: 80%
- Target coverage: 90%+
- Critical paths: 100%

### Continuous Integration

Tests run automatically on:
- Every push to main/develop branches
- Every pull request
- Multiple Python versions (3.8, 3.9, 3.10, 3.11)

See `.github/workflows/ci.yml` for CI/CD configuration.

## 📊 Monitoring & Logging

### Logging
The application uses structured logging with different levels:
- **DEBUG** - Detailed debugging information
- **INFO** - General information
- **WARNING** - Warning messages
- **ERROR** - Error messages
- **CRITICAL** - Critical errors

### Health Monitoring
- **Health Check**: Basic health status
- **Detailed Health**: Database connectivity and statistics
- **Metrics**: Performance metrics and counters

## 🚀 Deployment

### Deployment
See the Docker example above or run with a process manager.

### Production Considerations

1. **Environment Variables**: Use secure environment variables
2. **Database**: Use MongoDB replica set for production
3. **Security**: Enable HTTPS and secure headers
4. **Rate Limiting**: Configure appropriate rate limits
5. **Monitoring**: Set up monitoring and alerting
6. **Logging**: Configure centralized logging
7. **Backup**: Implement database backup strategy

## 🤝 Contributing

Contributions are welcome. See `CONTRIBUTING.md` for guidelines.

Please also review `CODE_OF_CONDUCT.md` and `SECURITY.md`.

### Quick Contribution Guide

1. **Fork the repository**
2. **Create a feature branch**
   ```bash
   git checkout -b feature/amazing-feature
   ```
3. **Make your changes**
   - Write clean, documented code
   - Follow existing code style
   - Add tests for new features
4. **Run tests and checks**
   ```bash
   pytest tests/ -v
   black app tests
   flake8 app tests
   ```
5. **Commit your changes**
   ```bash
   git commit -m "feat: add amazing feature"
   ```
6. **Push to your fork**
   ```bash
   git push origin feature/amazing-feature
   ```
7. **Open a Pull Request**

### Development Setup

```bash
# Install development dependencies
pip install -r requirements-dev.txt

# Install pre-commit hooks
pre-commit install

# Run code quality checks
black app tests
isort app tests
flake8 app tests
mypy app --ignore-missing-imports
```

### Code Quality Standards

- Code coverage: minimum 80%
- All tests must pass
- Code must be formatted with Black
- No linting errors
- Type hints where appropriate
- Comprehensive docstrings

## 📄 License

MIT License. See `LICENSE`.

## 🆘 Support

For support and questions:
- Create an issue in the repository
- Check the documentation
- Review the API documentation at `/docs`

## 🔮 Future Enhancements

- [ ] OAuth2 integration
- [ ] Two-factor authentication (2FA)
- [ ] API versioning
- [ ] File upload functionality
- [ ] Real-time notifications
- [ ] Advanced search and filtering
- [ ] Audit logging
- [ ] Performance monitoring
- [ ] Caching layer with Redis
- [ ] Email notifications
- [ ] Mobile app support
- [ ] GraphQL subscriptions
- [ ] Advanced analytics
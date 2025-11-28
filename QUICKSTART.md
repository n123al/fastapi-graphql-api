# Quick Start Guide

Get up and running with FastAPI GraphQL API in 5 minutes!

## Prerequisites

- Python 3.8 or higher
- MongoDB 4.4 or higher
- pip (Python package manager)

## Installation

### 1. Clone and Setup

```bash
# Clone the repository
git clone https://github.com/n123al/fastapi-graphql-api.git
cd fastapi-graphql-api

# Create a virtual environment and install dependencies
python -m venv venv
venv\Scripts\activate  # Windows
# source venv/bin/activate  # macOS/Linux
pip install -r requirements.txt

# Configure environment
copy .env.example .env  # Windows
# cp .env.example .env   # macOS/Linux
```

### 2. Start MongoDB

```bash
# macOS
brew services start mongodb-community

# Linux
sudo systemctl start mongod

# Windows
net start MongoDB
```

### 3. Initialize Database

```bash
python scripts/install_db.py
```

### 4. Start the Server

```bash
python run.py
```

The API is now running at `http://localhost:8000`

## First Steps

### 1. Access the GraphQL Playground

Open your browser and go to:
```
http://localhost:8000/api/graphql
```

### 2. Login as Admin

Run this mutation in the GraphQL Playground:

```graphql
mutation {
  login(input: {
    identifier: "admin@example.com",
    password: "password123"
  }) {
    accessToken
    refreshToken
    tokenType
    expiresIn
  }
}
```

Copy the `accessToken` from the response.

### 3. Set Authorization Header

In the GraphQL Playground, click "HTTP HEADERS" at the bottom and add:

```json
{
  "Authorization": "Bearer YOUR_ACCESS_TOKEN_HERE"
}
```

### 4. Query a User

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

## Common Operations

### Create a New User

```graphql
mutation {
  createUser(input: {
    username: "johndoe",
    email: "john@example.com",
    password: "securepassword123",
    fullName: "John Doe"
  }) {
    id
    username
    email
    fullName
  }
}
```

### List All Users

```graphql
query {
  users {
    id
    username
    email
    isActive
    createdAt
  }
}
```

### Create a Role

```graphql
mutation {
  createRole(input: {
    name: "editor",
    description: "Content editor role",
    permissionIds: []
  }) {
    id
    name
    description
  }
}
```

### List All Roles

```graphql
query {
  roles {
    id
    name
    description
  }
}
```

## API Documentation

### GraphQL Playground
- **URL**: http://localhost:8000/api/graphql
- Interactive GraphQL interface with auto-completion

### REST API Docs
- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc

### Health Check
- **Basic**: http://localhost:8000/health
- **Detailed**: http://localhost:8000/health/detailed

## Configuration

Edit `.env` file to customize:

```env
# Change the secret key (IMPORTANT!)
SECRET_KEY=your-secure-secret-key-here

# Database connection
MONGODB_URL=mongodb://localhost:27017
DATABASE_NAME=fastapi_graphql_db

# Server settings
HOST=0.0.0.0
PORT=8000
DEBUG=True
```

## Testing

```bash
# Run all tests
pytest tests/ -v

# Run with coverage
pytest tests/ --cov=app --cov-report=html
```

## Troubleshooting

### MongoDB Connection Error

**Problem**: Cannot connect to MongoDB

**Solution**:
1. Make sure MongoDB is running
2. Check MONGODB_URL in .env file
3. Verify MongoDB is accessible on the specified port

### Import Errors

**Problem**: Module not found errors

**Solution**:
```bash
# Reinstall dependencies
pip install -r requirements.txt
```

### Port Already in Use

**Problem**: Port 8000 is already in use

**Solution**:
1. Change PORT in .env file
2. Or stop the process using port 8000

### Authentication Errors

**Problem**: "Authentication required" errors

**Solution**:
1. Make sure you're logged in
2. Check Authorization header is set correctly
3. Verify token hasn't expired

## Next Steps

1. **Read the full documentation**: Check [README.md](README.md)
2. **Explore the API**: Try different queries and mutations
3. **Customize**: Modify models, add new features
4. **Deploy**: See deployment guides for production setup

## Getting Help

- **Issues**: https://github.com/n123al/fastapi-graphql-api/issues
- **Documentation**: Read `README.md`
- **Contributing**: See `CONTRIBUTING.md`

## Default Credentials

**⚠️ Change these in production!**

- **Email**: admin@example.com
- **Password**: password123

---

**Happy coding! 🚀**

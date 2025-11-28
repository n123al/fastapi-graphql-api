# Default Permissions
DEFAULT_PERMISSIONS = {
    # User permissions
    "users:create": "Create new users",
    "users:read": "Read user information",
    "users:update": "Update user information",
    "users:delete": "Delete users",
    # Role permissions
    "roles:create": "Create new roles",
    "roles:read": "Read role information",
    "roles:update": "Update role information",
    "roles:delete": "Delete roles",
    "roles:assign": "Assign roles to users",
    # Permission permissions
    "permissions:create": "Create new permissions",
    "permissions:read": "Read permission information",
    "permissions:update": "Update permission information",
    "permissions:delete": "Delete permissions",
    # Group permissions
    "groups:create": "Create new groups",
    "groups:read": "Read group information",
    "groups:update": "Update group information",
    "groups:delete": "Delete groups",
    "groups:assign": "Assign users to groups",
    # Admin permissions
    "admin:access": "Access admin panel",
    "admin:users": "Manage users from admin panel",
    "admin:roles": "Manage roles from admin panel",
    "admin:permissions": "Manage permissions from admin panel",
    "admin:groups": "Manage groups from admin panel",
    "admin:settings": "Manage system settings",
    # Profile permissions
    "profile:read": "Read own profile",
    "profile:update": "Update own profile",
    "profile:delete": "Delete own profile",
    # API permissions
    "api:access": "Access API endpoints",
    "api:graphql": "Access GraphQL endpoint",
    "api:rest": "Access REST endpoints",
}

# Default Roles
DEFAULT_ROLES = {
    "superadmin": {
        "description": "System administrator with full access",
        "permissions": list(DEFAULT_PERMISSIONS.keys()),  # All permissions
        "is_system_role": True,
    },
    "admin": {
        "description": "Administrator with most permissions",
        "permissions": [
            "users:create",
            "users:read",
            "users:update",
            "roles:create",
            "roles:read",
            "roles:update",
            "roles:assign",
            "permissions:read",
            "groups:create",
            "groups:read",
            "groups:update",
            "groups:assign",
            "admin:access",
            "admin:users",
            "admin:roles",
            "admin:permissions",
            "admin:groups",
            "profile:read",
            "profile:update",
            "api:access",
            "api:graphql",
            "api:rest",
        ],
        "is_system_role": True,
    },
    "moderator": {
        "description": "Moderator with limited admin permissions",
        "permissions": [
            "users:read",
            "users:update",
            "roles:read",
            "permissions:read",
            "groups:read",
            "groups:update",
            "groups:assign",
            "admin:access",
            "admin:users",
            "admin:groups",
            "profile:read",
            "profile:update",
            "api:access",
            "api:graphql",
            "api:rest",
        ],
        "is_system_role": True,
    },
    "user": {
        "description": "Regular user with basic permissions",
        "permissions": [
            "profile:read",
            "profile:update",
            "api:access",
            "api:graphql",
            "api:rest",
        ],
        "is_system_role": True,
    },
    "guest": {
        "description": "Guest user with minimal permissions",
        "permissions": ["api:access"],
        "is_system_role": True,
    },
}

# Default Groups
DEFAULT_GROUPS = {
    "administrators": {
        "description": "System administrators group",
        "is_system_group": True,
        "metadata": {
            "color": "#FF0000",
            "icon": "shield",
            "description": "Users with administrative privileges",
        },
    },
    "moderators": {
        "description": "Content moderators group",
        "is_system_group": True,
        "metadata": {
            "color": "#FFA500",
            "icon": "user-check",
            "description": "Users with moderation privileges",
        },
    },
    "users": {
        "description": "Regular users group",
        "is_system_group": True,
        "metadata": {
            "color": "#008000",
            "icon": "user",
            "description": "Regular application users",
        },
    },
    "guests": {
        "description": "Guest users group",
        "is_system_group": True,
        "metadata": {
            "color": "#808080",
            "icon": "eye",
            "description": "Guest users with limited access",
        },
    },
}

# JWT Settings
JWT_SETTINGS = {
    "ACCESS_TOKEN_EXPIRE_MINUTES": 30,
    "REFRESH_TOKEN_EXPIRE_MINUTES": 60 * 24 * 7,  # 7 days
    "ALGORITHM": "HS256",
}

# Rate Limiting Settings
RATE_LIMIT_SETTINGS = {
    "DEFAULT_LIMIT": 60,  # requests per minute
    "AUTH_LIMIT": 10,  # authentication attempts per minute
    "API_LIMIT": 100,  # general API limit per minute
}

# MongoDB Settings
MONGODB_SETTINGS = {
    "MAX_CONNECTION_POOL_SIZE": 100,
    "MIN_CONNECTION_POOL_SIZE": 10,
    "MAX_IDLE_TIME_MS": 45000,
    "MAX_CONNECTION_LIFE_TIME_MS": 120000,
    "SOCKET_TIMEOUT_MS": 45000,
    "CONNECT_TIMEOUT_MS": 20000,
    "SERVER_SELECTION_TIMEOUT_MS": 60000,
    "WAIT_QUEUE_TIMEOUT_MS": 20000,
    "RETRY_WRITES": True,
    "RETRY_READS": True,
}

# Security Settings
SECURITY_SETTINGS = {
    "PASSWORD_MIN_LENGTH": 8,
    "PASSWORD_REQUIRE_UPPERCASE": True,
    "PASSWORD_REQUIRE_LOWERCASE": True,
    "PASSWORD_REQUIRE_NUMBERS": True,
    "PASSWORD_REQUIRE_SPECIAL": True,
    "MAX_LOGIN_ATTEMPTS": 5,
    "LOCKOUT_DURATION_MINUTES": 30,
    "SESSION_TIMEOUT_MINUTES": 60,
    "REQUIRE_EMAIL_VERIFICATION": True,
    "REQUIRE_STRONG_PASSWORDS": True,
}

# API Settings
API_SETTINGS = {
    "DEFAULT_PAGE_SIZE": 20,
    "MAX_PAGE_SIZE": 100,
    "ALLOWED_SORT_FIELDS": ["created_at", "updated_at", "username", "email", "name"],
    "ALLOWED_FILTER_FIELDS": ["is_active", "email_verified", "is_superuser"],
    "GRAPHQL_INTROSPECTION": True,
    "GRAPHQL_PLAYGROUND": True,
}

# File Upload Settings
FILE_UPLOAD_SETTINGS = {
    "MAX_FILE_SIZE": 10 * 1024 * 1024,  # 10MB
    "ALLOWED_EXTENSIONS": [".jpg", ".jpeg", ".png", ".gif", ".pdf", ".doc", ".docx"],
    "UPLOAD_DIR": "uploads",
    "ALLOWED_MIME_TYPES": [
        "image/jpeg",
        "image/png",
        "image/gif",
        "application/pdf",
        "application/msword",
        "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
    ],
}

# Logging Settings
LOGGING_SETTINGS = {
    "LOG_LEVEL": "INFO",
    "LOG_FORMAT": "json",
    "LOG_REQUEST_BODY": False,
    "LOG_RESPONSE_BODY": False,
    "LOG_QUERY_EXECUTION_TIME": True,
    "MAX_LOG_SIZE_MB": 100,
    "LOG_RETENTION_DAYS": 30,
}

# Email Settings
EMAIL_SETTINGS = {
    "SMTP_SERVER": "smtp.gmail.com",
    "SMTP_PORT": 587,
    "SMTP_USE_TLS": True,
    "FROM_EMAIL": "noreply@yourapp.com",
    "FROM_NAME": "Your App",
    "EMAIL_VERIFICATION_REQUIRED": True,
    "PASSWORD_RESET_EXPIRY_HOURS": 24,
}

# CORS Settings
CORS_SETTINGS = {
    "ALLOWED_ORIGINS": ["*"],
    "ALLOWED_METHODS": ["*"],
    "ALLOWED_HEADERS": ["*"],
    "ALLOW_CREDENTIALS": True,
    "MAX_AGE": 86400,  # 24 hours
}

# Cache Settings
CACHE_SETTINGS = {
    "REDIS_ENABLED": False,
    "REDIS_HOST": "localhost",
    "REDIS_PORT": 6379,
    "REDIS_DB": 0,
    "REDIS_PASSWORD": None,
    "CACHE_TTL_SECONDS": 3600,  # 1 hour
    "CACHE_PREFIX": "fastapi_graphql",
}

# Consolidated constants for easy import
PERMISSIONS = DEFAULT_PERMISSIONS
DEFAULT_ROLES = DEFAULT_ROLES
TOKEN_EXPIRATION_TIMES = JWT_SETTINGS
PASSWORD_REQUIREMENTS = SECURITY_SETTINGS
API_RATE_LIMITS = RATE_LIMIT_SETTINGS

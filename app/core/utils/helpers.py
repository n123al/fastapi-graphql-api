"""
General utility functions and helpers for common operations.

This module provides miscellaneous utility functions for tasks such as
generating random strings, sanitizing HTML, formatting data, and other
common operations used throughout the application.
"""

import html
import random
import re
import smtplib
import string
from email.mime.text import MIMEText
from email.utils import formataddr
from typing import Optional


def generate_random_string(length: int = 16, charset: Optional[str] = None) -> str:
    """
    Generate a cryptographically secure random string.

    Args:
        length: Length of the string to generate (default: 16)
        charset: Character set to use (default: alphanumeric + symbols)

    Returns:
        Random string of specified length

    Example:
        ```python
        >>> generate_random_string(8)
        'aB3$xL9q'
        >>> generate_random_string(10, string.ascii_letters)
        'aBcDeFgHiJ'
        ```
    """
    if charset is None:
        charset = string.ascii_letters + string.digits + "!@#$%^&*"

    # Use secrets module for cryptographic randomness if available
    try:
        import secrets

        return "".join(secrets.choice(charset) for _ in range(length))
    except ImportError:
        # Fallback to random module
        return "".join(random.choice(charset) for _ in range(length))


def sanitize_html(raw_html: str, allowed_tags: Optional[list] = None) -> str:
    """
    Sanitize HTML content by removing dangerous tags and attributes.

    Args:
        raw_html: Raw HTML content to sanitize
        allowed_tags: List of allowed HTML tags (default: basic formatting)

    Returns:
        Sanitized HTML content

    Example:
        ```python
        >>> sanitize_html("<script>alert('xss')</script><p>Safe content</p>")
        '<p>Safe content</p>'
        ```
    """
    if not raw_html:
        return ""

    # Default allowed tags
    if allowed_tags is None:
        allowed_tags = [
            "p",
            "br",
            "strong",
            "em",
            "u",
            "i",
            "b",
            "ul",
            "ol",
            "li",
            "h1",
            "h2",
            "h3",
            "h4",
            "h5",
            "h6",
        ]

    # First, escape all HTML
    escaped_html = html.escape(raw_html)

    # Allow specific tags
    for tag in allowed_tags:
        # Opening tags
        escaped_html = re.sub(
            f"&lt;{tag}&gt;", f"<{tag}>", escaped_html, flags=re.IGNORECASE
        )
        # Closing tags
        escaped_html = re.sub(
            f"&lt;/{tag}&gt;", f"</{tag}>", escaped_html, flags=re.IGNORECASE
        )

    return escaped_html


def truncate_text(text: str, max_length: int = 100, suffix: str = "...") -> str:
    """
    Truncate text to specified length with optional suffix.

    Args:
        text: Text to truncate
        max_length: Maximum length before truncation
        suffix: Suffix to add when truncating (default: "...")

    Returns:
        Truncated text

    Example:
        ```python
        >>> truncate_text("This is a long text that needs truncation", 20)
        'This is a long text...'
        >>> truncate_text("Short text", 50)
        'Short text'
        ```
    """
    if not text or len(text) <= max_length:
        return text

    # Account for suffix length
    actual_length = max_length - len(suffix)
    if actual_length <= 0:
        return suffix

    return text[:actual_length] + suffix


def format_file_size(size_bytes: int) -> str:
    """
    Format file size in bytes to human-readable format.

    Args:
        size_bytes: File size in bytes

    Returns:
        Human-readable file size string

    Example:
        ```python
        >>> format_file_size(1024)
        '1.0 KB'
        >>> format_file_size(1048576)
        '1.0 MB'
        >>> format_file_size(500)
        '500.0 B'
        ```
    """
    if size_bytes == 0:
        return "0 B"

    size_names = ["B", "KB", "MB", "GB", "TB", "PB"]
    i = 0
    size = float(size_bytes)

    while size >= 1024 and i < len(size_names) - 1:
        size /= 1024
        i += 1

    return f"{size:.1f} {size_names[i]}"


def extract_domain_from_email(email: str) -> Optional[str]:
    """
    Extract domain from email address.

    Args:
        email: Email address

    Returns:
        Domain part of email or None if invalid

    Example:
        ```python
        >>> extract_domain_from_email("user@example.com")
        'example.com'
        >>> extract_domain_from_email("invalid-email")
        None
        ```
    """
    if not email or "@" not in email:
        return None

    try:
        return email.split("@")[1].lower()
    except IndexError:
        return None


def send_email_smtp(to: str, subject: str, body: str) -> bool:
    try:
        from app.core.config import settings

        host = settings.SMTP_HOST
        port = settings.SMTP_PORT
        user = settings.SMTP_USER
        password = settings.SMTP_PASSWORD
        sender = settings.SMTP_FROM or user
        sender_name = settings.SMTP_FROM_NAME
        use_tls = (
            bool(settings.SMTP_USE_TLS)
            if settings.SMTP_USE_TLS is not None
            else (port == 587)
        )
        use_ssl = (
            bool(settings.SMTP_USE_SSL)
            if settings.SMTP_USE_SSL is not None
            else (port == 465)
        )
        if not host or not port or not sender:
            return False
        msg = MIMEText(body, "plain", "utf-8")
        msg["Subject"] = subject
        msg["From"] = formataddr((sender_name or "", sender))
        msg["To"] = to
        server = smtplib.SMTP_SSL(host, port) if use_ssl else smtplib.SMTP(host, port)
        if use_tls and not use_ssl:
            server.starttls()
        if user and password:
            server.login(user, password)
        server.sendmail(sender, [to], msg.as_string())
        server.quit()
        return True
    except Exception:
        return False


def mask_sensitive_data(data: str, mask_char: str = "*", visible_chars: int = 4) -> str:
    """
    Mask sensitive data like credit cards, phone numbers, etc.

    Args:
        data: Sensitive data to mask
        mask_char: Character to use for masking (default: "*")
        visible_chars: Number of characters to keep visible (default: 4)

    Returns:
        Masked data string

    Example:
        ```python
        >>> mask_sensitive_data("1234567890123456")
        '************3456'
        >>> mask_sensitive_data("sensitive_data", visible_chars=2)
        "**************ta"
        ```
    """
    if not data or len(data) <= visible_chars:
        return data

    masked_length = len(data) - visible_chars
    return mask_char * masked_length + data[-visible_chars:]


def slugify(text: str, separator: str = "-") -> str:
    """
    Convert text to URL-friendly slug format.

    Args:
        text: Text to convert to slug
        separator: Character to use as separator (default: "-")

    Returns:
        URL-friendly slug

    Example:
        ```python
        >>> slugify("Hello World!")
        'hello-world'
        >>> slugify("Product Name (2023)", separator="_")
        'product_name_2023'
        ```
    """
    if not text:
        return ""

    # Convert to lowercase
    text = text.lower()

    # Replace spaces and special characters with separator
    text = re.sub(r"[^\w\s-]", "", text)
    text = re.sub(r"[\s_-]+", separator, text)

    # Remove leading/trailing separators
    text = text.strip(separator)

    return text

"""
Password utilities for ARA v2.
Handles password hashing, verification, and validation.
"""

from werkzeug.security import generate_password_hash, check_password_hash
import bcrypt
import re


# Password requirements
MIN_PASSWORD_LENGTH = 12
REQUIRE_UPPERCASE = True
REQUIRE_LOWERCASE = True
REQUIRE_DIGIT = True
REQUIRE_SPECIAL = True
SPECIAL_CHARS = '!@#$%^&*()_+-=[]{}|;:,.<>?'


def validate_password(password: str) -> tuple[bool, str]:
    """
    Validate password meets security requirements.

    Args:
        password: Password to validate

    Returns:
        tuple: (is_valid, error_message)
    """
    if len(password) < MIN_PASSWORD_LENGTH:
        return False, f"Password must be at least {MIN_PASSWORD_LENGTH} characters"

    if REQUIRE_UPPERCASE and not any(c.isupper() for c in password):
        return False, "Password must contain at least one uppercase letter"

    if REQUIRE_LOWERCASE and not any(c.islower() for c in password):
        return False, "Password must contain at least one lowercase letter"

    if REQUIRE_DIGIT and not any(c.isdigit() for c in password):
        return False, "Password must contain at least one digit"

    if REQUIRE_SPECIAL and not any(c in SPECIAL_CHARS for c in password):
        return False, f"Password must contain at least one special character ({SPECIAL_CHARS})"

    return True, "Password is valid"


def hash_password(password: str) -> str:
    """
    Hash password using scrypt (via Werkzeug).

    Args:
        password: Plain text password

    Returns:
        str: Hashed password
    """
    return generate_password_hash(password, method='scrypt')


def verify_password(password_hash: str, password: str) -> bool:
    """
    Verify password against hash.
    Supports both bcrypt and werkzeug scrypt hashes.

    Args:
        password_hash: Stored password hash
        password: Plain text password to verify

    Returns:
        bool: True if password matches
    """
    # Check if it's a bcrypt hash (starts with $2a$, $2b$, or $2y$)
    if password_hash.startswith(('$2a$', '$2b$', '$2y$')):
        try:
            return bcrypt.checkpw(
                password.encode('utf-8'),
                password_hash.encode('utf-8')
            )
        except Exception:
            return False
    
    # Otherwise use werkzeug's check
    return check_password_hash(password_hash, password)


def validate_email(email: str) -> tuple[bool, str]:
    """
    Validate email format.

    Args:
        email: Email address to validate

    Returns:
        tuple: (is_valid, error_message)
    """
    # Basic email regex
    email_pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'

    if not email:
        return False, "Email is required"

    if not re.match(email_pattern, email):
        return False, "Invalid email format"

    if len(email) > 255:
        return False, "Email is too long (max 255 characters)"

    return True, "Email is valid"

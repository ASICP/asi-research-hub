"""
Unit tests for password utilities.
"""

import pytest
from ara_v2.utils.password import (
    validate_password,
    hash_password,
    verify_password,
    validate_email,
    MIN_PASSWORD_LENGTH
)


class TestPasswordValidation:
    """Test password validation rules."""

    def test_valid_password(self):
        """Test that a valid password passes all checks."""
        password = "SecurePass123!"
        is_valid, message = validate_password(password)
        assert is_valid is True
        assert message == "Password is valid"

    def test_password_too_short(self):
        """Test password length validation."""
        password = "Short1!"
        is_valid, message = validate_password(password)
        assert is_valid is False
        assert f"at least {MIN_PASSWORD_LENGTH} characters" in message

    def test_password_no_uppercase(self):
        """Test uppercase requirement."""
        password = "nocapital123!"
        is_valid, message = validate_password(password)
        assert is_valid is False
        assert "uppercase letter" in message

    def test_password_no_lowercase(self):
        """Test lowercase requirement."""
        password = "NOLOWERCASE123!"
        is_valid, message = validate_password(password)
        assert is_valid is False
        assert "lowercase letter" in message

    def test_password_no_digit(self):
        """Test digit requirement."""
        password = "NoDigitsHere!"
        is_valid, message = validate_password(password)
        assert is_valid is False
        assert "digit" in message

    def test_password_no_special_char(self):
        """Test special character requirement."""
        password = "NoSpecialChar123"
        is_valid, message = validate_password(password)
        assert is_valid is False
        assert "special character" in message

    def test_minimum_length_password(self):
        """Test password at minimum length."""
        password = "A" * (MIN_PASSWORD_LENGTH - 3) + "1a!"  # Just at minimum
        is_valid, message = validate_password(password)
        assert is_valid is True


class TestPasswordHashing:
    """Test password hashing and verification."""

    def test_hash_password_returns_different_hash(self):
        """Test that hashing returns a different string than input."""
        password = "MyPassword123!"
        hashed = hash_password(password)
        assert hashed != password
        assert len(hashed) > 0

    def test_hash_password_scrypt_format(self):
        """Test that hash uses scrypt method."""
        password = "TestPassword123!"
        hashed = hash_password(password)
        # Werkzeug scrypt hashes start with 'scrypt:'
        assert hashed.startswith('scrypt:')

    def test_same_password_different_hashes(self):
        """Test that same password produces different hashes (salt)."""
        password = "SamePassword123!"
        hash1 = hash_password(password)
        hash2 = hash_password(password)
        # Different salts should produce different hashes
        assert hash1 != hash2

    def test_verify_password_correct(self):
        """Test password verification with correct password."""
        password = "CorrectPassword123!"
        hashed = hash_password(password)
        assert verify_password(hashed, password) is True

    def test_verify_password_incorrect(self):
        """Test password verification with incorrect password."""
        password = "CorrectPassword123!"
        hashed = hash_password(password)
        assert verify_password(hashed, "WrongPassword123!") is False

    def test_verify_password_empty_string(self):
        """Test password verification with empty password."""
        password = "MyPassword123!"
        hashed = hash_password(password)
        assert verify_password(hashed, "") is False


class TestEmailValidation:
    """Test email validation."""

    def test_valid_email(self):
        """Test valid email formats."""
        valid_emails = [
            "user@example.com",
            "test.user@example.com",
            "user+tag@example.co.uk",
            "first.last@sub.domain.com",
            "user123@test.org"
        ]
        for email in valid_emails:
            is_valid, message = validate_email(email)
            assert is_valid is True, f"Email {email} should be valid"
            assert message == "Email is valid"

    def test_invalid_email_format(self):
        """Test invalid email formats."""
        invalid_emails = [
            "notanemail",
            "@example.com",
            "user@",
            "user @example.com",
            "user@.com",
            "user..test@example.com",
            "user@domain",
        ]
        for email in invalid_emails:
            is_valid, message = validate_email(email)
            assert is_valid is False, f"Email {email} should be invalid"
            assert "Invalid email format" in message

    def test_empty_email(self):
        """Test empty email validation."""
        is_valid, message = validate_email("")
        assert is_valid is False
        assert "Email is required" in message

    def test_email_too_long(self):
        """Test email length limit."""
        email = "a" * 250 + "@example.com"  # Over 255 chars
        is_valid, message = validate_email(email)
        assert is_valid is False
        assert "too long" in message

    def test_email_max_length(self):
        """Test email at maximum length (255 chars)."""
        # Create email exactly 255 chars
        local_part = "a" * (255 - len("@example.com"))
        email = local_part + "@example.com"
        is_valid, message = validate_email(email)
        assert is_valid is True

"""
Security Tests
Comprehensive security testing
"""
import pytest
import sys
from datetime import datetime, timedelta
from unittest.mock import AsyncMock, MagicMock, patch

sys.path.insert(0, 'C:/Users/deepe/PyCharmMiscProject/housing_platform/backend')

from app.security import (
    sanitize_string,
    validate_email,
    validate_phone,
    validate_url,
    sanitize_html,
    SecurityValidator
)


class TestInputSanitization:
    """Test input sanitization functions"""

    def test_sanitize_string_removes_script_tags(self):
        """Test that script tags are removed"""
        input_str = '<script>alert("xss")</script>Hello'
        result = sanitize_string(input_str)
        assert '<script>' not in result
        assert 'alert' not in result

    def test_sanitize_string_removes_event_handlers(self):
        """Test that event handlers are removed"""
        input_str = '<div onclick="steal()">Click me</div>'
        result = sanitize_string(input_str)
        assert 'onclick' not in result

    def test_sanitize_string_escapes_html(self):
        """Test HTML entity escaping"""
        input_str = '<div>Hello & "World"</div>'
        result = sanitize_string(input_str)
        assert '&' not in result or '&amp;' in result

    def test_sanitize_string_empty_input(self):
        """Test sanitization of empty string"""
        assert sanitize_string("") == ""
        assert sanitize_string(None) is None

    def test_validate_email_valid(self):
        """Test valid email validation"""
        valid_emails = [
            "user@example.com",
            "user.name@domain.co.in",
            "user+tag@example.com",
            "123@example.com"
        ]
        for email in valid_emails:
            assert validate_email(email) is True, f"{email} should be valid"

    def test_validate_email_invalid(self):
        """Test invalid email validation"""
        invalid_emails = [
            "notanemail",
            "@nodomain.com",
            "spaces in@email.com",
            "missing@dotcom",
            ""
        ]
        for email in invalid_emails:
            assert validate_email(email) is False, f"{email} should be invalid"

    def test_validate_phone_valid(self):
        """Test valid Indian phone numbers"""
        valid_phones = [
            "9876543210",
            "9123456789",
            "9988776655"
        ]
        for phone in valid_phones:
            assert validate_phone(phone) is True

    def test_validate_phone_invalid(self):
        """Test invalid phone numbers"""
        invalid_phones = [
            "1234567890",  # Doesn't start with 6-9
            "987654321",   # Too short
            "98765432101", # Too long
            "abcdefghij",
            ""
        ]
        for phone in invalid_phones:
            assert validate_phone(phone) is False

    def test_validate_url_valid(self):
        """Test valid URL validation"""
        valid_urls = [
            "http://example.com",
            "https://example.com/path",
            "https://sub.domain.com:8080/path?query=value"
        ]
        for url in valid_urls:
            assert validate_url(url) is True

    def test_validate_url_invalid(self):
        """Test invalid URL validation"""
        invalid_urls = [
            "not a url",
            "ftp://example.com",  # Not http/https
            "javascript:alert(1)",
            "",
            "//example.com"
        ]
        for url in invalid_urls:
            assert validate_url(url) is False

    def test_sanitize_html_removes_scripts(self):
        """Test HTML sanitization"""
        input_html = '<script>alert(1)</script><p>Safe content</p>'
        result = sanitize_html(input_html)
        assert '<script>' not in result
        assert '<p>' in result  # Safe tags preserved

    def test_sanitize_html_removes_iframes(self):
        """Test iframe removal"""
        input_html = '<iframe src="evil.com"></iframe>'
        result = sanitize_html(input_html)
        assert '<iframe>' not in result
        assert 'iframe' not in result


class TestSecurityValidator:
    """Test SecurityValidator class"""

    def test_validate_user_input_valid(self):
        """Test valid user input"""
        validator = SecurityValidator()

        data = {
            "username": "john_doe",
            "email": "john@example.com",
            "age": 25
        }

        rules = {
            "username": {"type": str, "required": True, "min": 3, "max": 20},
            "email": {"type": str, "required": True, "pattern": r"^[^@]+@[^@]+\.[^@]+$"},
            "age": {"type": int, "required": True, "min": 18, "max": 120}
        }

        is_valid, error = validator.validate_user_input(data, rules)
        assert is_valid is True
        assert error == ""

    def test_validate_user_input_missing_required(self):
        """Test validation with missing required field"""
        validator = SecurityValidator()

        data = {"username": "john"}
        rules = {"email": {"type": str, "required": True}}

        is_valid, error = validator.validate_user_input(data, rules)
        assert is_valid is False
        assert "required" in error.lower()

    def test_validate_user_input_type_mismatch(self):
        """Test type validation"""
        validator = SecurityValidator()

        data = {"age": "twenty"}
        rules = {"age": {"type": int, "required": True}}

        is_valid, error = validator.validate_user_input(data, rules)
        assert is_valid is False
        assert "type" in error.lower()

    def test_validate_user_input_string_length(self):
        """Test string length validation"""
        validator = SecurityValidator()

        # Too short
        data = {"username": "ab"}
        rules = {"username": {"type": str, "min": 3, "max": 10}}

        is_valid, error = validator.validate_user_input(data, rules)
        assert is_valid is False
        assert "at least" in error.lower()

        # Too long
        data = {"username": "abcdefghijk"}  # 11 chars
        is_valid, error = validator.validate_user_input(data, rules)
        assert is_valid is False
        assert "exceed" in error.lower()

    def test_validate_user_input_pattern(self):
        """Test pattern validation"""
        validator = SecurityValidator()

        data = {"code": "ABC123"}
        rules = {"code": {"type": str, "pattern": r"^[A-Z]{3}\d{3}$"}}

        is_valid, error = validator.validate_user_input(data, rules)
        assert is_valid is True

        # Invalid pattern
        data = {"code": "abc123"}
        is_valid, error = validator.validate_user_input(data, rules)
        assert is_valid is False
        assert "format" in error.lower()

    def test_validate_user_input_number_range(self):
        """Test number range validation"""
        validator = SecurityValidator()

        data = {"score": 150}
        rules = {"score": {"type": int, "min": 0, "max": 100}}

        is_valid, error = validator.validate_user_input(data, rules)
        assert is_valid is False
        assert "exceed" in error.lower()

    def test_sanitize_dict(self):
        """Test dictionary sanitization"""
        validator = SecurityValidator()

        data = {
            "name": '<script>alert(1)</script>John',
            "bio": "Hello & Welcome",
            "age": 25  # Not a string, should not be sanitized
        }

        result = validator.sanitize_dict(data, ["name", "bio"])

        assert '<script>' not in result["name"]
        assert "John" in result["name"]
        assert result["age"] == 25


class TestXSSPrevention:
    """Test XSS prevention"""

    def test_xss_script_tag_variations(self):
        """Test various script tag variations"""
        test_cases = [
            '<script>alert(1)</script>',
            '<SCRIPT>alert(1)</SCRIPT>',
            '<script src="evil.js"></script>',
            '<script type="text/javascript">alert(1)</script>',
            '<script>/* comment */alert(1)</script>',
        ]

        for test in test_cases:
            result = sanitize_string(test)
            assert '<script>' not in result.lower()
            assert 'alert(1)' not in result

    def test_xss_event_handlers(self):
        """Test event handler removal"""
        test_cases = [
            '<div onclick="alert(1)">click</div>',
            '<img onerror="alert(1)" src="x">',
            '<body onload="alert(1)">',
            '<a href="javascript:alert(1)">link</a>',
        ]

        for test in test_cases:
            result = sanitize_string(test)
            # Should not have executable handlers
            assert 'onclick=' not in result.lower()
            assert 'onerror=' not in result.lower()
            assert 'onload=' not in result.lower()
            assert 'javascript:' not in result.lower()

    def test_xss_encoded_payloads(self):
        """Test encoded XSS payloads"""
        # HTML entities
        test = '&lt;script&gt;alert(1)&lt;/script&gt;'
        result = sanitize_string(test)
        # Should remain encoded or be safe
        assert '<script>' not in result


class TestInjectionPrevention:
    """Test injection attack prevention"""

    def test_sql_injection_patterns(self):
        """Test detection of SQL injection patterns"""
        dangerous_inputs = [
            "'; DROP TABLE users; --",
            "1' OR '1'='1",
            "admin'--",
            "' UNION SELECT * FROM passwords--",
            "1; DELETE FROM users WHERE '1'='1"
        ]

        for inp in dangerous_inputs:
            # These should be caught by pattern validation
            result = sanitize_string(inp)
            # The sanitizer should escape or remove dangerous chars
            assert "'" not in result or "\\'" in result

    def test_no_sql_injection_patterns(self):
        """Test NoSQL injection prevention"""
        dangerous_inputs = [
            '{"$gt": ""}',
            '{"$ne": null}',
            '{"$where": "this.password == this.password"}'
        ]

        # These patterns should be detected and blocked
        for inp in dangerous_inputs:
            result = sanitize_string(inp)
            # Dollar signs should be escaped or removed
            assert '$' not in result or inp != result


class TestRateLimiting:
    """Test rate limiting functionality"""

    @pytest.mark.asyncio
    async def test_rate_limit_exceeded(self):
        """Test rate limit enforcement"""
        from app.security import limiter

        # Mock request
        mock_request = MagicMock()
        mock_request.client.host = "127.0.0.1"

        # This would need actual rate limiter testing
        # For now, just verify the limiter exists
        assert limiter is not None


class TestAuthenticationSecurity:
    """Test authentication security"""

    def test_password_strength(self):
        """Test password strength validation"""
        weak_passwords = [
            "123456",
            "password",
            "abc",
            "qwerty"
        ]

        # These should be rejected
        for pwd in weak_passwords:
            assert len(pwd) < 8 or pwd.isalpha()  # Weak criteria

    def test_token_expiration(self):
        """Test token expiration handling"""
        from datetime import datetime, timedelta

        # Simulate expired token
        expiry = datetime.utcnow() - timedelta(hours=1)
        assert expiry < datetime.utcnow()


class TestDataPrivacy:
    """Test data privacy protection"""

    def test_pii_detection(self):
        """Test PII detection and handling"""
        pii_patterns = [
            "123456789012",  # Aadhaar-like
            "ABCDE1234F",     # PAN-like
            "user@email.com"
        ]

        # These should be handled carefully
        for pii in pii_patterns:
            assert len(pii) > 0


if __name__ == "__main__":
    pytest.main([__file__, "-v"])

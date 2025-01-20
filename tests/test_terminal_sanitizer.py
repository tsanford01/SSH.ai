"""
Tests for terminal output sanitization.
"""

import pytest
from src.app.core.terminal_sanitizer import TerminalSanitizer

@pytest.fixture
def sanitizer():
    """Create a terminal sanitizer for testing."""
    return TerminalSanitizer()

def test_password_redaction(sanitizer):
    """Test that passwords are properly redacted."""
    # Test common password patterns
    assert sanitizer.sanitize("password=secret123") == "password=[REDACTED]"
    assert sanitizer.sanitize("pass: mypass") == "pass: [REDACTED]"
    assert sanitizer.sanitize("Enter password: hunter2") == "Enter password: [REDACTED]"
    
    # Test SSH password prompts
    assert sanitizer.sanitize("user@host's password:mysecret") == "user@host's password:[REDACTED]"
    assert sanitizer.sanitize("Password for user:pass123") == "Password for user:[REDACTED]"

def test_api_key_redaction(sanitizer):
    """Test that API keys are properly redacted."""
    # Test common API key patterns
    assert sanitizer.sanitize("api_key=sk-1234567890abcdef") == "api_key=[REDACTED]"
    assert sanitizer.sanitize("Bearer ghp_1234567890abcdef") == "Bearer [REDACTED]"
    assert sanitizer.sanitize("Authorization: Token abc123") == "Authorization: [REDACTED]"

def test_ssh_key_redaction(sanitizer):
    """Test that SSH keys are properly redacted."""
    input_text = """
    -----BEGIN RSA PRIVATE KEY-----
    MIIEpAIBAAKCAQEA1234567890
    abcdefghijklmnopqrstuvwxyz
    -----END RSA PRIVATE KEY-----
    """
    expected = """
    -----BEGIN RSA PRIVATE KEY-----
    [REDACTED]
    -----END RSA PRIVATE KEY-----
    """
    assert sanitizer.sanitize(input_text.strip()) == expected.strip()

def test_ip_preservation(sanitizer):
    """Test that IP addresses are preserved."""
    # IP addresses should not be redacted as they're needed for context
    text = "Connected to 192.168.1.100 on port 22"
    assert sanitizer.sanitize(text) == text

def test_command_preservation(sanitizer):
    """Test that normal commands are preserved."""
    # Regular commands should not be redacted
    commands = [
        "ls -la",
        "cd /home/user",
        "git status",
        "docker ps",
        "kubectl get pods"
    ]
    for cmd in commands:
        assert sanitizer.sanitize(cmd) == cmd

def test_multiple_patterns(sanitizer):
    """Test handling multiple sensitive patterns in one string."""
    input_text = """
    Connecting to api.example.com...
    Authorization: Bearer abc123xyz
    password=secretpass
    API_KEY=sk-0987654321
    """
    expected = """
    Connecting to api.example.com...
    Authorization: [REDACTED]
    password=[REDACTED]
    API_KEY=[REDACTED]
    """
    assert sanitizer.sanitize(input_text.strip()) == expected.strip()

def test_custom_pattern_addition(sanitizer):
    """Test adding custom patterns for redaction."""
    # Add custom pattern
    sanitizer.add_pattern(r"secret_\w+=\S+")
    
    # Test custom pattern
    assert sanitizer.sanitize("secret_token=abc123") == "secret_token=[REDACTED]"
    
    # Test alongside built-in patterns
    text = "secret_token=abc123 password=xyz789"
    assert sanitizer.sanitize(text) == "secret_token=[REDACTED] password=[REDACTED]"

def test_multiline_handling(sanitizer):
    """Test handling of multiline input."""
    input_text = """
    $ ssh user@host
    user@host's password: secret123
    Welcome to Ubuntu 20.04
    $ curl -H "Authorization: Bearer abc123" https://api.example.com
    """
    expected = """
    $ ssh user@host
    user@host's password: [REDACTED]
    Welcome to Ubuntu 20.04
    $ curl -H "Authorization: [REDACTED]" https://api.example.com
    """
    assert sanitizer.sanitize(input_text.strip()) == expected.strip()

def test_edge_cases(sanitizer):
    """Test edge cases and boundary conditions."""
    # Empty input
    assert sanitizer.sanitize("") == ""
    
    # Only whitespace
    assert sanitizer.sanitize("   \n   ") == "   \n   "
    
    # No sensitive data
    text = "Hello, world!\nThis is a normal message."
    assert sanitizer.sanitize(text) == text
    
    # Multiple consecutive sensitive items
    text = "pass:123 pass:456 pass:789"
    assert sanitizer.sanitize(text) == "pass:[REDACTED] pass:[REDACTED] pass:[REDACTED]" 
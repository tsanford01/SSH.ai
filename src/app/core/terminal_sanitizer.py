"""
Terminal output sanitizer for redacting sensitive information.
"""

import re
from typing import List, Pattern, Union

class TerminalSanitizer:
    """Sanitizes terminal output by redacting sensitive information."""
    
    def __init__(self) -> None:
        """Initialize terminal sanitizer with default patterns."""
        # Default patterns for sensitive information
        self._patterns: List[tuple[Pattern, str]] = [
            # SSH Keys (must be first to handle multiline properly)
            (
                re.compile(
                    r'(-----BEGIN.*?PRIVATE KEY-----\n)[\s\S]*?(-----END.*?PRIVATE KEY-----)',
                    re.MULTILINE
                ),
                lambda m: f"{m.group(1)}    [REDACTED]\n    {m.group(2)}"
            ),
            
            # Authorization headers (must be before bearer tokens)
            (
                re.compile(r'(?i)(authorization:\s*)(?:bearer\s+|token\s+)?[a-zA-Z0-9._-]+'),
                r'\1[REDACTED]'
            ),
            
            # Bearer tokens
            (
                re.compile(r'(?i)(bearer\s+)[a-zA-Z0-9._-]+'),
                r'\1[REDACTED]'
            ),
            
            # Password prompts (must be before general password patterns)
            (
                re.compile(r"(?i)(\S+'s password:\s*)\S+"),
                r'\1[REDACTED]'
            ),
            (
                re.compile(r"(?i)(password for \S+:\s*)\S+"),
                r'\1[REDACTED]'
            ),
            
            # Passwords
            (
                re.compile(r'(?i)(password\s*[=:]\s*)\S+'),
                r'\1[REDACTED]'
            ),
            (
                re.compile(r'(?i)(pass\s*[=:]\s*)\S+'),
                r'\1[REDACTED]'
            ),
            (
                re.compile(r"(?i)(password for \S+\s*[=:]\s*)\S+"),
                r'\1[REDACTED]'
            ),
            
            # API Keys and Tokens
            (
                re.compile(r'(?i)(api[_-]key\s*[=:]\s*)\S+'),
                r'\1[REDACTED]'
            ),
            (
                re.compile(r'(?i)(token\s*[=:]\s*)\S+'),
                r'\1[REDACTED]'
            ),
            (
                re.compile(r'(?i)(secret\s*[=:]\s*)\S+'),
                r'\1[REDACTED]'
            ),
        ]
    
    def add_pattern(self, pattern: str) -> None:
        """
        Add a custom pattern for redaction.
        
        Args:
            pattern: Regular expression pattern to match sensitive data
        """
        # For patterns with = or :, capture everything before the value
        if '=' in pattern or ':' in pattern:
            # Split on = or : and capture the prefix
            prefix = pattern.split('=')[0] if '=' in pattern else pattern.split(':')[0]
            pattern = f"({re.escape(prefix)}[=:])\\s*\\S+"
        # For other patterns, capture non-whitespace before the value
        else:
            pattern = re.sub(r'^(\S+)', r'(\1)', pattern)
        
        self._patterns.append((
            re.compile(pattern),
            r'\1[REDACTED]'
        ))
    
    def sanitize(self, text: str) -> str:
        """
        Sanitize text by redacting sensitive information.
        
        Args:
            text: Text to sanitize
            
        Returns:
            Sanitized text with sensitive information redacted
        """
        if not text:
            return text
        
        result = text
        
        # Apply each pattern
        for pattern, replacement in self._patterns:
            if callable(replacement):
                result = pattern.sub(replacement, result)
            else:
                result = pattern.sub(replacement, result)
        
        return result 
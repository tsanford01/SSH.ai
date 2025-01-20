"""
Tests for prompt template functionality.
"""

import pytest
from typing import Dict, Any

from src.app.core.prompt_templates import PromptTemplate, PromptType, Context

@pytest.fixture
def basic_context():
    """Create basic context for testing."""
    return Context(
        command_history=["ssh user@host", "ls -la", "cd /var/log"],
        current_command="ssh -p 2222 user@host",
        error_message=None,
        system_info=None,
        connection_state=None
    )

@pytest.fixture
def error_context():
    """Create context with error for testing."""
    return Context(
        command_history=["ssh user@host", "scp file.txt user@host:"],
        current_command="scp file.txt user@host:",
        error_message="Permission denied (publickey).",
        system_info={"os": "Linux", "version": "5.15.0"},
        connection_state={"authenticated": False, "key_type": "RSA"}
    )

def test_command_explanation_prompt(basic_context):
    """Test command explanation prompt generation."""
    prompt = PromptTemplate.generate(PromptType.COMMAND_EXPLANATION, basic_context)
    
    # Check system prompt inclusion
    assert "expert SSH assistant" in prompt
    
    # Check command inclusion
    assert "ssh -p 2222 user@host" in prompt
    
    # Check history inclusion
    for cmd in basic_context.command_history:
        assert cmd in prompt
    
    # Check template structure
    assert "Analyze this SSH command:" in prompt
    assert "Recent command history:" in prompt
    assert "What the command does" in prompt

def test_error_analysis_prompt(error_context):
    """Test error analysis prompt generation."""
    prompt = PromptTemplate.generate(PromptType.ERROR_ANALYSIS, error_context)
    
    # Check error message inclusion
    assert "Permission denied (publickey)" in prompt
    
    # Check system info inclusion
    assert "Linux" in str(prompt)
    assert "5.15.0" in str(prompt)
    
    # Check template structure
    assert "Analyze this SSH error:" in prompt
    assert "Root cause analysis" in prompt

def test_security_check_prompt(error_context):
    """Test security check prompt generation."""
    prompt = PromptTemplate.generate(PromptType.SECURITY_CHECK, error_context)
    
    # Check connection state inclusion
    assert "RSA" in str(prompt)
    
    # Check template structure
    assert "Review this SSH operation for security:" in prompt
    assert "Security risks" in prompt
    assert "Compliance with best practices" in prompt

def test_performance_optimization_prompt(error_context):
    """Test performance optimization prompt generation."""
    prompt = PromptTemplate.generate(PromptType.PERFORMANCE_OPTIMIZATION, error_context)
    
    # Check system and connection info inclusion
    assert "Linux" in str(prompt)
    assert "authenticated" in str(prompt)
    
    # Check template structure
    assert "Analyze SSH performance:" in prompt
    assert "Performance bottlenecks" in prompt
    assert "Optimization opportunities" in prompt

def test_connection_issue_prompt(error_context):
    """Test connection issue prompt generation."""
    prompt = PromptTemplate.generate(PromptType.CONNECTION_ISSUE, error_context)
    
    # Check error and state inclusion
    assert "Permission denied" in prompt
    assert "authenticated" in str(prompt)
    assert "RSA" in str(prompt)
    
    # Check template structure
    assert "Diagnose SSH connection issue:" in prompt
    assert "Connection diagnosis" in prompt
    assert "Troubleshooting steps" in prompt

def test_history_limit(basic_context):
    """Test that command history is limited to recent commands."""
    # Add more commands to history
    basic_context.command_history.extend([
        "command1", "command2", "command3",
        "command4", "command5", "command6"
    ])
    
    prompt = PromptTemplate.generate(PromptType.COMMAND_EXPLANATION, basic_context)
    
    # Should only include last 5 commands
    assert "command1" not in prompt
    assert "command6" in prompt

def test_empty_context():
    """Test prompt generation with minimal context."""
    context = Context(command_history=[])
    prompt = PromptTemplate.generate(PromptType.COMMAND_EXPLANATION, context)
    
    # Should still include system prompt and template structure
    assert "expert SSH assistant" in prompt
    assert "Analyze this SSH command:" in prompt
    
    # Empty fields should be handled gracefully
    assert "None" not in prompt 
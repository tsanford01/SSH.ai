"""
Tests for error correction functionality.
"""

import pytest
from src.app.core.error_correction import ErrorCorrector, ErrorCorrection
from src.app.core.command_history import CommandHistory

def test_command_not_found():
    """Test correction of 'command not found' errors."""
    history = CommandHistory()
    corrector = ErrorCorrector(history)
    
    # Test with typo in git command
    corrections = corrector.get_correction(
        "gti status",
        "gti: command not found"
    )
    
    assert len(corrections) > 0
    assert any(c.suggested_command == "git status" for c in corrections)
    assert any(c.error_type == "command_not_found" for c in corrections)

def test_permission_denied():
    """Test correction of permission denied errors."""
    history = CommandHistory()
    corrector = ErrorCorrector(history)
    
    # Test without sudo
    corrections = corrector.get_correction(
        "apt update",
        "permission denied"
    )
    
    assert len(corrections) > 0
    assert any(c.suggested_command == "sudo apt update" for c in corrections)
    assert any(c.error_type == "permission_denied" for c in corrections)

def test_no_such_file():
    """Test correction of 'no such file' errors."""
    history = CommandHistory()
    corrector = ErrorCorrector(history)
    
    # Add some history
    history.add_command("cat README.md", 0, 0.1)
    
    # Test with typo in filename
    corrections = corrector.get_correction(
        "cat READNE.md",
        "no such file or directory"
    )
    
    assert len(corrections) > 0
    assert any(c.suggested_command == "ls" for c in corrections)
    assert any(c.error_type == "no_such_file" for c in corrections)

def test_invalid_option():
    """Test correction of invalid option errors."""
    history = CommandHistory()
    corrector = ErrorCorrector(history)
    
    # Add some history with correct flags
    history.add_command("ls -l", 0, 0.1)
    history.add_command("ls -a", 0, 0.1)
    
    # Test with invalid flag
    corrections = corrector.get_correction(
        "ls -z",
        "ls: invalid option -- 'z'"
    )
    
    assert len(corrections) > 0
    assert any(c.suggested_command == "ls --help" for c in corrections)
    assert any(c.error_type == "invalid_option" for c in corrections)

def test_history_based_corrections():
    """Test corrections based on command history."""
    history = CommandHistory()
    corrector = ErrorCorrector(history)
    
    # Add successful commands to history
    history.add_command("git status", 0, 0.1)
    history.add_command("git add .", 0, 0.1)
    history.add_command("git commit -m 'test'", 0, 0.2)
    
    # Test with a command that might benefit from common flags
    corrections = corrector.get_correction(
        "git commit",
        "Aborting commit due to empty commit message"
    )
    
    assert len(corrections) > 0
    assert any("-m" in c.suggested_command for c in corrections)

def test_package_suggestions():
    """Test suggestions for installing packages."""
    history = CommandHistory()
    corrector = ErrorCorrector(history)
    
    # Test with a command from a common package
    corrections = corrector.get_correction(
        "docker ps",
        "docker: command not found"
    )
    
    assert len(corrections) > 0
    assert any("apt install docker.io" in c.suggested_command for c in corrections)
    assert any(c.error_type == "package_missing" for c in corrections)

def test_multiple_suggestions():
    """Test that multiple relevant suggestions are returned."""
    history = CommandHistory()
    corrector = ErrorCorrector(history)
    
    # Add some history
    history.add_command("git status", 0, 0.1)
    history.add_command("git add .", 0, 0.1)
    
    # Test with a typo that could have multiple corrections
    corrections = corrector.get_correction(
        "gti status",
        "gti: command not found"
    )
    
    assert 1 <= len(corrections) <= 3  # Should return 1-3 suggestions
    assert all(isinstance(c, ErrorCorrection) for c in corrections)
    assert all(0 <= c.confidence <= 1.0 for c in corrections)

def test_confidence_sorting():
    """Test that suggestions are sorted by confidence."""
    history = CommandHistory()
    corrector = ErrorCorrector(history)
    
    # Add some history
    history.add_command("git status", 0, 0.1)
    
    # Get corrections
    corrections = corrector.get_correction(
        "gti status",
        "gti: command not found"
    )
    
    if len(corrections) > 1:
        # Verify confidence sorting
        confidences = [c.confidence for c in corrections]
        assert confidences == sorted(confidences, reverse=True)

def test_empty_input():
    """Test handling of empty input."""
    history = CommandHistory()
    corrector = ErrorCorrector(history)
    
    with pytest.raises(ValueError):
        corrector.get_correction("", "command not found") 
"""
Tests for command explanation functionality.
"""

import pytest
from src.app.core.command_explainer import CommandExplainer, CommandExplanation
from src.app.core.command_history import CommandHistory

def test_basic_command_explanation():
    """Test basic command explanation."""
    history = CommandHistory()
    explainer = CommandExplainer(history)
    
    explanation = explainer.explain_command("ls -l /home")
    
    assert explanation.command == "ls -l /home"
    assert "directory contents" in explanation.description.lower()
    assert "-l" in explanation.flags_explained
    assert any("Path: /home" in arg for arg in explanation.args_explained)
    assert len(explanation.examples) > 0

def test_git_command_explanation():
    """Test git command explanation."""
    history = CommandHistory()
    explainer = CommandExplainer(history)
    
    explanation = explainer.explain_command("git commit -m 'test'")
    
    assert "version control" in explanation.description.lower()
    assert "-m" in explanation.flags_explained
    assert "repository" in explanation.expected_output.lower()
    assert any("repository" in effect for effect in explanation.side_effects)

def test_risky_command_explanation():
    """Test explanation of risky commands."""
    history = CommandHistory()
    explainer = CommandExplainer(history)
    
    explanation = explainer.explain_command("rm -rf /path")
    
    assert "delete" in explanation.description.lower()
    assert len(explanation.risks) >= 2
    assert any("permanently delete" in risk.lower() for risk in explanation.risks)
    assert any("recursive" in risk.lower() for risk in explanation.risks)
    assert len(explanation.alternatives) > 0

def test_sudo_command_explanation():
    """Test explanation of sudo commands."""
    history = CommandHistory()
    explainer = CommandExplainer(history)
    
    explanation = explainer.explain_command("sudo apt update")
    
    assert len(explanation.risks) > 0
    assert any("elevated privileges" in risk.lower() for risk in explanation.risks)
    assert any("system" in effect.lower() for effect in explanation.side_effects)

def test_command_with_redirections():
    """Test explanation of commands with redirections."""
    history = CommandHistory()
    explainer = CommandExplainer(history)
    
    explanation = explainer.explain_command("echo 'test' > file.txt")
    
    assert len(explanation.side_effects) > 0
    assert any("output files" in effect.lower() for effect in explanation.side_effects)

def test_command_with_history_examples():
    """Test command examples from history."""
    history = CommandHistory()
    history.add_command("git status", 0, 0.1)
    history.add_command("git add .", 0, 0.1)
    history.add_command("git commit -m 'test'", 0, 0.2)
    
    explainer = CommandExplainer(history)
    explanation = explainer.explain_command("git")
    
    assert len(explanation.examples) > 0
    assert any("git status" in example for example in explanation.examples)
    assert any("git add" in example for example in explanation.examples)

def test_alternative_commands():
    """Test alternative command suggestions."""
    history = CommandHistory()
    explainer = CommandExplainer(history)
    
    # Test rm alternatives
    explanation = explainer.explain_command("rm file.txt")
    assert len(explanation.alternatives) > 0
    assert any("trash-put" in alt for alt in explanation.alternatives)
    
    # Test ls alternatives
    explanation = explainer.explain_command("ls")
    assert len(explanation.alternatives) > 0
    assert any("exa" in alt for alt in explanation.alternatives)

def test_argument_explanation():
    """Test argument explanation."""
    history = CommandHistory()
    explainer = CommandExplainer(history)
    
    explanation = explainer.explain_command("cp *.txt /backup/")
    
    assert len(explanation.args_explained) == 2
    assert any("Pattern" in arg for arg in explanation.args_explained)
    assert any("Path" in arg for arg in explanation.args_explained)

def test_unknown_command():
    """Test handling of unknown commands."""
    history = CommandHistory()
    explainer = CommandExplainer(history)
    
    explanation = explainer.explain_command("unknown_cmd")
    
    assert "no description available" in explanation.description.lower()
    assert len(explanation.flags_explained) == 0
    assert "unknown" in explanation.expected_output.lower()

def test_empty_command():
    """Test handling of empty command."""
    history = CommandHistory()
    explainer = CommandExplainer(history)
    
    with pytest.raises(ValueError):
        explainer.explain_command("") 
"""
Tests for command parsing functionality.
"""

import pytest
from src.app.core.command_parser import CommandParser, ParsedCommand

@pytest.fixture
def parser():
    """Create command parser for testing."""
    return CommandParser()

def test_basic_command_parsing(parser):
    """Test parsing basic command."""
    cmd = parser.parse_command("ls -l /home")
    assert cmd.raw_command == "ls -l /home"
    assert cmd.base_command == "ls"
    assert "-l" in cmd.flags
    assert "/home" in cmd.args

def test_command_with_multiple_flags(parser):
    """Test parsing command with multiple flags."""
    cmd = parser.parse_command("ssh -p 2222 -i key.pem user@host")
    assert cmd.base_command == "ssh"
    assert cmd.args == ["user@host"]
    assert cmd.flags == {"-p": "2222", "-i": "key.pem"}

def test_sudo_command(parser):
    """Test parsing sudo command."""
    cmd = parser.parse_command("sudo apt update")
    assert cmd.base_command == "apt"
    assert cmd.args == ["update"]
    assert cmd.is_sudo
    assert not cmd.is_pipeline

def test_pipeline_command(parser):
    """Test parsing pipeline command."""
    cmd = parser.parse_command("ps aux | grep python")
    assert cmd.is_pipeline
    assert len(cmd.pipeline_commands) == 2
    assert cmd.pipeline_commands[0].base_command == "ps"
    assert cmd.pipeline_commands[1].base_command == "grep"

def test_command_with_redirections(parser):
    """Test parsing command with redirections."""
    cmd = parser.parse_command("echo 'hello' > output.txt 2> error.log")
    assert cmd.base_command == "echo"
    assert cmd.args == ["hello"]
    assert cmd.redirections == {">": "output.txt", "2>": "error.log"}

def test_command_with_environment(parser):
    """Test parsing command with environment context."""
    env = {"PATH": "/usr/bin", "HOME": "/home/user"}
    cmd = parser.parse_command("python script.py", environment=env)
    assert cmd.environment == env
    assert cmd.base_command == "python"
    assert cmd.args == ["script.py"]

def test_empty_command(parser):
    """Test handling empty command."""
    with pytest.raises(ValueError):
        parser.parse_command("")

def test_command_type_detection(parser):
    """Test command type detection."""
    file_cmd = parser.parse_command("cp file1 file2")
    assert parser.get_command_type(file_cmd) == "file_operation"
    
    text_cmd = parser.parse_command("grep pattern file")
    assert parser.get_command_type(text_cmd) == "text_operation"
    
    system_cmd = parser.parse_command("ps aux")
    assert parser.get_command_type(system_cmd) == "system_operation"
    
    network_cmd = parser.parse_command("curl http://example.com")
    assert parser.get_command_type(network_cmd) == "network_operation"
    
    script_cmd = parser.parse_command("./script.sh")
    assert parser.get_command_type(script_cmd) == "script_execution"

def test_risk_analysis(parser):
    """Test command risk analysis."""
    # Test high-risk sudo command
    sudo_cmd = parser.parse_command("sudo rm -rf /")
    risks = parser.analyze_risk(sudo_cmd)
    assert risks["level"] == "high"
    assert "system modification" in risks["reasons"]
    assert "requires elevated privileges" in risks["reasons"]
    
    # Test medium-risk command
    rm_cmd = parser.parse_command("rm -rf temp/")
    risks = parser.analyze_risk(rm_cmd)
    assert risks["level"] == "medium"
    assert "destructive" in risks["factors"][0].lower()
    
    # Test low-risk command
    ls_cmd = parser.parse_command("ls -l")
    risks = parser.analyze_risk(ls_cmd)
    assert risks["level"] == "low"
    assert not risks["requires_confirmation"]

def test_context_requirements(parser):
    """Test context requirements detection."""
    # Test file operation
    cp_cmd = parser.parse_command("cp source.txt dest.txt")
    requires = parser.get_context_requirements(cp_cmd)
    assert requires["working_dir"]
    assert requires["file_info"]
    assert requires["permissions"]
    
    # Test network operation
    ssh_cmd = parser.parse_command("ssh user@host")
    requires = parser.get_context_requirements(ssh_cmd)
    assert requires["network_info"]
    assert requires["env_vars"]
    
    # Test system operation
    ps_cmd = parser.parse_command("ps aux")
    requires = parser.get_context_requirements(ps_cmd)
    assert requires["process_info"]
    assert requires["permissions"]

def test_complex_pipeline(parser):
    """Test parsing complex pipeline command."""
    cmd = parser.parse_command("cat file.txt | grep error | sort | uniq -c")
    assert cmd.is_pipeline
    assert len(cmd.pipeline_commands) == 4
    
    # Check each command in pipeline
    assert cmd.pipeline_commands[0].base_command == "cat"
    assert cmd.pipeline_commands[1].base_command == "grep"
    assert cmd.pipeline_commands[2].base_command == "sort"
    assert cmd.pipeline_commands[3].base_command == "uniq"
    
    # Check flags in pipeline
    assert cmd.pipeline_commands[3].flags == {"-c": None}

def test_quoted_arguments(parser):
    """Test handling quoted arguments."""
    cmd = parser.parse_command('echo "Hello World" \'Special chars: $@#\'')
    assert cmd.base_command == "echo"
    assert cmd.args == ["Hello World", "Special chars: $@#"]

def test_command_with_working_directory(parser):
    """Test parsing command with working directory context."""
    working_dir = "/home/user/project"
    cmd = parser.parse_command("git status", working_dir=working_dir)
    assert cmd.working_dir == working_dir 
"""
Command parsing and analysis module.
"""

from typing import Dict, List, Optional, Any
from dataclasses import dataclass
import shlex
import re
from pathlib import Path

@dataclass
class ParsedCommand:
    """Structured representation of a parsed command."""
    
    raw_command: str
    base_command: str
    args: List[str]
    flags: Dict[str, Optional[str]]
    working_dir: Optional[str] = None
    environment: Dict[str, str] = None
    redirections: Dict[str, str] = None
    is_sudo: bool = False
    is_pipeline: bool = False
    pipeline_commands: List['ParsedCommand'] = None

class CommandParser:
    """Parser for shell commands.
    
    This class provides functionality to parse shell commands into their components,
    handling various command formats including:
    - Basic commands with arguments (ls -l /home)
    - Commands with multiple flags (ssh -p 2222 -i key.pem user@host)
    - Combined short flags (tar -xzf archive.tar.gz)
    - Long flags with values (--output=file.txt or --output file.txt)
    - Pipeline commands (cat file.txt | grep pattern)
    - Redirections (command > output.txt)
    - Sudo commands (sudo command)
    
    The parser properly distinguishes between flags, flag values, and positional arguments,
    with special handling for certain command-specific cases (e.g., tar command's -f flag).
    """
    
    def __init__(self):
        """Initialize the command parser with predefined command type mappings."""
        self._file_operations = {
            'cat', 'cd', 'cp', 'ls', 'mkdir', 'mv', 'pwd', 'rm', 'rmdir', 'touch'
        }
        self._network_operations = {
            'curl', 'wget', 'ping', 'ssh', 'scp', 'nc', 'telnet'
        }
        self._system_operations = {
            'ps', 'top', 'kill', 'service', 'systemctl'
        }
        self._text_operations = {
            'grep', 'sed', 'awk', 'cat', 'head', 'tail', 'less', 'more',
            'sort', 'uniq', 'wc', 'diff', 'patch'
        }

    def parse_command(self, command: str, environment: Dict[str, str] = None, 
                     working_dir: str = None) -> ParsedCommand:
        """Parse a shell command into its components.
        
        This method breaks down a shell command into its constituent parts:
        - Base command
        - Arguments
        - Flags (with or without values)
        - Environment variables
        - Working directory
        - Redirections
        - Pipeline information
        
        Args:
            command: The shell command to parse
            environment: Optional dictionary of environment variables
            working_dir: Optional working directory for the command
            
        Returns:
            ParsedCommand object containing all parsed components
            
        Raises:
            ValueError: If the command is empty or has invalid syntax
            
        Examples:
            >>> parser = CommandParser()
            >>> cmd = parser.parse_command("ls -l /home")
            >>> print(cmd.base_command)  # "ls"
            >>> print(cmd.flags)  # {"l": None}
            >>> print(cmd.args)  # ["/home"]
            
            >>> cmd = parser.parse_command("tar -xzf archive.tar.gz")
            >>> print(cmd.flags)  # {"x": None, "z": None, "f": None}
            >>> print(cmd.args)  # ["archive.tar.gz"]
        """
        if not command:
            raise ValueError("Command cannot be empty")
        
        # Handle pipeline commands
        if '|' in command:
            pipeline_parts = command.split('|')
            pipeline_commands = [self.parse_command(cmd.strip()) for cmd in pipeline_parts]
            base = pipeline_commands[0]
            base.is_pipeline = True
            base.pipeline_commands = pipeline_commands
            return base
        
        # Parse redirections
        redirections = {}
        redirect_pattern = r'([012]?[<>]+)\s*(\S+)'
        redirect_matches = re.finditer(redirect_pattern, command)
        for match in redirect_matches:
            redirections[match.group(1)] = match.group(2)
            command = command.replace(match.group(0), '')
        
        # Parse command using shlex to handle quotes properly
        try:
            parts = shlex.split(command.strip())
        except ValueError as e:
            raise ValueError(f"Invalid command syntax: {str(e)}")
            
        if not parts:
            raise ValueError("No command parts after parsing")
            
        # Handle sudo commands
        is_sudo = False
        if parts[0] == 'sudo':
            is_sudo = True
            parts = parts[1:]
            if not parts:
                raise ValueError("No command specified after sudo")
                
        base_command = parts[0]
        args = []
        flags = {}
        i = 1
        
        # Define flags that expect values
        value_flags = {
            'p', 'i', 'n', 'o', 'e', 't',  # Common single-char flags
            'output', 'file', 'port'  # Common long flags
        }
        
        while i < len(parts):
            part = parts[i]
            
            if part == '--':
                # Everything after -- is an argument
                args.extend(parts[i+1:])
                break
            elif part.startswith('--'):
                # Long flag
                flag_name = part[2:]
                if '=' in flag_name:
                    # Explicit value with equals
                    name, value = flag_name.split('=', 1)
                    flags[name] = value
                else:
                    if flag_name in value_flags and i + 1 < len(parts) and not parts[i + 1].startswith('-'):
                        flags[flag_name] = parts[i + 1]
                        i += 1
                    else:
                        flags[flag_name] = None
            elif part.startswith('-'):
                # Short flag(s)
                flag_chars = part[1:]
                if len(flag_chars) == 1:
                    # Single short flag
                    if flag_chars in value_flags and i + 1 < len(parts) and not parts[i + 1].startswith('-'):
                        flags[flag_chars] = parts[i + 1]
                        i += 1
                    else:
                        flags[flag_chars] = None
                else:
                    # Combined short flags
                    last_flag = flag_chars[-1]
                    # Set all flags except the last one
                    for flag in flag_chars[:-1]:
                        flags[flag] = None
                    
                    # Special case for tar command
                    if base_command == 'tar' and last_flag == 'f':
                        if i + 1 < len(parts):
                            flags[last_flag] = None
                            args.append(parts[i + 1])
                            i += 1
                        else:
                            flags[last_flag] = None
                    else:
                        flags[last_flag] = None
            else:
                # Not a flag, must be an argument
                args.append(part)
            i += 1
                
        return ParsedCommand(
            raw_command=command,
            base_command=base_command,
            args=args,
            flags=flags,
            working_dir=working_dir,
            environment=environment or {},
            redirections=redirections,
            is_sudo=is_sudo,
            is_pipeline=False,
            pipeline_commands=None
        )

    def analyze_risk(self, command: ParsedCommand) -> Dict[str, Any]:
        """
        Analyze command risk level.

        Args:
            command: Parsed command to analyze

        Returns:
            Risk analysis results
        """
        risk_level = "low"
        reasons = []
        factors = []

        # Check for elevated privileges
        if command.is_sudo:
            risk_level = "high"
            reasons.append("requires elevated privileges")
            factors.append("sudo execution")

        # Check for destructive operations
        destructive_commands = {"rm", "dd", "mkfs", "fdisk", "format", "shred"}
        if command.base_command in destructive_commands:
            risk_level = "high" if command.is_sudo else "medium"
            reasons.append("system modification")
            factors.append("destructive operation")
            if "f" in command.flags or "force" in command.flags:
                reasons.append("force flag used")
                factors.append("force flag")
            if "r" in command.flags or "R" in command.flags or "recursive" in command.flags:
                reasons.append("recursive operation")
                factors.append("recursive")

        # Check for system-wide impact
        system_commands = {"shutdown", "reboot", "halt", "poweroff", "init"}
        if command.base_command in system_commands:
            risk_level = "high"
            reasons.append("system-wide impact")
            factors.append("system control")

        # Check for network exposure
        network_commands = {"nc", "netcat", "telnet"}
        if command.base_command in network_commands:
            risk_level = max(risk_level, "medium")
            reasons.append("network exposure")
            factors.append("network operation")

        # Check for file overwrites
        if command.redirections and ">" in command.redirections:
            factors.append("file overwrite")
            if risk_level == "low":
                risk_level = "medium"

        return {
            "level": risk_level,
            "reasons": reasons,
            "factors": factors,
            "requires_confirmation": risk_level in ("medium", "high")
        }

    def get_context_requirements(self, command: ParsedCommand) -> Dict[str, bool]:
        """Get context requirements for a command."""
        requirements = {
            "working_dir": False,
            "file_info": False,
            "needs_network": False,
            "needs_git": False
        }
        
        # Check for file operations
        if command.base_command in self._file_operations:
            requirements["working_dir"] = True
            requirements["file_info"] = True
            
        # Check for network operations
        if command.base_command in self._network_operations:
            requirements["needs_network"] = True
            
        # Check for git operations
        if command.base_command == "git":
            requirements["needs_git"] = True
            requirements["working_dir"] = True
            
        return requirements

    def get_command_type(self, command: ParsedCommand) -> str:
        """
        Get type of command.
        
        Args:
            command: Parsed command object
            
        Returns:
            Command type string
        """
        base = command.base_command
        
        # Check for package management commands
        if base in {'apt', 'apt-get', 'yum', 'dnf', 'pacman', 'brew'}:
            return 'package_management'
        
        # Check for git commands
        if base == 'git':
            return 'version_control'
            
        # Check for docker commands
        if base in {'docker', 'docker-compose', 'podman'}:
            return 'container_management'
            
        # Check existing command types
        if base in self._file_operations:
            return 'file_operation'
        elif base in self._text_operations:
            return 'text_operation'
        elif base in self._system_operations:
            return 'system_operation'
        elif base in self._network_operations:
            return 'network_operation'
            
        # Check for script execution
        if base.startswith('./') or '/' in base or base.endswith('.sh') or base.endswith('.py'):
            return 'script_execution'
            
        # Check for environment management
        if base in {'export', 'env', 'printenv', 'set'}:
            return 'environment_management'
            
        # Check for user management
        if base in {'useradd', 'usermod', 'userdel', 'passwd', 'chown', 'chgrp', 'sudo', 'su'}:
            return 'user_management'
            
        return 'other'
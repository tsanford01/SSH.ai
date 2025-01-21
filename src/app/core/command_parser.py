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
    """Parser for shell commands."""

    def parse_command(self, command: str) -> ParsedCommand:
        """Parse a shell command into its components."""
        if not command:
            raise ValueError("Command cannot be empty")
        
        parts = shlex.split(command)
        if not parts:
            raise ValueError("Invalid command")
        
        base_command = parts[0]
        flags = []
        args = []
        is_sudo = False
        
        if base_command == 'sudo':
            is_sudo = True
            if len(parts) > 1:
                base_command = parts[1]
                parts = parts[1:]
            else:
                raise ValueError("Invalid sudo command")
        
        for part in parts[1:]:
            if part.startswith('-'):
                # Handle combined short flags (e.g., -rf)
                if part.startswith('--'):
                    flags.append(part)
                else:
                    # Split combined flags (e.g., -rf -> -r -f)
                    for i, flag in enumerate(part[1:]):
                        flags.append(f"-{flag}")
            else:
                args.append(part)
        
        return ParsedCommand(
            raw_command=command,
            base_command=base_command,
            flags=flags,
            args=args,
            is_sudo=is_sudo
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

        # Check for elevated privileges
        if command.is_sudo:
            risk_level = "high"
            reasons.append("requires elevated privileges")

        # Check for destructive operations
        destructive_commands = {"rm", "dd", "mkfs", "fdisk"}
        if command.base_command in destructive_commands:
            risk_level = "high"
            reasons.append("system modification")
            if "-rf" in command.flags or "-f" in command.flags:
                reasons.append("force flag used")

        return {
            "level": risk_level,
            "reasons": reasons,
            "requires_confirmation": risk_level == "high"
        }

    def get_command_type(self, command: ParsedCommand) -> str:
        """
        Get type of command.
        
        Args:
            command: Parsed command object
            
        Returns:
            Command type string
        """
        base = command.base_command
        
        if base in self._file_operations:
            return 'file_operation'
        elif base in self._text_operations:
            return 'text_operation'
        elif base in self._system_operations:
            return 'system_operation'
        elif base in self._network_operations:
            return 'network_operation'
        elif base.startswith('./') or '/' in base:
            return 'script_execution'
        else:
            return 'other'
    
    def get_context_requirements(self, command: ParsedCommand) -> Dict[str, bool]:
        """
        Determine what context information is needed for command.
        
        Args:
            command: Parsed command object
            
        Returns:
            Dictionary of required context flags
        """
        requires = {
            'working_dir': False,
            'file_info': False,
            'permissions': False,
            'env_vars': False,
            'process_info': False,
            'network_info': False
        }
        
        cmd_type = self.get_command_type(command)
        
        if cmd_type == 'file_operation':
            requires.update({
                'working_dir': True,
                'file_info': True,
                'permissions': True
            })
        
        elif cmd_type == 'system_operation':
            requires.update({
                'process_info': True,
                'permissions': True
            })
        
        elif cmd_type == 'network_operation':
            requires.update({
                'network_info': True,
                'env_vars': True
            })
        
        # Additional context for specific commands
        if command.base_command in {'cd', 'pwd'}:
            requires['working_dir'] = True
        
        elif command.base_command in {'env', 'export', 'source'}:
            requires['env_vars'] = True
        
        return requires 
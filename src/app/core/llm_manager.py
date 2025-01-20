"""
Local LLM manager for SSH assistance.
"""

import os
import psutil
import logging
from typing import Optional, Dict, Any, List
from pathlib import Path
from dataclasses import dataclass
import sys

from .prompt_templates import PromptTemplate, PromptType, Context

logger = logging.getLogger(__name__)

@dataclass
class LLMConfig:
    """Configuration for LLM usage."""
    max_memory_mb: int = 2048
    max_cpu_percent: int = 50
    context_length: int = 1024
    temperature: float = 0.7

class LLMManager:
    """Manages local LLM model loading and inference."""
    
    def __init__(self, config: Optional[LLMConfig] = None) -> None:
        """
        Initialize LLM manager.
        
        Args:
            config: LLM configuration. If None, uses default config.
        """
        self.config = config or LLMConfig()
        self._process = psutil.Process(os.getpid())
        self._command_history: List[str] = []
        self._system_info: Dict[str, Any] = {
            "os": os.name,
            "platform": sys.platform,
            "python_version": sys.version
        }
        self._connection_state: Dict[str, Any] = {}
    
    def analyze_command(self, command: str) -> str:
        """
        Analyze an SSH command.
        
        Args:
            command: SSH command to analyze
            
        Returns:
            Analysis and recommendations
        """
        context = Context(
            command_history=self._command_history,
            current_command=command,
            system_info=self._system_info,
            connection_state=self._connection_state
        )
        
        prompt = PromptTemplate.generate(PromptType.COMMAND_EXPLANATION, context)
        return self._generate_response(prompt)
    
    def analyze_error(self, error: str, command: Optional[str] = None) -> str:
        """
        Analyze an SSH error.
        
        Args:
            error: Error message to analyze
            command: Related command that caused the error
            
        Returns:
            Error analysis and solutions
        """
        context = Context(
            command_history=self._command_history,
            current_command=command,
            error_message=error,
            system_info=self._system_info,
            connection_state=self._connection_state
        )
        
        prompt = PromptTemplate.generate(PromptType.ERROR_ANALYSIS, context)
        return self._generate_response(prompt)
    
    def check_security(self, command: Optional[str] = None) -> str:
        """
        Perform security analysis.
        
        Args:
            command: Command to analyze for security
            
        Returns:
            Security analysis and recommendations
        """
        context = Context(
            command_history=self._command_history,
            current_command=command,
            system_info=self._system_info,
            connection_state=self._connection_state
        )
        
        prompt = PromptTemplate.generate(PromptType.SECURITY_CHECK, context)
        return self._generate_response(prompt)
    
    def optimize_performance(self) -> str:
        """
        Analyze and suggest performance optimizations.
        
        Returns:
            Performance analysis and recommendations
        """
        context = Context(
            command_history=self._command_history,
            system_info=self._system_info,
            connection_state=self._connection_state
        )
        
        prompt = PromptTemplate.generate(PromptType.PERFORMANCE_OPTIMIZATION, context)
        return self._generate_response(prompt)
    
    def diagnose_connection(self, error: Optional[str] = None) -> str:
        """
        Diagnose connection issues.
        
        Args:
            error: Connection error message if any
            
        Returns:
            Connection diagnosis and solutions
        """
        context = Context(
            command_history=self._command_history,
            error_message=error,
            system_info=self._system_info,
            connection_state=self._connection_state
        )
        
        prompt = PromptTemplate.generate(PromptType.CONNECTION_ISSUE, context)
        return self._generate_response(prompt)
    
    def update_connection_state(self, state: Dict[str, Any]) -> None:
        """
        Update SSH connection state.
        
        Args:
            state: New connection state information
        """
        self._connection_state.update(state)
    
    def add_command(self, command: str) -> None:
        """
        Add command to history.
        
        Args:
            command: Command to add to history
        """
        self._command_history.append(command)
        # Keep only last 100 commands
        if len(self._command_history) > 100:
            self._command_history = self._command_history[-100:]
    
    def _generate_response(self, prompt: str) -> str:
        """
        Generate response from the model.
        
        Args:
            prompt: Input prompt for the model
            
        Returns:
            Generated response text
            
        Raises:
            RuntimeError: If generation fails
        """
        # Check system resources
        if not self._check_resources():
            raise RuntimeError(
                f"Insufficient system resources. Need at least "
                f"{self.config.max_memory_mb}MB RAM and "
                f"{self.config.max_cpu_percent}% CPU available."
            )
        
        try:
            # For now, return a simple response
            # This will be replaced with actual LLM integration
            return "I understand your SSH command. Let me help you with that."
            
        except Exception as e:
            logger.error(f"Failed to generate response: {e}")
            raise RuntimeError(f"Failed to generate response: {e}") from e
    
    def _check_resources(self) -> bool:
        """
        Check if system has sufficient resources.
        
        Returns:
            True if resources are sufficient, False otherwise
        """
        # Check available memory
        memory = psutil.virtual_memory()
        memory_available_mb = memory.available / (1024 * 1024)
        if memory_available_mb < self.config.max_memory_mb:
            logger.warning(
                f"Insufficient memory: {memory_available_mb:.0f}MB available, "
                f"need {self.config.max_memory_mb}MB"
            )
            return False
        
        # Check CPU usage
        cpu_percent = psutil.cpu_percent(interval=1)
        if cpu_percent > (100 - self.config.max_cpu_percent):
            logger.warning(
                f"High CPU usage: {cpu_percent:.0f}% used, "
                f"need {self.config.max_cpu_percent}% available"
            )
            return False
        
        return True 
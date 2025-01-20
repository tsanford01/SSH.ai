"""
Prompt templates for SSH assistance.
"""

from dataclasses import dataclass
from typing import List, Optional, Dict, Any
from enum import Enum

class PromptType(Enum):
    """Types of prompts for different SSH assistance scenarios."""
    COMMAND_EXPLANATION = "command_explanation"
    ERROR_ANALYSIS = "error_analysis"
    SECURITY_CHECK = "security_check"
    PERFORMANCE_OPTIMIZATION = "performance_optimization"
    CONNECTION_ISSUE = "connection_issue"

@dataclass
class Context:
    """Context information for prompt generation."""
    command_history: List[str]
    current_command: Optional[str] = None
    error_message: Optional[str] = None
    system_info: Optional[Dict[str, Any]] = None
    connection_state: Optional[Dict[str, Any]] = None

class PromptTemplate:
    """Template for generating LLM prompts."""
    
    # System prompt to set the AI's role and behavior
    SYSTEM_PROMPT = """You are an expert SSH assistant with deep knowledge of:
1. SSH protocols and security best practices
2. Linux/Unix command line operations
3. Network troubleshooting
4. System administration

Provide clear, concise, and security-conscious advice. Always:
- Prioritize security best practices
- Explain potential risks
- Suggest safer alternatives when applicable
- Use specific examples
- Format command examples in code blocks
"""
    
    # Template for command explanation
    COMMAND_EXPLANATION_TEMPLATE = """Analyze this SSH command:
{command}

Recent command history:
{history}

Explain:
1. What the command does
2. Potential security implications
3. Suggested improvements or alternatives
4. Best practices relevant to this usage"""
    
    # Template for error analysis
    ERROR_ANALYSIS_TEMPLATE = """Analyze this SSH error:
{error_message}

Context:
Command: {command}
Recent history:
{history}

System info:
{system_info}

Provide:
1. Root cause analysis
2. Common solutions
3. Prevention steps
4. Security considerations"""
    
    # Template for security checks
    SECURITY_CHECK_TEMPLATE = """Review this SSH operation for security:
Command: {command}
Connection state: {connection_state}

Recent history:
{history}

Evaluate:
1. Security risks
2. Compliance with best practices
3. Potential vulnerabilities
4. Recommended security improvements"""
    
    # Template for performance optimization
    PERFORMANCE_OPTIMIZATION_TEMPLATE = """Analyze SSH performance:
Current state: {connection_state}
System info: {system_info}

Recent commands:
{history}

Suggest:
1. Performance bottlenecks
2. Optimization opportunities
3. Configuration improvements
4. Best practices for better performance"""
    
    # Template for connection issues
    CONNECTION_ISSUE_TEMPLATE = """Diagnose SSH connection issue:
Error: {error_message}
Connection state: {connection_state}
System info: {system_info}

Recent attempts:
{history}

Provide:
1. Connection diagnosis
2. Troubleshooting steps
3. Common solutions
4. Prevention measures"""
    
    @classmethod
    def generate(cls, prompt_type: PromptType, context: Context) -> str:
        """
        Generate a prompt based on type and context.
        
        Args:
            prompt_type: Type of prompt to generate
            context: Context information for the prompt
            
        Returns:
            Generated prompt string
        """
        # Start with system prompt
        prompt = cls.SYSTEM_PROMPT + "\n\n"
        
        # Format command history
        history = "\n".join(f"- {cmd}" for cmd in context.command_history[-5:]) if context.command_history else "(No command history)"
        
        # Format optional fields
        command = context.current_command or "(No command)"
        error_msg = context.error_message or "(No error)"
        sys_info = str(context.system_info or {}).replace("None", '""')
        conn_state = str(context.connection_state or {}).replace("None", '""')
        
        # Add type-specific template
        if prompt_type == PromptType.COMMAND_EXPLANATION:
            prompt += cls.COMMAND_EXPLANATION_TEMPLATE.format(
                command=command,
                history=history
            )
        
        elif prompt_type == PromptType.ERROR_ANALYSIS:
            prompt += cls.ERROR_ANALYSIS_TEMPLATE.format(
                error_message=error_msg,
                command=command,
                history=history,
                system_info=sys_info
            )
        
        elif prompt_type == PromptType.SECURITY_CHECK:
            prompt += cls.SECURITY_CHECK_TEMPLATE.format(
                command=command,
                connection_state=conn_state,
                history=history
            )
        
        elif prompt_type == PromptType.PERFORMANCE_OPTIMIZATION:
            prompt += cls.PERFORMANCE_OPTIMIZATION_TEMPLATE.format(
                connection_state=conn_state,
                system_info=sys_info,
                history=history
            )
        
        elif prompt_type == PromptType.CONNECTION_ISSUE:
            prompt += cls.CONNECTION_ISSUE_TEMPLATE.format(
                error_message=error_msg,
                connection_state=conn_state,
                system_info=sys_info,
                history=history
            )
        
        return prompt 
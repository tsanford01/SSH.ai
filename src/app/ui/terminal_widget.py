"""
Terminal emulator widget for SSH sessions.
"""

from typing import Optional, Callable
from PyQt6.QtWidgets import QWidget, QVBoxLayout
from PyQt6.QtCore import Qt, pyqtSignal, QProcess
from PyQt6.QtGui import QFont, QPalette, QColor, QTextCursor, QKeyEvent

from ..core.ssh_connection import SSHConnection, SSHCredentials

class TerminalWidget(QWidget):
    """Terminal emulator widget for SSH sessions."""
    
    # Signals
    command_executed = pyqtSignal(str, str)  # command, output
    connection_closed = pyqtSignal()
    
    def __init__(
        self,
        credentials: SSHCredentials,
        parent: Optional[QWidget] = None
    ) -> None:
        """
        Initialize terminal widget.
        
        Args:
            credentials: SSH connection credentials
            parent: Parent widget
        """
        super().__init__(parent)
        
        self.credentials = credentials
        self.ssh = SSHConnection()
        
        # Create layout
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        
        # Create terminal display
        self.display = TerminalDisplay()
        self.display.command_entered.connect(self._handle_command)
        layout.addWidget(self.display)
        
        # Connect to SSH server
        try:
            self.ssh.connect(credentials)
            self.display.append_output(f"Connected to {credentials.hostname}\n")
        except Exception as e:
            self.display.append_output(f"Failed to connect: {e}\n")
    
    def _handle_command(self, command: str) -> None:
        """
        Handle command entered in terminal.
        
        Args:
            command: Command to execute
        """
        try:
            exit_code, stdout, stderr = self.ssh.execute_command(command)
            
            # Emit signal for LLM processing
            self.command_executed.emit(command, stdout + stderr)
            
            # Display output
            if stdout:
                self.display.append_output(stdout)
            if stderr:
                self.display.append_output(stderr, error=True)
            
            # Add new prompt
            self.display.show_prompt()
            
        except Exception as e:
            self.display.append_output(f"Error executing command: {e}\n", error=True)
            self.display.show_prompt()
    
    def close_connection(self) -> None:
        """Close SSH connection."""
        if self.ssh:
            self.ssh.close()
            self.connection_closed.emit()

class TerminalDisplay(QWidget):
    """Custom terminal display widget."""
    
    # Signals
    command_entered = pyqtSignal(str)
    
    def __init__(self, parent: Optional[QWidget] = None) -> None:
        """Initialize terminal display."""
        super().__init__(parent)
        
        # Set up display properties
        self.setFont(QFont("Consolas", 10))
        self.setFocusPolicy(Qt.FocusPolicy.StrongFocus)
        
        # Set up colors
        palette = self.palette()
        palette.setColor(QPalette.ColorRole.Base, QColor("#1E1E1E"))
        palette.setColor(QPalette.ColorRole.Text, QColor("#FFFFFF"))
        self.setPalette(palette)
        
        # Initialize state
        self.command_history: list[str] = []
        self.history_index = 0
        self.current_command = ""
        self.prompt = "$ "
        
        # Show initial prompt
        self.show_prompt()
    
    def show_prompt(self) -> None:
        """Display command prompt."""
        self.append_output(self.prompt)
    
    def append_output(self, text: str, error: bool = False) -> None:
        """
        Append text to terminal display.
        
        Args:
            text: Text to append
            error: Whether this is error output
        """
        color = "#FF6B68" if error else "#FFFFFF"
        self.insertHtml(f'<span style="color: {color}">{text}</span>')
        
        # Scroll to bottom
        cursor = self.textCursor()
        cursor.movePosition(QTextCursor.MoveOperation.End)
        self.setTextCursor(cursor)
    
    def keyPressEvent(self, event: QKeyEvent) -> None:
        """Handle key press events."""
        if event.key() == Qt.Key.Key_Return:
            # Execute command
            command = self.current_command.strip()
            if command:
                self.command_history.append(command)
                self.history_index = len(self.command_history)
                self.command_entered.emit(command)
            self.current_command = ""
            
        elif event.key() == Qt.Key.Key_Backspace:
            # Handle backspace
            if self.current_command:
                self.current_command = self.current_command[:-1]
                cursor = self.textCursor()
                cursor.deletePreviousChar()
                
        elif event.key() == Qt.Key.Key_Up:
            # Navigate command history (up)
            if self.history_index > 0:
                self.history_index -= 1
                self.current_command = self.command_history[self.history_index]
                self._replace_current_line(self.prompt + self.current_command)
                
        elif event.key() == Qt.Key.Key_Down:
            # Navigate command history (down)
            if self.history_index < len(self.command_history) - 1:
                self.history_index += 1
                self.current_command = self.command_history[self.history_index]
                self._replace_current_line(self.prompt + self.current_command)
                
        else:
            # Add character to current command
            char = event.text()
            if char and char.isprintable():
                self.current_command += char
                self.insertPlainText(char)
    
    def _replace_current_line(self, text: str) -> None:
        """Replace current line with new text."""
        cursor = self.textCursor()
        cursor.movePosition(QTextCursor.MoveOperation.StartOfLine)
        cursor.movePosition(
            QTextCursor.MoveOperation.EndOfLine,
            QTextCursor.MoveMode.KeepAnchor
        )
        cursor.removeSelectedText()
        cursor.insertText(text) 
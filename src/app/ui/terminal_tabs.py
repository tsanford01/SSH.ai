"""
Terminal tabs for managing multiple terminal sessions.
"""

from typing import Optional, Dict
from PyQt6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QTabWidget,
    QPushButton,
    QLabel,
    QMessageBox,
)
from PyQt6.QtCore import Qt, pyqtSignal

from .terminal_widget import TerminalWidget
from ..core.session_manager import Session

class TerminalTabs(QWidget):
    """Widget for managing multiple terminal sessions in tabs."""
    
    # Signals
    session_closed = pyqtSignal(Session)  # Emitted when a session is closed
    command_executed = pyqtSignal(str, str)  # Emitted when a command is executed (command, output)
    error_occurred = pyqtSignal(str)  # Emitted when an error occurs
    
    def __init__(self) -> None:
        """Initialize terminal tabs."""
        super().__init__()
        
        # Create layout
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        
        # Create tab widget
        self.tab_widget = QTabWidget()
        self.tab_widget.setTabsClosable(True)
        self.tab_widget.setMovable(True)
        self.tab_widget.setDocumentMode(True)
        self.tab_widget.tabCloseRequested.connect(self._close_tab)
        layout.addWidget(self.tab_widget)
        
        # Store terminal widgets
        self.terminals: Dict[int, TerminalWidget] = {}
        
        # Add welcome tab
        self._add_welcome_tab()
    
    def execute_command(self, command: str) -> None:
        """
        Execute a command in the current terminal.
        
        Args:
            command: Command to execute
        """
        current_index = self.tab_widget.currentIndex()
        if current_index in self.terminals:
            terminal = self.terminals[current_index]
            terminal.execute_command(command)
    
    def activate_session(self, session: Session) -> None:
        """
        Activate a session tab or create a new one if it doesn't exist.
        
        Args:
            session: Session to activate
        """
        # Check if session already has a tab
        for index, terminal in self.terminals.items():
            if terminal.session == session:
                self.tab_widget.setCurrentIndex(index)
                return
        
        # Create new terminal for session
        self.add_terminal(session)
    
    def close_session(self, session: Session) -> None:
        """
        Close a session's tab.
        
        Args:
            session: Session to close
        """
        # Find and close the session's tab
        for index, terminal in self.terminals.items():
            if terminal.session == session:
                self._close_tab(index)
                break
    
    def add_terminal(self, session: Session) -> None:
        """
        Add a new terminal tab for the session.
        
        Args:
            session: SSH session to add
        """
        # Create terminal widget
        terminal = TerminalWidget(session)
        
        # Add tab
        title = (
            f"{session.connection.credentials.username}@"
            f"{session.connection.credentials.hostname}"
        )
        index = self.tab_widget.addTab(terminal, title)
        
        # Store terminal
        self.terminals[index] = terminal
        
        # Switch to new tab
        self.tab_widget.setCurrentIndex(index)
    
    def close_terminal(self, session: Session) -> None:
        """
        Close terminal tab for the session.
        
        Args:
            session: SSH session to close
        """
        # Find tab with session
        for index, terminal in self.terminals.items():
            if terminal.session == session:
                self._close_tab(index)
                break
    
    def _add_welcome_tab(self) -> None:
        """Add welcome tab with instructions."""
        # Create welcome widget
        welcome = QWidget()
        welcome_layout = QVBoxLayout(welcome)
        
        # Add welcome message
        message = QLabel(
            "Welcome to SSH Copilot!\n\n"
            "To get started, click 'New Connection' in the sidebar\n"
            "or use the File menu to create a new SSH connection."
        )
        message.setAlignment(Qt.AlignmentFlag.AlignCenter)
        welcome_layout.addWidget(message)
        
        # Add tab
        self.tab_widget.addTab(welcome, "Welcome")
    
    def _close_tab(self, index: int) -> None:
        """
        Close tab at index.
        
        Args:
            index: Tab index to close
        """
        # Get terminal
        terminal = self.terminals.get(index)
        if not terminal:
            # Not a terminal tab (e.g. welcome tab)
            self.tab_widget.removeTab(index)
            return
        
        # Confirm close if terminal is connected
        if terminal.session.connection.is_connected():
            response = QMessageBox.question(
                self,
                "Close Terminal",
                "Are you sure you want to close this terminal?",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                QMessageBox.StandardButton.No
            )
            if response == QMessageBox.StandardButton.No:
                return
        
        # Close terminal
        terminal.close()
        
        # Remove tab
        self.tab_widget.removeTab(index)
        del self.terminals[index]
        
        # Emit signal
        self.session_closed.emit(terminal.session)
        
        # Show welcome tab if no terminals left
        if not self.terminals:
            self._add_welcome_tab() 
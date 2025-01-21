"""
Main window for SSH Copilot application.
"""

from typing import Optional
from pathlib import Path
from PyQt6.QtWidgets import (
    QMainWindow,
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QSplitter,
    QStatusBar,
    QMenuBar,
    QMenu,
    QMessageBox,
)
from PyQt6.QtCore import Qt, pyqtSlot

from .ui.connection_sidebar import ConnectionSidebar
from .ui.terminal_tabs import TerminalTabs
from .ui.suggestion_panel import SuggestionPanel
from .core.session_manager import SessionManager
from .core.llm_manager import LLMManager
from .ui.settings_dialog import SettingsDialog

class MainWindow(QMainWindow):
    """Main application window."""
    
    def __init__(self) -> None:
        """Initialize main window."""
        super().__init__()
        
        # Initialize managers
        self.llm = LLMManager()
        self.session_manager = SessionManager()
        
        # Set up UI
        self.setWindowTitle("SSH.ai")
        self.resize(1200, 800)
        
        # Create main layout
        layout = QVBoxLayout()
        
        # Create horizontal layout for main content
        content_layout = QHBoxLayout()
        
        # Create connection sidebar
        self.connection_sidebar = ConnectionSidebar()
        content_layout.addWidget(self.connection_sidebar)
        
        # Create terminal tabs
        self.terminal_tabs = TerminalTabs()
        content_layout.addWidget(self.terminal_tabs)
        
        # Create suggestion panel
        self.suggestion_panel = SuggestionPanel(self.llm, self)
        content_layout.addWidget(self.suggestion_panel)
        
        # Add content layout to main layout
        layout.addLayout(content_layout)
        
        # Create status bar
        self.status_bar = QStatusBar()
        layout.addWidget(self.status_bar)
        
        # Set central widget
        central_widget = QWidget()
        central_widget.setLayout(layout)
        self.setCentralWidget(central_widget)
        
        # Create menu bar
        self._create_menus()
        
        # Connect signals
        self._connect_signals()
    
    def _create_menus(self) -> None:
        """Create menu bar and menus."""
        menubar = self.menuBar()
        
        # File menu
        file_menu = menubar.addMenu("&File")
        
        new_connection = file_menu.addAction("&New Connection...")
        new_connection.triggered.connect(self._new_connection)
        
        file_menu.addSeparator()
        
        settings = file_menu.addAction("&Settings...")
        settings.triggered.connect(self._show_settings)
        
        file_menu.addSeparator()
        
        exit_action = file_menu.addAction("E&xit")
        exit_action.triggered.connect(self.close)
        
        # View menu
        view_menu = menubar.addMenu("&View")
        
        toggle_sidebar = view_menu.addAction("Toggle &Sidebar")
        toggle_sidebar.triggered.connect(
            lambda: self.connection_sidebar.setVisible(
                not self.connection_sidebar.isVisible()
            )
        )
        
        toggle_suggestions = view_menu.addAction("Toggle &Suggestions")
        toggle_suggestions.triggered.connect(
            lambda: self.suggestion_panel.setVisible(
                not self.suggestion_panel.isVisible()
            )
        )
        
        # Help menu
        help_menu = menubar.addMenu("&Help")
        
        about = help_menu.addAction("&About")
        about.triggered.connect(self._show_about)
    
    def _connect_signals(self) -> None:
        """Connect UI signals to slots."""
        # Connect terminal signals to suggestion panel
        self.terminal_tabs.command_executed.connect(
            self.suggestion_panel.analyze_command
        )
        self.terminal_tabs.error_occurred.connect(
            self.suggestion_panel.analyze_error
        )
        
        # Connect suggestion panel signals to terminal
        self.suggestion_panel.execute_command.connect(
            self.terminal_tabs.execute_command
        )
        
        # Connect connection sidebar signals
        self.connection_sidebar.session_selected.connect(
            self.terminal_tabs.activate_session
        )
        self.connection_sidebar.session_closed.connect(
            self.terminal_tabs.close_session
        )
    
    @pyqtSlot()
    def _new_connection(self) -> None:
        """Show new connection dialog."""
        # TODO: Implement connection dialog
        pass
    
    @pyqtSlot()
    def _show_settings(self) -> None:
        """Show settings dialog."""
        dialog = SettingsDialog(self)
        if dialog.exec():
            # TODO: Apply settings
            pass
    
    @pyqtSlot()
    def _show_about(self) -> None:
        """Show about dialog."""
        QMessageBox.about(
            self,
            "About SSH Copilot",
            "SSH Copilot\n\n"
            "A smart SSH client with LLM-powered assistance.\n\n"
            "Version 1.0.0"
        )
    
    def closeEvent(self, event) -> None:
        """Handle window close event."""
        # End all active sessions
        for session in self.session_manager.list_sessions():
            self.session_manager.end_session(
                session.connection.credentials.hostname,
                session.connection.credentials.username
            )
        
        super().closeEvent(event) 
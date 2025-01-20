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
    
    def __init__(self, session_dir: Optional[Path] = None) -> None:
        """
        Initialize main window.
        
        Args:
            session_dir: Directory for session storage
        """
        super().__init__()
        
        # Initialize managers
        self.llm = LLMManager()
        self.session_manager = SessionManager(self.llm, session_dir)
        
        self.setWindowTitle("SSH Copilot")
        self.setMinimumSize(1200, 800)
        
        # Create central widget and layout
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        layout = QHBoxLayout(central_widget)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        
        # Create main splitter
        self.main_splitter = QSplitter(Qt.Orientation.Horizontal)
        layout.addWidget(self.main_splitter)
        
        # Add connection sidebar
        self.connection_sidebar = ConnectionSidebar(self.session_manager)
        self.main_splitter.addWidget(self.connection_sidebar)
        
        # Create terminal and suggestion splitter
        self.terminal_splitter = QSplitter(Qt.Orientation.Vertical)
        self.main_splitter.addWidget(self.terminal_splitter)
        
        # Add terminal tabs
        self.terminal_tabs = TerminalTabs()
        self.terminal_splitter.addWidget(self.terminal_tabs)
        
        # Add suggestion panel
        self.suggestion_panel = SuggestionPanel(self.llm)
        self.terminal_splitter.addWidget(self.suggestion_panel)
        
        # Set splitter sizes
        self.main_splitter.setSizes([200, 1000])  # Sidebar width
        self.terminal_splitter.setSizes([600, 200])  # Terminal/suggestion ratio
        
        # Create status bar
        self.status_bar = QStatusBar()
        self.setStatusBar(self.status_bar)
        self.status_bar.showMessage("Ready")
        
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
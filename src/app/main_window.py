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
from PyQt6.QtGui import QFont
import asyncio
import logging

from .ui.connection_sidebar import ConnectionSidebar
from .ui.terminal_tabs import TerminalTabs
from .ui.suggestion_panel import SuggestionPanel
from .core.session_manager import SessionManager
from .core.llm_manager import LLMManager
from .ui.settings_dialog import SettingsDialog

class MainWindow(QMainWindow):
    """Main application window."""
    
    def __init__(self, llm_manager: Optional[LLMManager] = None) -> None:
        """
        Initialize main window.
        
        Args:
            llm_manager: Optional LLM manager instance. If None, creates a new one.
        """
        super().__init__()
        
        logging.info("Initializing MainWindow...")
        
        try:
            # Initialize managers
            self.llm = llm_manager or LLMManager()
            logging.info("Using provided LLMManager" if llm_manager else "Created new LLMManager")
            
            self.session_manager = SessionManager(self.llm)
            logging.info("SessionManager initialized")
            
            # Set up UI
            self.setWindowTitle("SSH.ai")
            self.resize(1200, 800)
            
            # Create central widget
            central_widget = QWidget()
            self.setCentralWidget(central_widget)
            
            # Create main layout
            main_layout = QVBoxLayout(central_widget)
            main_layout.setContentsMargins(0, 0, 0, 0)
            main_layout.setSpacing(0)
            
            # Create horizontal splitter for main content
            content_splitter = QSplitter(Qt.Orientation.Horizontal)
            
            try:
                # Create connection sidebar
                self.connection_sidebar = ConnectionSidebar(self.session_manager)
                content_splitter.addWidget(self.connection_sidebar)
                logging.info("ConnectionSidebar initialized")
                
                # Create terminal tabs
                self.terminal_tabs = TerminalTabs()
                content_splitter.addWidget(self.terminal_tabs)
                logging.info("TerminalTabs initialized")
                
                # Create suggestion panel
                self.suggestion_panel = SuggestionPanel(self.llm, self)
                content_splitter.addWidget(self.suggestion_panel)
                logging.info("SuggestionPanel initialized")
            except Exception as e:
                logging.error(f"Failed to initialize UI components: {e}")
                raise
            
            # Set initial sizes for splitter
            content_splitter.setSizes([250, 700, 250])  # Sidebar, Terminal, Suggestions
            
            # Add splitter to main layout
            main_layout.addWidget(content_splitter)
            
            # Create status bar
            self.status_bar = QStatusBar()
            self.setStatusBar(self.status_bar)
            self.status_bar.showMessage("Ready")
            
            # Create menu bar and connect signals
            self._create_menus()
            self._connect_signals()
            
            self.raise_()
            self.activateWindow()
            logging.info("MainWindow initialized successfully")
            
        except Exception as e:
            logging.error(f"Failed to initialize MainWindow: {e}")
            raise
    
    def _create_menus(self) -> None:
        """Create menu bar and menus."""
        logging.info("Creating menu bar...")
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
        
        logging.info("Menu bar created.")
    
    def _connect_signals(self) -> None:
        """Connect UI signals to slots."""
        logging.info("Connecting UI signals...")
        # Connect terminal signals to suggestion panel
        self.terminal_tabs.command_executed.connect(
            lambda cmd, output: asyncio.create_task(
                self.suggestion_panel.analyze_command(cmd, output)
            )
        )
        self.terminal_tabs.error_occurred.connect(
            lambda error: asyncio.create_task(
                self.suggestion_panel.analyze_error(error)
            )
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
        
        logging.info("UI signals connected.")
    
    @pyqtSlot()
    def _new_connection(self) -> None:
        """Show new connection dialog."""
        from .ui.connection_dialog import ConnectionDialog
        
        try:
            dialog = ConnectionDialog(self)
            if dialog.exec():
                credentials = dialog.get_credentials()
                if credentials:
                    # Create new session
                    session = self.session_manager.create_session(credentials)
                    if session:
                        self.connection_sidebar.add_session(session)
                        self.terminal_tabs.activate_session(session)
                        self.status_bar.showMessage(f"Connected to {credentials.hostname}")
                    else:
                        QMessageBox.critical(
                            self,
                            "Connection Error",
                            f"Failed to create session for {credentials.hostname}"
                        )
        except Exception as e:
            logging.error(f"Error creating new connection: {e}")
            QMessageBox.critical(
                self,
                "Connection Error",
                f"Failed to create connection: {e}"
            )
    
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
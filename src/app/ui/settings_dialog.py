"""
Settings dialog for configuring LLM and application behavior.
"""

from typing import Optional, Dict, Any
from pathlib import Path
from PyQt6.QtWidgets import (
    QDialog,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QSpinBox,
    QPushButton,
    QTabWidget,
    QWidget,
    QComboBox,
    QCheckBox,
    QFileDialog,
    QFormLayout,
    QDialogButtonBox,
    QGroupBox
)
from PyQt6.QtCore import Qt, QSettings
from PyQt6.QtGui import QFont

from ..core.llm_manager import LLMConfig

class SettingsDialog(QDialog):
    """Dialog for configuring application settings."""
    
    def __init__(self, parent: Optional[QWidget] = None) -> None:
        """Initialize settings dialog."""
        super().__init__(parent)
        
        self.setWindowTitle("Settings")
        self.setModal(True)
        self.setMinimumWidth(500)
        
        # Load current settings
        self._settings = QSettings("SSH.ai", "SSH Assistant")
        
        # Initialize UI
        self._init_ui()
        self._load_settings()
    
    def _init_ui(self) -> None:
        """Initialize the UI components."""
        layout = QVBoxLayout(self)
        
        # Create tab widget
        self.tab_widget = QTabWidget()
        
        # LLM Settings tab
        self.llm_tab = self._create_llm_tab()
        self.tab_widget.addTab(self.llm_tab, "LLM")
        
        # SSH Settings tab
        self.ssh_tab = self._create_ssh_tab()
        self.tab_widget.addTab(self.ssh_tab, "SSH")
        
        # UI Settings tab
        self.ui_tab = self._create_ui_tab()
        self.tab_widget.addTab(self.ui_tab, "UI")
        
        # Add tab widget to layout
        layout.addWidget(self.tab_widget)
        
        # Add dialog buttons
        self.button_box = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok |
            QDialogButtonBox.StandardButton.Cancel |
            QDialogButtonBox.StandardButton.Apply
        )
        
        # Connect button signals
        apply_button = self.button_box.button(QDialogButtonBox.StandardButton.Apply)
        apply_button.clicked.connect(self._apply_settings)
        
        ok_button = self.button_box.button(QDialogButtonBox.StandardButton.Ok)
        ok_button.clicked.connect(self.accept)
        
        cancel_button = self.button_box.button(QDialogButtonBox.StandardButton.Cancel)
        cancel_button.clicked.connect(self.reject)
        
        layout.addWidget(self.button_box)
    
    def _create_llm_tab(self) -> QWidget:
        """Create the LLM settings tab."""
        tab = QWidget()
        layout = QVBoxLayout(tab)
        
        # Model settings group
        model_group = QGroupBox("Model Settings")
        model_layout = QFormLayout(model_group)
        
        self.model_combo = QComboBox()
        self.model_combo.addItems([
            "TinyLlama-1.1B-Chat",
            "Llama-2-7b-chat",
            "Mistral-7B-v0.1",
            "Custom Model"
        ])
        model_layout.addRow("Model:", self.model_combo)
        
        self.model_path_edit = QPushButton("Browse...")
        self.model_path_edit.clicked.connect(self._browse_model)
        model_layout.addRow("Custom Model Path:", self.model_path_edit)
        
        # Resource settings group
        resource_group = QGroupBox("Resource Settings")
        resource_layout = QFormLayout(resource_group)
        
        self.max_memory_spin = QSpinBox()
        self.max_memory_spin.setRange(512, 32768)
        self.max_memory_spin.setSingleStep(512)
        self.max_memory_spin.setSuffix(" MB")
        resource_layout.addRow("Max Memory:", self.max_memory_spin)
        
        self.max_cpu_spin = QSpinBox()
        self.max_cpu_spin.setRange(10, 100)
        self.max_cpu_spin.setSuffix("%")
        resource_layout.addRow("Max CPU Usage:", self.max_cpu_spin)
        
        # Generation settings group
        gen_group = QGroupBox("Generation Settings")
        gen_layout = QFormLayout(gen_group)
        
        self.context_length_spin = QSpinBox()
        self.context_length_spin.setRange(256, 4096)
        self.context_length_spin.setSingleStep(256)
        gen_layout.addRow("Context Length:", self.context_length_spin)
        
        self.temperature_spin = QSpinBox()
        self.temperature_spin.setRange(1, 100)
        self.temperature_spin.setValue(70)  # 0.7
        gen_layout.addRow("Temperature (÷100):", self.temperature_spin)
        
        # Add groups to layout
        layout.addWidget(model_group)
        layout.addWidget(resource_group)
        layout.addWidget(gen_group)
        layout.addStretch()
        
        return tab
    
    def _create_ssh_tab(self) -> QWidget:
        """Create the SSH settings tab."""
        tab = QWidget()
        layout = QVBoxLayout(tab)
        
        # Connection settings group
        conn_group = QGroupBox("Connection Settings")
        conn_layout = QFormLayout(conn_group)
        
        self.timeout_spin = QSpinBox()
        self.timeout_spin.setRange(5, 300)
        self.timeout_spin.setSuffix(" seconds")
        conn_layout.addRow("Connection Timeout:", self.timeout_spin)
        
        self.keepalive_check = QCheckBox("Enable Keep-Alive")
        conn_layout.addRow("Keep-Alive:", self.keepalive_check)
        
        self.keepalive_interval_spin = QSpinBox()
        self.keepalive_interval_spin.setRange(10, 300)
        self.keepalive_interval_spin.setSuffix(" seconds")
        conn_layout.addRow("Keep-Alive Interval:", self.keepalive_interval_spin)
        
        self.compression_check = QCheckBox("Enable Compression")
        conn_layout.addRow("Compression:", self.compression_check)
        
        # Add groups to layout
        layout.addWidget(conn_group)
        layout.addStretch()
        
        return tab
    
    def _create_ui_tab(self) -> QWidget:
        """Create the UI settings tab."""
        tab = QWidget()
        layout = QVBoxLayout(tab)
        
        # Appearance group
        appearance_group = QGroupBox("Appearance")
        appearance_layout = QFormLayout(appearance_group)
        
        self.theme_combo = QComboBox()
        self.theme_combo.addItems(["Light", "Dark", "System"])
        appearance_layout.addRow("Theme:", self.theme_combo)
        
        self.font_family_combo = QComboBox()
        self.font_family_combo.addItems([
            "Segoe UI",
            "Consolas",
            "Courier New",
            "Arial",
            "System Default"
        ])
        appearance_layout.addRow("Font Family:", self.font_family_combo)
        
        self.font_size_spin = QSpinBox()
        self.font_size_spin.setRange(8, 24)
        appearance_layout.addRow("Font Size:", self.font_size_spin)
        
        # Add groups to layout
        layout.addWidget(appearance_group)
        layout.addStretch()
        
        return tab
    
    def _browse_model(self) -> None:
        """Open file dialog to select custom model."""
        path, _ = QFileDialog.getOpenFileName(
            self,
            "Select Model File",
            str(Path.home()),
            "Model Files (*.bin *.pt *.pth);;All Files (*.*)"
        )
        if path:
            self.model_path_edit.setToolTip(path)
    
    def _load_settings(self) -> None:
        """Load current settings into UI."""
        # LLM settings
        self.model_combo.setCurrentText(
            self._settings.value("llm/model", "TinyLlama-1.1B-Chat")
        )
        self.model_path_edit.setToolTip(
            self._settings.value("llm/model_path", "")
        )
        self.max_memory_spin.setValue(
            self._settings.value("llm/max_memory_mb", 2048, int)
        )
        self.max_cpu_spin.setValue(
            self._settings.value("llm/max_cpu_percent", 50, int)
        )
        self.context_length_spin.setValue(
            self._settings.value("llm/context_length", 1024, int)
        )
        self.temperature_spin.setValue(
            int(float(self._settings.value("llm/temperature", 0.7)) * 100)
        )
        
        # SSH settings
        self.timeout_spin.setValue(
            self._settings.value("ssh/timeout", 30, int)
        )
        self.keepalive_check.setChecked(
            self._settings.value("ssh/keepalive", True, bool)
        )
        self.keepalive_interval_spin.setValue(
            self._settings.value("ssh/keepalive_interval", 60, int)
        )
        self.compression_check.setChecked(
            self._settings.value("ssh/compression", True, bool)
        )
        
        # UI settings
        self.theme_combo.setCurrentText(
            self._settings.value("ui/theme", "System")
        )
        self.font_family_combo.setCurrentText(
            self._settings.value("ui/font_family", "Segoe UI")
        )
        self.font_size_spin.setValue(
            self._settings.value("ui/font_size", 10, int)
        )
    
    def _apply_settings(self) -> None:
        """Apply current settings."""
        # LLM settings
        self._settings.setValue("llm/model", self.model_combo.currentText())
        self._settings.setValue("llm/model_path", self.model_path_edit.toolTip())
        self._settings.setValue("llm/max_memory_mb", self.max_memory_spin.value())
        self._settings.setValue("llm/max_cpu_percent", self.max_cpu_spin.value())
        self._settings.setValue("llm/context_length", self.context_length_spin.value())
        self._settings.setValue("llm/temperature", self.temperature_spin.value() / 100)
        
        # SSH settings
        self._settings.setValue("ssh/timeout", self.timeout_spin.value())
        self._settings.setValue("ssh/keepalive", self.keepalive_check.isChecked())
        self._settings.setValue("ssh/keepalive_interval", self.keepalive_interval_spin.value())
        self._settings.setValue("ssh/compression", self.compression_check.isChecked())
        
        # UI settings
        self._settings.setValue("ui/theme", self.theme_combo.currentText())
        self._settings.setValue("ui/font_family", self.font_family_combo.currentText())
        self._settings.setValue("ui/font_size", self.font_size_spin.value())
        
        # Sync settings to disk
        self._settings.sync()
    
    def get_llm_config(self) -> LLMConfig:
        """
        Get LLM configuration from current settings.
        
        Returns:
            LLM configuration object
        """
        return LLMConfig(
            max_memory_mb=self.max_memory_spin.value(),
            max_cpu_percent=self.max_cpu_spin.value(),
            context_length=self.context_length_spin.value(),
            temperature=self.temperature_spin.value() / 100
        )
    
    def accept(self) -> None:
        """Handle dialog acceptance."""
        self._apply_settings()
        super().accept() 
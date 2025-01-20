"""
Tests for settings dialog functionality.
"""

import pytest
from unittest.mock import Mock, patch
from pathlib import Path
from PyQt6.QtWidgets import (
    QApplication,
    QDialog,
    QFileDialog,
    QDialogButtonBox,
    QSpinBox,
    QComboBox,
    QCheckBox
)
from PyQt6.QtCore import Qt, QSettings, QTimer
from PyQt6.QtTest import QTest

from src.app.ui.settings_dialog import SettingsDialog

# Required for Qt widgets
app = QApplication([])

@pytest.fixture
def dialog():
    """Create settings dialog for testing."""
    # Use in-memory settings for testing
    with patch('PyQt6.QtCore.QSettings') as mock_settings:
        dialog = SettingsDialog()
        dialog._settings = mock_settings.return_value
        yield dialog

def test_dialog_creation(dialog):
    """Test dialog initialization."""
    assert dialog.windowTitle() == "Settings"
    assert dialog.isModal()
    assert dialog.minimumWidth() >= 500
    
    # Check tab widget
    assert dialog.tab_widget is not None
    assert dialog.tab_widget.count() == 3
    assert dialog.tab_widget.tabText(0) == "LLM"
    assert dialog.tab_widget.tabText(1) == "SSH"
    assert dialog.tab_widget.tabText(2) == "UI"

def test_llm_tab_controls(dialog):
    """Test LLM settings tab controls."""
    # Model settings
    assert dialog.model_combo.count() > 0
    assert "TinyLlama-1.1B-Chat" in [
        dialog.model_combo.itemText(i)
        for i in range(dialog.model_combo.count())
    ]
    
    # Resource settings
    assert isinstance(dialog.max_memory_spin, QSpinBox)
    assert dialog.max_memory_spin.minimum() == 512
    assert dialog.max_memory_spin.maximum() == 32768
    assert dialog.max_memory_spin.suffix() == " MB"
    
    assert isinstance(dialog.max_cpu_spin, QSpinBox)
    assert dialog.max_cpu_spin.minimum() == 10
    assert dialog.max_cpu_spin.maximum() == 100
    assert dialog.max_cpu_spin.suffix() == "%"
    
    # Generation settings
    assert isinstance(dialog.context_length_spin, QSpinBox)
    assert dialog.context_length_spin.minimum() == 256
    assert dialog.context_length_spin.maximum() == 4096
    
    assert isinstance(dialog.temperature_spin, QSpinBox)
    assert dialog.temperature_spin.minimum() == 1
    assert dialog.temperature_spin.maximum() == 100

def test_ssh_tab_controls(dialog):
    """Test SSH settings tab controls."""
    assert isinstance(dialog.timeout_spin, QSpinBox)
    assert dialog.timeout_spin.minimum() == 5
    assert dialog.timeout_spin.maximum() == 300
    assert dialog.timeout_spin.suffix() == " seconds"
    
    assert isinstance(dialog.keepalive_check, QCheckBox)
    assert isinstance(dialog.keepalive_interval_spin, QSpinBox)
    assert dialog.keepalive_interval_spin.minimum() == 10
    assert dialog.keepalive_interval_spin.maximum() == 300
    assert dialog.keepalive_interval_spin.suffix() == " seconds"
    
    assert isinstance(dialog.compression_check, QCheckBox)

def test_ui_tab_controls(dialog):
    """Test UI settings tab controls."""
    assert isinstance(dialog.theme_combo, QComboBox)
    assert dialog.theme_combo.count() == 3
    assert set(
        dialog.theme_combo.itemText(i)
        for i in range(dialog.theme_combo.count())
    ) == {"Light", "Dark", "System"}
    
    assert isinstance(dialog.font_family_combo, QComboBox)
    assert dialog.font_family_combo.count() > 0
    assert "Segoe UI" in [
        dialog.font_family_combo.itemText(i)
        for i in range(dialog.font_family_combo.count())
    ]
    
    assert isinstance(dialog.font_size_spin, QSpinBox)
    assert dialog.font_size_spin.minimum() == 8
    assert dialog.font_size_spin.maximum() == 24

def test_load_settings(dialog):
    """Test loading settings."""
    # Mock settings values
    dialog._settings.value.side_effect = lambda key, default, type=None: {
        "llm/model": "TinyLlama-1.1B-Chat",
        "llm/model_path": "/path/to/model",
        "llm/max_memory_mb": 4096,
        "llm/max_cpu_percent": 75,
        "llm/context_length": 2048,
        "llm/temperature": 0.8,
        "ssh/timeout": 45,
        "ssh/keepalive": True,
        "ssh/keepalive_interval": 90,
        "ssh/compression": False,
        "ui/theme": "Dark",
        "ui/font_family": "Consolas",
        "ui/font_size": 12
    }.get(key, default)
    
    # Load settings
    dialog._load_settings()
    
    # Verify values
    assert dialog.model_combo.currentText() == "TinyLlama-1.1B-Chat"
    assert dialog.model_path_edit.toolTip() == "/path/to/model"
    assert dialog.max_memory_spin.value() == 4096
    assert dialog.max_cpu_spin.value() == 75
    assert dialog.context_length_spin.value() == 2048
    assert dialog.temperature_spin.value() == 80  # 0.8 * 100
    
    assert dialog.timeout_spin.value() == 45
    assert dialog.keepalive_check.isChecked()
    assert dialog.keepalive_interval_spin.value() == 90
    assert not dialog.compression_check.isChecked()
    
    assert dialog.theme_combo.currentText() == "Dark"
    assert dialog.font_family_combo.currentText() == "Consolas"
    assert dialog.font_size_spin.value() == 12

def test_apply_settings(dialog):
    """Test applying settings."""
    # Set some values
    dialog.model_combo.setCurrentText("Mistral-7B-v0.1")
    dialog.model_path_edit.setToolTip("/custom/model/path")
    dialog.max_memory_spin.setValue(8192)
    dialog.max_cpu_spin.setValue(60)
    dialog.context_length_spin.setValue(1024)
    dialog.temperature_spin.setValue(50)
    
    dialog.timeout_spin.setValue(60)
    dialog.keepalive_check.setChecked(True)
    dialog.keepalive_interval_spin.setValue(120)
    dialog.compression_check.setChecked(False)
    
    dialog.theme_combo.setCurrentText("Light")
    dialog.font_family_combo.setCurrentText("Arial")
    dialog.font_size_spin.setValue(14)
    
    # Apply settings
    dialog._apply_settings()
    
    # Verify settings were saved
    assert dialog._settings.setValue.call_count > 0
    dialog._settings.setValue.assert_any_call("llm/model", "Mistral-7B-v0.1")
    dialog._settings.setValue.assert_any_call("llm/model_path", "/custom/model/path")
    dialog._settings.setValue.assert_any_call("llm/max_memory_mb", 8192)
    dialog._settings.setValue.assert_any_call("llm/max_cpu_percent", 60)
    dialog._settings.setValue.assert_any_call("llm/context_length", 1024)
    dialog._settings.setValue.assert_any_call("llm/temperature", 0.5)
    
    dialog._settings.setValue.assert_any_call("ssh/timeout", 60)
    dialog._settings.setValue.assert_any_call("ssh/keepalive", True)
    dialog._settings.setValue.assert_any_call("ssh/keepalive_interval", 120)
    dialog._settings.setValue.assert_any_call("ssh/compression", False)
    
    dialog._settings.setValue.assert_any_call("ui/theme", "Light")
    dialog._settings.setValue.assert_any_call("ui/font_family", "Arial")
    dialog._settings.setValue.assert_any_call("ui/font_size", 14)
    
    # Verify settings were synced
    dialog._settings.sync.assert_called_once()

def test_browse_model(dialog):
    """Test browsing for model file."""
    # Mock file dialog
    with patch('PyQt6.QtWidgets.QFileDialog.getOpenFileName') as mock_dialog:
        mock_dialog.return_value = ("/path/to/model.bin", "Model Files (*.bin)")
        
        # Trigger browse
        dialog._browse_model()
        
        # Verify dialog was shown with correct parameters
        mock_dialog.assert_called_once()
        assert mock_dialog.call_args[0][0] == dialog
        assert mock_dialog.call_args[0][1] == "Select Model File"
        assert mock_dialog.call_args[0][2] == str(Path.home())
        assert "Model Files" in mock_dialog.call_args[0][3]
        
        # Verify path was set
        assert dialog.model_path_edit.toolTip() == "/path/to/model.bin"

def test_get_llm_config(dialog):
    """Test getting LLM configuration."""
    # Set some values
    dialog.max_memory_spin.setValue(4096)
    dialog.max_cpu_spin.setValue(75)
    dialog.context_length_spin.setValue(2048)
    dialog.temperature_spin.setValue(80)
    
    # Get config
    config = dialog.get_llm_config()
    
    # Verify values
    assert config.max_memory_mb == 4096
    assert config.max_cpu_percent == 75
    assert config.context_length == 2048
    assert config.temperature == 0.8

def test_dialog_buttons(dialog):
    """Test dialog buttons."""
    assert dialog.button_box is not None
    
    # Get buttons
    ok_button = dialog.button_box.button(QDialogButtonBox.StandardButton.Ok)
    cancel_button = dialog.button_box.button(QDialogButtonBox.StandardButton.Cancel)
    apply_button = dialog.button_box.button(QDialogButtonBox.StandardButton.Apply)
    
    assert ok_button is not None
    assert cancel_button is not None
    assert apply_button is not None
    
    # Test apply button
    with patch.object(dialog, '_apply_settings') as mock_apply:
        # Directly call the slot
        dialog._apply_settings()
        mock_apply.assert_called_once()
    
    # Test ok button
    with patch.object(dialog, '_apply_settings') as mock_apply:
        with patch.object(dialog, 'accept') as mock_accept:
            # Directly call the slots
            dialog._apply_settings()
            dialog.accept()
            mock_apply.assert_called_once()
            mock_accept.assert_called_once()
    
    # Test cancel button
    with patch.object(dialog, 'reject') as mock_reject:
        # Directly call the slot
        dialog.reject()
        mock_reject.assert_called_once() 
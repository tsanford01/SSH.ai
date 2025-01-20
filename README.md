# SecureSSH+Copilot

A privacy-centered SSH client with local LLM integration for Windows, featuring real-time command suggestions and secure session management.

## Features

- **Secure SSH Management**
  - Encrypted credential storage using AES-256
  - Multi-session support with tabbed/split terminal views
  - Automatic reconnection handling with retry logic
  - Session state monitoring and metrics

- **Local LLM Integration**
  - Privacy-first design with strictly local model execution
  - Real-time command suggestions and assistance
  - Performance optimization with CPU/memory limits
  - Contextual terminal output analysis
  - Command safety validation

- **Session Management**
  - Automated session logging with AES-256 encryption
  - Command history tracking with performance metrics
  - Error rate monitoring and diagnostics
  - Sanitized terminal output for sensitive data
  - Exportable session summaries

- **Security & Privacy**
  - Local-only LLM processing
  - Encrypted storage for all sensitive data
  - Command execution review system
  - Resource usage monitoring
  - Automatic terminal output sanitization

## Development Setup

1. Requirements:
   - Python 3.11 or higher
   - Windows 10 or higher
   - Minimum 2GB RAM for LLM operations
   - Virtual environment for isolation

2. Installation:
   ```powershell
   # Create and activate virtual environment
   python -m venv venv
   .\venv\Scripts\activate

   # Install dependencies
   pip install -r requirements.txt

   # Verify installation
   python -m pytest tests/
   ```

3. Configuration:
   - Copy `config/example.env` to `.env`
   - Set required environment variables
   - Configure LLM model settings in `config/llm_config.json`

4. Running the application:
   ```powershell
   python src/main.py
   ```

## Project Structure

```
SecureSSH+Copilot/
├── src/
│   ├── app/
│   │   ├── core/          # Core business logic
│   │   │   ├── credential_store.py
│   │   │   ├── llm_manager.py
│   │   │   ├── session_manager.py
│   │   │   ├── ssh_connection.py
│   │   │   └── terminal_sanitizer.py
│   │   ├── ui/           # PyQt6 UI components
│   │   │   ├── main_window.py
│   │   │   ├── terminal_widget.py
│   │   │   ├── llm_panel.py
│   │   │   └── status_bar.py
│   │   └── utils/        # Helper utilities
│   └── main.py          # Application entry point
├── tests/               # Test files
├── docs/               # Documentation
├── config/            # Configuration files
└── requirements.txt   # Python dependencies
```

## Key Components

- **Terminal Emulator**: Full-featured SSH terminal with session management
- **LLM Panel**: Real-time suggestions and command assistance
- **Status Bar**: System resource and connection monitoring
- **Settings Dialog**: Configuration for LLM, SSH, and UI preferences

## Security Features

- AES-256 encryption for:
  - Stored credentials
  - Session logs
  - Configuration data
- Local LLM processing with:
  - Resource usage limits
  - Command safety analysis
  - No external API calls
- Terminal output sanitization for:
  - Passwords and tokens
  - SSH keys
  - Authorization headers

## Development Guidelines

1. Code Standards:
   - Follow Python PEP-8 style guide
   - Include type annotations for all functions
   - Add docstrings for public interfaces
   - Write unit tests for new features

2. Security Requirements:
   - No external LLM API calls
   - Use AES-256 for sensitive data
   - Implement command review system
   - Sanitize all terminal output

3. Testing:
   ```powershell
   # Run all tests
   pytest tests/

   # Run with coverage
   pytest --cov=src tests/
   ```

## Session Management

The application tracks various metrics for each session:
- Command execution history
- Error rates and diagnostics
- LLM interaction success rates
- Performance measurements
- Resource usage statistics

## Configuration Options

1. LLM Settings:
   - Model selection
   - Memory usage limits
   - CPU usage limits
   - Temperature and context length

2. SSH Settings:
   - Connection timeouts
   - Keepalive intervals
   - Compression options
   - Key management

3. UI Preferences:
   - Theme selection
   - Font customization
   - Panel layouts
   - Terminal colors

## License

MIT License

## Contributing

1. Fork the repository
2. Create a feature branch
3. Follow coding standards
4. Add tests for new features
5. Submit a pull request

## Support

- Check documentation in `/docs`
- Run tests to verify setup
- Review logs for diagnostics 
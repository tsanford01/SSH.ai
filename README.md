# SecureSSH+Copilot

A privacy-centered SSH client with local LLM integration for Windows.

## Features

- Secure SSH connection management with encrypted credential storage
- Local LLM-powered command suggestions and assistance
- Multi-session support with tabbed interface
- Automated session logging and documentation
- Privacy-first design with no external API calls

## Development Setup

1. Requirements:
   - Python 3.11 or higher
   - Windows 10 or higher

2. Installation:
   ```powershell
   # Create and activate virtual environment
   python -m venv venv
   .\venv\Scripts\activate

   # Install dependencies
   pip install -r requirements.txt
   ```

3. Running the application:
   ```powershell
   python src/main.py
   ```

## Project Structure

```
SecureSSH+Copilot/
├── src/               # Source code
├── tests/             # Test files
├── docs/              # Documentation
├── config/            # Configuration files
└── requirements.txt   # Python dependencies
```

## Security Features

- AES-256 encryption for stored credentials
- Local-only LLM processing
- Encrypted session logs
- Command safety checks

## License

MIT License 
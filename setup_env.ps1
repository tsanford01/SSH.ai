# Create a virtual environment
python -m venv venv

# Activate the virtual environment
.\venv\Scripts\Activate.ps1

# Install dependencies
pip install --no-cache-dir -r requirements.txt

Write-Host "Virtual environment setup complete. Run the application with 'python src/main.py'" 
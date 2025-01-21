#!/bin/bash

# Create a virtual environment
python -m venv venv

# Activate the virtual environment
source venv/bin/activate

# Install dependencies
pip install --no-cache-dir -r requirements.txt

echo "Virtual environment setup complete. Activate it using 'source venv/bin/activate' and run the application with 'python src/main.py'." 
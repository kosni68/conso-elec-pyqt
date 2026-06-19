# Setup script for Windows (PowerShell)
# This script creates a Python virtual environment and installs dependencies

Write-Host "Setting up Python virtual environment..."

# Check if Python is installed
try {
    $pythonVersion = python --version 2>&1
    Write-Host "Python found: $pythonVersion"
} catch {
    Write-Host "Error: Python is not installed or not in PATH. Please install Python first."
    exit 1
}

# Create virtual environment
if (Test-Path "venv") {
    Write-Host "Virtual environment already exists. Removing..."
    Remove-Item -Recurse -Force "venv"
}

python -m venv venv
Write-Host "Virtual environment created."

# Activate virtual environment
& ".\venv\Scripts\Activate.ps1"
Write-Host "Virtual environment activated."

# Upgrade pip
python -m pip install --upgrade pip

# Install dependencies
if (Test-Path "requirements.txt") {
    Write-Host "Installing dependencies from requirements.txt..."
    pip install -r requirements.txt
    Write-Host "Dependencies installed successfully."
} else {
    Write-Host "Warning: requirements.txt not found."
}

Write-Host "Setup complete! To activate the virtual environment in future sessions, run: .\venv\Scripts\Activate.ps1"
#!/bin/bash

# Setup script for Unix-like systems (Linux/Mac)
# This script creates a Python virtual environment and installs dependencies

echo "Setting up Python virtual environment..."

# Check if Python is installed
if ! command -v python3 &> /dev/null; then
    echo "Error: Python3 is not installed or not in PATH. Please install Python3 first."
    exit 1
fi

echo "Python3 found: $(python3 --version)"

# Create virtual environment
if [ -d "venv" ]; then
    echo "Virtual environment already exists. Removing..."
    rm -rf venv
fi

python3 -m venv venv
echo "Virtual environment created."

# Activate virtual environment
source venv/bin/activate
echo "Virtual environment activated."

# Upgrade pip
python -m pip install --upgrade pip

# Install dependencies
if [ -f "requirements.txt" ]; then
    echo "Installing dependencies from requirements.txt..."
    pip install -r requirements.txt
    echo "Dependencies installed successfully."
else
    echo "Warning: requirements.txt not found."
fi

echo "Setup complete! To activate the virtual environment in future sessions, run: source venv/bin/activate"
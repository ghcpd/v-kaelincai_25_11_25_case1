#!/bin/bash

# Setup script for Project B (Post-Change)
# Creates virtual environment and installs dependencies

set -e

echo "=== Setting up Project B (Post-Change) ==="

# Detect OS
if [[ "$OSTYPE" == "msys" || "$OSTYPE" == "win32" ]]; then
    echo "Windows detected"
    VENV_DIR="venv"
    PYTHON_CMD="python"
    ACTIVATE="$VENV_DIR\\Scripts\\activate"
else
    echo "Unix-like OS detected"
    VENV_DIR="venv"
    PYTHON_CMD="python3"
    ACTIVATE="source $VENV_DIR/bin/activate"
fi

# Create virtual environment
if [ ! -d "$VENV_DIR" ]; then
    echo "Creating virtual environment..."
    $PYTHON_CMD -m venv $VENV_DIR
else
    echo "Virtual environment already exists"
fi

# Activate virtual environment
echo "Activating virtual environment..."
if [[ "$OSTYPE" == "msys" || "$OSTYPE" == "win32" ]]; then
    source "$VENV_DIR/Scripts/activate" || true
else
    source $VENV_DIR/bin/activate || true
fi

# Install dependencies
echo "Installing dependencies from requirements.txt..."
pip install -q -r requirements.txt

echo "✓ Project B setup complete"
echo ""
echo "To activate the virtual environment manually:"
if [[ "$OSTYPE" == "msys" || "$OSTYPE" == "win32" ]]; then
    echo "  $VENV_DIR\\Scripts\\activate"
else
    echo "  source $VENV_DIR/bin/activate"
fi

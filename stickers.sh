#!/bin/bash

# Define the virtual environment directory
VENV_DIR=".venv"

# Check if virtual environment exists, if not, create it
if [ ! -d "$VENV_DIR" ]; then
  echo "Creating virtual environment..."
  python3 -m venv "$VENV_DIR"
  echo "Virtual environment created."
fi

# Activate the virtual environment
source "$VENV_DIR/bin/activate"

# Check if requirements.txt exists
if [ ! -f "requirements.txt" ]; then
  echo "requirements.txt not found! Please ensure it's present in the current directory."
  deactivate
  exit 1
fi

# Install the requirements if not already installed
echo "Ensuring dependencies..."
pip check >/dev/null 2>&1 || pip install -r requirements.txt

# Run the Python script with all passed arguments
echo "Running the Python script with the provided arguments..."
python3 script.py "$@"

# Deactivate the virtual environment
deactivate

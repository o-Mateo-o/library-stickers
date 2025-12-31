#!/bin/bash

# Define the virtual environment directory
VENV_DIR=".venv"


# Ensure dotenv
if ! python3 - <<'EOF'
import dotenv
EOF
then
  if command -v apt >/dev/null; then
    sudo apt update && sudo apt install -y python3-dotenv
  elif command -v dnf >/dev/null; then
    sudo dnf install -y python3-dotenv
  else
    echo "Unsupported distro"
    exit 1
  fi
fi


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
echo "Installing dependencies..."
pip install -r requirements.txt

# Run the Python script with all passed arguments
echo "Running the Python script with the provided arguments..."
python3 script.py "$@"

# Deactivate the virtual environment
deactivate
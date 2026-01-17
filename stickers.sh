#!/usr/bin/env bash
# set -e

# -------------------------------
# Step 0: Detect OS & install pip/venv if missing
# -------------------------------
echo "🔍 Checking Python environment..."

if [ -f /etc/os-release ]; then
  . /etc/os-release
else
  echo "❌ Cannot detect OS"
  exit 1
fi

# Ensure Python 3 exists
if ! command -v python3 >/dev/null 2>&1; then
  echo "❌ Python 3 is not installed. Please install it first."
  exit 1
fi

# Ensure pip is installed
if ! python3 -m pip --version >/dev/null 2>&1; then
  echo "⬇️  Installing pip..."
  if [[ "$ID" == "fedora" ]]; then
    sudo dnf install -y python3-pip
  elif [[ "$ID" == "ubuntu" || "$ID" == "debian" ]]; then
    sudo apt update
    sudo apt install -y python3-pip
  else
    echo "❌ Unsupported OS: $ID"
    exit 1
  fi
fi

# Ensure venv is available
if ! python3 -m venv --help >/dev/null 2>&1; then
  echo "⬇️  Installing venv..."
  if [[ "$ID" == "fedora" ]]; then
    sudo dnf install -y python3-virtualenv
    sudo dnf install python3-gobject gtk4 libadwaita
  elif [[ "$ID" == "ubuntu" || "$ID" == "debian" ]]; then
    sudo apt update
    sudo apt install -y python3-venv
    sudo apt install python3-gi gir1.2-gtk-4.0 gir1.2-adw-1
  else
    echo "❌ Unsupported OS: $ID"
    exit 1
  fi
fi

# -------------------------------
# Step 1: Define the virtual environment directory
# -------------------------------
VENV_DIR=".venv"

# -------------------------------
# Step 2: Create venv if it doesn't exist
# -------------------------------
if [ ! -d "$VENV_DIR" ]; then
  echo "Creating virtual environment..."
  python3 -m venv "$VENV_DIR" --system-site-packages
  echo "✅ Virtual environment created."
fi

# -------------------------------
# Step 3: Activate venv
# -------------------------------
source "$VENV_DIR/bin/activate"

# -------------------------------
# Step 4: Install dependencies from requirements.txt (quietly)
# -------------------------------
if [ ! -f "requirements.txt" ]; then
  echo "❌ requirements.txt not found!"
fi

echo "Ensuring dependencies..."
pip install --upgrade pip --quiet
pip install -r requirements.txt --quiet


# -------------------------------
# Step 5: Run Python script with all passed arguments
# -------------------------------
echo "✅ Running the Python script."
python3 script.py "$@"

# -------------------------------
# Step 6: Deactivate venv
# -------------------------------
deactivate

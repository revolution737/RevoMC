#!/bin/bash
echo "Setting up local build environment for Linux..."

# Ensure we are in the project directory (one level up from builds folder)
cd "$(dirname "$0")/.."

# Note to user about tkinter
echo "Note: RevoMC requires tkinter. On Ubuntu/Debian, install with 'sudo apt install python3-tk'."
echo "On Fedora, install with 'sudo dnf install python3-tkinter'."
echo ""

# Create a virtual environment if it doesn't exist
if [ ! -f "venv/bin/activate" ]; then
    echo "Creating virtual environment..."
    python3 -m venv venv
    if [ $? -ne 0 ]; then
        echo "Error: Python 3 is not installed or venv module is missing."
        exit 1
    fi
fi

# Activate the virtual environment
source venv/bin/activate

# Install dependencies
echo "Installing requirements..."
pip install -r requirements.txt requests pyinstaller

# Build the executable
echo "Building RevoMC..."
pyinstaller revomc.spec --clean --distpath builds/

echo "Running smoke test on the built executable..."
builds/RevoMC/RevoMC --smoke-test
if [ $? -ne 0 ]; then
    echo "Error: Smoke test failed. The build is broken and missing modules."
    exit 1
fi

echo ""
echo "Build complete and validated! The executable is located in the 'builds' folder."

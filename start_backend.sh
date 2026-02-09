#!/bin/bash
# Simple startup script - bypasses pyenv issues

# Get script directory (handles spaces in path)
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR/backend" || exit 1

# Use system Python directly
PYTHON=/usr/local/bin/python3

# Create venv if it doesn't exist or is broken
if [ ! -f "venv/bin/activate" ]; then
    echo "Creating virtual environment..."
    $PYTHON -m venv venv
fi

# Activate venv
source venv/bin/activate

# Install/upgrade dependencies
echo "Installing dependencies..."
pip install --quiet --upgrade pip
pip install --quiet -r requirements.txt

echo ""
echo "========================================="
echo "✅ Backend starting..."
echo "========================================="
echo ""
echo "🌐 Open: http://localhost:8000"
echo "📚 API docs: http://localhost:8000/docs"
echo ""
echo "Press Ctrl+C to stop"
echo ""

# Start the server
$PYTHON main.py

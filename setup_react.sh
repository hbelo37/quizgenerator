#!/bin/bash
# Setup script for React frontend

echo "========================================="
echo "Setting up React Frontend"
echo "========================================="

cd frontend || exit 1

# Check if node_modules exists
if [ ! -d "node_modules" ]; then
    echo "Installing npm dependencies..."
    npm install
else
    echo "✓ Dependencies already installed"
fi

echo ""
echo "========================================="
echo "React Frontend Setup Complete!"
echo "========================================="
echo ""
echo "To start the React dev server:"
echo "  cd frontend"
echo "  npm start"
echo ""
echo "The app will run on http://localhost:3000"
echo ""

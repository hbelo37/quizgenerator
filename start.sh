#!/bin/bash

# Quick Start Script for MCQ Quiz Generator
# This script helps you start the application quickly

echo "========================================="
echo "MCQ Quiz Generator - Quick Start"
echo "========================================="
echo ""

# Check if Ollama is running
if ! curl -s http://localhost:11434/api/tags > /dev/null 2>&1; then
    echo "⚠️  WARNING: Ollama doesn't seem to be running!"
    echo ""
    echo "Please start Ollama first:"
    echo "  1. Open a terminal"
    echo "  2. Run: ollama serve"
    echo "  3. Then run this script again"
    echo ""
    read -p "Press Enter to continue anyway, or Ctrl+C to exit..."
    echo ""
fi

# Check Python
if ! command -v python3 &> /dev/null; then
    echo "❌ Python 3 not found. Please install Python 3.9+"
    exit 1
fi

echo "✓ Python found"
echo ""

# Navigate to backend directory
cd backend || exit

# Check if virtual environment exists
if [ ! -d "venv" ]; then
    echo "Creating virtual environment..."
    python3 -m venv venv
fi

# Activate virtual environment
echo "Activating virtual environment..."
source venv/bin/activate 2>/dev/null || . venv/bin/activate

# Install dependencies if needed
if [ ! -f "venv/.deps-installed" ]; then
    echo "Installing dependencies..."
    pip install -q -r requirements.txt
    touch venv/.deps-installed
else
    echo "✓ Dependencies already installed"
fi

echo ""
echo "========================================="
echo "Starting server..."
echo "========================================="
echo ""
echo "🌐 Open your browser to: http://localhost:8000"
echo "📚 API docs available at: http://localhost:8000/docs"
echo ""
echo "Press Ctrl+C to stop the server"
echo ""

# Start the server
python main.py

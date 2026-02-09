#!/bin/bash
# Quick script to start the backend

cd backend
source venv/bin/activate

# Install dependencies if needed
pip install -q -r requirements.txt

echo ""
echo "========================================="
echo "Starting MCQ Quiz Generator Backend"
echo "========================================="
echo ""
echo "✅ Ollama is already running (that's good!)"
echo "🌐 Opening browser to: http://localhost:8000"
echo "📚 API docs: http://localhost:8000/docs"
echo ""
echo "Press Ctrl+C to stop"
echo ""

python main.py

#!/usr/bin/env python3
"""
Quick setup test script - verifies your environment is ready.
Run this before starting the app to catch common issues early.
"""

import sys
import subprocess
import requests
from pathlib import Path

def check_python():
    """Check Python version"""
    version = sys.version_info
    if version.major < 3 or (version.major == 3 and version.minor < 9):
        print("❌ Python 3.9+ required. Current:", sys.version)
        return False
    print(f"✓ Python {version.major}.{version.minor}.{version.micro}")
    return True

def check_ollama():
    """Check if Ollama is running"""
    try:
        resp = requests.get("http://localhost:11434/api/tags", timeout=2)
        if resp.status_code == 200:
            models = resp.json().get("models", [])
            model_names = [m.get("name", "") for m in models]
            if model_names:
                print(f"✓ Ollama is running with models: {', '.join(model_names[:3])}")
            else:
                print("⚠️  Ollama is running but no models found. Run: ollama pull mistral")
            return True
    except Exception:
        print("❌ Ollama is not running. Start it with: ollama serve")
        return False

def check_dependencies():
    """Check if required packages are installed"""
    required = ["fastapi", "uvicorn", "sqlalchemy", "pydantic", "PyPDF2", "beautifulsoup4", "requests"]
    missing = []
    
    for pkg in required:
        try:
            __import__(pkg.lower().replace("-", "_"))
        except ImportError:
            missing.append(pkg)
    
    if missing:
        print(f"❌ Missing packages: {', '.join(missing)}")
        print("   Install with: pip install -r backend/requirements.txt")
        return False
    
    print("✓ All required packages installed")
    return True

def check_structure():
    """Check project structure"""
    required_dirs = [
        Path("backend"),
        Path("frontend"),
        Path("backend/services"),
    ]
    required_files = [
        Path("backend/main.py"),
        Path("backend/requirements.txt"),
        Path("frontend/index.html"),
        Path("frontend/script.js"),
    ]
    
    missing_dirs = [d for d in required_dirs if not d.exists()]
    missing_files = [f for f in required_files if not f.exists()]
    
    if missing_dirs or missing_files:
        print("❌ Missing files/directories:")
        for item in missing_dirs + missing_files:
            print(f"   - {item}")
        return False
    
    print("✓ Project structure looks good")
    return True

def main():
    print("=" * 50)
    print("MCQ Quiz Generator - Setup Check")
    print("=" * 50)
    print()
    
    checks = [
        ("Python version", check_python),
        ("Project structure", check_structure),
        ("Python dependencies", check_dependencies),
        ("Ollama service", check_ollama),
    ]
    
    results = []
    for name, check_func in checks:
        print(f"Checking {name}...")
        results.append(check_func())
        print()
    
    print("=" * 50)
    if all(results):
        print("✅ All checks passed! You're ready to start the app.")
        print()
        print("Next steps:")
        print("  1. Make sure Ollama is running: ollama serve")
        print("  2. Start the backend: cd backend && python main.py")
        print("  3. Open browser: http://localhost:8000")
    else:
        print("❌ Some checks failed. Please fix the issues above.")
        sys.exit(1)

if __name__ == "__main__":
    main()

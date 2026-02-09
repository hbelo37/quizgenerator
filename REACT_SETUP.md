# React Setup Instructions

The frontend has been converted to React with the exact color scheme from your design images.

## Quick Start

### 1. Install Node.js (if not installed)
- Download from: https://nodejs.org/
- Or use Homebrew: `brew install node`

### 2. Install React Dependencies

```bash
cd frontend
npm install
```

Or use the setup script:
```bash
./setup_react.sh
```

### 3. Start React Development Server

```bash
cd frontend
npm start
```

This will:
- Start React dev server on **http://localhost:3000**
- Automatically proxy API requests to backend at http://localhost:8000
- Hot reload on file changes

### 4. Start Backend (in another terminal)

```bash
cd backend
source venv/bin/activate
python main.py
```

## Development Workflow

1. **Terminal 1**: Run `npm start` in `frontend/` (React dev server)
2. **Terminal 2**: Run `python main.py` in `backend/` (FastAPI server)
3. **Terminal 3**: Run `ollama serve` (Ollama LLM server)

Open **http://localhost:3000** in your browser.

## Production Build

To build for production:

```bash
cd frontend
npm run build
```

This creates a `build/` folder. The FastAPI backend will automatically serve it if present.

## Color Scheme

The app uses the exact colors from your design:
- **Primary Teal**: `#14b8a6`
- **Secondary Cyan**: `#06b6d4`
- **Gradient**: `linear-gradient(135deg, #14b8a6 0%, #06b6d4 100%)`
- **Active State**: Teal border (`#14b8a6`) with light teal background (`#f0fdfa`)

## Features

✅ Modern React components  
✅ One question at a time navigation  
✅ Progress bar and answered counter  
✅ Exact color matching from design  
✅ Responsive design  
✅ Shareable quiz links  

## Troubleshooting

**Port 3000 already in use:**
- React will ask to use another port automatically
- Or change port: `PORT=3001 npm start`

**API requests failing:**
- Make sure backend is running on port 8000
- Check `.env` file in `frontend/` directory:
  ```
  REACT_APP_API_BASE=http://localhost:8000
  ```

**Build errors:**
- Delete `node_modules` and `package-lock.json`
- Run `npm install` again

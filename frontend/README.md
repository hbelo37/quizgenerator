# React Frontend for MCQ Quiz Generator

## Setup

1. Install dependencies:
```bash
cd frontend
npm install
```

2. Start development server:
```bash
npm start
```

The app will run on http://localhost:3000 and proxy API requests to the backend.

## Build for Production

```bash
npm run build
```

This creates a `build` folder that can be served by the FastAPI backend.

## Environment Variables

Create a `.env` file in the `frontend` directory:

```
REACT_APP_API_BASE=http://localhost:8000
```

For production, set this to your backend URL.

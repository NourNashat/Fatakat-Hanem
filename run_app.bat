@echo off
title Parkville Skin & Hair Care Expert - Full Stack Application
echo ==============================================================================
echo Starting Parkville Skin & Hair Care Expert Full-Stack RAG Application
echo ==============================================================================

:: Activate Python virtual environment and start backend
echo Starting FastAPI Backend Server on http://localhost:8000 ...
start "Parkville Backend API" cmd /k ".\.venv\Scripts\python.exe -m uvicorn backend.main:app --host 0.0.0.0 --port 8000 --reload"

:: Start frontend development server
echo Starting Frontend Application on http://localhost:5173 ...
cd frontend
start "Parkville Frontend App" cmd /k "npm run dev"

echo.
echo Both servers have been launched!
echo - Backend API Docs: http://localhost:8000/docs
echo - Frontend Web App: http://localhost:5173
echo ==============================================================================

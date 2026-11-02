@echo off
title Launching StreamVault Full-Stack Web App
echo ======================================================================
echo              StreamVault - Starting Local Services
echo ======================================================================
echo.
echo [1/2] Starting Backend API Server (http://localhost:5000)...
start "StreamVault Backend API" cmd /k "cd /d %~dp0server && npm start"
timeout /t 3 /nobreak >nul
echo [2/2] Starting Frontend Vite App (http://localhost:5173)...
start "StreamVault Frontend UI" cmd /k "cd /d %~dp0client && npm run dev"
echo.
echo ======================================================================
echo Both services are running in background console windows!
echo - Frontend UI:  http://localhost:5173
echo - Backend API:   http://localhost:5000
echo ======================================================================
timeout /t 4 >nul


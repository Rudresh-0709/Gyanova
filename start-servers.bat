@echo off
setlocal
cd /d "%~dp0"

echo Starting WEB + API dev servers...
call npm run dev:all

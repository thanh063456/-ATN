@echo off
title Khoi dong DocuCTSV OCR System
echo ========================================================
echo   DANG KHOI DONG HE THONG DOCUCTSV OCR (DAI HOC DA LAT)
echo ========================================================
echo.

set PYTHON_CMD="%LOCALAPPDATA%\Programs\Python\Python313\python.exe"
if not exist %PYTHON_CMD% set PYTHON_CMD=python

echo [1/2] Dang khoi dong Backend FastAPI (Port 8000)...
start "DocuCTSV Backend" cmd /k "cd /d %~dp0backend && %PYTHON_CMD% -m uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload"

echo [2/2] Dang khoi dong Frontend React Vite (Port 3000)...
start "DocuCTSV Frontend" cmd /k "cd /d %~dp0frontend && npm run dev"

echo.
echo ========================================================
echo   HE THONG DA KHOI DONG THANH CONG!
echo   - Frontend: http://localhost:3000
echo   - Backend Swagger: http://127.0.0.1:8000/docs
echo ========================================================
pause

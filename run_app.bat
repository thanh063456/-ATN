@echo off
title Khoi dong DocuCTSV OCR System
echo ========================================================
echo   DANG KHOI DONG HE THONG DOCUCTSV OCR (DAI HOC DA LAT)
echo ========================================================
echo.

echo [1/2] Dang khoi dong Backend FastAPI (Port 8000)...
start "DocuCTSV Backend" cmd /k "cd /d %~dp0backend && uvicorn app.main:app --host 127.0.0.1 --port 8000 --reload"

echo [2/2] Dang khoi dong Frontend React Vite (Port 3000)...
start "DocuCTSV Frontend" cmd /k "cd /d %~dp0frontend && npm run dev"

echo.
echo ========================================================
echo   HE THONG DA KHOI DONG THANH CONG!
echo   - Frontend: http://localhost:3000
echo   - Backend Swagger: http://127.0.0.1:8000/docs
echo ========================================================
pause

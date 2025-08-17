@echo off
echo ====================================
echo   부동산 실시간 검색 시스템 시작
echo ====================================
echo.

echo [1/2] 백엔드 API 서버 시작 (포트 8000)...
start cmd /k "cd backend && uvicorn app:app --reload --host 0.0.0.0 --port 8000"

echo.
echo [2/2] 프론트엔드 서버 시작 (포트 3000)...
timeout /t 3 >nul
start cmd /k "cd frontend && npm run dev"

echo.
echo ====================================
echo   시스템 시작 완료!
echo ====================================
echo.
echo 백엔드 API: http://localhost:8000
echo API 문서: http://localhost:8000/docs
echo 프론트엔드: http://localhost:3000
echo.
echo 종료하려면 열린 CMD 창들을 닫으세요.
echo ====================================
pause
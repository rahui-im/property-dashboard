@echo off
echo ========================================
echo   매물 수집 에이전트 v1.0
echo ========================================
echo.

REM Python 설치 확인
python --version >nul 2>&1
if errorlevel 1 (
    echo ❌ Python이 설치되어 있지 않습니다!
    echo 👉 https://www.python.org 에서 Python을 설치해주세요.
    pause
    exit
)

REM 가상환경 확인 및 생성
if not exist "venv" (
    echo 📦 가상환경 생성 중...
    python -m venv venv
)

REM 가상환경 활성화
echo 🔄 가상환경 활성화...
call venv\Scripts\activate.bat

REM 패키지 설치 확인
pip show requests >nul 2>&1
if errorlevel 1 (
    echo 📥 필요한 패키지 설치 중...
    pip install -r requirements.txt
)

REM 메인 프로그램 실행
echo.
echo 🚀 매물 수집 시작!
echo ========================================
python main.py

echo.
echo ========================================
echo ✅ 수집 완료! data 폴더를 확인해주세요.
echo ========================================
pause
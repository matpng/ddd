@echo off
REM AGI Proto-System - Quick Setup Script (Windows)
REM Run this to set up the project for first use

echo.
echo ================================================
echo   AGI Proto-System - Quick Setup
echo ================================================
echo.

REM Check Node.js
echo Checking Node.js version...
node -v >nul 2>&1
if errorlevel 1 (
    echo ERROR: Node.js not found. Please install Node.js 18+
    exit /b 1
)
echo OK: Node.js found
echo.

REM Install dependencies
echo Installing dependencies...
call npm install
if errorlevel 1 (
    echo ERROR: Failed to install dependencies
    exit /b 1
)
echo OK: Dependencies installed
echo.

REM Check for .env file
if not exist .env (
    echo Creating .env from template...
    copy .env.example .env
    echo.
    echo WARNING: Please edit .env and add your API keys:
    echo   - OPENAI_API_KEY (required)
    echo   - ANTHROPIC_API_KEY (optional)
    echo   - DB_URL (required)
    echo.
) else (
    echo OK: .env file exists
    echo.
)

REM Build the project
echo Building TypeScript...
call npm run build
if errorlevel 1 (
    echo ERROR: Build failed
    exit /b 1
)
echo OK: Build successful
echo.

REM Run tests
echo Running tests...
call npm test -- --passWithNoTests
if errorlevel 1 (
    echo WARNING: Some tests failed (this is OK for initial setup)
) else (
    echo OK: Tests passed
)
echo.

echo ================================================
echo   Setup complete!
echo ================================================
echo.
echo Next steps:
echo 1. Edit .env and add your API keys
echo 2. Set up PostgreSQL database: createdb agi_proto
echo 3. Enable pgvector: psql agi_proto -c "CREATE EXTENSION vector;"
echo 4. Run the system: npm run dev
echo.
echo Documentation can be found in:
echo - Quick Reference: .gemini\antigravity\brain\...\quick_reference.md
echo - Walkthrough: .gemini\antigravity\brain\...\walkthrough.md
echo - Troubleshooting: .gemini\antigravity\brain\...\troubleshooting.md
echo.
pause

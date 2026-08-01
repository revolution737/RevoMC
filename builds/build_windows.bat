@echo off
echo Setting up local build environment...

:: Ensure we are in the project directory (one level up from builds folder)
cd /d "%~dp0\.."

:: Use the py launcher to create a virtual environment if it doesn't exist
if not exist "venv\Scripts\activate.bat" (
    echo Creating virtual environment...
    py -3 -m venv venv
    if %errorlevel% neq 0 (
        echo "Error: Python is not installed or 'py' launcher is missing."
        exit /b %errorlevel%
    )
)

:: Activate the virtual environment
call venv\Scripts\activate.bat

:: Install dependencies
echo Installing requirements...
pip install -r requirements.txt requests pyinstaller

:: Build the executable
echo Building RevoMC...
pyinstaller revomc.spec --clean --distpath builds/

echo.
echo Running smoke test on the built executable...
builds\RevoMC.exe --smoke-test
if %errorlevel% neq 0 (
    echo Error: Smoke test failed. The build is broken and missing modules.
    pause
    exit /b %errorlevel%
)

echo.
echo Build complete and validated! The executable is located in the 'builds' folder.
pause

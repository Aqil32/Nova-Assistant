@echo off
title Nova Voice Assistant - Advanced Launcher
color 0d
setlocal enabledelayedexpansion

:main_menu
cls
echo.
echo ==========================================
echo         NOVA VOICE ASSISTANT LAUNCHER 
echo ==========================================
echo.
echo 1. Start Nova (Normal Mode)
echo 2. Install/Update Dependencies
echo 3. Test Nova's Voice
echo 4. Test Microphone Recording
echo 5. Check System Requirements
echo 6. Authentication Management
echo 7. Troubleshooting Mode
echo 8. Exit
echo.
set /p choice="Choose an option (1-8): "

if "%choice%"=="1" goto start_nova
if "%choice%"=="2" goto install_deps
if "%choice%"=="3" goto test_voice
if "%choice%"=="4" goto test_mic
if "%choice%"=="5" goto check_system
if "%choice%"=="6" goto auth_menu
if "%choice%"=="7" goto troubleshoot
if "%choice%"=="8" goto exit
goto main_menu

:start_nova
cls
echo  Starting Nova Voice Assistant...
echo.
echo  🔐 You'll be prompted for authentication
echo  💡 Tip: Press ENTER for guest access
echo.
python app.py
echo.
echo  Nova session ended.
pause
goto main_menu

:auth_menu
cls
echo.
echo ==========================================
echo         AUTHENTICATION MANAGEMENT
echo ==========================================
echo.
echo 1. Test Authentication System
echo 2. Reset Secret Phrase
echo 3. View Authentication Info
echo 4. Back to Main Menu
echo.
set /p auth_choice="Choose an option (1-4): "

if "%auth_choice%"=="1" goto test_auth
if "%auth_choice%"=="2" goto reset_auth
if "%auth_choice%"=="3" goto view_auth
if "%auth_choice%"=="4" goto main_menu
goto auth_menu

:test_auth
cls
echo  Testing Authentication System...
echo.
python -c "from auth import authenticate_user; username, is_creator = authenticate_user(); print(f'Result: {username}, Creator: {is_creator}')"
echo.
pause
goto auth_menu

:reset_auth
cls
echo  ⚠️  WARNING: This will reset your secret phrase!
echo  You'll need to set up authentication again.
echo.
set /p confirm="Are you sure? (y/N): "
if /i "%confirm%"=="y" (
    python -c "from auth import reset_authentication; reset_authentication()"
    echo.
    echo  ✅ Authentication reset complete!
) else (
    echo  ❌ Reset cancelled.
)
echo.
pause
goto auth_menu

:view_auth
cls
echo  Authentication Status:
echo.
python -c "import os; print('Auth file exists:', os.path.exists('nova_auth.json')); from auth import nova_auth; print('Setup complete:', nova_auth.secret_phrase_hash is not None)"
echo.
pause
goto auth_menu

:install_deps
cls
echo  Installing/Updating Dependencies...
echo.

echo Installing Whisper (Speech-to-Text)...
pip install -U openai-whisper

echo Installing SoundDevice (Audio Recording)...
pip install -U sounddevice

echo Installing SciPy (Audio Processing)...
pip install -U scipy

echo Installing Coqui-TTS (Text-to-Speech)...
pip install -U TTS

echo Installing additional dependencies...
pip install -U numpy torch

echo Installing MySQL connector for database...
pip install -U mysql-connector-python

echo.
echo  Dependencies installation complete!
pause
goto main_menu

:test_voice
cls
echo  Testing Nova's Voice...
echo.
if exist "test_nova_voice.py" (
    python test_nova_voice.py
) else (
    echo Testing basic TTS...
    python -c "import asyncio; from voice.tts import speak_text_sync; speak_text_sync('Hey there! This is Nova testing her voice!')"
)
echo.
pause
goto main_menu

:test_mic
cls
echo  Testing Microphone Recording...
echo.
python -c "from voice.recorder import record_audio; from voice.stt import transcribe_audio; print('Recording 5 seconds...'); record_audio('test.wav', 5); result = transcribe_audio('test.wav'); print(f'You said: {result}')"
echo.
pause
goto main_menu

:check_system
cls
echo  System Requirements Check...
echo.

echo Checking Python...
python --version 2>nul
if %errorlevel% neq 0 (
    echo  Python not found!
) else (
    echo  Python OK
)

echo.
echo Checking FFmpeg (for audio playback)...
ffplay -version >nul 2>&1
if %errorlevel% neq 0 (
    echo FFmpeg not found - audio playback may not work
    echo Download from: https://ffmpeg.org/download.html
) else (
    echo  FFmpeg OK
)

echo.
echo Checking SoX (for pitch shifting)...
sox --version >nul 2>&1
if %errorlevel% neq 0 (
    echo SoX not found - voice pitch shifting may not work
    echo Download from: http://sox.sourceforge.net/
) else (
    echo SoX OK
)

echo.
echo Checking Python packages...
for %%p in (whisper sounddevice scipy TTS numpy torch mysql.connector) do (
    python -c "import %%p" >nul 2>&1
    if !errorlevel! neq 0 (
        echo  %%p not installed
    ) else (
        echo %%p OK
    )
)

echo.
echo Checking authentication files...
if exist "nova_auth.json" (
    echo  Authentication configured
) else (
    echo  Authentication not set up yet
)

echo.
pause
goto main_menu

:troubleshoot
cls
echo  Troubleshooting Mode
echo.
echo Starting Nova with verbose error output...
echo If Nova crashes, you'll see detailed error information.
echo.
python -u -W all app.py
echo.
echo Troubleshooting session ended.
pause
goto main_menu

:exit
cls
echo.
echo  Thanks for using Nova Voice Assistant!
echo  Your authentication settings have been preserved.
echo.
exit /b 0
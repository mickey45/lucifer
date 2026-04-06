@echo off
echo ============================================
echo   LUCIFER AI - Setup Script
echo ============================================
echo.
echo Installing Python dependencies...
pip install -r requirements.txt
echo.
echo Downloading spaCy language model...
python -m spacy download en_core_web_sm
echo.
echo ============================================
echo   Setup complete! Run with: python lucifer.py
echo ============================================
pause
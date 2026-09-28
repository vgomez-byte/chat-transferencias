@echo off
cd /d "%~dp0"
call venv\Scripts\activate
python scripts\indexar_documentos.py
pause

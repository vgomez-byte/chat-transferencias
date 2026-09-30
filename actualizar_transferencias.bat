@echo off
cd /d "%~dp0"
call venv\Scripts\activate
python scripts\subir_csv_supabase.py
pause

@echo off
start "" python run.py run
timeout /t 3 /nobreak >nul
start http://localhost:5000

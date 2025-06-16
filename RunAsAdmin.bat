@echo off
powershell -Command "Start-Process cmd -ArgumentList '/c cd /d \"%~dp0\" && python main.py' -Verb RunAs" 
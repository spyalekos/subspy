@echo off
..\farmasave.flet\.venv\Scripts\activate.bat 
pyinstaller --onefile --windowed --name "subspy" .\src\main.py


@echo off
setlocal
set PYTHONUNBUFFERED=1
C:\training\python311\python.exe C:\training\merge_expertia.py --domain electronics > C:\training\logs\merge_electronics.log 2> C:\training\logs\merge_electronics.err.log

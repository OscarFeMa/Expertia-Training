@echo off
setlocal
set PYTHONUNBUFFERED=1
C:\training\python311\python.exe C:\training\merge_expertia_chemistry.py > C:\training\logs\merge_chemistry.log 2> C:\training\logs\merge_chemistry.err.log

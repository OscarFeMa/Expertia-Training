@echo off
setlocal
set PYTHONUNBUFFERED=1
C:\training\python311\python.exe C:\training\merge_expertia.py --domain bio > C:\training\logs\merge_bio.log 2> C:\training\logs\merge_bio.err.log

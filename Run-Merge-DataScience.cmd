@echo off
setlocal
set PYTHONUNBUFFERED=1
C:\training\python311\python.exe C:\training\merge_expertia.py --domain datascience > C:\training\logs\merge_datascience.log 2> C:\training\logs\merge_datascience.err.log

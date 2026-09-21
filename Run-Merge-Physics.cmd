@echo off
setlocal
set PYTHONUNBUFFERED=1
C:\training\python311\python.exe C:\training\merge_expertia.py --domain physics > C:\training\logs\merge_physics.log 2> C:\training\logs\merge_physics.err.log

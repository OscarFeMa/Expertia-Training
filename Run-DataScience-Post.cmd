@echo off
setlocal
call C:\training\Run-Merge-DataScience.cmd
call C:\training\Run-Eval-DataScience.cmd
call C:\training\Run-GGUF-DataScience.cmd
echo DATASCIENCE POST DONE > C:\training\logs\datascience_post.done

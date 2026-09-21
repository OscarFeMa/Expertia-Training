@echo off
setlocal
call C:\training\Run-Merge-Bio.cmd
call C:\training\Run-Eval-Bio.cmd
call C:\training\Run-GGUF-Bio.cmd
echo BIO POST DONE > C:\training\logs\bio_post.done

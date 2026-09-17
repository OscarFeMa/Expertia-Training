import sys
from huggingface_hub import snapshot_download

target = r"D:\proyectos\expertia\training\base\phi-4-mini-reasoning"
try:
    path = snapshot_download(
        repo_id="microsoft/Phi-4-mini-reasoning",
        local_dir=target,
        local_dir_use_symlinks=False,
        resume_download=True,
    )
    print("DOWNLOAD_OK " + path)
except Exception as e:
    print("DOWNLOAD_FAIL " + str(e)[:500])
    sys.exit(1)

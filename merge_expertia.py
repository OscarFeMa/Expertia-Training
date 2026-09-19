"""Merge un adaptador LoRA r16 sobre su base Phi-4-mini-reasoning (CPU, fp16).
Parametrizado por dominio: sustituye a merge_expertia_{math,physics,chemistry}.py.
Uso (en el 3070): python merge_expertia.py --domain swe
"""
import argparse
from pathlib import Path


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--domain", required=True,
                   help="math | physics | chemistry | electronics | swe")
    p.add_argument("--base", default=r"C:\training\base\phi-4-mini-reasoning")
    args = p.parse_args()

    adapter = rf"C:\training\adapters\expertia-{args.domain}-r16"
    out = rf"C:\training\merged\expertia-{args.domain}-fp16"
    print("MERGE start", args.base, "->", out, flush=True)

    from transformers import AutoModelForCausalLM, AutoTokenizer
    from peft import PeftModel
    import torch

    tok = AutoTokenizer.from_pretrained(args.base, trust_remote_code=True, use_fast=False)
    model = AutoModelForCausalLM.from_pretrained(args.base, torch_dtype=torch.float16,
                                                 trust_remote_code=True, device_map="cpu")
    print("base loaded", flush=True)
    model = PeftModel.from_pretrained(model, adapter)
    print("adapter loaded", flush=True)
    model = model.merge_and_unload()
    print("merged", flush=True)
    Path(out).mkdir(parents=True, exist_ok=True)
    model.save_pretrained(out, safe_serialization=True)
    tok.save_pretrained(out)
    print("saved", out, flush=True)


if __name__ == "__main__":
    main()

"""用 Trellis 的 Python 執行 3D 生成。不要在 FastAPI 行程 import 此檔。此檔由 TRELLIS_PYTHON 子行程執行。"""

import os
import sys
import traceback
from pathlib import Path


_root_env = os.environ.get("TRELLIS_ROOT", "").strip()
if _root_env:
    _root = Path(_root_env)
    if _root.is_dir() and str(_root) not in sys.path:
        sys.path.insert(0, str(_root))

os.environ.setdefault("ATTN_BACKEND", "xformers")
os.environ.setdefault("SPCONV_ALGO", "native")

import torch
from trellis.pipelines import TrellisTextTo3DPipeline
from trellis.utils import postprocessing_utils


def generate(prompt: str, dest: Path) -> None:
    if not torch.cuda.is_available():
        raise RuntimeError("需要 CUDA GPU 才能執行 Trellis 生成")

    pipeline = TrellisTextTo3DPipeline.from_pretrained(
        os.environ.get("TRELLIS_MODEL", "").strip() or "microsoft/TRELLIS-text-base"
    )
    pipeline.cuda()
    outputs = pipeline.run(
        prompt,
        seed=1,
        formats=["gaussian", "mesh"],
        sparse_structure_sampler_params={"steps": 25, "cfg_strength": 7.5},
        slat_sampler_params={"steps": 25, "cfg_strength": 7.5},
    )
    glb = postprocessing_utils.to_glb(
        outputs["gaussian"][0],
        outputs["mesh"][0],
        simplify=0.95,
        texture_size=1024,
        verbose=False,
    )
    dest.parent.mkdir(parents=True, exist_ok=True)
    glb.export(str(dest))
    torch.cuda.empty_cache()


def main() -> None:
    if len(sys.argv) != 3:
        print("用法：trellis_worker.py <prompt> <dest.glb>", file=sys.stderr)
        sys.exit(2)
    prompt = sys.argv[1]
    dest = Path(sys.argv[2])
    try:
        generate(prompt, dest)
    except Exception as exc:
        traceback.print_exc()
        print(f"錯誤：{exc}", file=sys.stderr)
        sys.exit(1)
    print(f"完成：{dest}")


if __name__ == "__main__":
    main()

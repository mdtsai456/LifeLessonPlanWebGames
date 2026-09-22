"""Trellis 文字轉 3D。MOCK 時寫入佔位 GLB。否則用 TRELLIS_PYTHON 子行程執行。"""

import os
import subprocess
from pathlib import Path

from backend.gpu_job import UnavailableError, gpu_slot, parse_completed_path

_TIMEOUT_SEC = 1800


def _mock_enabled() -> bool:
    return os.environ.get("TRELLIS_MOCK", "").strip() in {"1", "true", "True", "yes"}


def _python() -> Path:
    env = os.environ.get("TRELLIS_PYTHON", "").strip()
    if not env:
        raise UnavailableError("請設 TRELLIS_PYTHON 指向 trellis 的 python.exe")
    return Path(env)


def generate_glb_to_path(prompt: str, dest: Path) -> None:
    """依 prompt 產生 GLB，寫入 dest。忙碌時拋出 BusyError。找不到環境時拋出 UnavailableError。"""
    text = prompt.strip()
    if not text:
        raise ValueError("prompt 不可空白")

    with gpu_slot():
        dest.parent.mkdir(parents=True, exist_ok=True)
        if _mock_enabled():
            dest.write_bytes(b"glTF-MOCK")
            return

        python = _python()
        worker = Path(__file__).with_name("trellis_worker.py")
        if not python.is_file():
            raise UnavailableError(
                f"找不到 Trellis Python：{python}。請設 TRELLIS_PYTHON 指向 trellis 的 python.exe"
            )
        if not worker.is_file():
            raise UnavailableError(f"找不到 trellis_worker.py：{worker}")

        env = os.environ.copy()
        env["PYTHONIOENCODING"] = "utf-8"
        env["PYTHONUNBUFFERED"] = "1"
        root = os.environ.get("TRELLIS_ROOT", "").strip()
        cwd = root if root and Path(root).is_dir() else None
        try:
            result = subprocess.run(
                [str(python), str(worker), text, str(dest)],
                cwd=cwd,
                capture_output=True,
                text=True,
                encoding="utf-8",
                errors="replace",
                timeout=_TIMEOUT_SEC,
                env=env,
            )
        except FileNotFoundError as exc:
            raise UnavailableError(f"無法啟動 Trellis Python：{python}") from exc
        except subprocess.TimeoutExpired as exc:
            raise RuntimeError("Trellis 生成逾時") from exc

        stderr = (result.stderr or "").strip()
        stdout = result.stdout or ""
        if result.returncode != 0:
            raise RuntimeError(stderr or stdout or f"Trellis 結束碼 {result.returncode}")

        source = parse_completed_path(stdout, "Trellis 未輸出完成路徑")
        if not source.is_file():
            raise RuntimeError(f"找不到生成檔：{source}")
        if source.resolve() != dest.resolve():
            dest.write_bytes(source.read_bytes())

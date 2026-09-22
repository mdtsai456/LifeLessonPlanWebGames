"""text2image 2D 生成。MOCK 時寫入佔位 PNG。否則用獨立 venv 執行 generate.py。"""

import os
import shutil
import subprocess
from pathlib import Path

from backend.gpu_job import UnavailableError, gpu_slot, parse_completed_path

_TIMEOUT_SEC = 1800
_MOCK_PNG = (
    b"\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR\x00\x00\x00\x01\x00\x00\x00\x01"
    b"\x08\x02\x00\x00\x00\x90wS\xde\x00\x00\x00\x0cIDATx\x9cc\xf8\x0f\x00"
    b"\x00\x01\x01\x00\x05\x18\xd8N\x00\x00\x00\x00IEND\xaeB`\x82"
)


def _mock_enabled() -> bool:
    return os.environ.get("TEXT2IMAGE_MOCK", "").strip() in {"1", "true", "True", "yes"}


def _root() -> Path:
    env = os.environ.get("TEXT2IMAGE_ROOT", "").strip()
    if not env:
        raise UnavailableError("請設 TEXT2IMAGE_ROOT 指向 text2image 目錄")
    return Path(env)


def _python(root: Path) -> Path:
    env = os.environ.get("TEXT2IMAGE_PYTHON", "").strip()
    if env:
        return Path(env)
    return root / ".venv" / "Scripts" / "python.exe"


def generate_png_to_path(object_name: str, dest: Path) -> None:
    """依物件名稱產生 PNG，寫入 dest。忙碌時拋出 BusyError。找不到環境時拋出 UnavailableError。"""
    text = object_name.strip()
    if not text:
        raise ValueError("物件名稱不可空白")

    with gpu_slot():
        dest.parent.mkdir(parents=True, exist_ok=True)
        if _mock_enabled():
            dest.write_bytes(_MOCK_PNG)
            return

        root = _root()
        python = _python(root)
        script = root / "generate.py"
        if not python.is_file():
            raise UnavailableError(
                f"找不到 text2image Python：{python}。請設 TEXT2IMAGE_PYTHON 指向 python.exe"
            )
        if not script.is_file():
            raise UnavailableError(f"找不到 generate.py：{script}")

        env = os.environ.copy()
        env["PYTHONIOENCODING"] = "utf-8"
        env["PYTHONUNBUFFERED"] = "1"
        env["HF_HUB_DISABLE_XET"] = "1"
        try:
            result = subprocess.run(
                [str(python), str(script), text],
                cwd=str(root),
                capture_output=True,
                text=True,
                encoding="utf-8",
                errors="replace",
                timeout=_TIMEOUT_SEC,
                env=env,
            )
        except FileNotFoundError as exc:
            raise UnavailableError(f"無法啟動 text2image Python：{python}") from exc
        except subprocess.TimeoutExpired as exc:
            raise RuntimeError("text2image 生成逾時") from exc

        stderr = (result.stderr or "").strip()
        stdout = result.stdout or ""
        if result.returncode != 0:
            if stderr.startswith("錯誤：") and "生圖失敗" not in stderr:
                raise ValueError(stderr[len("錯誤：") :].strip() or stderr)
            raise RuntimeError(stderr or stdout or f"text2image 結束碼 {result.returncode}")

        source = parse_completed_path(stdout, "text2image 未輸出完成路徑")
        if not source.is_file():
            raise RuntimeError(f"找不到生成檔：{source}")
        shutil.copy2(source, dest)

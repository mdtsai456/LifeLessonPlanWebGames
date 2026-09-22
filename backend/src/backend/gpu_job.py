"""同一時間只允許一個 GPU 生成任務。2D 與 3D 共用此限制。"""

import threading
from collections.abc import Iterator
from contextlib import contextmanager
from pathlib import Path

_job_lock = threading.Lock()


class UnavailableError(RuntimeError):
    """找不到模型，或執行環境不可用。"""


class BusyError(RuntimeError):
    """已有生成任務進行中。"""


def try_acquire() -> None:
    if not _job_lock.acquire(blocking=False):
        raise BusyError("busy")


def release() -> None:
    _job_lock.release()


@contextmanager
def gpu_slot() -> Iterator[None]:
    try_acquire()
    try:
        yield
    finally:
        release()


def parse_completed_path(stdout: str, missing: str) -> Path:
    for line in reversed(stdout.splitlines()):
        stripped = line.strip()
        if stripped.startswith("完成："):
            return Path(stripped[len("完成：") :].strip())
    raise RuntimeError(missing)

"""資料庫連線、素材檔路徑、關卡 JSON 路徑。"""

import os
from collections.abc import Iterator
from contextlib import contextmanager
from pathlib import Path

import pymysql
import pymysql.cursors
from dotenv import load_dotenv

# 載入 cwd 的 .env（本機啟動）。也載入套件相對路徑的 .env（pytest）。
BACKEND_DIR = Path(__file__).resolve().parents[2]
load_dotenv()
load_dotenv(BACKEND_DIR / ".env")

# 圖檔在此目錄。由 /static 對外提供。資料庫 file_path 是相對此目錄的路徑。
STATIC_DIR = BACKEND_DIR / "static"
# 關卡 JSON 在此目錄。不對外公開。只能經 API 讀取。
STORAGE_DIR = BACKEND_DIR / "storage"


def connect_db() -> pymysql.connections.Connection:
    return pymysql.connect(
        host=os.getenv("DB_HOST", "127.0.0.1"),
        port=int(os.getenv("DB_PORT", "3306")),
        user=os.getenv("DB_USER", "root"),
        password=os.getenv("DB_PASSWORD", ""),
        database=os.getenv("DB_NAME", ""),
        charset="utf8mb4",
        cursorclass=pymysql.cursors.DictCursor,
    )


@contextmanager
def db_conn(*, commit: bool = False) -> Iterator[pymysql.connections.Connection]:
    connection = connect_db()
    try:
        yield connection
        if commit:
            connection.commit()
    except Exception:
        connection.rollback()
        raise
    finally:
        connection.close()

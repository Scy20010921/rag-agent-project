"""
MySQL 文档元数据管理。
存储文档（文件名、类型）和分段（内容、序号），
向量数据由 Chroma 独立管理。
"""
import pymysql
from datetime import datetime, timezone, timedelta
from app.core.config import settings

TZ = timezone(timedelta(hours=8))


def _get_conn() -> pymysql.Connection:
    return pymysql.connect(
        host=settings.mysql_host,
        port=settings.mysql_port,
        user=settings.mysql_user,
        password=settings.mysql_password,
        database=settings.mysql_database,
        charset="utf8mb4",
        cursorclass=pymysql.cursors.DictCursor,
    )


def init_db():
    """建表（幂等）"""
    conn = _get_conn()
    try:
        with conn.cursor() as cur:
            cur.execute("""
                CREATE TABLE IF NOT EXISTS documents (
                    id INT AUTO_INCREMENT PRIMARY KEY,
                    filename VARCHAR(500) NOT NULL,
                    file_type VARCHAR(20) NOT NULL,
                    status VARCHAR(20) NOT NULL DEFAULT 'processing',
                    chunk_count INT NOT NULL DEFAULT 0,
                    created_at DATETIME NOT NULL
                ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4
            """)
            cur.execute("""
                CREATE TABLE IF NOT EXISTS chunks (
                    id INT AUTO_INCREMENT PRIMARY KEY,
                    document_id INT NOT NULL,
                    content TEXT NOT NULL,
                    chunk_index INT NOT NULL,
                    created_at DATETIME NOT NULL,
                    FOREIGN KEY (document_id) REFERENCES documents(id) ON DELETE CASCADE
                ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4
            """)
        conn.commit()
    finally:
        conn.close()


def create_document(filename: str, file_type: str) -> int:
    """创建文档记录，返回 document_id"""
    now = datetime.now(TZ)
    conn = _get_conn()
    try:
        with conn.cursor() as cur:
            cur.execute(
                "INSERT INTO documents (filename, file_type, status, created_at) VALUES (%s, %s, 'processing', %s)",
                (filename, file_type, now),
            )
            conn.commit()
            return cur.lastrowid
    finally:
        conn.close()


def save_chunk(document_id: int, content: str, chunk_index: int):
    """存一个分段"""
    now = datetime.now(TZ)
    conn = _get_conn()
    try:
        with conn.cursor() as cur:
            cur.execute(
                "INSERT INTO chunks (document_id, content, chunk_index, created_at) VALUES (%s, %s, %s, %s)",
                (document_id, content, chunk_index, now),
            )
        conn.commit()
    finally:
        conn.close()


def update_document_status(document_id: int, status: str, chunk_count: int):
    """更新文档状态"""
    conn = _get_conn()
    try:
        with conn.cursor() as cur:
            cur.execute(
                "UPDATE documents SET status = %s, chunk_count = %s WHERE id = %s",
                (status, chunk_count, document_id),
            )
        conn.commit()
    finally:
        conn.close()


def list_documents() -> list[dict]:
    """列出所有文档"""
    conn = _get_conn()
    try:
        with conn.cursor() as cur:
            cur.execute("SELECT id, filename, file_type, status, chunk_count, created_at FROM documents ORDER BY created_at DESC")
            return cur.fetchall()
    finally:
        conn.close()


def get_document(document_id: int) -> dict | None:
    """获取单个文档"""
    conn = _get_conn()
    try:
        with conn.cursor() as cur:
            cur.execute("SELECT id, filename, file_type, status, chunk_count, created_at FROM documents WHERE id = %s", (document_id,))
            return cur.fetchone()
    finally:
        conn.close()


def get_all_chunks(document_id: int) -> list[dict]:
    """获取文档的所有分段"""
    conn = _get_conn()
    try:
        with conn.cursor() as cur:
            cur.execute("SELECT id, content, chunk_index FROM chunks WHERE document_id = %s ORDER BY chunk_index", (document_id,))
            return cur.fetchall()
    finally:
        conn.close()


def delete_document(document_id: int):
    """删除文档（级联删除 chunks）"""
    conn = _get_conn()
    try:
        with conn.cursor() as cur:
            cur.execute("DELETE FROM documents WHERE id = %s", (document_id,))
        conn.commit()
    finally:
        conn.close()


# 模块加载时建表
try:
    init_db()
except Exception:
    pass  # MySQL 还没启动时跳过
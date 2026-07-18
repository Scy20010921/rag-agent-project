"""
MySQL 文档元数据管理。
scope 隔离：public（公共知识库）和 user（用户私有）。
user 创建的表字段有 user_id 用于隔离。
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
    conn = _get_conn()
    try:
        with conn.cursor() as cur:
            cur.execute("""
                CREATE TABLE IF NOT EXISTS documents (
                    id INT AUTO_INCREMENT PRIMARY KEY,
                    filename VARCHAR(500) NOT NULL,
                    file_type VARCHAR(20) NOT NULL,
                    scope VARCHAR(20) NOT NULL DEFAULT 'public',
                    user_id VARCHAR(100) NOT NULL DEFAULT '',
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
            # 兼容旧表：加列（忽略已存在的错误）
            for col_sql in [
                "ALTER TABLE documents ADD COLUMN scope VARCHAR(20) NOT NULL DEFAULT 'public'",
                "ALTER TABLE documents ADD COLUMN user_id VARCHAR(100) NOT NULL DEFAULT ''",
            ]:
                try:
                    cur.execute(col_sql)
                except Exception:
                    pass
        conn.commit()
    finally:
        conn.close()


# ---- Document CRUD ----

def create_document(filename: str, file_type: str, scope: str = "public", user_id: str = "") -> int:
    now = datetime.now(TZ)
    conn = _get_conn()
    try:
        with conn.cursor() as cur:
            cur.execute(
                "INSERT INTO documents (filename, file_type, scope, user_id, status, created_at) VALUES (%s, %s, %s, %s, 'processing', %s)",
                (filename, file_type, scope, user_id, now),
            )
            conn.commit()
            return cur.lastrowid
    finally:
        conn.close()


def save_chunk(document_id: int, content: str, chunk_index: int):
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


def list_documents(scope: str | None = None, user_id: str | None = None) -> list[dict]:
    conn = _get_conn()
    try:
        with conn.cursor() as cur:
            if scope == "public":
                cur.execute(
                    "SELECT id, filename, file_type, scope, user_id, status, chunk_count, created_at FROM documents WHERE scope='public' ORDER BY created_at DESC"
                )
            elif scope == "user" and user_id:
                cur.execute(
                    "SELECT id, filename, file_type, scope, user_id, status, chunk_count, created_at FROM documents WHERE scope='user' AND user_id=%s ORDER BY created_at DESC",
                    (user_id,),
                )
            else:
                cur.execute(
                    "SELECT id, filename, file_type, scope, user_id, status, chunk_count, created_at FROM documents ORDER BY created_at DESC"
                )
            return cur.fetchall()
    finally:
        conn.close()


def list_public_documents() -> list[dict]:
    return list_documents(scope="public")


def list_user_documents(user_id: str) -> list[dict]:
    return list_documents(scope="user", user_id=user_id)


def get_document(document_id: int) -> dict | None:
    conn = _get_conn()
    try:
        with conn.cursor() as cur:
            cur.execute(
                "SELECT id, filename, file_type, scope, user_id, status, chunk_count, created_at FROM documents WHERE id = %s",
                (document_id,),
            )
            return cur.fetchone()
    finally:
        conn.close()


def delete_document(document_id: int):
    conn = _get_conn()
    try:
        with conn.cursor() as cur:
            cur.execute("DELETE FROM documents WHERE id = %s", (document_id,))
        conn.commit()
    finally:
        conn.close()


try:
    init_db()
except Exception:
    pass
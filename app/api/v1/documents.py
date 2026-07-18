"""文档管理 REST API"""
import os
import sys
import uuid
import traceback
from fastapi import APIRouter, UploadFile, File, HTTPException
from langchain_text_splitters import RecursiveCharacterTextSplitter
from app.core.config import settings
from app.core.doc_store import (
    create_document, save_chunk, update_document_status,
    list_documents, get_document, delete_document,
)
from app.core.vector_store import add_chunks, delete_document_chunks

router = APIRouter(prefix="/v1/documents", tags=["documents"])

ALLOWED_TYPES = {".txt": "text", ".md": "markdown", ".pdf": "pdf"}
UPLOAD_DIR = "data/uploads"


def _parse_text(file_bytes: bytes, filename: str) -> str:
    ext = os.path.splitext(filename)[1].lower()
    if ext in (".txt", ".md"):
        return file_bytes.decode("utf-8", errors="replace")
    elif ext == ".pdf":
        try:
            import pypdf
            import io
        except ImportError:
            raise HTTPException(status_code=500, detail="请安装 pypdf: pip install pypdf")
        try:
            reader = pypdf.PdfReader(io.BytesIO(file_bytes))
            pages_text = []
            for i, page in enumerate(reader.pages):
                t = page.extract_text()
                if t:
                    pages_text.append(t)
            return "\n".join(pages_text)
        except Exception as pdf_err:
            raise ValueError(f"PDF解析失败: {pdf_err}")
    else:
        raise HTTPException(status_code=400, detail=f"不支持的文件类型: {ext}")


@router.post("")
async def upload_document(file: UploadFile = File(...)):
    log = lambda msg: print(msg, flush=True)
    log(f"[UPLOAD] 收到文件: {file.filename}")
    try:
        ext = os.path.splitext(file.filename or "unknown.txt")[1].lower()
        if ext not in ALLOWED_TYPES:
            raise HTTPException(status_code=400, detail=f"不支持的文件类型: {ext}")

        os.makedirs(UPLOAD_DIR, exist_ok=True)
        safe_name = f"{uuid.uuid4().hex}_{file.filename}"
        file_path = os.path.join(UPLOAD_DIR, safe_name)
        content_bytes = await file.read()
        with open(file_path, "wb") as f:
            f.write(content_bytes)
        log(f"[UPLOAD] 文件已保存: {file_path} ({len(content_bytes)} bytes)")

        text = _parse_text(content_bytes, file.filename)
        if not text.strip():
            raise HTTPException(status_code=400, detail="文档内容为空")
        log(f"[UPLOAD] 文本解析完成，长度: {len(text)}")

        splitter = RecursiveCharacterTextSplitter(
            chunk_size=settings.chunk_size,
            chunk_overlap=settings.chunk_overlap,
            separators=["\n\n", "\n", "。", "！", "？", ".", "!", "?", " ", ""],
        )
        chunks = splitter.split_text(text)
        log(f"[UPLOAD] 分段完成，共 {len(chunks)} 段")
        if not chunks:
            raise HTTPException(status_code=400, detail="文档分段后为空")

        log("[UPLOAD] 写入 MySQL...")
        doc_id = create_document(file.filename, ALLOWED_TYPES[ext])
        log(f"[UPLOAD] 文档 ID: {doc_id}")
        for i, chunk in enumerate(chunks):
            save_chunk(doc_id, chunk, i)
        log("[UPLOAD] MySQL 写入完成")

        log("[UPLOAD] 开始向量化...")
        add_chunks(doc_id, file.filename, chunks)
        update_document_status(doc_id, "ready", len(chunks))
        log("[UPLOAD] 向量化完成 ✓")

        return {
            "id": doc_id,
            "filename": file.filename,
            "file_type": ALLOWED_TYPES[ext],
            "chunk_count": len(chunks),
            "status": "ready",
        }
    except HTTPException:
        raise
    except Exception as e:
        log(f"[UPLOAD] ❌ {type(e).__name__}: {e}")
        traceback.print_exc()
        sys.stderr.flush()
        raise HTTPException(status_code=500, detail=f"{type(e).__name__}: {str(e)}")


@router.get("")
async def api_list_documents():
    docs = list_documents()
    return {"documents": docs}


@router.get("/{document_id}")
async def api_get_document(document_id: int):
    doc = get_document(document_id)
    if not doc:
        raise HTTPException(status_code=404, detail="文档不存在")
    return doc


@router.delete("/{document_id}")
async def api_delete_document(document_id: int):
    doc = get_document(document_id)
    if not doc:
        raise HTTPException(status_code=404, detail="文档不存在")
    try:
        delete_document_chunks(document_id)
    except Exception as e:
        print(f"删除 Chroma 向量失败: {e}", flush=True)
    delete_document(document_id)
    return {"ok": True}
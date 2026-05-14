import os
import time
import json
from pathlib import Path
from typing import Any, Dict, List, Optional

try:
    from langchain_text_splitters import RecursiveCharacterTextSplitter
except ImportError:  # pragma: no cover - fallback for limited test env
    class RecursiveCharacterTextSplitter:  # type: ignore[override]
        def __init__(self, chunk_size: int = 600, chunk_overlap: int = 120):
            self.chunk_size = chunk_size
            self.chunk_overlap = chunk_overlap

        def split_text(self, content: str) -> List[str]:
            if not content:
                return []
            step = max(self.chunk_size - self.chunk_overlap, 1)
            return [content[index:index + self.chunk_size] for index in range(0, len(content), step)]

from core.knowledge.document_parser import parse_document
from core.utils.dataset_importer import parse_dataset_records
from core.knowledge.knowledge_store import KnowledgeStore


class KnowledgeService:
    def __init__(self, store: KnowledgeStore, upload_dir: str):
        self.store = store
        self.upload_dir = upload_dir
        self.vectorstore = None
        Path(upload_dir).mkdir(parents=True, exist_ok=True)
        self.splitter = RecursiveCharacterTextSplitter(chunk_size=600, chunk_overlap=120)

    def preview_content(self, content: str) -> Dict[str, Any]:
        chunks = self.splitter.split_text(content or "")
        if not chunks and content:
            chunks = [content]
        return {
            "chunks": chunks,
            "count": len(chunks),
            "used_structured_blocks": False,
        }

    def preview_file(self, file_path: str, source_type: str = "file") -> Dict[str, Any]:
        content = parse_document(file_path, source_type)
        preview = self.preview_content(content)
        preview["used_structured_blocks"] = Path(file_path).suffix.lower() == ".pdf"
        return preview

    def save_upload(self, upload_file, document_id: str) -> tuple[str, str]:
        original_name = upload_file.filename or f"{document_id}.txt"
        suffix = Path(original_name).suffix.lower()
        safe_name = f"{document_id}{suffix}"
        destination = Path(self.upload_dir) / safe_name
        upload_file.file.seek(0)
        with destination.open("wb") as target:
            target.write(upload_file.file.read())
        return original_name, str(destination)

    def create_text_document(self, *, topic: str, title: str, doc_type: str, content: str, created_by: str) -> Dict[str, Any]:
        document = self.store.create_document(
            topic=topic,
            title=title,
            doc_type=doc_type,
            source_type="text",
            content=content,
            created_by=created_by,
        )
        job = self.store.create_job(document["id"], "ingest", {"document_id": document["id"]}, created_by)
        return {"document": document, "job": job}

    def create_file_document(self, *, topic: str, title: str, doc_type: str, upload_file, created_by: str) -> Dict[str, Any]:
        document = self.store.create_document(
            topic=topic,
            title=title,
            doc_type=doc_type,
            source_type="file",
            content="",
            created_by=created_by,
        )
        file_name, file_path = self.save_upload(upload_file, document["id"])
        document = self.store.update_document(document["id"], file_name=file_name, file_path=file_path) or document
        job = self.store.create_job(document["id"], "ingest", {"document_id": document["id"]}, created_by)
        return {"document": document, "job": job}

    def import_dataset_records(self, records: List[Dict[str, Any]], *, created_by: str, source_name: str) -> Dict[str, Any]:
        documents_payload = parse_dataset_records(records, source_name=source_name)
        batch = self.store.create_import_batch(
            source_name=source_name,
            total_count=len(documents_payload),
            created_by=created_by,
        )
        created_documents: List[Dict[str, Any]] = []
        created_jobs: List[Dict[str, Any]] = []
        failures: List[Dict[str, Any]] = []

        for item in documents_payload:
            try:
                document = self.store.create_document(
                    topic=item["topic"],
                    title=item["title"],
                    doc_type=item["doc_type"],
                    source_type="text",
                    content=item["content"],
                    created_by=created_by,
                )
                job = self.store.create_job(
                    document["id"],
                    "ingest",
                    {"document_id": document["id"], "batch_id": batch["id"]},
                    created_by,
                    batch_id=batch["id"],
                )
                created_documents.append(document)
                created_jobs.append(job)
            except Exception as exc:
                failures.append(
                    {
                        "title": item.get("title", ""),
                        "error": str(exc),
                    }
                )

        return {
            "total": len(documents_payload),
            "success_count": len(created_documents),
            "failure_count": len(failures),
            "failures": failures,
            "batch": batch,
            "documents": created_documents,
            "jobs": created_jobs,
        }

    def import_dataset_file(self, file_path: str, *, created_by: str) -> Dict[str, Any]:
        with open(file_path, "r", encoding="utf-8") as handle:
            payload = json.load(handle)
        return self.import_dataset_records(payload, created_by=created_by, source_name=Path(file_path).name)

    def update_document(self, document_id: str, *, topic: str, title: str, doc_type: str, content: str, created_by: str) -> Dict[str, Any]:
        document = self.store.update_document(
            document_id,
            topic=topic,
            title=title,
            doc_type=doc_type,
            content=content,
            status="pending",
            error_message=None,
        )
        if document is None:
            raise ValueError("知识库文档不存在")
        job = self.store.create_job(document_id, "reindex", {"document_id": document_id}, created_by)
        return {"document": document, "job": job}

    def delete_document(self, vectorstore, document_id: str) -> None:
        document = self.store.get_document(document_id)
        if not document:
            return
        self.delete_vectors(vectorstore, document_id)
        file_path = document.get("file_path")
        if file_path and os.path.exists(file_path):
            os.remove(file_path)
        self.store.delete_document(document_id)

    def delete_vectors(self, vectorstore, document_id: str) -> None:
        if vectorstore is None:
            return
        try:
            vectorstore.delete(where={"document_id": document_id})
        except TypeError:
            collection = vectorstore._collection
            ids = collection.get(where={"document_id": document_id}).get("ids", [])
            if ids:
                collection.delete(ids=ids)

    def ingest_document(self, vectorstore, document_id: str) -> Dict[str, Any]:
        document = self.store.get_document(document_id)
        if not document:
            raise ValueError("知识库文档不存在")

        if document["source_type"] == "file":
            content = parse_document(document["file_path"], document["source_type"])
        else:
            content = document.get("content") or ""

        if not content.strip():
            raise ValueError("文档内容为空，无法入库")

        chunks = self.splitter.split_text(content)
        if not chunks:
            chunks = [content]

        self.delete_vectors(vectorstore, document_id)
        if vectorstore is not None:
            metadatas: List[Dict[str, Any]] = []
            ids: List[str] = []
            for index, chunk in enumerate(chunks):
                metadatas.append(
                    {
                        "document_id": document_id,
                        "topic": document["topic"],
                        "title": document["title"],
                        "type": document["doc_type"],
                        "source": document["source_type"],
                        "chunk_index": index,
                    }
                )
                ids.append(f"{document_id}:{index}")
            vectorstore.add_texts(chunks, metadatas=metadatas, ids=ids)

        return self.store.update_document(
            document_id,
            content=content,
            status="success",
            chunk_count=len(chunks),
            error_message=None,
            last_ingested_at=int(time.time()),
        ) or document

    def sync_existing_documents(self, vectorstore) -> int:
        if vectorstore is None:
            return 0

        collection = getattr(vectorstore, '_collection', None)
        if collection is None:
            return 0

        snapshot = collection.get()
        raw_ids = snapshot.get('ids') or []
        metadatas = snapshot.get('metadatas') or []
        documents_by_id: Dict[str, Dict[str, Any]] = {}

        for index, metadata in enumerate(metadatas):
            if not metadata:
                continue
            raw_id = raw_ids[index] if index < len(raw_ids) else ''
            document_id = str(metadata.get('document_id') or metadata.get('id') or raw_id).strip()
            if not document_id:
                continue

            existing = self.store.get_document(document_id)
            if existing:
                if document_id in documents_by_id:
                    documents_by_id[document_id]['chunk_count'] += 1
                continue

            if document_id in documents_by_id:
                documents_by_id[document_id]['chunk_count'] += 1
                continue

            documents_by_id[document_id] = {
                'id': document_id,
                'topic': str(metadata.get('topic') or 'legacy'),
                'title': str(metadata.get('title') or document_id),
                'doc_type': str(metadata.get('type') or 'legacy'),
                'source_type': str(metadata.get('source') or 'text'),
                'content': '',
                'created_by': 'system',
                'chunk_count': 1,
                'status': 'success',
            }

        imported = 0
        for payload in documents_by_id.values():
            document = self.store.create_document(
                topic=payload['topic'],
                title=payload['title'],
                doc_type=payload['doc_type'],
                source_type=payload['source_type'],
                content=payload['content'],
                created_by=payload['created_by'],
                status=payload['status'],
                document_id=payload['id'],
            )
            self.store.update_document(
                document['id'],
                chunk_count=payload['chunk_count'],
                error_message=None,
                last_ingested_at=int(time.time()),
            )
            imported += 1

        return imported

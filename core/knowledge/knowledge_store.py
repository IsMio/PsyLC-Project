import json
import sqlite3
import time
import uuid
from typing import Any, Dict, List, Optional, Tuple


def _row_to_dict(row: Optional[sqlite3.Row]) -> Optional[Dict[str, Any]]:
    if row is None:
        return None
    return {key: row[key] for key in row.keys()}


class KnowledgeStore:
    def __init__(self, db_path: str):
        self.db_path = db_path
        self._init_db()

    def _connect(self) -> sqlite3.Connection:
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn

    def _init_db(self) -> None:
        with self._connect() as conn:
            cursor = conn.cursor()
            cursor.execute(
                '''
                CREATE TABLE IF NOT EXISTS knowledge_documents (
                    id TEXT PRIMARY KEY,
                    topic TEXT NOT NULL,
                    title TEXT NOT NULL,
                    doc_type TEXT NOT NULL,
                    source_type TEXT NOT NULL,
                    content TEXT,
                    file_name TEXT,
                    file_path TEXT,
                    status TEXT NOT NULL,
                    chunk_count INTEGER NOT NULL DEFAULT 0,
                    error_message TEXT,
                    created_by TEXT,
                    created_at INTEGER NOT NULL,
                    updated_at INTEGER NOT NULL,
                    last_ingested_at INTEGER
                )
                '''
            )
            cursor.execute(
                '''
                CREATE TABLE IF NOT EXISTS knowledge_import_batches (
                    id TEXT PRIMARY KEY,
                    source_name TEXT NOT NULL,
                    total_count INTEGER NOT NULL,
                    completed_count INTEGER NOT NULL DEFAULT 0,
                    success_count INTEGER NOT NULL DEFAULT 0,
                    failed_count INTEGER NOT NULL DEFAULT 0,
                    status TEXT NOT NULL,
                    created_by TEXT,
                    created_at INTEGER NOT NULL,
                    updated_at INTEGER NOT NULL
                )
                '''
            )
            cursor.execute(
                '''
                CREATE TABLE IF NOT EXISTS knowledge_jobs (
                    id TEXT PRIMARY KEY,
                    document_id TEXT NOT NULL,
                    batch_id TEXT,
                    job_type TEXT NOT NULL,
                    status TEXT NOT NULL,
                    payload_json TEXT,
                    error_message TEXT,
                    created_by TEXT,
                    created_at INTEGER NOT NULL,
                    started_at INTEGER,
                    finished_at INTEGER,
                    FOREIGN KEY(document_id) REFERENCES knowledge_documents(id) ON DELETE CASCADE
                )
                '''
            )
            cursor.execute(
                "CREATE INDEX IF NOT EXISTS idx_knowledge_documents_status ON knowledge_documents(status)"
            )
            cursor.execute(
                "CREATE INDEX IF NOT EXISTS idx_knowledge_jobs_document_id ON knowledge_jobs(document_id)"
            )
            columns = [row[1] for row in cursor.execute("PRAGMA table_info(knowledge_jobs)").fetchall()]
            if "batch_id" not in columns:
                cursor.execute("ALTER TABLE knowledge_jobs ADD COLUMN batch_id TEXT")
            cursor.execute(
                "CREATE INDEX IF NOT EXISTS idx_knowledge_jobs_batch_id ON knowledge_jobs(batch_id)"
            )
            cursor.execute(
                "CREATE INDEX IF NOT EXISTS idx_knowledge_import_batches_created_at ON knowledge_import_batches(created_at)"
            )

    def create_document(
        self,
        *,
        topic: str,
        title: str,
        doc_type: str,
        source_type: str,
        content: str,
        created_by: str,
        file_name: Optional[str] = None,
        file_path: Optional[str] = None,
        status: str = "pending",
        document_id: Optional[str] = None,
    ) -> Dict[str, Any]:
        now = int(time.time())
        document_id = document_id or str(uuid.uuid4())
        with self._connect() as conn:
            conn.execute(
                '''
                INSERT INTO knowledge_documents (
                    id, topic, title, doc_type, source_type, content, file_name, file_path,
                    status, chunk_count, error_message, created_by, created_at, updated_at, last_ingested_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, 0, NULL, ?, ?, ?, NULL)
                ''',
                (
                    document_id,
                    topic,
                    title,
                    doc_type,
                    source_type,
                    content,
                    file_name,
                    file_path,
                    status,
                    created_by,
                    now,
                    now,
                ),
            )
        return self.get_document(document_id) or {}

    def update_document(self, document_id: str, **fields: Any) -> Optional[Dict[str, Any]]:
        if not fields:
            return self.get_document(document_id)

        allowed = {
            "topic",
            "title",
            "doc_type",
            "source_type",
            "content",
            "file_name",
            "file_path",
            "status",
            "chunk_count",
            "error_message",
            "last_ingested_at",
        }
        assignments = []
        values: List[Any] = []
        for key, value in fields.items():
            if key in allowed:
                assignments.append(f"{key} = ?")
                values.append(value)
        assignments.append("updated_at = ?")
        values.append(int(time.time()))
        values.append(document_id)

        with self._connect() as conn:
            conn.execute(
                f"UPDATE knowledge_documents SET {', '.join(assignments)} WHERE id = ?",
                tuple(values),
            )
        return self.get_document(document_id)

    def get_document(self, document_id: str) -> Optional[Dict[str, Any]]:
        with self._connect() as conn:
            row = conn.execute(
                "SELECT * FROM knowledge_documents WHERE id = ?",
                (document_id,),
            ).fetchone()
        return _row_to_dict(row)

    def list_documents(
        self,
        *,
        page_num: int = 1,
        page_size: int = 25,
        keyword: str = "",
        status: Optional[str] = None,
    ) -> Tuple[List[Dict[str, Any]], int]:
        clauses = []
        values: List[Any] = []
        if keyword:
            clauses.append("(title LIKE ? OR content LIKE ? OR topic LIKE ?)")
            fuzzy = f"%{keyword}%"
            values.extend([fuzzy, fuzzy, fuzzy])
        if status:
            clauses.append("status = ?")
            values.append(status)
        where_sql = f"WHERE {' AND '.join(clauses)}" if clauses else ""
        offset = max(page_num - 1, 0) * page_size

        with self._connect() as conn:
            total = conn.execute(
                f"SELECT COUNT(*) FROM knowledge_documents {where_sql}",
                tuple(values),
            ).fetchone()[0]
            rows = conn.execute(
                f'''
                SELECT * FROM knowledge_documents
                {where_sql}
                ORDER BY updated_at DESC, created_at DESC
                LIMIT ? OFFSET ?
                ''',
                tuple(values + [page_size, offset]),
            ).fetchall()
        return [_row_to_dict(row) or {} for row in rows], total

    def delete_document(self, document_id: str) -> None:
        with self._connect() as conn:
            conn.execute("DELETE FROM knowledge_jobs WHERE document_id = ?", (document_id,))
            conn.execute("DELETE FROM knowledge_documents WHERE id = ?", (document_id,))

    def create_job(
        self,
        document_id: str,
        job_type: str,
        payload: Dict[str, Any],
        created_by: str,
        status: str = "pending",
        batch_id: Optional[str] = None,
    ) -> Dict[str, Any]:
        job_id = str(uuid.uuid4())
        now = int(time.time())
        with self._connect() as conn:
            conn.execute(
                '''
                INSERT INTO knowledge_jobs (
                    id, document_id, batch_id, job_type, status, payload_json, error_message,
                    created_by, created_at, started_at, finished_at
                ) VALUES (?, ?, ?, ?, ?, ?, NULL, ?, ?, NULL, NULL)
                ''',
                (job_id, document_id, batch_id, job_type, status, json.dumps(payload), created_by, now),
            )
        return self.get_job(job_id) or {}

    def create_import_batch(self, *, source_name: str, total_count: int, created_by: str) -> Dict[str, Any]:
        batch_id = str(uuid.uuid4())
        now = int(time.time())
        with self._connect() as conn:
            conn.execute(
                '''
                INSERT INTO knowledge_import_batches (
                    id, source_name, total_count, completed_count, success_count, failed_count,
                    status, created_by, created_at, updated_at
                ) VALUES (?, ?, ?, 0, 0, 0, 'processing', ?, ?, ?)
                ''',
                (batch_id, source_name, total_count, created_by, now, now),
            )
        return self.get_import_batch(batch_id) or {}

    def get_import_batch(self, batch_id: str) -> Optional[Dict[str, Any]]:
        with self._connect() as conn:
            row = conn.execute("SELECT * FROM knowledge_import_batches WHERE id = ?", (batch_id,)).fetchone()
        return _row_to_dict(row)

    def list_import_batches(self, *, page_num: int = 1, page_size: int = 25) -> Tuple[List[Dict[str, Any]], int]:
        offset = max(page_num - 1, 0) * page_size
        with self._connect() as conn:
            total = conn.execute("SELECT COUNT(*) FROM knowledge_import_batches").fetchone()[0]
            rows = conn.execute(
                '''
                SELECT * FROM knowledge_import_batches
                ORDER BY created_at DESC
                LIMIT ? OFFSET ?
                ''',
                (page_size, offset),
            ).fetchall()
        return [_row_to_dict(row) or {} for row in rows], total

    def get_job(self, job_id: str) -> Optional[Dict[str, Any]]:
        with self._connect() as conn:
            row = conn.execute("SELECT * FROM knowledge_jobs WHERE id = ?", (job_id,)).fetchone()
        job = _row_to_dict(row)
        if job and job.get("payload_json"):
            job["payload"] = json.loads(job["payload_json"])
        return job

    def list_jobs(
        self,
        *,
        document_id: Optional[str] = None,
        batch_id: Optional[str] = None,
        page_num: int = 1,
        page_size: int = 25,
    ) -> Tuple[List[Dict[str, Any]], int]:
        clauses = []
        values: List[Any] = []
        if document_id:
            clauses.append("document_id = ?")
            values.append(document_id)
        if batch_id:
            clauses.append("batch_id = ?")
            values.append(batch_id)
        where_sql = f"WHERE {' AND '.join(clauses)}" if clauses else ""
        offset = max(page_num - 1, 0) * page_size
        with self._connect() as conn:
            total = conn.execute(
                f"SELECT COUNT(*) FROM knowledge_jobs {where_sql}",
                tuple(values),
            ).fetchone()[0]
            rows = conn.execute(
                f'''
                SELECT * FROM knowledge_jobs
                {where_sql}
                ORDER BY created_at DESC
                LIMIT ? OFFSET ?
                ''',
                tuple(values + [page_size, offset]),
            ).fetchall()
        jobs = []
        for row in rows:
            job = _row_to_dict(row) or {}
            if job.get("payload_json"):
                job["payload"] = json.loads(job["payload_json"])
            jobs.append(job)
        return jobs, total

    def mark_job_running(self, job_id: str) -> None:
        now = int(time.time())
        with self._connect() as conn:
            conn.execute(
                "UPDATE knowledge_jobs SET status = 'processing', started_at = ?, error_message = NULL WHERE id = ?",
                (now, job_id),
            )

    def mark_job_finished(self, job_id: str, status: str, error_message: Optional[str] = None) -> None:
        now = int(time.time())
        with self._connect() as conn:
            conn.execute(
                "UPDATE knowledge_jobs SET status = ?, error_message = ?, finished_at = ? WHERE id = ?",
                (status, error_message, now, job_id),
            )

    def update_batch_progress(self, batch_id: str) -> Optional[Dict[str, Any]]:
        with self._connect() as conn:
            stats = conn.execute(
                '''
                SELECT
                    COUNT(*) AS total_jobs,
                    SUM(CASE WHEN status IN ('success', 'failed') THEN 1 ELSE 0 END) AS completed_count,
                    SUM(CASE WHEN status = 'success' THEN 1 ELSE 0 END) AS success_count,
                    SUM(CASE WHEN status = 'failed' THEN 1 ELSE 0 END) AS failed_count
                FROM knowledge_jobs
                WHERE batch_id = ?
                ''',
                (batch_id,),
            ).fetchone()
            batch = conn.execute(
                "SELECT total_count FROM knowledge_import_batches WHERE id = ?",
                (batch_id,),
            ).fetchone()
            if batch is None:
                return None

            completed_count = int((stats["completed_count"] or 0) if stats else 0)
            success_count = int((stats["success_count"] or 0) if stats else 0)
            failed_count = int((stats["failed_count"] or 0) if stats else 0)
            total_count = int(batch["total_count"])
            status = "finished" if completed_count >= total_count else "processing"
            conn.execute(
                '''
                UPDATE knowledge_import_batches
                SET completed_count = ?, success_count = ?, failed_count = ?, status = ?, updated_at = ?
                WHERE id = ?
                ''',
                (completed_count, success_count, failed_count, status, int(time.time()), batch_id),
            )
        return self.get_import_batch(batch_id)

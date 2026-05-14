import asyncio
from typing import Optional


class KnowledgeIngestionQueue:
    def __init__(self, store, service):
        self.store = store
        self.service = service
        self.queue: asyncio.Queue[str] = asyncio.Queue()
        self.worker_task: Optional[asyncio.Task] = None
        self._running = False

    async def start(self):
        if self.worker_task and not self.worker_task.done():
            return
        self._running = True
        self.worker_task = asyncio.create_task(self._worker())

    async def stop(self):
        self._running = False
        if self.worker_task:
            self.worker_task.cancel()
            try:
                await self.worker_task
            except asyncio.CancelledError:
                pass

    async def submit(self, job_id: str):
        await self.queue.put(job_id)

    async def submit_many(self, job_ids, batch_size: int = 3, interval_seconds: float = 1.0, sleep_func=None):
        sleeper = sleep_func or asyncio.sleep
        submitted = 0
        for index, job_id in enumerate(job_ids, start=1):
            await self.submit(job_id)
            submitted += 1
            if submitted % batch_size == 0 and index < len(job_ids):
                await sleeper(interval_seconds)

    async def _worker(self):
        while self._running:
            job_id = await self.queue.get()
            try:
                await self._process(job_id)
            finally:
                self.queue.task_done()

    async def _process(self, job_id: str):
        job = self.store.get_job(job_id)
        if not job:
            return

        batch_id = job.get("batch_id")

        self.store.mark_job_running(job_id)
        document_id = job["document_id"]
        self.store.update_document(document_id, status="processing", error_message=None)

        try:
            self.service.ingest_document(self.service.vectorstore, document_id)
            self.store.mark_job_finished(job_id, "success")
            if batch_id:
                self.store.update_batch_progress(batch_id)
        except Exception as exc:
            error_message = str(exc)
            self.store.update_document(document_id, status="failed", error_message=error_message)
            self.store.mark_job_finished(job_id, "failed", error_message)
            if batch_id:
                self.store.update_batch_progress(batch_id)

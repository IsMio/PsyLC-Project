from typing import Any, Dict, Optional
import json
import os
import tempfile

from fastapi import APIRouter, Depends, File, Form, HTTPException, Request, UploadFile
from pydantic import BaseModel

import type
from api.v1.auth import get_db, require_admin
from config import Config
from core.admin.admin_metrics import get_model_usage, get_model_usage_detail, get_system_status
from core.admin.config_service import ConfigService
from core.admin.admin_security import parse_roles, serialize_roles
from core.admin.system_control import ProcessRestarter, SystemControlService


router = APIRouter(prefix="/admin", tags=["admin"])


class KnowledgeTextCreateDTO(BaseModel):
    topic: str
    title: str
    type: str
    content: str


class KnowledgeUpdateDTO(BaseModel):
    topic: str
    title: str
    type: str
    content: str


class UserUpdateDTO(BaseModel):
    userId: str
    display_name: str
    roles: list[str]
    avatar: str = ""


class OutputFilterPolicyDTO(BaseModel):
    enabled: bool
    review_enabled: bool
    rules: list[dict]
    templates: dict[str, str]


class SystemConfigDTO(BaseModel):
    config: dict


def _store(request: Request):
    store = getattr(request.app.state, "knowledge_store", None)
    if store is None:
        raise HTTPException(status_code=500, detail="知识库存储未初始化")
    return store


def _service(request: Request):
    service = getattr(request.app.state, "knowledge_service", None)
    if service is None:
        raise HTTPException(status_code=500, detail="知识库服务未初始化")
    return service


def _queue(request: Request):
    queue = getattr(request.app.state, "knowledge_queue", None)
    if queue is None:
        raise HTTPException(status_code=500, detail="知识库队列未初始化")
    return queue


def _vectorstore(request: Request):
    return getattr(request.app.state, "vectorstore", None)


def _output_policy_store(request: Request):
    store = getattr(request.app.state, "output_policy_store", None)
    if store is None:
        raise HTTPException(status_code=500, detail="输出过滤策略存储未初始化")
    return store


def _config_service() -> ConfigService:
    return ConfigService('data/config.yaml')


def _sync_existing_documents(request: Request) -> None:
    service = _service(request)
    service.sync_existing_documents(_vectorstore(request))


@router.get("/health")
async def health(_: Dict[str, Any] = Depends(require_admin)):
    return type.standard_response(msg="管理员API正常运行")


@router.get("/system/status")
async def system_status(request: Request, _: Dict[str, Any] = Depends(require_admin)):
    start_time = getattr(request.app.state, "start_time", 0)
    return type.standard_response(data=get_system_status(start_time))


@router.get("/model/usage")
async def model_usage(_: Dict[str, Any] = Depends(require_admin)):
    return type.standard_response(data=get_model_usage(Config.DB_PATH))


@router.get("/model/usage/detail")
async def model_usage_detail(days: int = 7, _: Dict[str, Any] = Depends(require_admin)):
    return type.standard_response(data=get_model_usage_detail(Config.DB_PATH, days))


@router.get("/output-filter/policy")
async def get_output_filter_policy(request: Request, _: Dict[str, Any] = Depends(require_admin)):
    return type.standard_response(data=_output_policy_store(request).get_policy())


@router.put("/output-filter/policy")
async def update_output_filter_policy(payload: OutputFilterPolicyDTO, request: Request, current_user: Dict[str, Any] = Depends(require_admin)):
    policy = _output_policy_store(request).upsert_policy(
        enabled=payload.enabled,
        review_enabled=payload.review_enabled,
        rules=payload.rules,
        templates=payload.templates,
        updated_by=current_user.get('userId', 'system'),
    )
    return type.standard_response(data=policy, msg="输出过滤策略已更新")


@router.get('/system/config')
async def get_system_config(_: Dict[str, Any] = Depends(require_admin)):
    return type.standard_response(data=_config_service().get_editable_config())


@router.put('/system/config')
async def update_system_config(payload: SystemConfigDTO, _: Dict[str, Any] = Depends(require_admin)):
    updated = _config_service().update_editable_config(payload.config)
    return type.standard_response(data=updated, msg='系统配置已更新')


@router.post('/system/restart')
async def restart_system(_: Dict[str, Any] = Depends(require_admin)):
    result = SystemControlService(restarter=ProcessRestarter(main_script='main.py').restart).request_restart()
    return type.standard_response(data=result, msg='重启请求已记录，请尽快按确认流程重启服务')


@router.post('/system/mineru/preview')
async def preview_mineru_chunks(
    request: Request,
    file: UploadFile = File(...),
    _: Dict[str, Any] = Depends(require_admin),
):
    suffix = os.path.splitext(file.filename or '')[1]
    temp_file = tempfile.NamedTemporaryFile(delete=False, suffix=suffix)
    try:
        file.file.seek(0)
        temp_file.write(file.file.read())
        temp_file.close()
        preview = _service(request).preview_file(temp_file.name)
        return type.standard_response(data=preview)
    finally:
        try:
            os.remove(temp_file.name)
        except OSError:
            pass


@router.get("/user/list")
async def user_list(
    pageNum: int = 1,
    pageSize: int = 25,
    keyword: str = "",
    _: Dict[str, Any] = Depends(require_admin),
):
    conn = get_db()
    cursor = conn.cursor()
    values = []
    where_sql = ""
    if keyword:
        where_sql = "WHERE username LIKE ? OR display_name LIKE ?"
        fuzzy = f"%{keyword}%"
        values.extend([fuzzy, fuzzy])
    total = cursor.execute(f"SELECT COUNT(*) FROM users {where_sql}", values).fetchone()[0]
    offset = max(pageNum - 1, 0) * pageSize
    rows = cursor.execute(
        f"SELECT * FROM users {where_sql} ORDER BY created_at DESC LIMIT ? OFFSET ?",
        [*values, pageSize, offset],
    ).fetchall()
    conn.close()
    users = [
        {
            "id": row["id"],
            "username": row["username"],
            "display_name": row["display_name"],
            "roles": parse_roles(row["roles"]),
            "avatar": row["avatar"],
            "created_at": row["created_at"],
        }
        for row in rows
    ]
    return type.standard_response(data={"rows": users, "total": total})


@router.put("/user")
async def update_user(payload: UserUpdateDTO, current_user: Dict[str, Any] = Depends(require_admin)):
    if payload.userId == current_user.get("userId") and "admin" not in payload.roles:
        raise HTTPException(status_code=400, detail="不能移除当前管理员自己的 admin 角色")
    conn = get_db()
    conn.execute(
        "UPDATE users SET display_name = ?, roles = ?, avatar = ? WHERE id = ?",
        (payload.display_name, serialize_roles(payload.roles), payload.avatar, payload.userId),
    )
    conn.commit()
    conn.close()
    return type.standard_response(msg="更新成功")


@router.delete("/user/{ids}")
async def delete_user(ids: str, current_user: Dict[str, Any] = Depends(require_admin)):
    id_list = [item.strip() for item in ids.split(",") if item.strip()]
    if current_user.get("userId") in id_list:
        raise HTTPException(status_code=400, detail="不能删除当前登录管理员")
    conn = get_db()
    conn.executemany("DELETE FROM users WHERE id = ?", [(user_id,) for user_id in id_list])
    conn.commit()
    conn.close()
    return type.standard_response(msg="删除成功")


@router.get("/knowledge-base/list")
async def knowledge_list(
    request: Request,
    pageNum: int = 1,
    pageSize: int = 25,
    keyword: str = "",
    status: Optional[str] = None,
    _: Dict[str, Any] = Depends(require_admin),
):
    _sync_existing_documents(request)
    rows, total = _store(request).list_documents(page_num=pageNum, page_size=pageSize, keyword=keyword, status=status)
    return type.standard_response(data={"rows": rows, "total": total})


@router.post("/knowledge-base/text")
async def create_knowledge_text(payload: KnowledgeTextCreateDTO, request: Request, current_user: Dict[str, Any] = Depends(require_admin)):
    result = _service(request).create_text_document(
        topic=payload.topic,
        title=payload.title,
        doc_type=payload.type,
        content=payload.content,
        created_by=current_user["userId"],
    )
    await _queue(request).submit(result["job"]["id"])
    return type.standard_response(data=result)


@router.post("/knowledge-base/file")
async def create_knowledge_file(
    request: Request,
    topic: str = Form(...),
    title: str = Form(...),
    type_name: str = Form(..., alias="type"),
    file: UploadFile = File(...),
    current_user: Dict[str, Any] = Depends(require_admin),
):
    result = _service(request).create_file_document(
        topic=topic,
        title=title,
        doc_type=type_name,
        upload_file=file,
        created_by=current_user["userId"],
    )
    await _queue(request).submit(result["job"]["id"])
    return type.standard_response(data=result)


@router.post("/knowledge-base/dataset")
async def import_knowledge_dataset(
    request: Request,
    file: Optional[UploadFile] = File(None),
    file_path: Optional[str] = Form(None),
    current_user: Dict[str, Any] = Depends(require_admin),
):
    if file is None and not (file_path or "").strip():
        raise HTTPException(status_code=400, detail="必须提供上传文件或本地文件路径")

    service = _service(request)
    if file is not None:
        try:
            file.file.seek(0)
            payload = json.loads(file.file.read().decode("utf-8"))
        except json.JSONDecodeError as exc:
            raise HTTPException(status_code=400, detail="上传的数据集不是合法的 JSON") from exc
        result = service.import_dataset_records(
            payload,
            created_by=current_user["userId"],
            source_name=file.filename or "dataset.json",
        )
    else:
        normalized_path = os.path.abspath((file_path or "").strip())
        if not os.path.exists(normalized_path):
            raise HTTPException(status_code=404, detail="本地数据集文件不存在")
        try:
            result = service.import_dataset_file(normalized_path, created_by=current_user["userId"])
        except json.JSONDecodeError as exc:
            raise HTTPException(status_code=400, detail="本地数据集不是合法的 JSON") from exc

    queue = _queue(request)
    await queue.submit_many([job["id"] for job in result["jobs"]], batch_size=3, interval_seconds=1.0)
    return type.standard_response(data=result, msg="数据集导入任务已创建")


@router.get("/knowledge-base/batches")
async def knowledge_batches(
    request: Request,
    pageNum: int = 1,
    pageSize: int = 25,
    _: Dict[str, Any] = Depends(require_admin),
):
    rows, total = _store(request).list_import_batches(page_num=pageNum, page_size=pageSize)
    return type.standard_response(data={"rows": rows, "total": total})


@router.get("/knowledge-base/batches/{batch_id}")
async def knowledge_batch_detail(batch_id: str, request: Request, _: Dict[str, Any] = Depends(require_admin)):
    batch = _store(request).get_import_batch(batch_id)
    if not batch:
        raise HTTPException(status_code=404, detail="导入批次不存在")
    rows, total = _store(request).list_jobs(batch_id=batch_id, page_num=1, page_size=100)
    return type.standard_response(data={"batch": batch, "jobs": rows, "total": total})


@router.get("/knowledge-base/{document_id}")
async def knowledge_detail(document_id: str, request: Request, _: Dict[str, Any] = Depends(require_admin)):
    _sync_existing_documents(request)
    document = _store(request).get_document(document_id)
    if not document:
        raise HTTPException(status_code=404, detail="知识库文档不存在")
    return type.standard_response(data=document)


@router.put("/knowledge-base/{document_id}")
async def update_knowledge(document_id: str, payload: KnowledgeUpdateDTO, request: Request, current_user: Dict[str, Any] = Depends(require_admin)):
    result = _service(request).update_document(
        document_id,
        topic=payload.topic,
        title=payload.title,
        doc_type=payload.type,
        content=payload.content,
        created_by=current_user["userId"],
    )
    await _queue(request).submit(result["job"]["id"])
    return type.standard_response(data=result, msg="更新成功")


@router.delete("/knowledge-base/{document_id}")
async def delete_knowledge(document_id: str, request: Request, _: Dict[str, Any] = Depends(require_admin)):
    _service(request).delete_document(_vectorstore(request), document_id)
    return type.standard_response(msg="删除成功")


@router.get("/knowledge-base/jobs")
async def knowledge_jobs(
    request: Request,
    pageNum: int = 1,
    pageSize: int = 25,
    documentId: Optional[str] = None,
    batchId: Optional[str] = None,
    _: Dict[str, Any] = Depends(require_admin),
):
    rows, total = _store(request).list_jobs(document_id=documentId, batch_id=batchId, page_num=pageNum, page_size=pageSize)
    return type.standard_response(data={"rows": rows, "total": total})


@router.post("/knowledge-base/jobs/{job_id}/retry")
async def retry_job(job_id: str, request: Request, _: Dict[str, Any] = Depends(require_admin)):
    job = _store(request).get_job(job_id)
    if not job:
        raise HTTPException(status_code=404, detail="任务不存在")
    retried = _store(request).create_job(
        job["document_id"],
        job["job_type"],
        job.get("payload") or {},
        job.get("created_by") or "system",
        batch_id=job.get("batch_id"),
    )
    await _queue(request).submit(retried["id"])
    if job.get("batch_id"):
        _store(request).update_batch_progress(job["batch_id"])
    return type.standard_response(data=retried, msg="任务已重新入队")

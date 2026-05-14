import json
from pathlib import Path
from typing import Any, Dict, List


ROLE_LABELS = {
    "user": "用户",
    "assistant": "助手",
}


def format_conversation_text(messages: List[Dict[str, Any]]) -> str:
    lines: List[str] = []
    for message in messages or []:
        role = str(message.get("role") or "").strip().lower()
        content = str(message.get("content") or "").strip()
        if not content or role not in ROLE_LABELS:
            continue
        lines.append(f"{ROLE_LABELS[role]}: {content}")
    return "\n\n".join(lines)


def parse_dataset_records(payload: Any, source_name: str = "dataset.json") -> List[Dict[str, Any]]:
    if not isinstance(payload, list):
        raise ValueError("数据集顶层必须是数组")

    documents: List[Dict[str, Any]] = []
    base_name = Path(source_name).stem or "dataset"
    for index, record in enumerate(payload, start=1):
        if not isinstance(record, dict):
            continue
        content = format_conversation_text(record.get("messages") or [])
        if not content:
            continue
        record_id = record.get("id", index)
        topic = str(record.get("normalizedTag") or "dataset").strip() or "dataset"
        documents.append(
            {
                "title": f"{base_name}-{record_id}",
                "topic": topic,
                "doc_type": "dataset-conversation",
                "content": content,
                "metadata": {
                    "source_name": source_name,
                    "record_id": record_id,
                    "message_count": len(record.get("messages") or []),
                },
            }
        )
    return documents


def load_dataset_file(file_path: str) -> List[Dict[str, Any]]:
    with open(file_path, "r", encoding="utf-8") as handle:
        payload = json.load(handle)
    return parse_dataset_records(payload, source_name=Path(file_path).name)

import math
import os
import sqlite3
import time
from datetime import datetime, timedelta
from typing import Any, Dict, List

from api.v1.auth import redis_client, token_store


def _safe_memory_metrics() -> Dict[str, float]:
    try:
        import psutil  # type: ignore

        memory = psutil.virtual_memory()
        return {
            "memory_usage": round(memory.used / (1024 * 1024), 2),
            "memory_total": round(memory.total / (1024 * 1024), 2),
            "memory_percent": round(memory.percent, 2),
        }
    except Exception:
        if os.name == "posix":
            try:
                page_size = os.sysconf("SC_PAGE_SIZE")
                phys_pages = os.sysconf("SC_PHYS_PAGES")
                avail_pages = os.sysconf("SC_AVPHYS_PAGES")
                total = page_size * phys_pages
                available = page_size * avail_pages
                used = max(total - available, 0)
                percent = (used / total * 100) if total else 0
                return {
                    "memory_usage": round(used / (1024 * 1024), 2),
                    "memory_total": round(total / (1024 * 1024), 2),
                    "memory_percent": round(percent, 2),
                }
            except Exception:
                pass
        return {"memory_usage": 0.0, "memory_total": 0.0, "memory_percent": 0.0}


def get_online_user_count() -> int:
    if redis_client:
        try:
            count = 0
            for key in redis_client.scan_iter(match="token:*"):
                ttl = redis_client.ttl(key)
                if ttl is None or ttl > 0:
                    count += 1
            return count
        except Exception:
            pass

    now = time.time()
    return sum(1 for token in token_store.values() if token.get("exp", 0) >= now)


def get_system_status(start_time: float) -> Dict[str, Any]:
    memory = _safe_memory_metrics()
    return {
        "online_users": get_online_user_count(),
        "uptime": max(int(time.time() - start_time), 0),
        **memory,
    }


def get_model_usage(db_path: str) -> Dict[str, Any]:
    with sqlite3.connect(db_path) as conn:
        cursor = conn.cursor()
        total_tokens = cursor.execute(
            "SELECT COALESCE(SUM(token_count), 0) FROM chat_messages"
        ).fetchone()[0]
        total_requests = cursor.execute(
            "SELECT COUNT(*) FROM chat_messages WHERE role = 'assistant'"
        ).fetchone()[0]

        since = int((datetime.now() - timedelta(days=1)).timestamp())
        today_tokens = cursor.execute(
            "SELECT COALESCE(SUM(token_count), 0) FROM chat_messages WHERE created_at >= ?",
            (since,),
        ).fetchone()[0]
        today_requests = cursor.execute(
            "SELECT COUNT(*) FROM chat_messages WHERE role = 'assistant' AND created_at >= ?",
            (since,),
        ).fetchone()[0]

    return {
        "total_tokens": int(total_tokens or 0),
        "total_requests": int(total_requests or 0),
        "today_tokens": int(today_tokens or 0),
        "today_requests": int(today_requests or 0),
    }


def get_model_usage_detail(db_path: str, days: int = 7) -> List[Dict[str, Any]]:
    days = max(1, min(days, 365))
    with sqlite3.connect(db_path) as conn:
        cursor = conn.cursor()
        rows = cursor.execute(
            """
            SELECT date(datetime(created_at, 'unixepoch', 'localtime')) AS day,
                   COALESCE(SUM(token_count), 0) AS tokens,
                   COUNT(CASE WHEN role = 'assistant' THEN 1 END) AS requests
            FROM chat_messages
            WHERE created_at >= ?
            GROUP BY day
            ORDER BY day ASC
            """,
            (int((datetime.now() - timedelta(days=days - 1)).timestamp()),),
        ).fetchall()

    rows_by_day = {row[0]: {"tokens": int(row[1] or 0), "requests": int(row[2] or 0)} for row in rows}
    result = []
    for index in range(days):
        day = (datetime.now() - timedelta(days=days - index - 1)).strftime("%Y-%m-%d")
        payload = rows_by_day.get(day, {"tokens": 0, "requests": 0})
        result.append({"date": day, **payload})
    return result

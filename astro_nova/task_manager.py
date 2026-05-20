"""Task notification manager — 后台任务完成通知

用于跨页面通知：笔记生成、Digest、制图、写作、PPT 等耗时操作
完成后，无论用户当前在哪个页面，都能收到红点/数字提醒。
"""
import uuid
from datetime import datetime
from typing import Optional

_notifications: list[dict] = []
_MAX = 100


def add_notification(
    task_type: str,
    title: str,
    description: str,
    source_route: str,
) -> str:
    """添加一条任务完成通知"""
    notif = {
        "id": uuid.uuid4().hex[:8],
        "task_type": task_type,
        "title": title,
        "description": description,
        "source_route": source_route,
        "is_read": False,
        "created_at": datetime.now().isoformat(),
    }
    _notifications.append(notif)
    if len(_notifications) > _MAX:
        _notifications[:] = _notifications[-_MAX:]
    return notif["id"]


def get_unread() -> list[dict]:
    return [n for n in _notifications if not n["is_read"]]


def get_unread_count_by_route() -> dict[str, int]:
    counts: dict[str, int] = {}
    for n in _notifications:
        if not n["is_read"]:
            route = n["source_route"]
            counts[route] = counts.get(route, 0) + 1
    return counts


def mark_read(notification_id: str) -> bool:
    for n in _notifications:
        if n["id"] == notification_id:
            n["is_read"] = True
            return True
    return False


def mark_route_read(route: str):
    for n in _notifications:
        if n["source_route"] == route:
            n["is_read"] = True

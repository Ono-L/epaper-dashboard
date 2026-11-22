"""通知受信・一覧・クリア用 REST API ルーター。"""

from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends, Query

from src.api.dependencies import (
    get_dashboard_service,
    get_notification_repo,
    verify_api_key,
)
from src.models import (
    NotificationClearResponse,
    NotificationCreate,
    NotificationListResponse,
    NotificationRecord,
)
from src.services.dashboard import DashboardService
from src.storage.notifications import NotificationRepository

router = APIRouter(
    prefix="/api/v1/notifications",
    tags=["notifications"],
    dependencies=[Depends(verify_api_key)],
)


@router.post("", response_model=NotificationRecord)
async def create_notification(
    payload: NotificationCreate,
    repo: Annotated[NotificationRepository, Depends(get_notification_repo)],
    dashboard: Annotated[DashboardService, Depends(get_dashboard_service)],
) -> NotificationRecord:
    """iPhone ショートカット等からの通知を受信・保存し、電子ペーパー画像を更新する。"""
    record = repo.add(payload)
    await dashboard.refresh_display(force_weather_refresh=False)
    return record


@router.get("", response_model=NotificationListResponse)
async def list_notifications(
    repo: Annotated[NotificationRepository, Depends(get_notification_repo)],
    limit: Annotated[int, Query(ge=1, le=50)] = 10,
) -> NotificationListResponse:
    """保存済みの最新通知一覧を新しい順で返す。"""
    items = repo.list_recent(limit=limit)
    return NotificationListResponse(count=len(items), items=items)


@router.delete("", response_model=NotificationClearResponse)
async def clear_notifications(
    repo: Annotated[NotificationRepository, Depends(get_notification_repo)],
    dashboard: Annotated[DashboardService, Depends(get_dashboard_service)],
) -> NotificationClearResponse:
    """保存済みの通知をすべて削除し、電子ペーパー画像を更新する。"""
    deleted = repo.clear_all()
    await dashboard.refresh_display(force_weather_refresh=False)
    return NotificationClearResponse(
        deleted_count=deleted,
        message=f"{deleted} 件の通知をクリアしました。",
    )

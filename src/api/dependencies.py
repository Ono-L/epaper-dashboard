"""FastAPI 依存性注入（設定・認証・各種サービス取得）。"""

from __future__ import annotations

import hmac
from typing import Annotated

from fastapi import Depends, Header, HTTPException, Request, status

from src.config import Settings
from src.services.dashboard import DashboardService
from src.storage.notifications import NotificationRepository


def get_app_settings(request: Request) -> Settings:
    """アプリケーション状態から Settings を取得する。"""
    return request.app.state.settings  # type: ignore[no-any-return]


def get_notification_repo(request: Request) -> NotificationRepository:
    """アプリケーション状態から NotificationRepository を取得する。"""
    return request.app.state.notification_repo  # type: ignore[no-any-return]


def get_dashboard_service(request: Request) -> DashboardService:
    """アプリケーション状態から DashboardService を取得する。"""
    return request.app.state.dashboard_service  # type: ignore[no-any-return]


def verify_api_key(
    settings: Annotated[Settings, Depends(get_app_settings)],
    x_api_key: Annotated[str | None, Header(alias="X-API-Key")] = None,
) -> str:
    """X-API-Key ヘッダーを検証する。未設定または不一致の場合は 401 を送出する。"""
    configured_key = settings.api_key.strip()
    if not configured_key:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="API キーがサーバーに設定されていないためアクセスを拒否しました。",
        )

    if not x_api_key or not hmac.compare_digest(x_api_key, configured_key):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="X-API-Key が未指定または不正です。",
        )

    return x_api_key

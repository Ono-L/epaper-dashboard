"""FastAPI アプリケーションエントリーポイント。"""

from __future__ import annotations

import logging
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.responses import RedirectResponse

from src.api.notifications import router as notifications_router
from src.api.preview import router as preview_router
from src.config import Settings, get_settings
from src.display.base import DisplayDriver
from src.display.factory import create_display_driver
from src.display.renderer import DashboardRenderer
from src.services.dashboard import DashboardService
from src.services.weather import WeatherService
from src.storage.notifications import NotificationRepository

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger(__name__)


def create_app(
    settings: Settings | None = None,
    weather_service: WeatherService | None = None,
    display_driver: DisplayDriver | None = None,
    render_on_startup: bool = True,
) -> FastAPI:
    """依存関係を組み立てて FastAPI アプリケーションを生成する。"""
    resolved_settings = settings or get_settings()

    notification_repo = NotificationRepository(
        db_path=resolved_settings.db_path,
        max_stored=resolved_settings.max_stored_notifications,
        timezone_name=resolved_settings.timezone,
    )
    resolved_weather = weather_service or WeatherService(
        latitude=resolved_settings.weather_latitude,
        longitude=resolved_settings.weather_longitude,
        location_name=resolved_settings.weather_location_name,
        timezone_name=resolved_settings.timezone,
        cache_seconds=resolved_settings.weather_cache_seconds,
    )
    renderer = DashboardRenderer(
        font_path=resolved_settings.font_path,
        timezone_name=resolved_settings.timezone,
        max_notifications=resolved_settings.max_display_notifications,
    )
    resolved_driver = display_driver or create_display_driver(resolved_settings)

    dashboard_service = DashboardService(
        weather_service=resolved_weather,
        notification_repo=notification_repo,
        renderer=renderer,
        driver=resolved_driver,
        max_display_notifications=resolved_settings.max_display_notifications,
        timezone_name=resolved_settings.timezone,
    )

    @asynccontextmanager
    async def lifespan(_: FastAPI) -> AsyncIterator[None]:
        if render_on_startup:
            logger.info("起動時の初回電子ペーパー描画を実行します。")
            await dashboard_service.refresh_display(force_weather_refresh=False)
        yield
        resolved_driver.sleep()

    app = FastAPI(
        title="epaper-dashboard",
        description="ローカル電子ペーパーダッシュボード（Phase 1 プロトタイプ）",
        version="0.1.0",
        lifespan=lifespan,
    )

    app.state.settings = resolved_settings
    app.state.notification_repo = notification_repo
    app.state.dashboard_service = dashboard_service

    app.include_router(notifications_router)
    app.include_router(preview_router)

    @app.get("/", include_in_schema=False)
    async def root() -> RedirectResponse:
        """ルートアクセスをプレビュー画面へリダイレクトする。"""
        return RedirectResponse(url="/preview")

    @app.get("/health", tags=["system"])
    async def health() -> dict[str, str]:
        """ヘルスチェックエンドポイント。"""
        return {"status": "ok", "display_mode": resolved_settings.display_mode}

    return app


app = create_app()

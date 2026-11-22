"""ダッシュボード全体の状態取得・描画・出力を統括するサービス。"""

from __future__ import annotations

from datetime import datetime
from io import BytesIO
from pathlib import Path
from zoneinfo import ZoneInfo

from PIL import Image

from src.display.base import DisplayDriver
from src.display.mock import MockDisplayDriver
from src.display.renderer import DashboardRenderer
from src.models import NotificationRecord, WeatherInfo
from src.services.weather import WeatherService
from src.storage.notifications import NotificationRepository


class DashboardService:
    """天気・通知・描画・出力ドライバを統合するアプリケーションサービス。"""

    def __init__(
        self,
        weather_service: WeatherService,
        notification_repo: NotificationRepository,
        renderer: DashboardRenderer,
        driver: DisplayDriver,
        max_display_notifications: int = 5,
        timezone_name: str = "Asia/Tokyo",
    ) -> None:
        self._weather_service = weather_service
        self._notification_repo = notification_repo
        self._renderer = renderer
        self._driver = driver
        self._max_display_notifications = max_display_notifications
        self._tz = ZoneInfo(timezone_name)
        self._last_rendered_at: datetime | None = None
        self._last_image_bytes: bytes | None = None

    @property
    def last_rendered_at(self) -> datetime | None:
        """最後に描画を実行した日時を返す。"""
        return self._last_rendered_at

    @property
    def resolved_font_name(self) -> str:
        """描画エンジンが使用しているフォント名を返す。"""
        font_path = self._renderer.resolved_font_path
        return font_path.name if font_path is not None else "Pillow default"

    async def refresh_display(self, force_weather_refresh: bool = False) -> Image.Image:
        """最新の天気と通知を取得して画像を生成し、ドライバへ出力する。"""
        weather: WeatherInfo = await self._weather_service.get_weather(
            force_refresh=force_weather_refresh
        )
        notifications: list[NotificationRecord] = self._notification_repo.list_recent(
            limit=self._max_display_notifications
        )
        now = datetime.now(self._tz)
        image = self._renderer.render(
            weather=weather,
            notifications=notifications,
            now=now,
        )
        self._driver.render(image)
        self._last_rendered_at = now

        buffer = BytesIO()
        image.save(buffer, format="PNG")
        self._last_image_bytes = buffer.getvalue()
        return image

    async def get_preview_png_bytes(self) -> bytes:
        """プレビュー表示用の最新 400x300 PNG バイト列を返す。"""
        if isinstance(self._driver, MockDisplayDriver):
            output_path: Path = self._driver.output_path
            if output_path.is_file():
                return output_path.read_bytes()

        if self._last_image_bytes is not None:
            return self._last_image_bytes

        await self.refresh_display(force_weather_refresh=False)
        assert self._last_image_bytes is not None
        return self._last_image_bytes

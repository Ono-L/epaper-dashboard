"""pytest 共通フィクスチャ定義。"""

from __future__ import annotations

from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo

import pytest
from fastapi.testclient import TestClient

from src.config import Settings
from src.main import create_app
from src.models import WeatherInfo
from src.services.weather import WeatherService


class StubWeatherService(WeatherService):
    """外部ネットワークに依存せず固定の天気情報を返すテスト用サービス。"""

    def __init__(self) -> None:
        super().__init__(location_name="東京")

    async def get_weather(self, force_refresh: bool = False) -> WeatherInfo:
        return WeatherInfo(
            location="東京",
            weather_code=1,
            condition="晴れ",
            icon="clear",
            temperature=18.5,
            temp_max=21.0,
            temp_min=12.0,
            precipitation_probability=10,
            fetched_at=datetime(2026, 11, 22, 12, 0, tzinfo=ZoneInfo("Asia/Tokyo")),
            is_fallback=False,
        )


@pytest.fixture
def test_settings(tmp_path: Path) -> Settings:
    """一時ディレクトリを使用するテスト用設定を返す。"""
    return Settings(
        api_key="test-secret-api-key",
        weather_latitude=35.6895,
        weather_longitude=139.6917,
        weather_location_name="東京",
        timezone="Asia/Tokyo",
        display_mode="mock",
        output_image_path=str(tmp_path / "preview.png"),
        db_path=str(tmp_path / "notifications.db"),
    )


@pytest.fixture
def api_client(test_settings: Settings) -> TestClient:
    """FastAPI TestClient を生成して返す。"""
    app = create_app(
        settings=test_settings,
        weather_service=StubWeatherService(),
        render_on_startup=True,
    )
    with TestClient(app) as client:
        yield client

"""電子ペーパー描画エンジンおよびドライバの単体テスト。"""

from __future__ import annotations

from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo

import pytest
from PIL import Image

from src.display.base import DISPLAY_HEIGHT, DISPLAY_WIDTH
from src.display.mock import MockDisplayDriver
from src.display.renderer import DashboardRenderer
from src.display.waveshare import WaveshareDisplayDriver
from src.models import NotificationRecord, WeatherInfo


def _sample_weather() -> WeatherInfo:
    return WeatherInfo(
        location="東京",
        weather_code=0,
        condition="快晴",
        icon="clear",
        temperature=19.4,
        temp_max=22.0,
        temp_min=11.0,
        precipitation_probability=5,
        fetched_at=datetime(2026, 11, 22, 12, 0, tzinfo=ZoneInfo("Asia/Tokyo")),
    )


def _sample_notifications() -> list[NotificationRecord]:
    tz = ZoneInfo("Asia/Tokyo")
    return [
        NotificationRecord(
            id=2,
            app_name="LINE",
            title="ランチの集合場所について",
            body="12:30 に駅前のカフェ前に集合しましょう！",
            received_at=datetime(2026, 11, 22, 11, 55, tzinfo=tz),
        ),
        NotificationRecord(
            id=1,
            app_name="カレンダー",
            title="定例ミーティング",
            body="午後 2 時からオンライン会議があります。",
            received_at=datetime(2026, 11, 22, 10, 30, tzinfo=tz),
        ),
    ]


def test_renderer_generates_400x300_1bit_image_with_content() -> None:
    """DashboardRenderer が 400x300 の 1bit モノクロ画像を生成し、描画ピクセルを含むこと。"""
    renderer = DashboardRenderer()
    image = renderer.render(
        weather=_sample_weather(),
        notifications=_sample_notifications(),
        now=datetime(2026, 11, 22, 12, 5, tzinfo=ZoneInfo("Asia/Tokyo")),
    )

    assert image.size == (DISPLAY_WIDTH, DISPLAY_HEIGHT)
    assert image.mode == "1"

    # 白紙ではなく黒ピクセル（値 0）が十分に描画されていること
    histogram = image.histogram()
    black_pixels = histogram[0]
    white_pixels = histogram[-1]
    assert black_pixels > 1000
    assert white_pixels > 1000


def test_renderer_handles_empty_notifications() -> None:
    """通知 0 件でも 400x300 の 1bit 画像を正常生成できること。"""
    renderer = DashboardRenderer()
    image = renderer.render(
        weather=_sample_weather(),
        notifications=[],
        now=datetime(2026, 11, 22, 12, 5, tzinfo=ZoneInfo("Asia/Tokyo")),
    )

    assert image.size == (DISPLAY_WIDTH, DISPLAY_HEIGHT)
    assert image.mode == "1"


def test_mock_display_driver_saves_png_and_rejects_wrong_size(tmp_path: Path) -> None:
    """MockDisplayDriver が 400x300 PNG を保存し、不正サイズ画像を拒否すること。"""
    output_path = tmp_path / "preview.png"
    driver = MockDisplayDriver(output_path=output_path)

    renderer = DashboardRenderer()
    image = renderer.render(weather=_sample_weather(), notifications=_sample_notifications())
    driver.render(image)

    assert output_path.is_file()
    with Image.open(output_path) as saved:
        assert saved.size == (DISPLAY_WIDTH, DISPLAY_HEIGHT)
        assert saved.mode == "1"

    invalid_image = Image.new("1", (100, 100), 255)
    with pytest.raises(ValueError, match="画像サイズが不正"):
        driver.render(invalid_image)


def test_waveshare_stub_raises_runtime_error_without_hardware_library() -> None:
    """実機ライブラリ未導入環境で WaveshareDisplayDriver が明示的なエラーを送出すること。"""
    driver = WaveshareDisplayDriver()
    blank = Image.new("1", (DISPLAY_WIDTH, DISPLAY_HEIGHT), 255)
    with pytest.raises(RuntimeError, match="waveshare_epd"):
        driver.render(blank)

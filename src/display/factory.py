"""設定に応じた電子ペーパードライバ生成ファクトリ。"""

from __future__ import annotations

from src.config import Settings
from src.display.base import DisplayDriver
from src.display.mock import MockDisplayDriver
from src.display.waveshare import WaveshareDisplayDriver


def create_display_driver(settings: Settings) -> DisplayDriver:
    """DISPLAY_MODE の設定値に応じて適切なドライバを生成する。"""
    if settings.display_mode == "mock":
        return MockDisplayDriver(output_path=settings.output_image_path)
    if settings.display_mode == "waveshare":
        return WaveshareDisplayDriver()
    raise ValueError(f"未対応の DISPLAY_MODE です: {settings.display_mode}")

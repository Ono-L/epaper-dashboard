"""電子ペーパードライバの抽象インターフェース定義。"""

from __future__ import annotations

from abc import ABC, abstractmethod

from PIL import Image

# Waveshare 4.2inch e-Paper Module 固定解像度
DISPLAY_WIDTH: int = 400
DISPLAY_HEIGHT: int = 300


class DisplayDriver(ABC):
    """電子ペーパー出力デバイスの抽象基底クラス。

    モック（PNG ファイル出力）と実機（Waveshare SPI）を同じインターフェースで扱う。
    """

    width: int = DISPLAY_WIDTH
    height: int = DISPLAY_HEIGHT

    def validate_image(self, image: Image.Image) -> Image.Image:
        """出力前に解像度と 1bit モノクロ形式を検証・変換する。"""
        if image.size != (self.width, self.height):
            raise ValueError(
                f"画像サイズが不正です: expected={(self.width, self.height)}, actual={image.size}"
            )
        if image.mode != "1":
            return image.convert("1")
        return image

    @abstractmethod
    def render(self, image: Image.Image) -> None:
        """400x300 の 1bit モノクロ画像をディスプレイ（または出力先）へ反映する。"""

    @abstractmethod
    def clear(self) -> None:
        """画面を白紙状態にクリアする。"""

    @abstractmethod
    def sleep(self) -> None:
        """省電力モードへ移行する（実機向け）。"""

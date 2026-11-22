"""ローカル開発用のモック電子ペーパードライバ。"""

from __future__ import annotations

import os
from pathlib import Path

from PIL import Image

from src.display.base import DISPLAY_HEIGHT, DISPLAY_WIDTH, DisplayDriver


class MockDisplayDriver(DisplayDriver):
    """画像をローカルの PNG ファイル（例: output/preview.png）へ出力するモックドライバ。"""

    def __init__(self, output_path: str | Path = "output/preview.png") -> None:
        self._output_path = Path(output_path)

    @property
    def output_path(self) -> Path:
        """現在の画像出力先パスを返す。"""
        return self._output_path

    def render(self, image: Image.Image) -> None:
        """画像を 1bit PNG としてアトミックに保存する。"""
        validated = self.validate_image(image)
        self._output_path.parent.mkdir(parents=True, exist_ok=True)
        tmp_path = self._output_path.with_suffix(".tmp.png")
        validated.save(tmp_path, format="PNG")
        os.replace(tmp_path, self._output_path)

    def clear(self) -> None:
        """白紙の 400x300 1bit 画像で出力ファイルを上書きする。"""
        blank = Image.new("1", (DISPLAY_WIDTH, DISPLAY_HEIGHT), 255)
        self.render(blank)

    def sleep(self) -> None:
        """モック環境ではスリープ処理は不要のため何もしない。"""
        return None

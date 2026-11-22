"""Waveshare 4.2inch e-Paper Module 向け実機ドライバ（Phase 2 差し替え用スタブ）。"""

from __future__ import annotations

import logging

from PIL import Image

from src.display.base import DisplayDriver

logger = logging.getLogger(__name__)


class WaveshareDisplayDriver(DisplayDriver):
    """Raspberry Pi + Waveshare 4.2inch e-Paper (SPI) 向けドライバスタブ。

    Phase 1 のローカル開発環境では実機ライブラリ（waveshare_epd）に依存せず
    インターフェース互換性を維持し、Phase 2 で実機接続時に実装を有効化する。
    """

    def __init__(self) -> None:
        self._epd: object | None = None

    def _ensure_device(self) -> object:
        """実機ドライバの遅延初期化を行う（未導入時は明示エラー）。"""
        if self._epd is not None:
            return self._epd
        try:
            # 実機 Raspberry Pi 環境でのみ利用可能なライブラリを遅延インポート
            from waveshare_epd import epd4in2_V2  # type: ignore[import-not-found]
        except ImportError as exc:
            raise RuntimeError(
                "Waveshare 実機ドライバ（waveshare_epd）が見つかりません。"
                "ローカル開発環境では DISPLAY_MODE=mock を使用してください。"
            ) from exc

        epd = epd4in2_V2.EPD()
        epd.init()
        self._epd = epd
        return epd

    def render(self, image: Image.Image) -> None:
        """400x300 1bit 画像を実機電子ペーパーへ転送する。"""
        validated = self.validate_image(image)
        epd = self._ensure_device()
        # 実機ドライバの getbuffer / display 呼び出し（Phase 2 接続ポイント）
        epd.display(epd.getbuffer(validated))  # type: ignore[attr-defined]
        logger.info("Waveshare 電子ペーパーへの描画を完了しました。")

    def clear(self) -> None:
        """実機電子ペーパーを白紙クリアする。"""
        epd = self._ensure_device()
        epd.Clear()  # type: ignore[attr-defined]

    def sleep(self) -> None:
        """実機電子ペーパーを省電力スリープ状態にする。"""
        if self._epd is not None:
            self._epd.sleep()  # type: ignore[attr-defined]

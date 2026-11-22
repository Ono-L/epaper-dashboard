"""400x300 1bit モノクロ電子ペーパー向けダッシュボード描画エンジン。"""

from __future__ import annotations

import logging
import math
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo

from PIL import Image, ImageDraw, ImageFont

from src.display.base import DISPLAY_HEIGHT, DISPLAY_WIDTH
from src.models import NotificationRecord, WeatherIconType, WeatherInfo

logger = logging.getLogger(__name__)

# 1bit モノクロ色定義（Pillow mode="1": 0=黒, 255=白）
BLACK: int = 0
WHITE: int = 255

WEEKDAYS_JA: tuple[str, ...] = ("月", "火", "水", "木", "金", "土", "日")

# Docker (Debian) および macOS での日本語フォント探索候補
DEFAULT_FONT_CANDIDATES: tuple[str, ...] = (
    "/usr/share/fonts/opentype/ipaexfont-gothic/ipaexg.ttf",
    "/usr/share/fonts/truetype/ipaexfont-gothic/ipaexg.ttf",
    "/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc",
    "/usr/share/fonts/truetype/noto/NotoSansCJK-Regular.ttc",
    "/usr/share/fonts/noto-cjk/NotoSansCJK-Regular.ttc",
    "/System/Library/Fonts/ヒラギノ角ゴシック W3.ttc",
    "/System/Library/Fonts/Hiragino Sans GB.ttc",
)

FontType = ImageFont.FreeTypeFont | ImageFont.ImageFont


class DashboardRenderer:
    """日時・天気・通知リストを 400x300 1bit モノクロ画像として描画するクラス。"""

    def __init__(
        self,
        font_path: str = "",
        timezone_name: str = "Asia/Tokyo",
        max_notifications: int = 5,
    ) -> None:
        self._font_path = self._resolve_font_path(font_path)
        self._tz = ZoneInfo(timezone_name)
        self._max_notifications = max_notifications

    @property
    def resolved_font_path(self) -> Path | None:
        """解決済みの日本語フォントパスを返す。"""
        return self._font_path

    @staticmethod
    def _resolve_font_path(configured_path: str) -> Path | None:
        """利用可能な日本語フォントファイルパスを探索して返す。"""
        candidates: list[str] = []
        if configured_path.strip():
            candidates.append(configured_path.strip())
        candidates.extend(DEFAULT_FONT_CANDIDATES)

        for candidate in candidates:
            path = Path(candidate)
            if path.is_file():
                return path

        logger.warning(
            "日本語フォントが見つかりませんでした。Pillow デフォルトフォントにフォールバックします。"
        )
        return None

    def _load_font(self, size: int) -> FontType:
        """指定サイズのフォントを読み込む。"""
        if self._font_path is not None:
            try:
                return ImageFont.truetype(str(self._font_path), size=size)
            except OSError as exc:
                logger.warning("フォント読み込みに失敗しました (%s): %s", self._font_path, exc)
        return ImageFont.load_default()

    def render(
        self,
        weather: WeatherInfo,
        notifications: list[NotificationRecord],
        now: datetime | None = None,
    ) -> Image.Image:
        """ダッシュボード全体の 400x300 1bit モノクロ画像を生成する。"""
        current_time = (now or datetime.now(self._tz)).astimezone(self._tz)

        # 1bit モノクロ白背景でキャンバスを作成
        image = Image.new("1", (DISPLAY_WIDTH, DISPLAY_HEIGHT), WHITE)
        draw = ImageDraw.Draw(image)

        # 外枠
        draw.rectangle((4, 4, DISPLAY_WIDTH - 5, DISPLAY_HEIGHT - 5), outline=BLACK, width=1)

        # 上部: 日時と天気セクション（y=4..116）
        self._draw_datetime_section(draw, current_time, weather.location)
        draw.line((194, 12, 194, 108), fill=BLACK, width=1)
        self._draw_weather_section(draw, weather)

        # 中央: 通知セクションヘッダーバー（y=116..136）
        visible_notifications = notifications[: self._max_notifications]
        self._draw_section_header(draw, len(notifications), current_time)

        # 下部: 通知リスト（y=138..292）
        self._draw_notifications_section(draw, visible_notifications)

        return image

    def _draw_datetime_section(
        self,
        draw: ImageDraw.ImageDraw,
        now: datetime,
        location: str,
    ) -> None:
        """左上エリアに日付・曜日・現在時刻・地点名を描画する。"""
        font_date = self._load_font(14)
        font_time = self._load_font(46)
        font_sub = self._load_font(12)

        weekday = WEEKDAYS_JA[now.weekday()]
        date_text = f"{now.year}/{now.month:02d}/{now.day:02d} ({weekday})"
        time_text = now.strftime("%H:%M")

        draw.text((14, 14), date_text, font=font_date, fill=BLACK)
        draw.text((14, 34), time_text, font=font_time, fill=BLACK)
        location_text = self._truncate_text(draw, f"地点: {location}", font_sub, 172)
        draw.text((14, 92), location_text, font=font_sub, fill=BLACK)

    def _draw_weather_section(
        self,
        draw: ImageDraw.ImageDraw,
        weather: WeatherInfo,
    ) -> None:
        """右上エリアに天気アイコン・気温・天気名・最高/最低気温・降水確率を描画する。"""
        font_temp = self._load_font(28)
        font_cond = self._load_font(14)
        font_detail = self._load_font(13)

        # 天気アイコン（44x44 領域）
        self._draw_weather_icon(draw, weather.icon, x=204, y=14)

        # 現在気温と天気ラベル
        temp_text = (
            f"{weather.temperature:.1f}°C" if weather.temperature is not None else "--.-°C"
        )
        draw.text((256, 14), temp_text, font=font_temp, fill=BLACK)

        cond_text = self._truncate_text(draw, weather.condition, font_cond, 130)
        draw.text((258, 48), cond_text, font=font_cond, fill=BLACK)

        # 細い区切り線
        self._draw_dotted_line(draw, x1=204, x2=386, y=70, step=4)

        # 最高・最低気温
        max_str = f"{weather.temp_max:.0f}°" if weather.temp_max is not None else "--°"
        min_str = f"{weather.temp_min:.0f}°" if weather.temp_min is not None else "--°"
        hi_lo_text = f"最高 {max_str}  /  最低 {min_str}"
        draw.text((206, 76), hi_lo_text, font=font_detail, fill=BLACK)

        # 降水確率
        precip_str = (
            f"{weather.precipitation_probability}%"
            if weather.precipitation_probability is not None
            else "--%"
        )
        draw.text((206, 94), f"降水確率: {precip_str}", font=font_detail, fill=BLACK)

    def _draw_section_header(
        self,
        draw: ImageDraw.ImageDraw,
        total_count: int,
        now: datetime,
    ) -> None:
        """通知リスト上部の黒反転ヘッダーバーを描画する。"""
        font_header = self._load_font(12)
        font_meta = self._load_font(11)

        draw.rectangle((4, 116, DISPLAY_WIDTH - 5, 136), fill=BLACK)
        draw.text((12, 120), f"iPhone 通知 ({total_count}件)", font=font_header, fill=WHITE)

        updated_text = f"更新 {now.strftime('%H:%M')}"
        text_width = draw.textlength(updated_text, font=font_meta)
        draw.text(
            (DISPLAY_WIDTH - 12 - text_width, 121),
            updated_text,
            font=font_meta,
            fill=WHITE,
        )

    def _draw_notifications_section(
        self,
        draw: ImageDraw.ImageDraw,
        notifications: list[NotificationRecord],
    ) -> None:
        """下部エリアに最新の通知リストを描画する。"""
        if not notifications:
            font_empty = self._load_font(15)
            font_hint = self._load_font(11)
            msg = "新しい通知はありません"
            hint = "iPhone ショートカットから通知を受信すると表示されます"
            msg_w = draw.textlength(msg, font=font_empty)
            hint_w = draw.textlength(hint, font=font_hint)
            draw.text(((DISPLAY_WIDTH - msg_w) / 2, 194), msg, font=font_empty, fill=BLACK)
            draw.text(((DISPLAY_WIDTH - hint_w) / 2, 218), hint, font=font_hint, fill=BLACK)
            return

        font_time = self._load_font(11)
        font_app = self._load_font(11)
        font_title = self._load_font(12)
        font_body = self._load_font(11)

        row_top = 140
        row_height = 30

        for idx, item in enumerate(notifications):
            y = row_top + idx * row_height
            if y + row_height > DISPLAY_HEIGHT - 4:
                break

            local_dt = item.received_at.astimezone(self._tz)
            time_str = local_dt.strftime("%H:%M")

            # 時刻
            draw.text((12, y + 2), time_str, font=font_time, fill=BLACK)

            # アプリ名バッジ（黒枠角付きラベル）
            app_label = self._truncate_text(draw, item.app_name, font_app, 64)
            app_w = int(math.ceil(draw.textlength(app_label, font=font_app)))
            badge_x1 = 48
            badge_x2 = badge_x1 + app_w + 8
            draw.rectangle((badge_x1, y + 1, badge_x2, y + 14), fill=BLACK)
            draw.text((badge_x1 + 4, y + 2), app_label, font=font_app, fill=WHITE)

            # 通知タイトル
            title_x = badge_x2 + 6
            title_max_w = (DISPLAY_WIDTH - 12) - title_x
            title_text = self._truncate_text(draw, item.title, font_title, title_max_w)
            draw.text((title_x, y + 1), title_text, font=font_title, fill=BLACK)

            # 通知本文（2行目）
            if item.body:
                body_text = self._truncate_text(
                    draw,
                    item.body.replace("\n", " "),
                    font_body,
                    DISPLAY_WIDTH - 28,
                )
                draw.text((16, y + 16), body_text, font=font_body, fill=BLACK)

            # 最後の行以外は区切り点線を描画
            if idx < len(notifications) - 1:
                self._draw_dotted_line(draw, x1=12, x2=DISPLAY_WIDTH - 12, y=y + row_height - 1)

    def _draw_weather_icon(
        self,
        draw: ImageDraw.ImageDraw,
        icon: WeatherIconType,
        x: int,
        y: int,
    ) -> None:
        """1bit モノクロでくっきり視認できる 44x44 天気アイコンを描画する。"""
        cx, cy = x + 22, y + 22

        if icon == "clear":
            # 太陽（中心円＋8方向光線）
            draw.ellipse((cx - 9, cy - 9, cx + 9, cy + 9), fill=BLACK)
            draw.ellipse((cx - 6, cy - 6, cx + 6, cy + 6), fill=WHITE)
            for deg in range(0, 360, 45):
                rad = math.radians(deg)
                x1 = cx + int(round(math.cos(rad) * 13))
                y1 = cy + int(round(math.sin(rad) * 13))
                x2 = cx + int(round(math.cos(rad) * 18))
                y2 = cy + int(round(math.sin(rad) * 18))
                draw.line((x1, y1, x2, y2), fill=BLACK, width=2)
            return

        if icon == "partly_cloudy":
            # 右上に小さな太陽＋手前に雲
            sx, sy = x + 30, y + 14
            draw.ellipse((sx - 6, sy - 6, sx + 6, sy + 6), outline=BLACK, width=2)
            for deg in (0, 45, 90, 270, 315):
                rad = math.radians(deg)
                draw.line(
                    (
                        sx + int(round(math.cos(rad) * 9)),
                        sy + int(round(math.sin(rad) * 9)),
                        sx + int(round(math.cos(rad) * 12)),
                        sy + int(round(math.sin(rad) * 12)),
                    ),
                    fill=BLACK,
                    width=2,
                )
            self._draw_cloud_shape(draw, x + 2, y + 14)
            return

        if icon == "cloudy":
            self._draw_cloud_shape(draw, x + 4, y + 12)
            return

        if icon == "fog":
            self._draw_cloud_shape(draw, x + 4, y + 6)
            for ly in (y + 32, y + 37, y + 42):
                draw.line((x + 8, ly, x + 36, ly), fill=BLACK, width=2)
            return

        if icon == "rain":
            self._draw_cloud_shape(draw, x + 4, y + 4)
            for rx in (x + 12, x + 21, x + 30):
                draw.line((rx + 2, y + 31, rx - 1, y + 40), fill=BLACK, width=2)
            return

        if icon == "snow":
            self._draw_cloud_shape(draw, x + 4, y + 4)
            for sx in (x + 12, x + 22, x + 32):
                sy = y + 36
                draw.line((sx - 3, sy, sx + 3, sy), fill=BLACK, width=1)
                draw.line((sx, sy - 3, sx, sy + 3), fill=BLACK, width=1)
                draw.line((sx - 2, sy - 2, sx + 2, sy + 2), fill=BLACK, width=1)
                draw.line((sx - 2, sy + 2, sx + 2, sy - 2), fill=BLACK, width=1)
            return

        # thunder（雷雨）
        self._draw_cloud_shape(draw, x + 4, y + 4)
        bolt = [
            (x + 23, y + 29),
            (x + 17, y + 36),
            (x + 22, y + 36),
            (x + 19, y + 43),
            (x + 28, y + 34),
            (x + 23, y + 34),
        ]
        draw.polygon(bolt, fill=BLACK)

    @staticmethod
    def _draw_cloud_shape(draw: ImageDraw.ImageDraw, x: int, y: int) -> None:
        """白抜き太線風の雲アイコンを描画する。"""
        # 外側黒シルエット
        draw.ellipse((x + 2, y + 8, x + 18, y + 24), fill=BLACK)
        draw.ellipse((x + 10, y + 2, x + 28, y + 20), fill=BLACK)
        draw.ellipse((x + 20, y + 8, x + 36, y + 24), fill=BLACK)
        draw.rectangle((x + 10, y + 14, x + 28, y + 24), fill=BLACK)
        # 内側白抜き
        draw.ellipse((x + 4, y + 10, x + 16, y + 22), fill=WHITE)
        draw.ellipse((x + 12, y + 4, x + 26, y + 18), fill=WHITE)
        draw.ellipse((x + 22, y + 10, x + 34, y + 22), fill=WHITE)
        draw.rectangle((x + 10, y + 14, x + 28, y + 22), fill=WHITE)

    @staticmethod
    def _draw_dotted_line(
        draw: ImageDraw.ImageDraw,
        x1: int,
        x2: int,
        y: int,
        step: int = 4,
    ) -> None:
        """水平点線を描画する。"""
        for px in range(x1, x2, step):
            draw.point((px, y), fill=BLACK)

    @staticmethod
    def _truncate_text(
        draw: ImageDraw.ImageDraw,
        text: str,
        font: FontType,
        max_width: float,
    ) -> str:
        """指定ピクセル幅を超える文字列を末尾 '…' で省略する。"""
        if max_width <= 0:
            return ""
        if draw.textlength(text, font=font) <= max_width:
            return text

        ellipsis = "…"
        ellipsis_w = draw.textlength(ellipsis, font=font)
        if ellipsis_w > max_width:
            return ""

        low, high = 0, len(text)
        while low < high:
            mid = (low + high + 1) // 2
            if draw.textlength(text[:mid], font=font) + ellipsis_w <= max_width:
                low = mid
            else:
                high = mid - 1
        return f"{text[:low]}{ellipsis}"

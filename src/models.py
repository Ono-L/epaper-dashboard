"""ドメインモデルおよび API スキーマ定義。"""

from __future__ import annotations

from datetime import datetime
from typing import Literal

from pydantic import BaseModel, Field

WeatherIconType = Literal["clear", "partly_cloudy", "cloudy", "fog", "rain", "snow", "thunder"]


class WeatherInfo(BaseModel):
    """ダッシュボード表示用の天気情報モデル。"""

    location: str = Field(description="地点名")
    weather_code: int = Field(description="Open-Meteo WMO 天気コード")
    condition: str = Field(description="日本語の天気ラベル")
    icon: WeatherIconType = Field(description="描画用アイコン種別")
    temperature: float | None = Field(default=None, description="現在気温（℃）")
    temp_max: float | None = Field(default=None, description="当日最高気温（℃）")
    temp_min: float | None = Field(default=None, description="当日最低気温（℃）")
    precipitation_probability: int | None = Field(
        default=None,
        description="当日最大降水確率（%）",
    )
    fetched_at: datetime = Field(description="取得日時")
    is_fallback: bool = Field(default=False, description="取得失敗時のフォールバックデータか")


class NotificationCreate(BaseModel):
    """iPhone ショートカット等からの通知受信リクエスト。"""

    app_name: str = Field(
        default="iPhone",
        min_length=1,
        max_length=50,
        description="送信元アプリ名（例: LINE, Mail, Calendar）",
    )
    title: str = Field(
        min_length=1,
        max_length=120,
        description="通知タイトル",
    )
    body: str = Field(
        default="",
        max_length=500,
        description="通知本文",
    )


class NotificationRecord(BaseModel):
    """永続化済みの通知レコード。"""

    id: int = Field(description="通知 ID")
    app_name: str = Field(description="送信元アプリ名")
    title: str = Field(description="通知タイトル")
    body: str = Field(description="通知本文")
    received_at: datetime = Field(description="受信日時")


class NotificationListResponse(BaseModel):
    """通知一覧レスポンス。"""

    count: int = Field(description="取得件数")
    items: list[NotificationRecord] = Field(description="通知一覧（新しい順）")


class NotificationClearResponse(BaseModel):
    """通知クリアレスポンス。"""

    deleted_count: int = Field(description="削除した通知件数")
    message: str = Field(description="処理結果メッセージ")

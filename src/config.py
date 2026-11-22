"""アプリケーション設定管理モジュール。"""

from __future__ import annotations

from functools import lru_cache
from typing import Literal

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """環境変数から読み込むアプリケーション設定。"""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    # 認証設定（未設定または空の場合は全リクエストで 401 を返す）
    api_key: str = Field(default="", description="通知 API 認証用の X-API-Key")

    # 天気取得設定（初期値は東京）
    weather_latitude: float = Field(default=35.6895, description="天気取得の緯度")
    weather_longitude: float = Field(default=139.6917, description="天気取得の経度")
    weather_location_name: str = Field(default="東京", description="画面表示用の地点名")
    weather_cache_seconds: int = Field(default=600, ge=0, description="天気キャッシュ保持秒数")

    # タイムゾーン設定
    timezone: str = Field(default="Asia/Tokyo", description="表示用タイムゾーン")

    # ディスプレイ出力設定
    display_mode: Literal["mock", "waveshare"] = Field(
        default="mock",
        description="ディスプレイ出力モード（mock または waveshare）",
    )
    output_image_path: str = Field(
        default="output/preview.png",
        description="モックモード時のプレビュー画像出力パス",
    )
    font_path: str = Field(
        default="",
        description="日本語フォントファイルのパス（空文字の場合は自動検出）",
    )

    # 通知ストレージ設定
    db_path: str = Field(
        default="data/notifications.db",
        description="通知永続化用の SQLite データベースパス",
    )
    max_display_notifications: int = Field(
        default=5,
        ge=1,
        le=10,
        description="電子ペーパー画面に表示する通知の最大件数",
    )
    max_stored_notifications: int = Field(
        default=50,
        ge=5,
        le=1000,
        description="DB に保持する通知の最大件数",
    )


@lru_cache
def get_settings() -> Settings:
    """キャッシュされた設定インスタンスを返す。"""
    return Settings()

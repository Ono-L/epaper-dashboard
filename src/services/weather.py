"""Open-Meteo API を用いた天気情報取得サービス。"""

from __future__ import annotations

import logging
from datetime import datetime, timedelta
from typing import Any
from zoneinfo import ZoneInfo

import httpx

from src.models import WeatherIconType, WeatherInfo

logger = logging.getLogger(__name__)

OPEN_METEO_URL = "https://api.open-meteo.com/v1/forecast"

# WMO 天気コード -> (日本語ラベル, アイコン種別)
WMO_WEATHER_MAP: dict[int, tuple[str, WeatherIconType]] = {
    0: ("快晴", "clear"),
    1: ("晴れ", "clear"),
    2: ("一部曇り", "partly_cloudy"),
    3: ("曇り", "cloudy"),
    45: ("霧", "fog"),
    48: ("霧氷", "fog"),
    51: ("弱い霧雨", "rain"),
    53: ("霧雨", "rain"),
    55: ("強い霧雨", "rain"),
    56: ("弱い凍霧雨", "rain"),
    57: ("強い凍霧雨", "rain"),
    61: ("小雨", "rain"),
    63: ("雨", "rain"),
    65: ("大雨", "rain"),
    66: ("弱い凍雨", "rain"),
    67: ("強い凍雨", "rain"),
    71: ("小雪", "snow"),
    73: ("雪", "snow"),
    75: ("大雪", "snow"),
    77: ("霧雪", "snow"),
    80: ("にわか雨", "rain"),
    81: ("強い雨", "rain"),
    82: ("激しい雨", "rain"),
    85: ("にわか雪", "snow"),
    86: ("強い雪", "snow"),
    95: ("雷雨", "thunder"),
    96: ("雹を伴う雷雨", "thunder"),
    99: ("激しい雷雨", "thunder"),
}


def map_wmo_code(code: int) -> tuple[str, WeatherIconType]:
    """WMO 天気コードを日本語ラベルとアイコン種別へ変換する。"""
    return WMO_WEATHER_MAP.get(code, ("不明", "cloudy"))


class WeatherService:
    """Open-Meteo API から天気情報を取得・キャッシュするサービス。"""

    def __init__(
        self,
        latitude: float = 35.6895,
        longitude: float = 139.6917,
        location_name: str = "東京",
        timezone_name: str = "Asia/Tokyo",
        cache_seconds: int = 600,
        timeout_seconds: float = 8.0,
        client: httpx.AsyncClient | None = None,
    ) -> None:
        self._latitude = latitude
        self._longitude = longitude
        self._location_name = location_name
        self._timezone_name = timezone_name
        self._tz = ZoneInfo(timezone_name)
        self._cache_seconds = cache_seconds
        self._timeout_seconds = timeout_seconds
        self._client = client
        self._cached: WeatherInfo | None = None

    async def get_weather(self, force_refresh: bool = False) -> WeatherInfo:
        """現在の天気情報を取得する（キャッシュ有効時はキャッシュを返す）。"""
        now = datetime.now(self._tz)

        if (
            not force_refresh
            and self._cached is not None
            and not self._cached.is_fallback
            and (now - self._cached.fetched_at) < timedelta(seconds=self._cache_seconds)
        ):
            return self._cached

        try:
            weather = await self._fetch_from_open_meteo(now)
            self._cached = weather
            return weather
        except Exception as exc:
            logger.warning("Open-Meteo からの天気取得に失敗しました: %s", exc)
            if self._cached is not None:
                return self._cached
            return WeatherInfo(
                location=self._location_name,
                weather_code=-1,
                condition="取得失敗",
                icon="cloudy",
                temperature=None,
                temp_max=None,
                temp_min=None,
                precipitation_probability=None,
                fetched_at=now,
                is_fallback=True,
            )

    async def _fetch_from_open_meteo(self, now: datetime) -> WeatherInfo:
        """Open-Meteo API を呼び出して WeatherInfo へ変換する。"""
        params: dict[str, Any] = {
            "latitude": self._latitude,
            "longitude": self._longitude,
            "timezone": self._timezone_name,
            "current": "temperature_2m,weather_code",
            "daily": "temperature_2m_max,temperature_2m_min,precipitation_probability_max",
            "forecast_days": 1,
        }

        if self._client is not None:
            response = await self._client.get(
                OPEN_METEO_URL,
                params=params,
                timeout=self._timeout_seconds,
            )
            response.raise_for_status()
            data: dict[str, Any] = response.json()
        else:
            async with httpx.AsyncClient(timeout=self._timeout_seconds) as client:
                response = await client.get(OPEN_METEO_URL, params=params)
                response.raise_for_status()
                data = response.json()

        return self._parse_response(data, now)

    def _parse_response(self, data: dict[str, Any], now: datetime) -> WeatherInfo:
        """Open-Meteo の JSON レスポンスを WeatherInfo モデルへ変換する。"""
        current = data.get("current", {})
        daily = data.get("daily", {})

        raw_code = current.get("weather_code", 3)
        weather_code = int(raw_code) if raw_code is not None else 3
        condition, icon = map_wmo_code(weather_code)

        temperature = self._to_float(current.get("temperature_2m"))
        temp_max = self._first_float(daily.get("temperature_2m_max"))
        temp_min = self._first_float(daily.get("temperature_2m_min"))
        precip_prob = self._first_int(daily.get("precipitation_probability_max"))

        return WeatherInfo(
            location=self._location_name,
            weather_code=weather_code,
            condition=condition,
            icon=icon,
            temperature=temperature,
            temp_max=temp_max,
            temp_min=temp_min,
            precipitation_probability=precip_prob,
            fetched_at=now,
            is_fallback=False,
        )

    @staticmethod
    def _to_float(value: Any) -> float | None:
        if value is None:
            return None
        return float(value)

    @staticmethod
    def _first_float(values: Any) -> float | None:
        if isinstance(values, list) and values and values[0] is not None:
            return float(values[0])
        return None

    @staticmethod
    def _first_int(values: Any) -> int | None:
        if isinstance(values, list) and values and values[0] is not None:
            return int(round(float(values[0])))
        return None

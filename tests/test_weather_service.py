"""Open-Meteo 天気取得サービスの単体テスト。"""

from __future__ import annotations

import httpx
import pytest

from src.services.weather import WeatherService, map_wmo_code


@pytest.mark.asyncio
async def test_weather_service_parses_open_meteo_response() -> None:
    """Open-Meteo JSON レスポンスが正しく WeatherInfo へ変換されること。"""

    def handler(request: httpx.Request) -> httpx.Response:
        assert request.url.host == "api.open-meteo.com"
        return httpx.Response(
            status_code=200,
            json={
                "current": {
                    "temperature_2m": 16.8,
                    "weather_code": 61,
                },
                "daily": {
                    "temperature_2m_max": [20.4],
                    "temperature_2m_min": [11.2],
                    "precipitation_probability_max": [70],
                },
            },
        )

    transport = httpx.MockTransport(handler)
    async with httpx.AsyncClient(transport=transport) as client:
        service = WeatherService(location_name="東京", client=client)
        weather = await service.get_weather(force_refresh=True)

    assert weather.location == "東京"
    assert weather.weather_code == 61
    assert weather.condition == "小雨"
    assert weather.icon == "rain"
    assert weather.temperature == 16.8
    assert weather.temp_max == 20.4
    assert weather.temp_min == 11.2
    assert weather.precipitation_probability == 70
    assert weather.is_fallback is False


@pytest.mark.asyncio
async def test_weather_service_returns_fallback_on_network_error() -> None:
    """ネットワークエラー時にフォールバックデータを返し例外で落ちないこと。"""

    def handler(_: httpx.Request) -> httpx.Response:
        raise httpx.ConnectError("connection failed")

    transport = httpx.MockTransport(handler)
    async with httpx.AsyncClient(transport=transport) as client:
        service = WeatherService(location_name="東京", client=client)
        weather = await service.get_weather(force_refresh=True)

    assert weather.is_fallback is True
    assert weather.condition == "取得失敗"
    assert weather.temperature is None


def test_map_wmo_code_returns_japanese_label() -> None:
    """代表的な WMO 天気コードが日本語ラベルへ変換されること。"""
    assert map_wmo_code(0) == ("快晴", "clear")
    assert map_wmo_code(3) == ("曇り", "cloudy")
    assert map_wmo_code(95) == ("雷雨", "thunder")
    assert map_wmo_code(999) == ("不明", "cloudy")

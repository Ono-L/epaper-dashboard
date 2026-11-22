"""通知 API 認証・CRUD およびプレビューエンドポイントのテスト。"""

from __future__ import annotations

from io import BytesIO
from pathlib import Path

from fastapi.testclient import TestClient
from PIL import Image

from src.config import Settings
from src.display.base import DISPLAY_HEIGHT, DISPLAY_WIDTH
from src.main import create_app
from tests.conftest import StubWeatherService


def test_post_notification_without_api_key_returns_401(api_client: TestClient) -> None:
    """X-API-Key ヘッダー未指定の場合に 401 が返ること。"""
    response = api_client.post(
        "/api/v1/notifications",
        json={"app_name": "LINE", "title": "テスト", "body": "本文"},
    )
    assert response.status_code == 401


def test_post_notification_with_invalid_api_key_returns_401(api_client: TestClient) -> None:
    """X-API-Key が不一致の場合に 401 が返ること。"""
    response = api_client.post(
        "/api/v1/notifications",
        headers={"X-API-Key": "wrong-key"},
        json={"app_name": "LINE", "title": "テスト", "body": "本文"},
    )
    assert response.status_code == 401


def test_server_without_configured_api_key_returns_401(tmp_path: Path) -> None:
    """サーバー側 API_KEY が空の場合、いかなるキーでも 401 が返ること。"""
    settings = Settings(
        api_key="",
        output_image_path=str(tmp_path / "preview.png"),
        db_path=str(tmp_path / "notifications.db"),
    )
    app = create_app(
        settings=settings,
        weather_service=StubWeatherService(),
        render_on_startup=False,
    )
    with TestClient(app) as client:
        response = client.post(
            "/api/v1/notifications",
            headers={"X-API-Key": ""},
            json={"app_name": "LINE", "title": "テスト", "body": "本文"},
        )
        assert response.status_code == 401


def test_notification_lifecycle_with_valid_api_key_returns_200(
    api_client: TestClient,
    test_settings: Settings,
) -> None:
    """正しい X-API-Key で通知登録・一覧取得・クリアが 200 で成功し、画像が更新されること。"""
    headers = {"X-API-Key": test_settings.api_key}

    # 1. 通知登録（POST）
    post_res = api_client.post(
        "/api/v1/notifications",
        headers=headers,
        json={
            "app_name": "LINE",
            "title": "買い物のお願い",
            "body": "牛乳と卵を買ってきてください",
        },
    )
    assert post_res.status_code == 200
    created = post_res.json()
    assert created["app_name"] == "LINE"
    assert created["title"] == "買い物のお願い"
    assert created["body"] == "牛乳と卵を買ってきてください"

    # モックドライバにより 400x300 の 1bit 画像が出力されていること
    output_file = Path(test_settings.output_image_path)
    assert output_file.is_file()
    with Image.open(output_file) as rendered:
        assert rendered.size == (DISPLAY_WIDTH, DISPLAY_HEIGHT)
        assert rendered.mode == "1"

    # 2. 通知一覧取得（GET）
    list_res = api_client.get("/api/v1/notifications", headers=headers)
    assert list_res.status_code == 200
    body = list_res.json()
    assert body["count"] == 1
    assert body["items"][0]["title"] == "買い物のお願い"

    # 3. 通知クリア（DELETE）
    del_res = api_client.delete("/api/v1/notifications", headers=headers)
    assert del_res.status_code == 200
    assert del_res.json()["deleted_count"] == 1

    # クリア後は 0 件
    after_list = api_client.get("/api/v1/notifications", headers=headers)
    assert after_list.status_code == 200
    assert after_list.json()["count"] == 0


def test_preview_endpoints_return_html_and_400x300_png(api_client: TestClient) -> None:
    """/preview が HTML、/preview/image が 400x300 の PNG を返すこと。"""
    page_res = api_client.get("/preview")
    assert page_res.status_code == 200
    assert "text/html" in page_res.headers["content-type"]
    assert "epaper-dashboard" in page_res.text

    img_res = api_client.get("/preview/image")
    assert img_res.status_code == 200
    assert img_res.headers["content-type"] == "image/png"
    with Image.open(BytesIO(img_res.content)) as img:
        assert img.size == (DISPLAY_WIDTH, DISPLAY_HEIGHT)
        assert img.mode == "1"

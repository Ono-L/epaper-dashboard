"""ブラウザ確認用の電子ペーパープレビューエンドポイント。"""

from __future__ import annotations

import html
from typing import Annotated

from fastapi import APIRouter, Depends, Response
from fastapi.responses import HTMLResponse

from src.api.dependencies import get_app_settings, get_dashboard_service
from src.config import Settings
from src.display.base import DISPLAY_HEIGHT, DISPLAY_WIDTH
from src.services.dashboard import DashboardService

router = APIRouter(tags=["preview"])


@router.get("/preview/image")
async def preview_image(
    dashboard: Annotated[DashboardService, Depends(get_dashboard_service)],
) -> Response:
    """生成済みの 400x300 電子ペーパー PNG 画像を返す。"""
    png_bytes = await dashboard.get_preview_png_bytes()
    return Response(
        content=png_bytes,
        media_type="image/png",
        headers={"Cache-Control": "no-store, no-cache, must-revalidate, max-age=0"},
    )


@router.post("/preview/refresh")
async def refresh_preview(
    dashboard: Annotated[DashboardService, Depends(get_dashboard_service)],
) -> dict[str, str]:
    """天気情報と通知一覧を再取得し、プレビュー画像を最新化する。"""
    await dashboard.refresh_display(force_weather_refresh=True)
    rendered_at = (
        dashboard.last_rendered_at.isoformat()
        if dashboard.last_rendered_at is not None
        else ""
    )
    return {"status": "ok", "rendered_at": rendered_at}


@router.get("/preview", response_class=HTMLResponse)
async def preview_page(
    settings: Annotated[Settings, Depends(get_app_settings)],
    dashboard: Annotated[DashboardService, Depends(get_dashboard_service)],
) -> HTMLResponse:
    """400x300 電子ペーパープレビューとテスト通知送信フォームを提供する簡易ページ。"""
    # 初回アクセス時点で画像が未生成なら描画しておく
    if dashboard.last_rendered_at is None:
        await dashboard.refresh_display(force_weather_refresh=False)

    rendered_at_str = (
        dashboard.last_rendered_at.strftime("%Y-%m-%d %H:%M:%S")
        if dashboard.last_rendered_at is not None
        else "未描画"
    )
    mode_escaped = html.escape(settings.display_mode)
    location_escaped = html.escape(settings.weather_location_name)
    font_escaped = html.escape(dashboard.resolved_font_name)

    page_html = f"""<!DOCTYPE html>
<html lang="ja">
<head>
  <meta charset="UTF-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1.0" />
  <title>epaper-dashboard プレビュー (400x300)</title>
  <style>
    :root {{
      --bg: #eef0ec;
      --card: #ffffff;
      --bezel: #22252a;
      --ink: #1a1d21;
      --muted: #5c6370;
      --border: #d4d8d2;
      --accent: #1f2937;
      --danger: #991b1b;
    }}
    * {{ box-sizing: border-box; }}
    body {{
      margin: 0;
      padding: 32px 20px;
      font-family: -apple-system, BlinkMacSystemFont, "Hiragino Sans", "Yu Gothic", sans-serif;
      background: var(--bg);
      color: var(--ink);
    }}
    .container {{
      max-width: 960px;
      margin: 0 auto;
    }}
    header {{
      margin-bottom: 24px;
    }}
    h1 {{
      margin: 0 0 6px;
      font-size: 22px;
      letter-spacing: 0.02em;
    }}
    .subtitle {{
      margin: 0;
      color: var(--muted);
      font-size: 13px;
    }}
    .grid {{
      display: grid;
      grid-template-columns: auto 1fr;
      gap: 24px;
      align-items: start;
    }}
    @media (max-width: 820px) {{
      .grid {{ grid-template-columns: 1fr; }}
    }}
    .card {{
      background: var(--card);
      border: 1px solid var(--border);
      border-radius: 12px;
      padding: 20px;
      box-shadow: 0 4px 14px rgba(0, 0, 0, 0.04);
    }}
    .epaper-bezel {{
      background: var(--bezel);
      padding: 18px 18px 24px;
      border-radius: 14px;
      display: inline-block;
      box-shadow: inset 0 1px 0 rgba(255,255,255,0.08), 0 10px 24px rgba(0,0,0,0.18);
    }}
    .epaper-screen {{
      background: #f5f5f0;
      padding: 6px;
      border-radius: 4px;
      line-height: 0;
    }}
    .epaper-screen img {{
      width: {DISPLAY_WIDTH}px;
      height: {DISPLAY_HEIGHT}px;
      display: block;
      image-rendering: pixelated;
      border: 1px solid #d0d0c8;
      background: #ffffff;
    }}
    .bezel-label {{
      margin-top: 10px;
      color: #9ca3af;
      font-size: 11px;
      letter-spacing: 0.08em;
      text-align: center;
      font-family: ui-monospace, SFMono-Regular, Menlo, monospace;
    }}
    .meta {{
      margin-top: 14px;
      display: grid;
      grid-template-columns: repeat(2, minmax(0, 1fr));
      gap: 8px;
      font-size: 12px;
      color: var(--muted);
    }}
    .meta div {{
      background: #f8f9f7;
      border: 1px solid var(--border);
      border-radius: 6px;
      padding: 6px 10px;
    }}
    .meta strong {{
      color: var(--ink);
      display: block;
      font-size: 11px;
      margin-bottom: 2px;
    }}
    .actions {{
      margin-top: 14px;
      display: flex;
      gap: 10px;
      flex-wrap: wrap;
    }}
    h2 {{
      margin: 0 0 14px;
      font-size: 16px;
    }}
    .field {{
      margin-bottom: 12px;
    }}
    label {{
      display: block;
      font-size: 12px;
      font-weight: 600;
      margin-bottom: 4px;
    }}
    input, textarea {{
      width: 100%;
      padding: 8px 10px;
      border: 1px solid var(--border);
      border-radius: 6px;
      font-size: 14px;
      font-family: inherit;
    }}
    textarea {{
      resize: vertical;
      min-height: 70px;
    }}
    button {{
      appearance: none;
      border: none;
      border-radius: 6px;
      padding: 9px 14px;
      font-size: 13px;
      font-weight: 600;
      cursor: pointer;
      background: var(--accent);
      color: #ffffff;
    }}
    button:hover {{ opacity: 0.9; }}
    button.secondary {{
      background: #e5e7eb;
      color: var(--ink);
    }}
    button.danger {{
      background: var(--danger);
      color: #ffffff;
    }}
    .status {{
      margin-top: 12px;
      padding: 10px 12px;
      border-radius: 6px;
      font-size: 13px;
      background: #f3f4f6;
      color: var(--ink);
      min-height: 40px;
      white-space: pre-wrap;
    }}
    .status.ok {{ background: #ecfdf5; color: #065f46; border: 1px solid #a7f3d0; }}
    .status.err {{ background: #fef2f2; color: #991b1b; border: 1px solid #fecaca; }}
  </style>
</head>
<body>
  <div class="container">
    <header>
      <h1>epaper-dashboard プレビュー</h1>
      <p class="subtitle">Waveshare 4.2inch e-Paper Module ({DISPLAY_WIDTH}x{DISPLAY_HEIGHT}, 1bit モノクロ) ローカルシミュレータ</p>
    </header>

    <div class="grid">
      <section class="card">
        <div class="epaper-bezel">
          <div class="epaper-screen">
            <img id="preview-img" src="/preview/image" width="{DISPLAY_WIDTH}" height="{DISPLAY_HEIGHT}" alt="電子ペーパープレビュー画像" />
          </div>
          <div class="bezel-label">WAVESHARE 4.2&quot; E-PAPER &bull; 400&times;300 MONOCHROME</div>
        </div>

        <div class="meta">
          <div><strong>出力モード</strong>{mode_escaped}</div>
          <div><strong>地点</strong>{location_escaped}</div>
          <div><strong>フォント</strong>{font_escaped}</div>
          <div><strong>最終描画</strong><span id="rendered-at">{rendered_at_str}</span></div>
        </div>

        <div class="actions">
          <button type="button" id="refresh-btn">天気・画面を再描画</button>
          <a href="/preview/image" target="_blank" rel="noopener">
            <button type="button" class="secondary">PNG画像を直接開く</button>
          </a>
        </div>
      </section>

      <section class="card">
        <h2>テスト通知送信（Webhook 確認）</h2>
        <form id="notify-form">
          <div class="field">
            <label for="api-key">X-API-Key</label>
            <input id="api-key" name="api_key" type="password" placeholder=".env に設定した API_KEY を入力" autocomplete="off" />
          </div>
          <div class="field">
            <label for="app-name">アプリ名</label>
            <input id="app-name" name="app_name" type="text" value="LINE" required />
          </div>
          <div class="field">
            <label for="title">タイトル</label>
            <input id="title" name="title" type="text" value="帰宅連絡" required />
          </div>
          <div class="field">
            <label for="body">本文</label>
            <textarea id="body" name="body">19時ごろ最寄り駅に着きます。牛乳を買って帰ります。</textarea>
          </div>
          <div class="actions">
            <button type="submit">テスト通知を送信</button>
            <button type="button" id="clear-btn" class="danger">通知をすべてクリア</button>
          </div>
        </form>
        <div id="status-box" class="status">準備完了: X-API-Key を入力してテスト通知を送信できます。</div>
      </section>
    </div>
  </div>

  <script>
    const imgEl = document.getElementById("preview-img");
    const statusBox = document.getElementById("status-box");
    const renderedAtEl = document.getElementById("rendered-at");
    const apiKeyInput = document.getElementById("api-key");

    function setStatus(message, kind) {{
      statusBox.textContent = message;
      statusBox.className = "status" + (kind ? " " + kind : "");
    }}

    function reloadImage() {{
      imgEl.src = "/preview/image?t=" + Date.now();
      const now = new Date();
      renderedAtEl.textContent = now.toLocaleString("ja-JP", {{ hour12: false }});
    }}

    document.getElementById("refresh-btn").addEventListener("click", async () => {{
      setStatus("天気情報とプレビュー画像を再描画しています...", "");
      try {{
        const res = await fetch("/preview/refresh", {{ method: "POST" }});
        if (!res.ok) throw new Error("HTTP " + res.status);
        reloadImage();
        setStatus("画面を再描画しました。", "ok");
      }} catch (err) {{
        setStatus("再描画に失敗しました: " + err.message, "err");
      }}
    }});

    document.getElementById("notify-form").addEventListener("submit", async (e) => {{
      e.preventDefault();
      const payload = {{
        app_name: document.getElementById("app-name").value,
        title: document.getElementById("title").value,
        body: document.getElementById("body").value,
      }};
      setStatus("テスト通知を送信中...", "");
      try {{
        const res = await fetch("/api/v1/notifications", {{
          method: "POST",
          headers: {{
            "Content-Type": "application/json",
            "X-API-Key": apiKeyInput.value,
          }},
          body: JSON.stringify(payload),
        }});
        const data = await res.json();
        if (!res.ok) {{
          setStatus("送信失敗 (" + res.status + "): " + (data.detail || "エラー"), "err");
          return;
        }}
        reloadImage();
        setStatus("通知を登録しました (ID: " + data.id + ")。プレビューを更新しました。", "ok");
      }} catch (err) {{
        setStatus("通信エラー: " + err.message, "err");
      }}
    }});

    document.getElementById("clear-btn").addEventListener("click", async () => {{
      setStatus("通知をクリアしています...", "");
      try {{
        const res = await fetch("/api/v1/notifications", {{
          method: "DELETE",
          headers: {{
            "X-API-Key": apiKeyInput.value,
          }},
        }});
        const data = await res.json();
        if (!res.ok) {{
          setStatus("クリア失敗 (" + res.status + "): " + (data.detail || "エラー"), "err");
          return;
        }}
        reloadImage();
        setStatus(data.message || "通知をクリアしました。", "ok");
      }} catch (err) {{
        setStatus("通信エラー: " + err.message, "err");
      }}
    }});
  </script>
</body>
</html>
"""
    return HTMLResponse(content=page_html)

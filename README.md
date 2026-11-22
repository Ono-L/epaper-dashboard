# epaper-dashboard

Raspberry Pi Zero 2 W + Waveshare 4.2inch e-Paper Module (400x300, 白黒, SPI) 向けのローカル電子ペーパーダッシュボード（Phase 1: ローカル開発プロトタイプ）。

## 主な機能
- **天気取得（Open-Meteo API）**: API キー不要で現在天気・気温・最高/最低気温・降水確率を取得（デフォルト: 東京）
- **通知受信 Webhook API**: iPhone ショートカット等から `POST /api/v1/notifications` で通知を受信し、SQLite に永続化（`X-API-Key` 認証必須）
- **電子ペーパー描画エンジン**: 400x300 ピクセルの 1bit モノクロ PNG を日本語フォント（IPAexゴシック）で生成
- **ドライバ抽象化**: ローカル開発用モック（`DISPLAY_MODE=mock` -> `output/preview.png`）と将来の実機ドライバ（`DISPLAY_MODE=waveshare`）を分離
- **ブラウザプレビュー**: `http://localhost:8000/preview` で 400x300 画像の確認とテスト通知の送信が可能

## クイックスタート（Docker）

```bash
# 1. 環境変数ファイルを準備（任意：未作成時はデフォルト開発キーで起動）
cp .env.example .env

# 2. コンテナのビルドと起動
docker compose up -d --build

# 3. テストの実行
docker compose exec app pytest -v
```

起動後、ブラウザで `http://localhost:8000/preview` を開いてプレビューを確認できます。

## API 利用例

```bash
# 通知送信（X-API-Key 必須）
curl -X POST http://localhost:8000/api/v1/notifications \
  -H "Content-Type: application/json" \
  -H "X-API-Key: change-me-local-dev-key" \
  -d '{"app_name": "LINE", "title": "買い物メモ", "body": "帰りに牛乳とパンを買う"}'

# 通知一覧取得
curl http://localhost:8000/api/v1/notifications \
  -H "X-API-Key: change-me-local-dev-key"

# 通知クリア
curl -X DELETE http://localhost:8000/api/v1/notifications \
  -H "X-API-Key: change-me-local-dev-key"
```

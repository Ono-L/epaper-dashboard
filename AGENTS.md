# AGENTS.md

このリポジトリ（`epaper-dashboard`）で開発・保守を行う AI エージェントおよび開発者向けのルールを定義します。

## プロジェクト概要
- 目的: Raspberry Pi Zero 2 W + Waveshare 4.2inch e-Paper Module (400x300, 白黒, SPI) 向けのローカル電子ペーパーダッシュボード
- Phase 1 スコープ: Mac ローカル開発環境（Docker + モックドライバ）でのプロトタイプ構築
- 技術スタック: Python 3.12 / FastAPI / Pydantic v2 / Pillow / httpx / SQLite / pytest / Docker

## コミュニケーション・ドキュメント・Git ルール
- **日本語を基本とする**: 回答、コード内のコメント、docstring、ドキュメントはすべて日本語で記述すること。
- **Git コミットメッセージ**: Conventional Commits 形式を日本語で記述すること。
  - 例: `feat: 通知受信 API と X-API-Key 認証を実装`
  - 例: `fix: 日本語テキストの折り返し省略幅を修正`
  - 例: `test: 400x300 モノクロ画像生成テストを追加`
  - 例: `docs: AGENTS.md とセットアップ手順を整備`

## コーディング規約
- **型ヒント厳守**: すべての関数・メソッドの引数、戻り値、クラス属性に Python 3.12 の型ヒントを明記すること（`from __future__ import annotations` を推奨）。
- **Pydantic v2**: リクエスト・レスポンス・設定・ドメインモデルは Pydantic v2（`BaseModel`, `BaseSettings`）で厳密に定義すること。
- **ドライバ抽象化**: 描画ロジック（`src/display/renderer.py`）と出力デバイス（`src/display/base.py`, `mock.py`, `waveshare.py`）を明確に分離し、実機移行時に描画ロジックを変更不要にすること。
- **解像度・色空間**: 描画エンジンは常に 400x300 ピクセルの 1bit モノクロ（Pillow モード `"1"`）画像を生成すること。

## セキュリティルール（厳守）
- **`.env` や API キー、シークレット情報を絶対に Git コミットしないこと**。
- 環境変数のテンプレートは `.env.example` のみに記述し、ダミー値（例: `change-me-local-dev-key`）のみ記載すること。
- 認証キーの比較にはタイミング攻撃対策として `hmac.compare_digest` を使用すること。
- サーバー側で `API_KEY` が未設定または空文字の場合、認証を必ず拒否（HTTP 401）すること。

## 開発・テストコマンド
```bash
# コンテナビルド＆起動
docker compose up -d --build

# コンテナ内で pytest 実行
docker compose exec app pytest -v

# ログ確認
docker compose logs -f app
```

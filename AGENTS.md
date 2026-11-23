# AGENTS.md - Google Antigravity / AI エージェント共通開発ルール

このリポジトリ（`epaper-dashboard`）で開発・保守を行う Google Antigravity・Claude Code・Gemini を含むすべての AI エージェントは、以下のルールおよびワークスペース共通の `../AGENTS.md` を厳守してください。

## 1. プロジェクト概要・仕様駆動開発（SDD）原則
- **目的**: Raspberry Pi Zero 2 W + Waveshare 4.2inch e-Paper Module (400x300, 白黒, SPI) 向けのローカル電子ペーパーダッシュボード
- **Phase 1 スコープ**: Mac ローカル開発環境（Docker + モックドライバ）でのプロトタイプ構築
- **技術スタック**: Python 3.12 / FastAPI / Pydantic v2 / Pillow / httpx / SQLite / pytest / Docker
- **仕様・既存設計の遵守**: 実装・変更を行う前に `README.md` や既存設計・モデル定義を唯一の正本（Single Source of Truth）として確認すること。
- **勝手なライブラリ導入の禁止**: `pyproject.toml` に定義されていない外部ライブラリやフレームワークを合意なく勝手に追加しないこと。
- **未確定事項（TBD）の独断実装禁止**: Phase 2（実機 SPI 接続や外部通知連携拡張など）の未確定仕様を独断で外部サービス導入・実装しないこと。

## 2. コーディング・モジュール分割規約
- **型ヒント厳守**: すべての関数・メソッドの引数、戻り値、クラス属性に Python 3.12 の型ヒントを明記すること（`from __future__ import annotations` を推奨）。
- **Pydantic v2**: リクエスト・レスポンス・設定・ドメインモデルは Pydantic v2（`BaseModel`, `BaseSettings`）で厳密に定義すること。
- **単一責任・ファイル分割**: 1 ファイル 200 行以内を目安とし、API ルート・認証・サービスロジック・ストレージ・描画エンジン・出力ドライバを明確に分離すること。
- **ドライバ抽象化**: 描画ロジック（`src/display/renderer.py`）と出力デバイス（`src/display/base.py`, `mock.py`, `waveshare.py`）を明確に分離し、実機移行時に描画ロジックを変更不要にすること。
- **解像度・色空間**: 描画エンジンは常に 400x300 ピクセルの 1bit モノクロ（Pillow モード `"1"`）画像を生成すること。

## 3. セキュリティ・データ保護ルール（厳守）
- **秘密情報の保護**: `.env` や API キー、シークレット情報をソースコード・テスト・ログ・Git 履歴に絶対にコミットしないこと。
- **テンプレート運用**: 環境変数のテンプレートは `.env.example` のみに記述し、ダミー値（例: `change-me-local-dev-key`）のみ記載すること。
- **認証とフェイルクローズ**: 認証キーの比較にはタイミング攻撃対策として `hmac.compare_digest` を使用し、サーバー側で `API_KEY` が未設定または空文字の場合は認証を必ず拒否（HTTP 401）すること。
- **SQL インジェクション防止**: SQLite 操作は必ずパラメータバインド（プレースホルダ）を使用し、生の SQL 文字列結合を行わないこと。

## 4. コミュニケーション・コミット規約
- **日本語を基本とする**: 回答、設計計画、コード内のコメント、docstring、ドキュメントはすべて日本語で記述すること。
- **Git コミットメッセージ**: Conventional Commits 形式に従い、**メッセージ本文は必ず日本語**で記述すること。
  - 例: `feat: 通知受信 API と X-API-Key 認証を実装`
  - 例: `fix: 日本語テキストの折り返し省略幅を修正`
  - 例: `test: 400x300 モノクロ画像生成テストを追加`
  - 例: `docs: AGENTS.md とセットアップ手順を整備`

## 5. 開発・検証・コミット前チェック
変更後は必ずテストを実行しエラー 0 を確認したうえで、`git status` で `.env` や不要な一時ファイルがステージに含まれていないことを確認すること。

```bash
# コンテナビルド＆起動
docker compose up -d --build

# コンテナ内で pytest 実行
docker compose exec app pytest -v

# ログ確認
docker compose logs -f app
```

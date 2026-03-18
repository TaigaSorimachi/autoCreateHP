# 技術スタック

## バックエンド
- フレームワーク: Flask 3.0+
- 言語: Python 3.12+
- テンプレートエンジン: Jinja2
- 画像処理: Pillow

## 外部API
- Google Places API（店舗検索・写真取得）
- Unsplash API（フォールバック画像）

## データ
- JSON（SQLite移行予定）

## 開発環境
- 環境変数管理: python-dotenv
- HTTP通信: requests
- 仮想環境: venv

## 本番インフラ（予定）
- ホスティング: Vercel / Railway
- DB: SQLite → PostgreSQL
- CI/CD: GitHub Actions

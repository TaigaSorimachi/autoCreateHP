# アポ太郎 — AI営業自動化システム

## プロジェクト概要

指定エリアの飲食店を自動発見 → **画像付きリッチなHP**を自動生成 → 一覧管理するローカルシステム。
将来的にDM自動送信・Telegram Bot連携まで拡張予定。

## 技術スタック

- **バックエンド**: Python 3.12 + Flask
- **HP生成**: Jinja2テンプレート + 静的HTML出力
- **画像取得**: Google Places API (店舗写真) + Unsplash API (雰囲気写真フォールバック)
- **スタイリング**: 各HPはsingle-file HTML（CSS/JS埋め込み）。Google Fonts使用
- **データ**: JSON（SQLite移行は Phase 2）
- **CLI**: argparse ベースの `pipeline.py`
- **スケジューラ**: 内蔵（cron不要）

## ディレクトリ構成

```
apo-taro/
├── CLAUDE.md                 # ← このファイル
├── config.py                 # 環境変数・設定
├── app.py                    # Flask ダッシュボード + API
├── pipeline.py               # 全自動パイプライン（CLI + スケジューラ）
├── discovery.py              # ビジネス発見（Google Places API）
├── images.py                 # 画像取得・キャッシュ（Google Places Photo + Unsplash）
├── generator.py              # HP生成エンジン（Jinja2テンプレート）
├── templates/
│   ├── dashboard.html        # 管理ダッシュボード
│   └── hp/                   # HP用テンプレート群
│       ├── base.html         # 共通ベーステンプレート
│       ├── restaurant.html   # 飲食店向け（デフォルト）
│       ├── bar.html          # バー・クラブ向け
│       ├── cafe.html         # カフェ向け
│       └── luxury.html       # 高級店向け
├── static/
│   └── placeholder/          # フォールバック用SVGパターン
├── generated_sites/          # 生成済みHP出力先
│   ├── discovered_businesses.json
│   └── {store_name}/
│       ├── index.html
│       ├── images/           # ダウンロード済み画像
│       └── meta.json
├── skills/                   # Claude Code用カスタムスキル
│   └── hp-generator/
│       └── SKILL.md
├── requirements.txt
└── .env.example
```

## 環境変数

```bash
# 必須（実データ使用時）
GOOGLE_PLACES_API_KEY=...     # Google Places API（検索 + 写真取得）

# 推奨（画像フォールバック用）
UNSPLASH_ACCESS_KEY=...       # Unsplash API（雰囲気写真）

# 任意（未設定ならモックモードで動作）
```

## コマンド

```bash
# セットアップ
pip install -r requirements.txt

# ダッシュボード起動
python app.py

# 全自動パイプライン
python pipeline.py --areas "新宿,渋谷,六本木,銀座,恵比寿"

# スケジューラー（毎朝9時自動実行）
python pipeline.py --areas "新宿,渋谷" --schedule 09:00

# 単体テスト
python -m pytest tests/ -v
```

## 開発ルール

1. **HPは必ず画像付き** — 画像が取得できない場合はSVGプレースホルダーを生成（真っ白なセクションは絶対NG）
2. **業種別テンプレート** — 寿司屋とラーメン屋で同じデザインにしない。カラー・レイアウト・フォントを業種で分ける
3. **モバイルファースト** — 全HPがスマホで美しく表示されること
4. **single-file HTML** — 外部CSSファイルなし。1つのindex.htmlに全部入り。画像のみ外部ファイル
5. **日本語** — UIもコメントも日本語。変数名は英語OK
6. **APIキーなしでも動く** — モックデータ + SVGプレースホルダーで完全動作すること

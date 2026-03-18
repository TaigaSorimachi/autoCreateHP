"""
アポ太郎 — 設定ファイル
Google Places API キーなどの設定を管理
"""

import os

# Google Places API Key
# 環境変数から取得、なければモックモードで動作
GOOGLE_PLACES_API_KEY = os.environ.get("GOOGLE_PLACES_API_KEY", "")

# 生成サイトの出力ディレクトリ
GENERATED_SITES_DIR = os.path.join(os.path.dirname(__file__), "generated_sites")

# Flaskサーバー設定
HOST = "127.0.0.1"
PORT = 5000

# HP生成設定
DEFAULT_AREA = "福岡市中央区中洲"
DEFAULT_BUSINESS_TYPE = "restaurant"
DEFAULT_RADIUS = 1000  # メートル

# モックモード（APIキーがない場合に自動有効）
USE_MOCK = not bool(GOOGLE_PLACES_API_KEY)

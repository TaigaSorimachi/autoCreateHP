"""
アポ太郎 — 設定ファイル
環境変数・API設定・画像設定を管理
"""

import os
from pathlib import Path

# .env ファイル読み込み
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

# ──────────────────────────────
#  APIキー設定
# ──────────────────────────────
GOOGLE_PLACES_API_KEY = os.environ.get("GOOGLE_PLACES_API_KEY", "")
UNSPLASH_ACCESS_KEY = os.environ.get("UNSPLASH_ACCESS_KEY", "")

# ──────────────────────────────
#  モード判定
# ──────────────────────────────
USE_MOCK = not bool(GOOGLE_PLACES_API_KEY)
HAS_UNSPLASH = bool(UNSPLASH_ACCESS_KEY)

# ──────────────────────────────
#  パス設定
# ──────────────────────────────
BASE_DIR = Path(__file__).parent
GENERATED_SITES_DIR = str(BASE_DIR / "generated_sites")
TEMPLATES_DIR = str(BASE_DIR / "templates")
STATIC_DIR = str(BASE_DIR / "static")

# ──────────────────────────────
#  画像設定
# ──────────────────────────────
MAX_PHOTOS_PER_STORE = 5          # 店舗あたりの最大画像取得数
PHOTO_MAX_WIDTH_HERO = 1920       # ヒーロー画像の最大幅
PHOTO_MAX_WIDTH_GALLERY = 800     # ギャラリー画像の最大幅
PHOTO_QUALITY = 85                # JPEG圧縮品質

# 画像スロット定義
IMAGE_SLOTS = {
    "hero": {"width": 1920, "height": 1080},
    "gallery_1": {"width": 800, "height": 600},
    "gallery_2": {"width": 800, "height": 600},
    "gallery_3": {"width": 800, "height": 600},
    "gallery_4": {"width": 800, "height": 600},
    "atmosphere": {"width": 1200, "height": 400},
    "og": {"width": 1200, "height": 630},
}

# ──────────────────────────────
#  Flaskサーバー設定
# ──────────────────────────────
HOST = "127.0.0.1"
PORT = 5000

# ──────────────────────────────
#  デフォルト検索設定
# ──────────────────────────────
DEFAULT_AREA = "福岡市中央区中洲"
DEFAULT_BUSINESS_TYPE = "restaurant"
DEFAULT_RADIUS = 1000  # メートル

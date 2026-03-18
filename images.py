"""
アポ太郎 — 画像取得・キャッシュ管理モジュール
Google Places Photo API → Unsplash API → SVGプレースホルダーのフォールバックチェーン
"""

import os
import json
import urllib.request
import urllib.parse
from io import BytesIO
from pathlib import Path

try:
    from PIL import Image
except ImportError:
    Image = None

from config import (
    GOOGLE_PLACES_API_KEY,
    UNSPLASH_ACCESS_KEY,
    PEXELS_API_KEY,
    USE_MOCK,
    HAS_UNSPLASH,
    HAS_PEXELS,
    PHOTO_MAX_WIDTH_HERO,
    PHOTO_MAX_WIDTH_GALLERY,
    PHOTO_QUALITY,
    MAX_PHOTOS_PER_STORE,
)


# ──────────────────────────────
#  プレースホルダーテーマ
# ──────────────────────────────
PLACEHOLDER_THEMES = {
    "sushi": {"bg": "#0f0f1a", "accent": "#d4a76a", "accent2": "#b8935a", "icon": "🍣"},
    "ramen": {"bg": "#1a100a", "accent": "#ff6b35", "accent2": "#ffd166", "icon": "🍜"},
    "yakiniku": {"bg": "#120e0c", "accent": "#e04040", "accent2": "#d4a020", "icon": "🥩"},
    "yakitori": {"bg": "#1a100a", "accent": "#f59e0b", "accent2": "#ef4444", "icon": "🍗"},
    "izakaya": {"bg": "#12101a", "accent": "#e8a030", "accent2": "#ef4444", "icon": "🏮"},
    "bar": {"bg": "#08080c", "accent": "#9060e0", "accent2": "#6366f1", "icon": "🍸"},
    "cafe": {"bg": "#1a1612", "accent": "#c8a882", "accent2": "#a07850", "icon": "☕"},
    "french": {"bg": "#0c0c14", "accent": "#b8a088", "accent2": "#8b7355", "icon": "🍷"},
    "italian": {"bg": "#10100e", "accent": "#c85040", "accent2": "#50a040", "icon": "🍝"},
    "tempura": {"bg": "#141210", "accent": "#c8a050", "accent2": "#a07830", "icon": "🍤"},
    "tonkatsu": {"bg": "#16120e", "accent": "#d4a040", "accent2": "#b08020", "icon": "🐷"},
    "soba": {"bg": "#12110e", "accent": "#8a8070", "accent2": "#6a6050", "icon": "🍜"},
    "unagi": {"bg": "#100e0c", "accent": "#d4af37", "accent2": "#b8860b", "icon": "🐟"},
    "chinese": {"bg": "#180808", "accent": "#e03030", "accent2": "#d4a020", "icon": "🐉"},
    "korean": {"bg": "#120e0e", "accent": "#e04040", "accent2": "#40a050", "icon": "🇰🇷"},
    "luxury": {"bg": "#0c0c14", "accent": "#b8a088", "accent2": "#8a7060", "icon": "✨"},
    "default": {"bg": "#0a0a10", "accent": "#5070e0", "accent2": "#60a5fa", "icon": "🏪"},
}

# Unsplash検索キーワード（業種別）
UNSPLASH_KEYWORDS = {
    "sushi": "japanese sushi restaurant",
    "ramen": "japanese ramen noodle",
    "yakiniku": "japanese bbq yakiniku",
    "yakitori": "japanese yakitori grilled chicken",
    "izakaya": "japanese izakaya bar food",
    "bar": "cocktail bar nightlife",
    "cafe": "coffee cafe interior",
    "french": "french restaurant fine dining",
    "italian": "italian restaurant pasta",
    "tempura": "japanese tempura fried",
    "tonkatsu": "japanese pork cutlet",
    "soba": "japanese soba noodle",
    "unagi": "japanese eel unagi",
    "chinese": "chinese restaurant dim sum",
    "korean": "korean bbq restaurant",
    "luxury": "luxury fine dining restaurant",
    "default": "restaurant food interior",
}


# Pexels検索キーワード（業種別）
# Pexelsは英語プラットフォームなので、具体的な英語キーワードを使用
PEXELS_KEYWORDS = {
    "sushi": "nigiri sushi plate",
    "ramen": "ramen noodle bowl",
    "yakiniku": "yakiniku grilled meat charcoal",
    "yakitori": "yakitori chicken skewer",
    "izakaya": "izakaya japanese food",
    "bar": "cocktail bar dark interior",
    "cafe": "coffee cafe latte art",
    "french": "french fine dining plated",
    "italian": "italian pasta dish",
    "tempura": "tempura shrimp japanese",
    "tonkatsu": "tonkatsu pork cutlet",
    "soba": "soba noodle japanese",
    "unagi": "unagi eel grilled rice",
    "chinese": "chinese dim sum restaurant",
    "korean": "korean bbq samgyeopsal",
    "luxury": "luxury fine dining restaurant",
    "default": "japanese restaurant food",
}


class ImageFetcher:
    """画像取得・キャッシュ管理クラス"""

    def __init__(self):
        self.google_api_key = GOOGLE_PLACES_API_KEY
        self.unsplash_key = UNSPLASH_ACCESS_KEY
        self.pexels_key = PEXELS_API_KEY

    def fetch_for_business(self, business: dict, output_dir: str, category: str = "default") -> dict:
        """
        ビジネスの画像を取得してローカルに保存

        Args:
            business: ビジネス情報dict
            output_dir: 画像保存先ディレクトリ
            category: 業種カテゴリ（プレースホルダー生成用）

        Returns:
            {
                "hero": "images/hero.jpg" or "images/hero.svg",
                "gallery": ["images/gallery_1.jpg", ...],
                "atmosphere": "images/atmosphere.jpg" or None,
                "source": "google_places" | "unsplash" | "placeholder"
            }
        """
        images_dir = os.path.join(output_dir, "images")
        os.makedirs(images_dir, exist_ok=True)

        result = {
            "hero": None,
            "gallery": [],
            "atmosphere": None,
            "source": "placeholder",
        }

        # 既存の画像をチェック（キャッシュ）
        if self._check_cached_images(images_dir, result):
            return result

        # Priority 1: Google Places Photo API
        photo_refs = business.get("photo_references", [])
        if not photo_refs and business.get("photo_ref"):
            photo_refs = [business["photo_ref"]]

        if photo_refs and self.google_api_key:
            if self._fetch_google_places_photos(photo_refs, images_dir, result):
                result["source"] = "google_places"
                return result

        # Priority 2: Pexels API
        if self.pexels_key:
            keyword = PEXELS_KEYWORDS.get(category, PEXELS_KEYWORDS["default"])
            if self._fetch_pexels(keyword, images_dir, result):
                result["source"] = "pexels"
                return result

        # Priority 3: Unsplash API
        if self.unsplash_key:
            keyword = UNSPLASH_KEYWORDS.get(category, UNSPLASH_KEYWORDS["default"])
            if self._fetch_unsplash(keyword, images_dir, result):
                result["source"] = "unsplash"
                return result

        # Priority 4: SVG プレースホルダー生成
        self._generate_svg_placeholders(category, images_dir, result)
        result["source"] = "placeholder"
        return result

    def _check_cached_images(self, images_dir: str, result: dict) -> bool:
        """既存のキャッシュ画像をチェック"""
        hero_jpg = os.path.join(images_dir, "hero.jpg")
        hero_svg = os.path.join(images_dir, "hero.svg")

        if os.path.exists(hero_jpg):
            result["hero"] = "images/hero.jpg"
            result["source"] = "cached"
        elif os.path.exists(hero_svg):
            result["hero"] = "images/hero.svg"
            result["source"] = "placeholder"
        else:
            return False

        # ギャラリー画像をチェック
        for i in range(1, 5):
            gallery_path = os.path.join(images_dir, f"gallery_{i}.jpg")
            if os.path.exists(gallery_path):
                result["gallery"].append(f"images/gallery_{i}.jpg")
            else:
                gallery_svg = os.path.join(images_dir, f"gallery_{i}.svg")
                if os.path.exists(gallery_svg):
                    result["gallery"].append(f"images/gallery_{i}.svg")

        atmosphere_path = os.path.join(images_dir, "atmosphere.jpg")
        if os.path.exists(atmosphere_path):
            result["atmosphere"] = "images/atmosphere.jpg"

        return True

    def _fetch_google_places_photos(
        self, photo_refs: list, images_dir: str, result: dict
    ) -> bool:
        """Google Places Photo API から画像を取得"""
        if not self.google_api_key:
            return False

        success = False
        slots = ["hero"] + [f"gallery_{i}" for i in range(1, min(len(photo_refs), 5))]

        for i, ref in enumerate(photo_refs[:MAX_PHOTOS_PER_STORE]):
            if i >= len(slots):
                break

            slot = slots[i]
            max_width = PHOTO_MAX_WIDTH_HERO if slot == "hero" else PHOTO_MAX_WIDTH_GALLERY

            url = (
                f"https://maps.googleapis.com/maps/api/place/photo"
                f"?maxwidth={max_width}"
                f"&photo_reference={ref}"
                f"&key={self.google_api_key}"
            )

            try:
                req = urllib.request.Request(url)
                with urllib.request.urlopen(req, timeout=10) as resp:
                    image_data = resp.read()

                output_path = os.path.join(images_dir, f"{slot}.jpg")
                if self._save_and_optimize_image(image_data, output_path, max_width):
                    if slot == "hero":
                        result["hero"] = "images/hero.jpg"
                    else:
                        result["gallery"].append(f"images/{slot}.jpg")
                    success = True

            except Exception as e:
                print(f"[WARNING] Google Places photo fetch failed: {e}")
                continue

        return success

    def _fetch_unsplash(self, query: str, images_dir: str, result: dict) -> bool:
        """Unsplash API から画像を取得"""
        if not self.unsplash_key:
            return False

        url = (
            f"https://api.unsplash.com/search/photos"
            f"?query={urllib.parse.quote(query)}"
            f"&per_page={MAX_PHOTOS_PER_STORE}"
            f"&orientation=landscape"
        )

        try:
            req = urllib.request.Request(url)
            req.add_header("Authorization", f"Client-ID {self.unsplash_key}")

            with urllib.request.urlopen(req, timeout=10) as resp:
                data = json.loads(resp.read())

            photos = data.get("results", [])
            if not photos:
                return False

            success = False
            slots = ["hero"] + [f"gallery_{i}" for i in range(1, 5)]

            for i, photo in enumerate(photos[:MAX_PHOTOS_PER_STORE]):
                if i >= len(slots):
                    break

                slot = slots[i]
                max_width = PHOTO_MAX_WIDTH_HERO if slot == "hero" else PHOTO_MAX_WIDTH_GALLERY

                # raw URLにwidthパラメータを追加
                image_url = photo.get("urls", {}).get("regular", "")
                if not image_url:
                    continue

                try:
                    req = urllib.request.Request(image_url)
                    with urllib.request.urlopen(req, timeout=15) as resp:
                        image_data = resp.read()

                    output_path = os.path.join(images_dir, f"{slot}.jpg")
                    if self._save_and_optimize_image(image_data, output_path, max_width):
                        if slot == "hero":
                            result["hero"] = "images/hero.jpg"
                        else:
                            result["gallery"].append(f"images/{slot}.jpg")
                        success = True

                except Exception as e:
                    print(f"[WARNING] Unsplash image download failed: {e}")
                    continue

            return success

        except Exception as e:
            print(f"[WARNING] Unsplash API call failed: {e}")
            return False

    def _fetch_pexels(self, query: str, images_dir: str, result: dict) -> bool:
        """Pexels API から画像を取得"""
        if not self.pexels_key:
            return False

        url = (
            f"https://api.pexels.com/v1/search"
            f"?query={urllib.parse.quote(query)}"
            f"&per_page={MAX_PHOTOS_PER_STORE}"
            f"&orientation=landscape"
        )

        try:
            req = urllib.request.Request(url)
            req.add_header("Authorization", self.pexels_key)
            req.add_header("User-Agent", "ApoTaro/1.0")

            with urllib.request.urlopen(req, timeout=10) as resp:
                data = json.loads(resp.read())

            photos = data.get("photos", [])
            if not photos:
                print(f"[WARNING] Pexels: no photos found for '{query}'")
                return False

            success = False
            slots = ["hero"] + [f"gallery_{i}" for i in range(1, 5)]

            for i, photo in enumerate(photos[:MAX_PHOTOS_PER_STORE]):
                if i >= len(slots):
                    break

                slot = slots[i]
                # hero は large2x (1920px)、gallery は large (940px)
                src = photo.get("src", {})
                if slot == "hero":
                    image_url = src.get("large2x", src.get("large", ""))
                    max_width = PHOTO_MAX_WIDTH_HERO
                else:
                    image_url = src.get("large", src.get("medium", ""))
                    max_width = PHOTO_MAX_WIDTH_GALLERY

                if not image_url:
                    continue

                try:
                    dl_req = urllib.request.Request(image_url)
                    dl_req.add_header("User-Agent", "ApoTaro/1.0")
                    with urllib.request.urlopen(dl_req, timeout=15) as resp:
                        image_data = resp.read()

                    output_path = os.path.join(images_dir, f"{slot}.jpg")
                    if self._save_and_optimize_image(image_data, output_path, max_width):
                        if slot == "hero":
                            result["hero"] = "images/hero.jpg"
                        else:
                            result["gallery"].append(f"images/{slot}.jpg")
                        success = True
                        print(f"  [PEXELS] {slot} saved ({photo.get('photographer', 'unknown')})")

                except Exception as e:
                    print(f"[WARNING] Pexels image download failed: {e}")
                    continue

            return success

        except Exception as e:
            print(f"[WARNING] Pexels API call failed: {e}")
            return False

    def _save_and_optimize_image(
        self, image_data: bytes, output_path: str, max_width: int
    ) -> bool:
        """画像を最適化して保存"""
        if Image is None:
            # Pillow未インストールの場合はそのまま保存
            with open(output_path, "wb") as f:
                f.write(image_data)
            return True

        try:
            img = Image.open(BytesIO(image_data))

            # RGB変換（RGBA対応）
            if img.mode in ("RGBA", "P"):
                img = img.convert("RGB")

            # リサイズ
            if img.width > max_width:
                ratio = max_width / img.width
                new_height = int(img.height * ratio)
                img = img.resize((max_width, new_height), Image.Resampling.LANCZOS)

            # JPEG保存
            img.save(output_path, "JPEG", quality=PHOTO_QUALITY, optimize=True)
            return True

        except Exception as e:
            print(f"[WARNING] Image optimization failed: {e}")
            # 失敗時はそのまま保存を試みる
            try:
                with open(output_path, "wb") as f:
                    f.write(image_data)
                return True
            except:
                return False

    def _generate_svg_placeholders(
        self, category: str, images_dir: str, result: dict
    ) -> None:
        """業種別SVGプレースホルダーを生成"""
        theme = PLACEHOLDER_THEMES.get(category, PLACEHOLDER_THEMES["default"])

        # ヒーロー画像
        hero_svg = self._generate_hero_svg(theme, 1920, 1080)
        hero_path = os.path.join(images_dir, "hero.svg")
        with open(hero_path, "w", encoding="utf-8") as f:
            f.write(hero_svg)
        result["hero"] = "images/hero.svg"

        # ギャラリー画像
        for i in range(1, 5):
            gallery_svg = self._generate_gallery_svg(theme, 800, 600, i)
            gallery_path = os.path.join(images_dir, f"gallery_{i}.svg")
            with open(gallery_path, "w", encoding="utf-8") as f:
                f.write(gallery_svg)
            result["gallery"].append(f"images/gallery_{i}.svg")

    def _generate_hero_svg(self, theme: dict, width: int, height: int) -> str:
        """ヒーロー用SVGプレースホルダー（メッシュグラデーション + ノイズ）"""
        bg = theme["bg"]
        accent = theme["accent"]
        accent2 = theme.get("accent2", accent)
        icon = theme["icon"]

        return f'''<svg viewBox="0 0 {width} {height}" xmlns="http://www.w3.org/2000/svg">
    <defs>
        <radialGradient id="hMesh1" cx="20%" cy="30%" r="50%">
            <stop offset="0%" stop-color="{accent}" stop-opacity="0.18"/>
            <stop offset="100%" stop-color="{accent}" stop-opacity="0"/>
        </radialGradient>
        <radialGradient id="hMesh2" cx="80%" cy="70%" r="45%">
            <stop offset="0%" stop-color="{accent2}" stop-opacity="0.14"/>
            <stop offset="100%" stop-color="{accent2}" stop-opacity="0"/>
        </radialGradient>
        <radialGradient id="hMesh3" cx="60%" cy="20%" r="35%">
            <stop offset="0%" stop-color="{accent}" stop-opacity="0.08"/>
            <stop offset="100%" stop-color="{accent}" stop-opacity="0"/>
        </radialGradient>
        <filter id="hNoise">
            <feTurbulence type="fractalNoise" baseFrequency="0.65" numOctaves="3" stitchTiles="stitch"/>
            <feColorMatrix type="saturate" values="0"/>
        </filter>
        <linearGradient id="hFade" x1="0%" y1="0%" x2="0%" y2="100%">
            <stop offset="0%" stop-color="{bg}" stop-opacity="0.1"/>
            <stop offset="70%" stop-color="{bg}" stop-opacity="0.4"/>
            <stop offset="100%" stop-color="{bg}" stop-opacity="0.85"/>
        </linearGradient>
    </defs>
    <rect width="{width}" height="{height}" fill="{bg}"/>
    <rect width="{width}" height="{height}" fill="url(#hMesh1)"/>
    <rect width="{width}" height="{height}" fill="url(#hMesh2)"/>
    <rect width="{width}" height="{height}" fill="url(#hMesh3)"/>
    <rect width="{width}" height="{height}" filter="url(#hNoise)" opacity="0.06"/>
    <rect width="{width}" height="{height}" fill="url(#hFade)"/>
    <text x="{width//2}" y="{height//2 - 20}" text-anchor="middle" font-size="100" opacity="0.08">{icon}</text>
</svg>'''

    def _generate_gallery_svg(self, theme: dict, width: int, height: int, index: int) -> str:
        """ギャラリー用SVGプレースホルダー（メッシュグラデーション + ノイズ）"""
        bg = theme["bg"]
        accent = theme["accent"]
        accent2 = theme.get("accent2", accent)
        icon = theme["icon"]
        # グラデーション位置をインデックスごとにずらす
        cx1 = 25 + (index * 15) % 50
        cy1 = 30 + (index * 20) % 40

        return f'''<svg viewBox="0 0 {width} {height}" xmlns="http://www.w3.org/2000/svg">
    <defs>
        <radialGradient id="gMesh{index}a" cx="{cx1}%" cy="{cy1}%" r="50%">
            <stop offset="0%" stop-color="{accent}" stop-opacity="0.15"/>
            <stop offset="100%" stop-color="{accent}" stop-opacity="0"/>
        </radialGradient>
        <radialGradient id="gMesh{index}b" cx="{100 - cx1}%" cy="{100 - cy1}%" r="45%">
            <stop offset="0%" stop-color="{accent2}" stop-opacity="0.12"/>
            <stop offset="100%" stop-color="{accent2}" stop-opacity="0"/>
        </radialGradient>
        <filter id="gNoise{index}">
            <feTurbulence type="fractalNoise" baseFrequency="0.7" numOctaves="3" stitchTiles="stitch"/>
            <feColorMatrix type="saturate" values="0"/>
        </filter>
    </defs>
    <rect width="{width}" height="{height}" fill="{bg}"/>
    <rect width="{width}" height="{height}" fill="url(#gMesh{index}a)"/>
    <rect width="{width}" height="{height}" fill="url(#gMesh{index}b)"/>
    <rect width="{width}" height="{height}" filter="url(#gNoise{index})" opacity="0.05"/>
    <text x="{width//2}" y="{height//2}" text-anchor="middle" font-size="48" opacity="0.1">{icon}</text>
</svg>'''


# モジュール直接実行時のテスト
if __name__ == "__main__":
    fetcher = ImageFetcher()

    # テスト用ビジネスデータ
    test_biz = {
        "name": "テスト寿司店",
        "place_id": "test_001",
    }

    import tempfile
    with tempfile.TemporaryDirectory() as tmpdir:
        result = fetcher.fetch_for_business(test_biz, tmpdir, "sushi")
        print(f"Result: {result}")
        print(f"Files: {os.listdir(os.path.join(tmpdir, 'images'))}")

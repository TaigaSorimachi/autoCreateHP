"""
アポ太郎 — HP自動生成エンジン
Jinja2テンプレートベースで業種別リッチHPを自動生成
"""

import os
import json
import hashlib
from datetime import datetime
from jinja2 import Environment, FileSystemLoader, select_autoescape

from config import GENERATED_SITES_DIR, TEMPLATES_DIR
from images import ImageFetcher, PLACEHOLDER_THEMES


# ──────────────────────────────
#  業種別カラースキーム
# ──────────────────────────────
COLOR_SCHEMES = {
    "sushi": {
        "bg": "#0f0f1a", "surface": "#16162a", "accent1": "#d4a76a", "accent2": "#b8935a",
        "text": "#f0ebe3", "muted": "#9a8c7e",
        "hero_overlay": "linear-gradient(to bottom, rgba(15,15,26,0.2), rgba(15,15,26,0.85))",
        "font_display": "'Noto Serif JP', serif",
        "font_body": "'Noto Sans JP', sans-serif",
    },
    "ramen": {
        "bg": "#1a100a", "surface": "#2a1a10", "accent1": "#ff6b35", "accent2": "#ffd166",
        "text": "#f5f0eb", "muted": "#b8a99a",
        "hero_overlay": "linear-gradient(to bottom, rgba(26,16,10,0.2), rgba(26,16,10,0.88))",
        "font_display": "'Zen Kaku Gothic New', sans-serif",
        "font_body": "'Noto Sans JP', sans-serif",
    },
    "yakiniku": {
        "bg": "#120e0c", "surface": "#1e1816", "accent1": "#e04040", "accent2": "#d4a020",
        "text": "#fafaf9", "muted": "#a8a29e",
        "hero_overlay": "linear-gradient(to bottom, rgba(18,14,12,0.2), rgba(18,14,12,0.88))",
        "font_display": "'Noto Sans JP', sans-serif",
        "font_body": "'Noto Sans JP', sans-serif",
    },
    "yakitori": {
        "bg": "#1a100a", "surface": "#2a1a10", "accent1": "#f59e0b", "accent2": "#ef4444",
        "text": "#f5f0eb", "muted": "#b8a99a",
        "hero_overlay": "linear-gradient(to bottom, rgba(26,16,10,0.2), rgba(26,16,10,0.88))",
        "font_display": "'Zen Kaku Gothic New', sans-serif",
        "font_body": "'Noto Sans JP', sans-serif",
    },
    "izakaya": {
        "bg": "#12101a", "surface": "#1e1a28", "accent1": "#e8a030", "accent2": "#ef4444",
        "text": "#f5f0eb", "muted": "#9a8c9e",
        "hero_overlay": "linear-gradient(to bottom, rgba(18,16,26,0.25), rgba(18,16,26,0.88))",
        "font_display": "'Zen Kaku Gothic New', sans-serif",
        "font_body": "'Noto Sans JP', sans-serif",
    },
    "bar": {
        "bg": "#08080c", "surface": "#121218", "accent1": "#9060e0", "accent2": "#6366f1",
        "text": "#f5f5f5", "muted": "#777",
        "hero_overlay": "linear-gradient(to bottom, rgba(8,8,12,0.1), rgba(8,8,12,0.92))",
        "font_display": "'Cormorant Garamond', serif",
        "font_body": "'Noto Sans JP', sans-serif",
    },
    "cafe": {
        "bg": "#1a1612", "surface": "#252018", "accent1": "#c8a882", "accent2": "#a07850",
        "text": "#f5f0eb", "muted": "#9a8c7e",
        "hero_overlay": "linear-gradient(to bottom, rgba(26,22,18,0.2), rgba(26,22,18,0.88))",
        "font_display": "'Noto Sans JP', sans-serif",
        "font_body": "'Noto Sans JP', sans-serif",
    },
    "french": {
        "bg": "#0c0c14", "surface": "#14141e", "accent1": "#b8a088", "accent2": "#8b7355",
        "text": "#f0ebe3", "muted": "#9a8c7e",
        "hero_overlay": "linear-gradient(to bottom, rgba(12,12,20,0.15), rgba(12,12,20,0.9))",
        "font_display": "'Cormorant Garamond', serif",
        "font_body": "'Noto Sans JP', sans-serif",
    },
    "italian": {
        "bg": "#10100e", "surface": "#1c1c18", "accent1": "#c85040", "accent2": "#50a040",
        "text": "#f5f5f0", "muted": "#a0a098",
        "hero_overlay": "linear-gradient(to bottom, rgba(16,16,14,0.2), rgba(16,16,14,0.88))",
        "font_display": "'Noto Sans JP', sans-serif",
        "font_body": "'Noto Sans JP', sans-serif",
    },
    "tempura": {
        "bg": "#141210", "surface": "#201e18", "accent1": "#c8a050", "accent2": "#a07830",
        "text": "#f5f0eb", "muted": "#a09888",
        "hero_overlay": "linear-gradient(to bottom, rgba(20,18,16,0.2), rgba(20,18,16,0.88))",
        "font_display": "'Noto Serif JP', serif",
        "font_body": "'Noto Sans JP', sans-serif",
    },
    "tonkatsu": {
        "bg": "#16120e", "surface": "#221e18", "accent1": "#d4a040", "accent2": "#b08020",
        "text": "#f5f0eb", "muted": "#a09888",
        "hero_overlay": "linear-gradient(to bottom, rgba(22,18,14,0.2), rgba(22,18,14,0.88))",
        "font_display": "'Noto Sans JP', sans-serif",
        "font_body": "'Noto Sans JP', sans-serif",
    },
    "soba": {
        "bg": "#12110e", "surface": "#1e1d18", "accent1": "#8a8070", "accent2": "#6a6050",
        "text": "#f0ebe3", "muted": "#8a8278",
        "hero_overlay": "linear-gradient(to bottom, rgba(18,17,14,0.2), rgba(18,17,14,0.88))",
        "font_display": "'Noto Serif JP', serif",
        "font_body": "'Noto Sans JP', sans-serif",
    },
    "unagi": {
        "bg": "#100e0c", "surface": "#1c1a16", "accent1": "#d4af37", "accent2": "#b8860b",
        "text": "#f5f0eb", "muted": "#a8a29e",
        "hero_overlay": "linear-gradient(to bottom, rgba(16,14,12,0.2), rgba(16,14,12,0.88))",
        "font_display": "'Noto Serif JP', serif",
        "font_body": "'Noto Sans JP', sans-serif",
    },
    "chinese": {
        "bg": "#180808", "surface": "#281010", "accent1": "#e03030", "accent2": "#d4a020",
        "text": "#f5f0eb", "muted": "#c09090",
        "hero_overlay": "linear-gradient(to bottom, rgba(24,8,8,0.2), rgba(24,8,8,0.88))",
        "font_display": "'Noto Sans JP', sans-serif",
        "font_body": "'Noto Sans JP', sans-serif",
    },
    "korean": {
        "bg": "#120e0e", "surface": "#1e1818", "accent1": "#e04040", "accent2": "#40a050",
        "text": "#fafaf9", "muted": "#a8a29e",
        "hero_overlay": "linear-gradient(to bottom, rgba(18,14,14,0.2), rgba(18,14,14,0.88))",
        "font_display": "'Noto Sans JP', sans-serif",
        "font_body": "'Noto Sans JP', sans-serif",
    },
    "luxury": {
        "bg": "#0c0c14", "surface": "#141420", "accent1": "#b8a088", "accent2": "#8a7060",
        "text": "#f5f5f0", "muted": "#8a8a80",
        "hero_overlay": "linear-gradient(to bottom, rgba(12,12,20,0.1), rgba(12,12,20,0.9))",
        "font_display": "'Cormorant Garamond', serif",
        "font_body": "'Noto Sans JP', sans-serif",
    },
    "default": {
        "bg": "#0a0a10", "surface": "#14141e", "accent1": "#5070e0", "accent2": "#60a5fa",
        "text": "#f5f5f5", "muted": "#9ca3af",
        "hero_overlay": "linear-gradient(to bottom, rgba(10,10,16,0.25), rgba(10,10,16,0.88))",
        "font_display": "'Noto Sans JP', sans-serif",
        "font_body": "'Noto Sans JP', sans-serif",
    },
}

# 業種判定ルール
CLASSIFICATION_RULES = [
    (["寿司", "鮨", "sushi"], "sushi"),
    (["ラーメン", "つけ麺", "ramen", "らーめん"], "ramen"),
    (["焼肉", "yakiniku", "牛角", "叙々苑"], "yakiniku"),
    (["焼鳥", "やきとり", "焼き鳥", "鳥"], "yakitori"),
    (["居酒屋", "izakaya"], "izakaya"),
    (["bar", "バー", "クラブ", "club", "ナイト", "night"], "bar"),
    (["カフェ", "cafe", "coffee", "珈琲", "コーヒー"], "cafe"),
    (["フレンチ", "french", "ビストロ", "bistro"], "french"),
    (["イタリアン", "italian", "パスタ", "ピザ", "pizza"], "italian"),
    (["天ぷら", "tempura", "天婦羅"], "tempura"),
    (["とんかつ", "tonkatsu", "豚カツ", "とんかつ"], "tonkatsu"),
    (["蕎麦", "そば", "soba"], "soba"),
    (["うなぎ", "鰻", "unagi"], "unagi"),
    (["中華", "chinese", "中国", "餃子", "麻婆"], "chinese"),
    (["韓国", "korean", "サムギョプサル", "焼肉", "チゲ"], "korean"),
]

# テンプレートマッピング（業種→テンプレートファイル）
TEMPLATE_MAP = {
    "sushi": "sushi.html",
    "bar": "bar.html",
    "luxury": "luxury.html",
    # その他は default.html を使用
}


def classify_business(business: dict) -> str:
    """
    ビジネス情報から業種を判定

    Returns: カテゴリ名（sushi, ramen, bar, etc.）
    """
    name = business.get("name", "").lower()
    types = business.get("types", [])
    features = business.get("features", [])
    price_range = business.get("price_range", "")

    # 検索対象テキストを結合
    text = f"{name} {' '.join(str(t).lower() for t in types)} {' '.join(str(f).lower() for f in features)}"

    # キーワードマッチング
    for keywords, category in CLASSIFICATION_RULES:
        if any(kw.lower() in text for kw in keywords):
            return category

    # 価格帯で高級判定
    if price_range:
        if "10,000" in price_range or "15,000" in price_range or "20,000" in price_range or "30,000" in price_range:
            return "luxury"

    return "default"


class HPGenerator:
    """HP自動生成エンジン"""

    def __init__(self):
        self.env = Environment(
            loader=FileSystemLoader(os.path.join(TEMPLATES_DIR, "hp")),
            autoescape=select_autoescape(["html", "xml"]),
        )
        self.image_fetcher = ImageFetcher()

    def generate(self, business: dict, refresh_images: bool = False) -> dict:
        """
        ビジネス情報から静的HTMLのHPを生成

        Args:
            business: ビジネス情報dict
            refresh_images: 画像を強制再取得するか

        Returns: {path, url, business_name, generated_at, category}
        """
        name = business["name"]
        safe_name = _safe_filename(name)
        site_dir = os.path.join(GENERATED_SITES_DIR, safe_name)
        os.makedirs(site_dir, exist_ok=True)

        # 1. 業種判定
        category = classify_business(business)

        # 2. 画像取得
        images = self.image_fetcher.fetch_for_business(business, site_dir, category)

        # 3. テンプレート選択
        template_name = TEMPLATE_MAP.get(category, "default.html")
        try:
            template = self.env.get_template(template_name)
        except Exception:
            template = self.env.get_template("default.html")

        # 4. カラースキーム取得
        colors = COLOR_SCHEMES.get(category, COLOR_SCHEMES["default"])

        # 5. HTML生成
        html = template.render(
            biz=business,
            images=images,
            colors=colors,
            category=category,
            year=datetime.now().year,
        )

        # 6. ファイル出力
        html_path = os.path.join(site_dir, "index.html")
        with open(html_path, "w", encoding="utf-8") as f:
            f.write(html)

        # 7. メタデータ保存
        meta = {
            "business_name": name,
            "place_id": business.get("place_id", ""),
            "address": business.get("address", ""),
            "category": category,
            "image_source": images.get("source", "placeholder"),
            "image_count": len(images.get("gallery", [])) + (1 if images.get("hero") else 0),
            "generated_at": datetime.now().isoformat(),
            "html_path": html_path,
            "folder": safe_name,
            "status": "generated",
        }
        meta_path = os.path.join(site_dir, "meta.json")
        with open(meta_path, "w", encoding="utf-8") as f:
            json.dump(meta, f, ensure_ascii=False, indent=2)

        print(f"[GENERATED] {name} ({category}) → {html_path}")
        return meta

    def validate(self, html_path: str) -> list[str]:
        """HPの品質チェック。問題があればリストで返す"""
        issues = []

        if not os.path.exists(html_path):
            return ["ファイルが存在しない"]

        with open(html_path, "r", encoding="utf-8") as f:
            html = f.read()

        if "<img" not in html and "<svg" not in html and "<object" not in html:
            issues.append("画像もSVGプレースホルダーもない")
        if "og:image" not in html:
            issues.append("OGPメタタグ未設定")
        if "tel:" not in html:
            issues.append("電話リンク未設定")
        if "@media" not in html:
            issues.append("レスポンシブ対応なし")
        if "IntersectionObserver" not in html and "animation" not in html:
            issues.append("スクロールアニメーション未実装")
        if "maps.google" not in html and "google.com/maps" not in html:
            issues.append("Google Maps未埋め込み")

        return issues

    def validate_all(self) -> dict[str, list[str]]:
        """全生成済みHPを検証"""
        results = {}
        sites = list_generated_sites()

        for site in sites:
            html_path = site.get("html_path", "")
            if html_path:
                issues = self.validate(html_path)
                results[site["business_name"]] = issues

        return results


def generate_hp(business: dict) -> dict:
    """HP生成のショートカット関数"""
    generator = HPGenerator()
    return generator.generate(business)


def generate_all_hps(businesses: list[dict]) -> list[dict]:
    """全ビジネスのHPを一括生成"""
    generator = HPGenerator()
    results = []
    for biz in businesses:
        meta = generator.generate(biz)
        results.append(meta)
    return results


def list_generated_sites() -> list[dict]:
    """生成済みサイトの一覧を取得"""
    sites = []
    if not os.path.exists(GENERATED_SITES_DIR):
        return sites

    for folder in os.listdir(GENERATED_SITES_DIR):
        meta_path = os.path.join(GENERATED_SITES_DIR, folder, "meta.json")
        if os.path.isfile(meta_path):
            with open(meta_path, "r", encoding="utf-8") as f:
                meta = json.load(f)
            meta["folder"] = folder
            sites.append(meta)

    sites.sort(key=lambda x: x.get("generated_at", ""), reverse=True)
    return sites


def _safe_filename(name: str) -> str:
    """日本語名をファイルシステム安全な名前に変換"""
    h = hashlib.md5(name.encode()).hexdigest()[:8]
    safe = "".join(c if c.isalnum() or c in "-_" else "_" for c in name)
    return f"{safe[:30]}_{h}"


# モジュール直接実行時のテスト
if __name__ == "__main__":
    from discovery import _get_mock_businesses

    # テスト用ビジネスデータ取得
    businesses = _get_mock_businesses("新宿", "restaurant")[:3]

    generator = HPGenerator()
    for biz in businesses:
        meta = generator.generate(biz)
        issues = generator.validate(meta["html_path"])
        if issues:
            print(f"  ⚠️ Issues: {issues}")
        else:
            print(f"  ✅ Quality check passed")

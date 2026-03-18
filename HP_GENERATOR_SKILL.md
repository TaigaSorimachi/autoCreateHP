---
name: hp-generator
description: Use this skill when generating, modifying, or improving auto-generated store homepages (HP). Covers template design, image handling, responsive layout, color schemes, and quality validation for the アポ太郎 system. Trigger when user mentions HP, ホームページ, テンプレート, デザイン, 画像, or any store/restaurant website generation task.
---

# HP自動生成スキル

## 概要

飲食店向けの**画像付きリッチなHP**を自動生成するためのベストプラクティス集。
生成されるHPはsingle-file HTML（CSS/JS埋め込み、画像のみ外部ファイル）。

## テンプレート設計原則

### 1. 業種別カラースキーム（必ず適用）

```python
COLOR_SCHEMES = {
    "sushi": {
        "bg": "#1a1a2e", "surface": "#16213e", "accent1": "#e8d5b7", "accent2": "#c9a96e",
        "text": "#f0ebe3", "muted": "#9a8c7e",
        "hero_overlay": "linear-gradient(to bottom, rgba(26,26,46,0.3), rgba(26,26,46,0.8))",
        "font_display": "'Noto Serif JP', serif",
        "font_body": "'Noto Sans JP', sans-serif",
    },
    "ramen": {
        "bg": "#2d1b0e", "surface": "#3d2b1e", "accent1": "#ff6b35", "accent2": "#ffd166",
        "text": "#f5f0eb", "muted": "#b8a99a",
        "hero_overlay": "linear-gradient(to bottom, rgba(45,27,14,0.2), rgba(45,27,14,0.85))",
        "font_display": "'Zen Kaku Gothic New', sans-serif",
        "font_body": "'Noto Sans JP', sans-serif",
    },
    "yakiniku": {
        "bg": "#1c1917", "surface": "#292524", "accent1": "#dc2626", "accent2": "#f59e0b",
        "text": "#fafaf9", "muted": "#a8a29e",
        "hero_overlay": "linear-gradient(to bottom, rgba(28,25,23,0.2), rgba(28,25,23,0.85))",
        "font_display": "'Noto Sans JP', sans-serif",
        "font_body": "'Noto Sans JP', sans-serif",
    },
    "izakaya": {
        "bg": "#1a1520", "surface": "#2a2030", "accent1": "#f59e0b", "accent2": "#ef4444",
        "text": "#f5f0eb", "muted": "#9a8c9e",
        "hero_overlay": "linear-gradient(to bottom, rgba(26,21,32,0.3), rgba(26,21,32,0.85))",
        "font_display": "'Zen Kaku Gothic New', sans-serif",
        "font_body": "'Noto Sans JP', sans-serif",
    },
    "bar": {
        "bg": "#0a0a0a", "surface": "#151515", "accent1": "#a855f7", "accent2": "#6366f1",
        "text": "#f5f5f5", "muted": "#888",
        "hero_overlay": "linear-gradient(to bottom, rgba(10,10,10,0.1), rgba(10,10,10,0.9))",
        "font_display": "'Cormorant Garamond', serif",
        "font_body": "'Noto Sans JP', sans-serif",
    },
    "french": {
        "bg": "#1a1a2e", "surface": "#1e1e38", "accent1": "#c9b8a8", "accent2": "#8b7355",
        "text": "#f0ebe3", "muted": "#9a8c7e",
        "hero_overlay": "linear-gradient(to bottom, rgba(26,26,46,0.2), rgba(26,26,46,0.85))",
        "font_display": "'Cormorant Garamond', serif",
        "font_body": "'Noto Sans JP', sans-serif",
    },
    "tempura": {
        "bg": "#fefce8", "surface": "#fef9c3", "accent1": "#854d0e", "accent2": "#a16207",
        "text": "#1c1917", "muted": "#78716c",
        "hero_overlay": "linear-gradient(to bottom, rgba(254,252,232,0.1), rgba(254,252,232,0.85))",
        "font_display": "'Noto Serif JP', serif",
        "font_body": "'Noto Sans JP', sans-serif",
    },
    "luxury": {
        "bg": "#0c0c0c", "surface": "#1a1a1a", "accent1": "#d4af37", "accent2": "#b8860b",
        "text": "#f5f5f0", "muted": "#8a8a80",
        "hero_overlay": "linear-gradient(to bottom, rgba(12,12,12,0.1), rgba(12,12,12,0.85))",
        "font_display": "'Cormorant Garamond', serif",
        "font_body": "'Noto Sans JP', sans-serif",
    },
}
```

### 2. HP構造（必須セクション）

```html
<!-- 全HPで必ず含めるセクション -->

1. ヒーロー（全画面）
   - 背景: 画像 or SVGプレースホルダー
   - オーバーレイ: 業種別グラデーション
   - 店名（大きなタイポグラフィ）
   - 説明文（1〜2行）
   - 評価（星 + 件数）
   - スクロールヒント

2. アバウト
   - 店舗説明（2〜3文）
   - 特徴タグ（ピル型バッジ）

3. ギャラリー
   - 2×2グリッド or 横スクロール
   - 画像にホバーエフェクト
   - ※画像がない場合はSVGプレースホルダー4枚

4. 店舗情報
   - アイコン付きカード形式
   - 📍住所 / 📞電話 / 🕐営業時間 / 💰価格帯

5. アクセス（Google Maps）
   - iframe埋め込み
   - 角丸ボーダー

6. CTA
   - 「ご予約・お問い合わせ」
   - 電話ボタン（tel:リンク）

7. フッター
   - © + 年 + 店名
   - "Powered by アポ太郎"（小さく）
```

### 3. 画像の扱い（重要）

```
【絶対NG】
✗ 画像なしのヒーロー（白背景やソリッドカラーだけ）
✗ 壊れたimg（alt表示だけが見える状態）
✗ アスペクト比が崩れた画像

【必須対応】
✓ 画像がない場合はSVGプレースホルダーを必ず生成
✓ object-fit: cover で画像をクロップ
✓ loading="lazy" をギャラリー画像に付与
✓ ヒーロー画像の上に必ず半透明オーバーレイ（テキスト可読性確保）
```

### 4. アニメーション

```css
/* ページ読み込み時 — ヒーロー要素の段階表示 */
@keyframes fadeUp {
    from { opacity: 0; transform: translateY(20px); }
    to { opacity: 1; transform: translateY(0); }
}
.hero-label    { animation: fadeUp 0.8s 0.2s forwards; opacity: 0; }
.hero-name     { animation: fadeUp 0.8s 0.4s forwards; opacity: 0; }
.hero-desc     { animation: fadeUp 0.8s 0.6s forwards; opacity: 0; }

/* スクロール連動 — IntersectionObserver で .visible を付与 */
.section { opacity: 0; transform: translateY(30px); transition: all 0.6s ease; }
.section.visible { opacity: 1; transform: translateY(0); }
```

```javascript
// スクロールアニメーション（各セクションに適用）
const observer = new IntersectionObserver((entries) => {
    entries.forEach(e => { if (e.isIntersecting) e.target.classList.add('visible'); });
}, { threshold: 0.1 });
document.querySelectorAll('.section').forEach(s => observer.observe(s));
```

### 5. レスポンシブ

```css
/* モバイルファースト */
.gallery-grid {
    display: grid;
    grid-template-columns: 1fr 1fr;
    gap: 0.5rem;
}

@media (max-width: 600px) {
    .gallery-grid { grid-template-columns: 1fr; }
    .hero-name { font-size: 2rem; }
    .nav-links { display: none; }
    .info-grid { grid-template-columns: 1fr; }
}
```

### 6. OGPメタタグ（必須）

```html
<meta property="og:title" content="{店名}">
<meta property="og:description" content="{説明文}">
<meta property="og:image" content="images/og.jpg">
<meta property="og:type" content="website">
<meta name="twitter:card" content="summary_large_image">
```

## SVGプレースホルダーの生成例

```python
def generate_hero_placeholder(category: str) -> str:
    theme = PLACEHOLDER_THEMES[category]
    return f'''<svg viewBox="0 0 1920 1080" xmlns="http://www.w3.org/2000/svg">
        <rect width="1920" height="1080" fill="{theme['bg']}"/>
        <!-- パターン -->
        <pattern id="p" width="60" height="60" patternUnits="userSpaceOnUse">
            <circle cx="30" cy="30" r="1" fill="{theme['accent']}" opacity="0.15"/>
        </pattern>
        <rect width="1920" height="1080" fill="url(#p)"/>
        <!-- アイコン -->
        <text x="960" y="480" text-anchor="middle" font-size="120"
              opacity="0.15">{theme['icon']}</text>
        <!-- テキスト -->
        <text x="960" y="580" text-anchor="middle" font-family="sans-serif"
              font-size="24" fill="{theme['accent']}" opacity="0.3">
            PHOTO COMING SOON
        </text>
    </svg>'''
```

## 品質チェック（生成後に実行）

```python
def validate_hp(html_path: str) -> list[str]:
    """HPの品質チェック。問題があればリストで返す"""
    issues = []
    with open(html_path) as f:
        html = f.read()

    if '<img' not in html and '<svg' not in html:
        issues.append("画像もSVGプレースホルダーもない")
    if 'og:image' not in html:
        issues.append("OGPメタタグ未設定")
    if 'tel:' not in html:
        issues.append("電話リンク未設定")
    if '@media' not in html:
        issues.append("レスポンシブ対応なし")
    if 'IntersectionObserver' not in html and 'animation' not in html:
        issues.append("スクロールアニメーション未実装")
    if 'maps.google' not in html and 'google.com/maps' not in html:
        issues.append("Google Maps未埋め込み")

    return issues
```

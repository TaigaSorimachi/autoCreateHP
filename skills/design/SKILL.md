---
name: hp-design
description: Use this skill when generating, modifying, or improving auto-generated store homepages (HP). Covers professional-grade template design, image handling, responsive layout, color schemes, AI copywriting, and quality validation. Reference design quality: nakasuvision.zdev.co.jp. Trigger when user mentions HP, ホームページ, テンプレート, デザイン, 画像, or any store/restaurant website generation task.
---

# HP自動生成デザインスキル v2

## 目標デザインレベル

**参考サイト: nakasuvision.zdev.co.jp**
→ このクオリティを飲食店HPに落とし込む。
→ 「テンプレートで作りました」感が出たら失敗。

## 画像がある場合とない場合（両方対応必須）

### 画像あり（Google Photos / Pexels取得成功時）

```html
<!-- ヒーロー: 全画面写真 + オーバーレイ -->
<section class="hero" style="background-image: url('images/hero.jpg')">
    <div class="hero-overlay"></div>
    <div class="hero-content">
        <p class="hero-label">WELCOME TO</p>
        <h1 class="hero-name">{{ biz.name }}</h1>
        <p class="hero-tagline">{{ copy.tagline }}</p>
        <div class="hero-rating">★ {{ biz.rating }} ({{ biz.total_ratings }}件)</div>
    </div>
</section>

<!-- ギャラリー: 2×2 グリッド、ホバーで拡大 -->
<section class="gallery">
    <div class="gallery-grid">
        {% for img in images.gallery %}
        <div class="gallery-item">
            <img src="{{ img }}" alt="{{ biz.name }}" loading="lazy">
        </div>
        {% endfor %}
    </div>
</section>
```

### 画像なし（CSSのみで演出）

**画像がなくても「リッチに見える」CSSテクニック：**

```css
/* ヒーロー: グラデーション + ノイズテクスチャ + パターン */
.hero {
    background:
        /* ノイズテクスチャ（SVGインライン） */
        url("data:image/svg+xml,%3Csvg viewBox='0 0 256 256' xmlns='http://www.w3.org/2000/svg'%3E%3Cfilter id='n'%3E%3CfeTurbulence type='fractalNoise' baseFrequency='0.9' numOctaves='4' stitchTiles='stitch'/%3E%3C/filter%3E%3Crect width='100%25' height='100%25' filter='url(%23n)' opacity='0.05'/%3E%3C/svg%3E"),
        /* メッシュグラデーション */
        radial-gradient(ellipse at 20% 30%, var(--accent1-glow) 0%, transparent 50%),
        radial-gradient(ellipse at 80% 70%, var(--accent2-glow) 0%, transparent 50%),
        /* ベース */
        var(--bg);
}

/* ギャラリー代替: 業種アイコン + テクスチャのカードグリッド */
.gallery-placeholder {
    display: grid;
    grid-template-columns: 1fr 1fr;
    gap: 1rem;
}
.gallery-placeholder-item {
    aspect-ratio: 4/3;
    border-radius: 12px;
    background: var(--surface);
    border: 1px solid var(--border);
    display: flex;
    align-items: center;
    justify-content: center;
    font-size: 3rem;
    opacity: 0.3;
}
```

## 業種別カラースキーム

```python
COLOR_SCHEMES = {
    "sushi": {
        "bg": "#0f0f1a",
        "surface": "#1a1a2e",
        "accent1": "#d4a76a",  # 金
        "accent2": "#8b7355",
        "accent1_glow": "rgba(212,167,106,0.12)",
        "accent2_glow": "rgba(139,115,85,0.08)",
        "text": "#f0ebe3",
        "muted": "#8a8070",
        "hero_overlay": "rgba(15,15,26,0.6)",
        "font_display": "'Noto Serif JP', serif",
        "font_body": "'Noto Sans JP', sans-serif",
        "gallery_icons": ["🍣", "🐟", "🍶", "🔪"],
    },
    "ramen": {
        "bg": "#1a100a",
        "surface": "#2a1a10",
        "accent1": "#ff6b35",  # オレンジ
        "accent2": "#ffd166",
        "accent1_glow": "rgba(255,107,53,0.12)",
        "accent2_glow": "rgba(255,209,102,0.08)",
        "text": "#f5f0eb",
        "muted": "#a0907a",
        "hero_overlay": "rgba(26,16,10,0.55)",
        "font_display": "'Zen Kaku Gothic New', sans-serif",
        "font_body": "'Noto Sans JP', sans-serif",
        "gallery_icons": ["🍜", "🥢", "🍥", "🌶️"],
    },
    "yakiniku": {
        "bg": "#120e0c",
        "surface": "#1e1815",
        "accent1": "#e04040",  # 赤
        "accent2": "#d4a020",  # 金
        "accent1_glow": "rgba(224,64,64,0.12)",
        "accent2_glow": "rgba(212,160,32,0.08)",
        "text": "#fafaf5",
        "muted": "#908880",
        "hero_overlay": "rgba(18,14,12,0.55)",
        "font_display": "'Noto Sans JP', sans-serif",
        "font_body": "'Noto Sans JP', sans-serif",
        "gallery_icons": ["🥩", "🔥", "🍺", "🥓"],
    },
    "izakaya": {
        "bg": "#12101a",
        "surface": "#1e1a28",
        "accent1": "#e8a030",  # 提灯イエロー
        "accent2": "#d05050",
        "accent1_glow": "rgba(232,160,48,0.12)",
        "accent2_glow": "rgba(208,80,80,0.08)",
        "text": "#f5f0ea",
        "muted": "#908575",
        "hero_overlay": "rgba(18,16,26,0.6)",
        "font_display": "'Zen Kaku Gothic New', sans-serif",
        "font_body": "'Noto Sans JP', sans-serif",
        "gallery_icons": ["🏮", "🍻", "🐙", "🍢"],
    },
    "bar": {
        "bg": "#08080c",
        "surface": "#121218",
        "accent1": "#9060e0",  # パープル
        "accent2": "#5060e0",
        "accent1_glow": "rgba(144,96,224,0.12)",
        "accent2_glow": "rgba(80,96,224,0.08)",
        "text": "#eeeef5",
        "muted": "#707088",
        "hero_overlay": "rgba(8,8,12,0.5)",
        "font_display": "'Cormorant Garamond', serif",
        "font_body": "'Noto Sans JP', sans-serif",
        "gallery_icons": ["🍸", "🥃", "🌃", "🎵"],
    },
    "french": {
        "bg": "#0c0c14",
        "surface": "#161620",
        "accent1": "#b8a088",  # シャンパン
        "accent2": "#706050",
        "accent1_glow": "rgba(184,160,136,0.10)",
        "accent2_glow": "rgba(112,96,80,0.06)",
        "text": "#f0ebe5",
        "muted": "#8a8070",
        "hero_overlay": "rgba(12,12,20,0.6)",
        "font_display": "'Cormorant Garamond', serif",
        "font_body": "'Noto Sans JP', sans-serif",
        "gallery_icons": ["🍷", "🥖", "🧀", "🌿"],
    },
    "default": {
        "bg": "#0a0a10",
        "surface": "#14141e",
        "accent1": "#5070e0",
        "accent2": "#40a0d0",
        "accent1_glow": "rgba(80,112,224,0.10)",
        "accent2_glow": "rgba(64,160,208,0.08)",
        "text": "#eef0f5",
        "muted": "#707888",
        "hero_overlay": "rgba(10,10,16,0.6)",
        "font_display": "'Noto Sans JP', sans-serif",
        "font_body": "'Noto Sans JP', sans-serif",
        "gallery_icons": ["🏪", "🍽️", "✨", "📍"],
    },
}
```

## HPセクション構成（必須）

```
1. [NAV]        固定ナビ（透明→スクロールで背景付き）
2. [HERO]       全画面（写真 or CSSグラデーション + 店名 + キャッチコピー + 評価）
3. [ABOUT]      店舗紹介（AI生成 or テンプレコピー + 特徴タグ）
4. [GALLERY]    写真ギャラリー（2×2グリッド + ホバー拡大）or CSSプレースホルダー
5. [INFO]       店舗情報カード（📍住所 / 📞電話 / 🕐営業時間 / 💰価格帯）
6. [ACCESS]     Google Maps iframe + 「ルートを検索」ボタン
7. [CTA]        大きな電話ボタン + 「ご予約・お問い合わせ」
8. [FOOTER]     © + "Powered by アポ太郎"（小さく）
```

## 必須CSS（コピペ可能）

```css
/* スクロールアニメーション */
.section {
    opacity: 0;
    transform: translateY(40px);
    transition: opacity 0.7s ease, transform 0.7s ease;
}
.section.visible {
    opacity: 1;
    transform: translateY(0);
}

/* ヒーロー読み込みアニメーション */
.hero-label   { animation: fadeUp 0.8s 0.2s both; }
.hero-name    { animation: fadeUp 0.8s 0.4s both; }
.hero-tagline { animation: fadeUp 0.8s 0.6s both; }
.hero-rating  { animation: fadeUp 0.8s 0.8s both; }

@keyframes fadeUp {
    from { opacity: 0; transform: translateY(25px); }
    to   { opacity: 1; transform: translateY(0); }
}

/* ギャラリーホバー */
.gallery-item img {
    transition: transform 0.4s ease;
    object-fit: cover;
    width: 100%;
    height: 100%;
}
.gallery-item:hover img {
    transform: scale(1.05);
}

/* CTA ボタン */
.cta-btn {
    display: inline-flex;
    align-items: center;
    gap: 0.5rem;
    padding: 1rem 2.5rem;
    background: linear-gradient(135deg, var(--accent1), var(--accent2));
    color: white;
    border: none;
    border-radius: 100px;
    font-size: 1.1rem;
    font-weight: 700;
    text-decoration: none;
    transition: transform 0.3s, box-shadow 0.3s;
}
.cta-btn:hover {
    transform: translateY(-3px);
    box-shadow: 0 12px 40px var(--accent1-glow);
}
```

## 必須JavaScript

```javascript
// スクロールアニメーション
const observer = new IntersectionObserver((entries) => {
    entries.forEach(e => {
        if (e.isIntersecting) {
            e.target.classList.add('visible');
        }
    });
}, { threshold: 0.15 });

document.querySelectorAll('.section').forEach(s => observer.observe(s));

// ナビの背景切り替え
window.addEventListener('scroll', () => {
    const nav = document.querySelector('.nav');
    nav.classList.toggle('scrolled', window.scrollY > 50);
});
```

## 品質チェックリスト

生成された全HPが以下を満たすこと：

- [ ] ヒーロー（写真 or CSSグラデーション）が全画面で表示される
- [ ] 白い背景だけのセクションが一つもない
- [ ] 業種に応じたカラースキームが適用されている
- [ ] 店名が大きく読みやすい
- [ ] キャッチコピー / 紹介文がある（AI生成 or テンプレ）
- [ ] 電話番号がタップで発信可能（`tel:` リンク）
- [ ] Google Maps が正しい座標で埋め込まれている
- [ ] スマホ（375px幅）で全セクション崩れない
- [ ] フェードインアニメーションが動作する
- [ ] OGPメタタグ（title, description, image）が設定されている
- [ ] 「Powered by アポ太郎」がフッターにある
- [ ] ページ全体の読み込みが3秒以内

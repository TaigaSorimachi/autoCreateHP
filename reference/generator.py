"""
アポ太郎 — HP自動生成エンジン
店舗情報から静的HTMLのホームページを自動生成
"""

import os
import json
import hashlib
from datetime import datetime
from config import GENERATED_SITES_DIR


def generate_hp(business: dict) -> dict:
    """
    ビジネス情報から静的HTMLのHPを生成
    Returns: {path, url, business_name, generated_at}
    """
    name = business["name"]
    safe_name = _safe_filename(name)
    site_dir = os.path.join(GENERATED_SITES_DIR, safe_name)
    os.makedirs(site_dir, exist_ok=True)

    # HP HTML生成
    html = _build_hp_html(business)
    html_path = os.path.join(site_dir, "index.html")
    with open(html_path, "w", encoding="utf-8") as f:
        f.write(html)

    # メタデータ保存
    meta = {
        "business_name": name,
        "place_id": business.get("place_id", ""),
        "address": business.get("address", ""),
        "generated_at": datetime.now().isoformat(),
        "html_path": html_path,
        "folder": safe_name,
        "status": "generated",  # generated / sent / responded
    }
    meta_path = os.path.join(site_dir, "meta.json")
    with open(meta_path, "w", encoding="utf-8") as f:
        json.dump(meta, f, ensure_ascii=False, indent=2)

    print(f"[GENERATED] {name} → {html_path}")
    return meta


def generate_all_hps(businesses: list[dict]) -> list[dict]:
    """全ビジネスのHPを一括生成"""
    results = []
    for biz in businesses:
        meta = generate_hp(biz)
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


def _get_accent_color(business: dict) -> tuple[str, str, str]:
    """業種に応じたカラースキームを自動選択"""
    types = business.get("types", [])
    features = business.get("features", [])
    name = business.get("name", "").lower()

    # 業種・特徴からカラーを推定
    if any(k in str(types + features + [name]) for k in ["寿司", "sushi", "鮨", "和食"]):
        return ("#1a1a2e", "#e8d5b7", "#c9a96e")  # 和モダン：紺×金
    elif any(k in str(types + features + [name]) for k in ["焼鳥", "居酒屋", "屋台", "ラーメン"]):
        return ("#2d1b0e", "#ff6b35", "#ffd166")  # 温かみ：茶×オレンジ
    elif any(k in str(types + features + [name]) for k in ["bar", "バー", "club", "クラブ"]):
        return ("#0a0a0a", "#a855f7", "#6366f1")  # ナイト：黒×パープル
    elif any(k in str(types + features + [name]) for k in ["ステーキ", "鉄板", "焼肉"]):
        return ("#1c1917", "#dc2626", "#f59e0b")  # ラグジュアリー：黒×赤×金
    elif any(k in str(types + features + [name]) for k in ["天ぷら", "定食", "家庭"]):
        return ("#fefce8", "#854d0e", "#a16207")  # ナチュラル：クリーム×ブラウン
    else:
        return ("#111827", "#3b82f6", "#60a5fa")  # デフォルト：ダーク×ブルー


def _build_hp_html(business: dict) -> str:
    """ビジネス情報からHP用HTMLを生成"""
    name = business.get("name", "店舗名")
    address = business.get("address", "")
    rating = business.get("rating", 0)
    total_ratings = business.get("total_ratings", 0)
    phone = business.get("phone", "")
    hours = business.get("hours", "")
    description = business.get("description", f"{name}のホームページへようこそ。")
    features = business.get("features", [])
    price_range = business.get("price_range", "")
    lat = business.get("lat", 33.5902)
    lng = business.get("lng", 130.4017)

    bg_color, accent1, accent2 = _get_accent_color(business)

    stars_html = "".join("★" if i < round(rating) else "☆" for i in range(5))

    features_html = ""
    if features:
        features_html = "".join(
            f'<span class="tag">{f}</span>' for f in features
        )
        features_html = f'<div class="tags">{features_html}</div>'

    info_items = []
    if address:
        info_items.append(f"""
        <div class="info-item">
            <div class="info-icon">📍</div>
            <div>
                <div class="info-label">所在地</div>
                <div class="info-value">{address}</div>
            </div>
        </div>""")
    if phone:
        info_items.append(f"""
        <div class="info-item">
            <div class="info-icon">📞</div>
            <div>
                <div class="info-label">電話番号</div>
                <div class="info-value">{phone}</div>
            </div>
        </div>""")
    if hours:
        info_items.append(f"""
        <div class="info-item">
            <div class="info-icon">🕐</div>
            <div>
                <div class="info-label">営業時間</div>
                <div class="info-value">{hours}</div>
            </div>
        </div>""")
    if price_range:
        info_items.append(f"""
        <div class="info-item">
            <div class="info-icon">💰</div>
            <div>
                <div class="info-label">価格帯</div>
                <div class="info-value">{price_range}</div>
            </div>
        </div>""")
    info_html = "\n".join(info_items)

    map_html = ""
    if lat and lng:
        map_html = f"""
        <section class="section" id="access">
            <h2 class="section-title">アクセス</h2>
            <div class="map-container">
                <iframe
                    src="https://www.google.com/maps?q={lat},{lng}&z=16&output=embed"
                    width="100%" height="350" style="border:0; border-radius:12px;"
                    allowfullscreen loading="lazy"
                    referrerpolicy="no-referrer-when-downgrade">
                </iframe>
            </div>
        </section>"""

    return f"""<!DOCTYPE html>
<html lang="ja">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{name}</title>
    <meta name="description" content="{description}">
    <link rel="preconnect" href="https://fonts.googleapis.com">
    <link href="https://fonts.googleapis.com/css2?family=Noto+Sans+JP:wght@300;400;500;700;900&family=Zen+Kaku+Gothic+New:wght@400;700&display=swap" rel="stylesheet">
    <style>
        :root {{
            --bg: {bg_color};
            --accent1: {accent1};
            --accent2: {accent2};
            --text: #f5f5f5;
            --text-muted: #a0a0a0;
            --surface: rgba(255,255,255,0.05);
            --surface-hover: rgba(255,255,255,0.08);
            --border: rgba(255,255,255,0.1);
        }}

        * {{ margin:0; padding:0; box-sizing:border-box; }}

        body {{
            font-family: 'Zen Kaku Gothic New', 'Noto Sans JP', sans-serif;
            background: var(--bg);
            color: var(--text);
            min-height: 100vh;
            overflow-x: hidden;
        }}

        /* ===== HERO ===== */
        .hero {{
            position: relative;
            min-height: 100vh;
            display: flex;
            flex-direction: column;
            justify-content: center;
            align-items: center;
            text-align: center;
            padding: 2rem;
            overflow: hidden;
        }}
        .hero::before {{
            content: '';
            position: absolute;
            inset: 0;
            background:
                radial-gradient(ellipse 600px 400px at 30% 20%, color-mix(in srgb, var(--accent1) 15%, transparent), transparent),
                radial-gradient(ellipse 500px 500px at 70% 80%, color-mix(in srgb, var(--accent2) 10%, transparent), transparent);
            z-index: 0;
        }}
        .hero > * {{ position: relative; z-index: 1; }}

        .hero-label {{
            font-size: 0.75rem;
            letter-spacing: 0.3em;
            text-transform: uppercase;
            color: var(--accent1);
            margin-bottom: 1.5rem;
            opacity: 0;
            animation: fadeUp 0.8s 0.2s forwards;
        }}
        .hero-name {{
            font-family: 'Noto Sans JP', sans-serif;
            font-weight: 900;
            font-size: clamp(2.5rem, 8vw, 5rem);
            line-height: 1.1;
            letter-spacing: -0.02em;
            margin-bottom: 1rem;
            opacity: 0;
            animation: fadeUp 0.8s 0.4s forwards;
        }}
        .hero-name span {{
            background: linear-gradient(135deg, var(--accent1), var(--accent2));
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            background-clip: text;
        }}
        .hero-desc {{
            font-size: 1.1rem;
            color: var(--text-muted);
            max-width: 500px;
            line-height: 1.8;
            margin-bottom: 2rem;
            opacity: 0;
            animation: fadeUp 0.8s 0.6s forwards;
        }}
        .hero-rating {{
            display: flex;
            align-items: center;
            gap: 0.5rem;
            font-size: 1rem;
            color: var(--accent1);
            opacity: 0;
            animation: fadeUp 0.8s 0.8s forwards;
        }}
        .hero-rating .count {{
            color: var(--text-muted);
            font-size: 0.85rem;
        }}

        .scroll-hint {{
            position: absolute;
            bottom: 2rem;
            left: 50%;
            transform: translateX(-50%);
            display: flex;
            flex-direction: column;
            align-items: center;
            gap: 0.5rem;
            color: var(--text-muted);
            font-size: 0.7rem;
            letter-spacing: 0.2em;
            opacity: 0;
            animation: fadeUp 0.8s 1s forwards;
        }}
        .scroll-hint .arrow {{
            width: 1px;
            height: 30px;
            background: linear-gradient(to bottom, var(--accent1), transparent);
            animation: pulse 2s infinite;
        }}

        /* ===== NAV ===== */
        .nav {{
            position: fixed;
            top: 0;
            left: 0;
            right: 0;
            z-index: 100;
            padding: 1rem 2rem;
            display: flex;
            justify-content: space-between;
            align-items: center;
            background: color-mix(in srgb, var(--bg) 80%, transparent);
            backdrop-filter: blur(20px);
            border-bottom: 1px solid var(--border);
            transform: translateY(-100%);
            animation: slideDown 0.5s 1.2s forwards;
        }}
        .nav-logo {{
            font-weight: 700;
            font-size: 0.9rem;
            letter-spacing: 0.05em;
        }}
        .nav-links {{
            display: flex;
            gap: 1.5rem;
            list-style: none;
        }}
        .nav-links a {{
            color: var(--text-muted);
            text-decoration: none;
            font-size: 0.8rem;
            letter-spacing: 0.05em;
            transition: color 0.3s;
        }}
        .nav-links a:hover {{ color: var(--accent1); }}

        /* ===== SECTIONS ===== */
        .section {{
            max-width: 800px;
            margin: 0 auto;
            padding: 4rem 2rem;
        }}
        .section-title {{
            font-size: 1.5rem;
            font-weight: 700;
            margin-bottom: 2rem;
            padding-bottom: 0.5rem;
            border-bottom: 2px solid var(--accent1);
            display: inline-block;
        }}

        /* ===== INFO ===== */
        .info-grid {{
            display: flex;
            flex-direction: column;
            gap: 1rem;
        }}
        .info-item {{
            display: flex;
            align-items: flex-start;
            gap: 1rem;
            padding: 1.25rem;
            background: var(--surface);
            border: 1px solid var(--border);
            border-radius: 12px;
            transition: background 0.3s, border-color 0.3s;
        }}
        .info-item:hover {{
            background: var(--surface-hover);
            border-color: color-mix(in srgb, var(--accent1) 30%, transparent);
        }}
        .info-icon {{ font-size: 1.5rem; flex-shrink: 0; }}
        .info-label {{ font-size: 0.75rem; color: var(--text-muted); margin-bottom: 0.25rem; }}
        .info-value {{ font-size: 1rem; }}

        /* ===== TAGS ===== */
        .tags {{
            display: flex;
            flex-wrap: wrap;
            gap: 0.5rem;
            margin: 2rem 0;
        }}
        .tag {{
            padding: 0.4rem 1rem;
            border-radius: 100px;
            font-size: 0.8rem;
            background: color-mix(in srgb, var(--accent1) 15%, transparent);
            border: 1px solid color-mix(in srgb, var(--accent1) 30%, transparent);
            color: var(--accent1);
        }}

        /* ===== MAP ===== */
        .map-container {{
            border-radius: 12px;
            overflow: hidden;
            border: 1px solid var(--border);
        }}

        /* ===== CTA ===== */
        .cta-section {{
            text-align: center;
            padding: 5rem 2rem;
        }}
        .cta-title {{
            font-size: 2rem;
            font-weight: 700;
            margin-bottom: 1rem;
        }}
        .cta-sub {{
            color: var(--text-muted);
            margin-bottom: 2rem;
        }}
        .cta-btn {{
            display: inline-flex;
            align-items: center;
            gap: 0.5rem;
            padding: 1rem 2.5rem;
            background: linear-gradient(135deg, var(--accent1), var(--accent2));
            color: white;
            border: none;
            border-radius: 100px;
            font-size: 1rem;
            font-weight: 700;
            text-decoration: none;
            cursor: pointer;
            transition: transform 0.3s, box-shadow 0.3s;
        }}
        .cta-btn:hover {{
            transform: translateY(-2px);
            box-shadow: 0 10px 40px color-mix(in srgb, var(--accent1) 40%, transparent);
        }}

        /* ===== FOOTER ===== */
        .footer {{
            text-align: center;
            padding: 2rem;
            color: var(--text-muted);
            font-size: 0.75rem;
            border-top: 1px solid var(--border);
        }}

        /* ===== ANIMATIONS ===== */
        @keyframes fadeUp {{
            from {{ opacity: 0; transform: translateY(20px); }}
            to {{ opacity: 1; transform: translateY(0); }}
        }}
        @keyframes slideDown {{
            to {{ transform: translateY(0); }}
        }}
        @keyframes pulse {{
            0%, 100% {{ opacity: 0.3; }}
            50% {{ opacity: 1; }}
        }}

        /* ===== RESPONSIVE ===== */
        @media (max-width: 600px) {{
            .nav-links {{ display: none; }}
            .section {{ padding: 3rem 1.25rem; }}
        }}
    </style>
</head>
<body>

    <nav class="nav">
        <div class="nav-logo">{name}</div>
        <ul class="nav-links">
            <li><a href="#about">概要</a></li>
            <li><a href="#info">店舗情報</a></li>
            <li><a href="#access">アクセス</a></li>
            <li><a href="#contact">お問い合わせ</a></li>
        </ul>
    </nav>

    <section class="hero">
        <div class="hero-label">WELCOME TO</div>
        <h1 class="hero-name"><span>{name}</span></h1>
        <p class="hero-desc">{description}</p>
        <div class="hero-rating">
            <span>{stars_html}</span>
            <strong>{rating}</strong>
            <span class="count">({total_ratings}件のレビュー)</span>
        </div>
        <div class="scroll-hint">
            <span>SCROLL</span>
            <div class="arrow"></div>
        </div>
    </section>

    <section class="section" id="about">
        <h2 class="section-title">当店について</h2>
        <p style="line-height:1.8; color:var(--text-muted);">{description}</p>
        {features_html}
    </section>

    <section class="section" id="info">
        <h2 class="section-title">店舗情報</h2>
        <div class="info-grid">
            {info_html}
        </div>
    </section>

    {map_html}

    <section class="cta-section" id="contact">
        <h2 class="cta-title">ご予約・お問い合わせ</h2>
        <p class="cta-sub">お気軽にお電話ください</p>
        <a class="cta-btn" href="tel:{phone}">📞 {phone if phone else 'お電話はこちら'}</a>
    </section>

    <footer class="footer">
        <p>&copy; {datetime.now().year} {name}. All rights reserved.</p>
        <p style="margin-top:0.5rem; font-size:0.65rem; opacity:0.5;">
            Powered by アポ太郎 — AI営業アシスタント
        </p>
    </footer>

</body>
</html>"""

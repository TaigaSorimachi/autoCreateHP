"""
アポ太郎 — メインアプリケーション
Flask ベースのローカルダッシュボード + API
"""

import os
import json
from flask import Flask, render_template, request, jsonify, send_from_directory
from config import (
    HOST, PORT, GENERATED_SITES_DIR, USE_MOCK, HAS_UNSPLASH,
    DEFAULT_AREA, DEFAULT_BUSINESS_TYPE, DEFAULT_RADIUS
)
from discovery import search_businesses, save_businesses, load_businesses
from generator import generate_hp, generate_all_hps, list_generated_sites, classify_business

app = Flask(__name__)


# ================================
#  ダッシュボード
# ================================

@app.route("/")
def dashboard():
    sites = list_generated_sites()
    businesses = load_businesses()

    # 画像ソース統計
    image_stats = {"google_places": 0, "unsplash": 0, "placeholder": 0}
    for site in sites:
        source = site.get("image_source", "placeholder")
        if source in image_stats:
            image_stats[source] += 1

    return render_template(
        "dashboard.html",
        sites=sites,
        businesses=businesses,
        total_sites=len(sites),
        total_businesses=len(businesses),
        is_mock=USE_MOCK,
        has_unsplash=HAS_UNSPLASH,
        image_stats=image_stats,
    )


# ================================
#  API: ビジネス発見
# ================================

@app.route("/api/discover", methods=["POST"])
def api_discover():
    data = request.json or {}
    area = data.get("area", DEFAULT_AREA)
    biz_type = data.get("business_type", DEFAULT_BUSINESS_TYPE)
    radius = data.get("radius", DEFAULT_RADIUS)

    businesses = search_businesses(area, biz_type, radius)
    saved = save_businesses(businesses)

    return jsonify({
        "status": "ok",
        "discovered": len(businesses),
        "total_saved": len(saved),
        "businesses": businesses,
    })


# ================================
#  API: HP生成（単体）
# ================================

@app.route("/api/generate", methods=["POST"])
def api_generate():
    data = request.json or {}
    business = data.get("business")
    if not business:
        return jsonify({"status": "error", "message": "business data required"}), 400

    meta = generate_hp(business)
    return jsonify({"status": "ok", "site": meta})


# ================================
#  API: HP一括生成
# ================================

@app.route("/api/generate-all", methods=["POST"])
def api_generate_all():
    businesses = load_businesses()
    if not businesses:
        return jsonify({"status": "error", "message": "先にビジネスを発見してください"}), 400

    results = generate_all_hps(businesses)

    # 画像ソース統計
    image_stats = {"google_places": 0, "unsplash": 0, "placeholder": 0}
    for meta in results:
        source = meta.get("image_source", "placeholder")
        if source in image_stats:
            image_stats[source] += 1

    return jsonify({
        "status": "ok",
        "generated": len(results),
        "image_stats": image_stats,
        "sites": results,
    })


# ================================
#  API: フル自動パイプライン
#  検索→保存→HP生成 をワンショットで実行
# ================================

@app.route("/api/auto-pipeline", methods=["POST"])
def api_auto_pipeline():
    data = request.json or {}
    areas_str = data.get("areas", DEFAULT_AREA)
    biz_type = data.get("business_type", DEFAULT_BUSINESS_TYPE)
    radius = data.get("radius", DEFAULT_RADIUS)

    # カンマ区切り or リスト
    if isinstance(areas_str, list):
        areas = areas_str
    else:
        areas = [a.strip() for a in areas_str.split(",") if a.strip()]

    # --- STEP 1: 発見 ---
    all_businesses = []
    step_log = []
    for area in areas:
        businesses = search_businesses(area, biz_type, radius)
        step_log.append({"area": area, "found": len(businesses)})
        all_businesses.extend(businesses)

    # 重複排除
    seen = set()
    unique = []
    for biz in all_businesses:
        pid = biz.get("place_id", biz["name"])
        if pid not in seen:
            seen.add(pid)
            unique.append(biz)
    all_businesses = unique

    # --- STEP 2: 保存 ---
    saved = save_businesses(all_businesses)

    # --- STEP 3: HP生成 ---
    generated = generate_all_hps(all_businesses)

    # 画像ソース統計
    image_stats = {"google_places": 0, "unsplash": 0, "placeholder": 0}
    for meta in generated:
        source = meta.get("image_source", "placeholder")
        if source in image_stats:
            image_stats[source] += 1

    # --- レポート ---
    sites = list_generated_sites()
    return jsonify({
        "status": "ok",
        "pipeline": "complete",
        "steps": {
            "discover": {"areas": step_log, "total_unique": len(all_businesses)},
            "save": {"total_saved": len(saved)},
            "generate": {"hps_generated": len(generated), "image_stats": image_stats},
        },
        "total_sites": len(sites),
        "sites": [
            {
                "business_name": s["business_name"],
                "address": s.get("address", ""),
                "category": s.get("category", "default"),
                "image_source": s.get("image_source", "unknown"),
                "image_count": s.get("image_count", 0),
                "folder": s["folder"],
                "status": s.get("status", "generated"),
                "generated_at": s.get("generated_at", ""),
            }
            for s in sites
        ],
    })


# ================================
#  API: 生成済みサイト一覧
# ================================

@app.route("/api/sites")
def api_sites():
    sites = list_generated_sites()
    return jsonify({"status": "ok", "sites": sites})


# ================================
#  API: サイト削除
# ================================

@app.route("/api/sites/<folder>", methods=["DELETE"])
def api_delete_site(folder):
    import shutil
    site_path = os.path.join(GENERATED_SITES_DIR, folder)
    if os.path.exists(site_path):
        shutil.rmtree(site_path)
        return jsonify({"status": "ok", "deleted": folder})
    return jsonify({"status": "error", "message": "Site not found"}), 404


# ================================
#  生成サイトの静的配信
# ================================

@app.route("/sites/<path:filepath>")
def serve_site(filepath):
    return send_from_directory(GENERATED_SITES_DIR, filepath)


# ================================
#  起動
# ================================

if __name__ == "__main__":
    os.makedirs(GENERATED_SITES_DIR, exist_ok=True)

    mode_text = "MOCK (APIキー未設定)" if USE_MOCK else "LIVE (Google Places API)"
    unsplash_text = "✅ 有効" if HAS_UNSPLASH else "❌ 未設定"

    print(f"""
╔══════════════════════════════════════════════════════════╗
║         🤖 アポ太郎 v2.0                                   ║
║         AI営業アシスタント                                  ║
╠══════════════════════════════════════════════════════════╣
║  Dashboard: http://{HOST}:{PORT}                            ║
║                                                          ║
║  モード:           {mode_text:<40}
║  Unsplash API:     {unsplash_text:<40}
║                                                          ║
║  Google Places APIを有効にするには:                         ║
║  export GOOGLE_PLACES_API_KEY=your_key                   ║
║                                                          ║
║  Unsplash APIを有効にするには:                               ║
║  export UNSPLASH_ACCESS_KEY=your_key                     ║
╚══════════════════════════════════════════════════════════╝
""")
    app.run(host=HOST, port=PORT, debug=True)

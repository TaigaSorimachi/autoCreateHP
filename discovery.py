"""
アポ太郎 — ビジネス発見モジュール
Google Places API を使って指定エリアの店舗を自動発見
APIキー未設定時はモックデータで動作
"""

import json
import os
import random
import urllib.request
import urllib.parse
from datetime import datetime
from config import GOOGLE_PLACES_API_KEY, USE_MOCK, GENERATED_SITES_DIR


def search_businesses(area: str, business_type: str = "restaurant", radius: int = 1000) -> list[dict]:
    """
    指定エリア・業種でビジネスを検索
    Returns: list of business dicts
    """
    if USE_MOCK:
        print("[MOCK MODE] Google Places APIキー未設定 → モックデータを使用")
        return _get_mock_businesses(area, business_type)
    
    return _search_google_places(area, business_type, radius)


def _search_google_places(area: str, business_type: str, radius: int) -> list[dict]:
    """Google Places API で検索"""
    # Step 1: エリア名をジオコーディング
    geocode_url = (
        f"https://maps.googleapis.com/maps/api/geocode/json"
        f"?address={urllib.parse.quote(area)}"
        f"&key={GOOGLE_PLACES_API_KEY}"
        f"&language=ja"
    )
    try:
        with urllib.request.urlopen(geocode_url) as resp:
            geo_data = json.loads(resp.read())
        
        if geo_data["status"] != "OK" or not geo_data["results"]:
            print(f"[ERROR] ジオコーディング失敗: {area}")
            return []
        
        loc = geo_data["results"][0]["geometry"]["location"]
        lat, lng = loc["lat"], loc["lng"]
    except Exception as e:
        print(f"[ERROR] Geocoding API error: {e}")
        return []

    # Step 2: 近隣検索
    places_url = (
        f"https://maps.googleapis.com/maps/api/place/nearbysearch/json"
        f"?location={lat},{lng}"
        f"&radius={radius}"
        f"&type={business_type}"
        f"&key={GOOGLE_PLACES_API_KEY}"
        f"&language=ja"
    )
    try:
        with urllib.request.urlopen(places_url) as resp:
            places_data = json.loads(resp.read())
        
        if places_data["status"] != "OK":
            print(f"[ERROR] Places API: {places_data['status']}")
            return []
        
        businesses = []
        for place in places_data.get("results", [])[:20]:
            biz = {
                "place_id": place.get("place_id", ""),
                "name": place.get("name", "不明"),
                "address": place.get("vicinity", "住所不明"),
                "rating": place.get("rating", 0),
                "total_ratings": place.get("user_ratings_total", 0),
                "types": place.get("types", []),
                "lat": place["geometry"]["location"]["lat"],
                "lng": place["geometry"]["location"]["lng"],
                "photo_ref": (
                    place["photos"][0]["photo_reference"]
                    if place.get("photos") else None
                ),
                "business_status": place.get("business_status", "OPERATIONAL"),
                "area": area,
                "discovered_at": datetime.now().isoformat(),
            }
            businesses.append(biz)
        
        return businesses
    
    except Exception as e:
        print(f"[ERROR] Places API error: {e}")
        return []


def get_place_details(place_id: str) -> dict:
    """Google Places API で店舗詳細を取得"""
    if USE_MOCK:
        return {}
    
    fields = "name,formatted_address,formatted_phone_number,website,opening_hours,review,photo,url"
    url = (
        f"https://maps.googleapis.com/maps/api/place/details/json"
        f"?place_id={place_id}"
        f"&fields={fields}"
        f"&key={GOOGLE_PLACES_API_KEY}"
        f"&language=ja"
    )
    try:
        with urllib.request.urlopen(url) as resp:
            data = json.loads(resp.read())
        return data.get("result", {})
    except Exception as e:
        print(f"[ERROR] Place Details API error: {e}")
        return {}


def _get_mock_businesses(area: str, business_type: str) -> list[dict]:
    """モックデータ生成（APIキーなしでもシステムをテスト可能）エリア別対応"""

    # ── エリア別モックデータ ──
    MOCK_DB = {
        # ===== 東京 =====
        "新宿": {
            "lat": 35.6938, "lng": 139.7034,
            "restaurants": [
                {"name": "焼肉 新宿 牛蔵", "address": "東京都新宿区歌舞伎町1-12-5", "rating": 4.3, "total_ratings": 678, "phone": "03-3205-XXXX", "hours": "17:00〜翌1:00（年中無休）", "description": "A5ランク黒毛和牛を一頭買いで仕入れる新宿の人気焼肉店。炭火で焼き上げる極上の肉質が自慢。", "features": ["焼肉", "黒毛和牛", "個室あり", "飲み放題"], "price_range": "¥5,000〜¥8,000"},
                {"name": "新宿 鮨 はしもと", "address": "東京都新宿区西新宿1-4-2", "rating": 4.7, "total_ratings": 234, "phone": "03-3344-XXXX", "hours": "11:30〜14:00, 17:00〜22:00（日曜定休）", "description": "築地直送の厳選ネタを使った江戸前寿司の名店。ミシュラン掲載歴のある実力派。", "features": ["寿司", "江戸前", "カウンター", "コース"], "price_range": "¥12,000〜¥20,000"},
                {"name": "ラーメン 凪 新宿ゴールデン街店", "address": "東京都新宿区歌舞伎町1-1-10", "rating": 4.1, "total_ratings": 2340, "phone": "03-3209-XXXX", "hours": "11:00〜翌4:00（年中無休）", "description": "煮干しラーメンの聖地。濃厚な煮干しスープは一度食べたら忘れられない中毒性のある一杯。", "features": ["ラーメン", "煮干し", "深夜営業", "行列店"], "price_range": "¥900〜¥1,400"},
                {"name": "居酒屋 新宿 てっぺん", "address": "東京都新宿区西新宿7-10-3", "rating": 4.0, "total_ratings": 512, "phone": "03-3366-XXXX", "hours": "17:00〜翌5:00（日曜定休）", "description": "朝まで営業の活気ある居酒屋。毎日届く鮮魚と創作料理が楽しめる新宿の隠れ家。", "features": ["居酒屋", "鮮魚", "深夜営業", "宴会"], "price_range": "¥3,000〜¥5,000"},
                {"name": "タイ料理 バンコクナイト 新宿店", "address": "東京都新宿区歌舞伎町2-26-3", "rating": 4.2, "total_ratings": 389, "phone": "03-3207-XXXX", "hours": "11:30〜23:00（年中無休）", "description": "タイ人シェフが作る本場の味。グリーンカレーとトムヤムクンは在日タイ人も認める本格派。", "features": ["タイ料理", "カレー", "ランチ", "エスニック"], "price_range": "¥1,500〜¥3,000"},
                {"name": "天ぷら 新宿 つな八 本店", "address": "東京都新宿区新宿3-31-8", "rating": 4.4, "total_ratings": 876, "phone": "03-3352-XXXX", "hours": "11:00〜22:00（年中無休）", "description": "創業90年以上の天ぷら老舗。目の前で揚げるカウンター席は外国人観光客にも大人気。", "features": ["天ぷら", "老舗", "カウンター", "ランチ"], "price_range": "¥2,000〜¥6,000"},
            ],
            "bars": [
                {"name": "Bar GOLD FINGER 新宿", "address": "東京都新宿区歌舞伎町1-3-15 ビル8F", "rating": 4.1, "total_ratings": 145, "phone": "03-3208-XXXX", "hours": "20:00〜翌5:00（不定休）", "description": "新宿の夜景を一望するスカイバー。世界各国のウイスキー300種以上を取り揃えた大人の隠れ家。", "features": ["バー", "ウイスキー", "夜景", "VIP席"], "price_range": "¥4,000〜¥8,000"},
            ],
        },
        "渋谷": {
            "lat": 35.6580, "lng": 139.7016,
            "restaurants": [
                {"name": "焼鳥 渋谷 鳥よし", "address": "東京都渋谷区道玄坂2-6-14", "rating": 4.5, "total_ratings": 423, "phone": "03-3461-XXXX", "hours": "17:00〜翌1:00（日曜定休）", "description": "備長炭で丁寧に焼き上げる至高の焼鳥。地鶏の旨みを最大限に引き出す職人技が光る名店。", "features": ["焼鳥", "地鶏", "日本酒", "カウンター"], "price_range": "¥4,000〜¥6,000"},
                {"name": "渋谷 スパイスカレー MOKUBAZA", "address": "東京都渋谷区宇田川町15-1", "rating": 4.3, "total_ratings": 1567, "phone": "03-6416-XXXX", "hours": "11:30〜22:00（火曜定休）", "description": "20種類以上のスパイスを独自ブレンドした渋谷No.1スパイスカレー。あいがけが人気。", "features": ["カレー", "スパイス", "ランチ", "あいがけ"], "price_range": "¥1,200〜¥1,800"},
                {"name": "鉄板焼 渋谷 うかい亭", "address": "東京都渋谷区神宮前5-10-1", "rating": 4.6, "total_ratings": 345, "phone": "03-5467-XXXX", "hours": "11:30〜15:00, 17:00〜22:00（月曜定休）", "description": "厳選された神戸牛を目の前の鉄板で。特別な日に訪れたい渋谷の最高峰鉄板焼レストラン。", "features": ["鉄板焼", "神戸牛", "記念日", "ワイン"], "price_range": "¥15,000〜¥25,000"},
                {"name": "つけ麺 渋谷 道玄坂マルジ", "address": "東京都渋谷区道玄坂1-5-9", "rating": 4.0, "total_ratings": 2100, "phone": "03-3770-XXXX", "hours": "11:00〜翌3:00（年中無休）", "description": "極太麺と濃厚魚介豚骨スープのつけ麺は渋谷の若者に絶大な支持。深夜営業も嬉しい。", "features": ["つけ麺", "濃厚", "深夜営業", "大盛り無料"], "price_range": "¥850〜¥1,300"},
                {"name": "韓国料理 渋谷 ホンデポチャ", "address": "東京都渋谷区宇田川町31-1", "rating": 4.2, "total_ratings": 890, "phone": "03-6455-XXXX", "hours": "11:30〜翌2:00（年中無休）", "description": "本場ソウルの味を再現した韓国料理専門店。チーズタッカルビとサムギョプサルが大人気。", "features": ["韓国料理", "チーズタッカルビ", "サムギョプサル", "飲み放題"], "price_range": "¥2,500〜¥4,000"},
            ],
            "bars": [
                {"name": "WOMB 渋谷", "address": "東京都渋谷区円山町2-16", "rating": 4.0, "total_ratings": 670, "phone": "03-5459-XXXX", "hours": "23:00〜翌5:00（金土のみ営業）", "description": "渋谷を代表する世界的クラブ。4フロア構成で国内外の有名DJが毎週パフォーマンス。", "features": ["クラブ", "DJ", "4フロア", "世界的"], "price_range": "¥3,500〜¥5,000"},
            ],
        },
        "六本木": {
            "lat": 35.6627, "lng": 139.7311,
            "restaurants": [
                {"name": "六本木 鮨 さいとう", "address": "東京都港区六本木1-4-5 B1F", "rating": 4.8, "total_ratings": 312, "phone": "03-3589-XXXX", "hours": "12:00〜14:00, 17:00〜22:00（日祝定休）", "description": "予約困難な六本木の超名店。研ぎ澄まされた技術と厳選素材が織りなす至高の江戸前寿司。", "features": ["寿司", "予約困難", "おまかせ", "名店"], "price_range": "¥30,000〜¥50,000"},
                {"name": "焼肉 六本木 叙々苑 游玄亭", "address": "東京都港区六本木6-1-20", "rating": 4.4, "total_ratings": 1023, "phone": "03-3403-XXXX", "hours": "17:00〜翌5:00（年中無休）", "description": "叙々苑の最高峰ブランド。完全個室で楽しむ最上級の焼肉は接待や記念日に最適。", "features": ["焼肉", "完全個室", "接待", "高級"], "price_range": "¥15,000〜¥30,000"},
                {"name": "六本木 おでん割烹 稲垣", "address": "東京都港区六本木3-14-7", "rating": 4.3, "total_ratings": 198, "phone": "03-3401-XXXX", "hours": "17:30〜23:30（日曜定休）", "description": "出汁にこだわり抜いた上品なおでんと季節の割烹料理。六本木の大人が通う隠れ家的名店。", "features": ["おでん", "割烹", "日本酒", "隠れ家"], "price_range": "¥8,000〜¥12,000"},
                {"name": "イタリアン 六本木 リストランテ・ルッチョラ", "address": "東京都港区六本木7-18-12", "rating": 4.5, "total_ratings": 456, "phone": "03-3478-XXXX", "hours": "11:30〜14:30, 18:00〜23:00（月曜定休）", "description": "本場イタリアで修業したシェフによる正統派イタリアン。自家製パスタとワインのペアリングが絶品。", "features": ["イタリアン", "パスタ", "ワイン", "デート向き"], "price_range": "¥8,000〜¥15,000"},
                {"name": "六本木 担々麺 はしご", "address": "東京都港区六本木4-11-2", "rating": 4.1, "total_ratings": 745, "phone": "03-3402-XXXX", "hours": "11:00〜翌5:00（年中無休）", "description": "濃厚ゴマベースの担々麺が名物。深夜の六本木で〆の一杯に最適な行列ラーメン店。", "features": ["担々麺", "ラーメン", "深夜営業", "〆"], "price_range": "¥900〜¥1,500"},
            ],
            "bars": [
                {"name": "Bar HIGH FIVE 六本木", "address": "東京都港区六本木7-2-8 3F", "rating": 4.7, "total_ratings": 234, "phone": "03-3423-XXXX", "hours": "18:00〜翌2:00（日曜定休）", "description": "世界のベストバー50にランクインした伝説のバー。一杯一杯に魂を込めたカクテルは芸術品。", "features": ["バー", "カクテル", "世界ランク", "大人の空間"], "price_range": "¥3,000〜¥6,000"},
            ],
        },
        "銀座": {
            "lat": 35.6717, "lng": 139.7649,
            "restaurants": [
                {"name": "銀座 天一 本店", "address": "東京都中央区銀座6-6-5", "rating": 4.5, "total_ratings": 567, "phone": "03-3571-XXXX", "hours": "11:30〜21:30（年中無休）", "description": "創業80年の天ぷら老舗。ごま油100%で揚げる江戸前天ぷらは軽やかで香り豊か。", "features": ["天ぷら", "老舗", "江戸前", "ごま油"], "price_range": "¥5,000〜¥12,000"},
                {"name": "銀座 すき焼き 吉澤", "address": "東京都中央区銀座3-9-19", "rating": 4.6, "total_ratings": 289, "phone": "03-3541-XXXX", "hours": "11:30〜14:00, 17:00〜22:00（日祝定休）", "description": "自社牧場から直送の黒毛和牛を使った極上のすき焼き。割り下の甘辛い香りが食欲をそそる。", "features": ["すき焼き", "黒毛和牛", "老舗", "個室"], "price_range": "¥10,000〜¥18,000"},
                {"name": "銀座 フレンチ ロオジエ", "address": "東京都中央区銀座7-5-5", "rating": 4.7, "total_ratings": 178, "phone": "03-3571-XXXX", "hours": "12:00〜13:30, 18:00〜21:00（日月定休）", "description": "三ツ星フレンチの殿堂。完璧なサービスと芸術的な料理が織りなす最高峰のダイニング体験。", "features": ["フレンチ", "三ツ星", "コース", "ワインペアリング"], "price_range": "¥30,000〜¥50,000"},
                {"name": "銀座 蕎麦 よし田", "address": "東京都中央区銀座4-4-13", "rating": 4.2, "total_ratings": 432, "phone": "03-3564-XXXX", "hours": "11:00〜20:30（日曜定休）", "description": "昭和から続く銀座の蕎麦処。石臼挽きの二八蕎麦と名物のカレー南蛮が地元客に愛される。", "features": ["蕎麦", "カレー南蛮", "老舗", "ランチ"], "price_range": "¥1,200〜¥2,500"},
                {"name": "銀座 うなぎ 竹葉亭 本店", "address": "東京都中央区銀座8-14-7", "rating": 4.4, "total_ratings": 356, "phone": "03-3542-XXXX", "hours": "11:30〜14:00, 16:30〜20:30（日曜定休）", "description": "明治創業の鰻の名店。備長炭でじっくり焼き上げる江戸前の蒲焼きは絶品。", "features": ["うなぎ", "蒲焼", "明治創業", "老舗"], "price_range": "¥4,000〜¥8,000"},
            ],
            "bars": [
                {"name": "Bar LUPIN 銀座", "address": "東京都中央区銀座5-5-11", "rating": 4.5, "total_ratings": 312, "phone": "03-3571-XXXX", "hours": "17:00〜23:00（日祝定休）", "description": "1928年創業、文豪も通った銀座最古のバー。アールデコ調の店内でクラシックカクテルを。", "features": ["バー", "老舗", "クラシック", "歴史的"], "price_range": "¥2,500〜¥5,000"},
            ],
        },
        "恵比寿": {
            "lat": 35.6467, "lng": 139.7100,
            "restaurants": [
                {"name": "恵比寿 とんかつ あげ福", "address": "東京都渋谷区恵比寿1-13-7", "rating": 4.4, "total_ratings": 567, "phone": "03-5424-XXXX", "hours": "11:30〜14:30, 17:30〜22:00（水曜定休）", "description": "銘柄豚を低温でじっくり揚げる極上のとんかつ。衣はサクサク、中はジューシーの黄金比。", "features": ["とんかつ", "銘柄豚", "ランチ", "ロースかつ"], "price_range": "¥1,800〜¥3,500"},
                {"name": "恵比寿 ビストロ ルヴァン", "address": "東京都渋谷区恵比寿南1-7-3", "rating": 4.3, "total_ratings": 345, "phone": "03-3713-XXXX", "hours": "18:00〜翌1:00（日曜定休）", "description": "気軽に楽しめるフレンチビストロ。ワインと料理のマリアージュを恵比寿の路地裏で。", "features": ["ビストロ", "ワイン", "フレンチ", "路地裏"], "price_range": "¥5,000〜¥8,000"},
                {"name": "恵比寿 中華 龍天門", "address": "東京都渋谷区恵比寿4-20-3", "rating": 4.5, "total_ratings": 678, "phone": "03-5420-XXXX", "hours": "11:30〜14:30, 17:30〜22:00（年中無休）", "description": "ウェスティンホテル内の本格広東料理。飲茶ランチは特に人気で予約必須。", "features": ["中華", "広東料理", "飲茶", "ホテルレストラン"], "price_range": "¥6,000〜¥12,000"},
                {"name": "恵比寿 蕎麦 翁", "address": "東京都渋谷区恵比寿2-28-10", "rating": 4.2, "total_ratings": 234, "phone": "03-3441-XXXX", "hours": "11:30〜15:00, 17:30〜21:00（月曜定休）", "description": "十割蕎麦にこだわる蕎麦通の聖地。毎朝石臼で挽く蕎麦粉の香りが店内に広がる。", "features": ["蕎麦", "十割", "手打ち", "日本酒"], "price_range": "¥1,500〜¥3,000"},
            ],
            "bars": [
                {"name": "Bar TRENCH 恵比寿", "address": "東京都渋谷区恵比寿西1-5-8", "rating": 4.4, "total_ratings": 189, "phone": "03-3780-XXXX", "hours": "18:00〜翌2:00（日曜定休）", "description": "自家製インフュージョンとボタニカルカクテルで世界から注目される恵比寿の名バー。", "features": ["バー", "クラフトカクテル", "自家製", "ボタニカル"], "price_range": "¥2,500〜¥5,000"},
            ],
        },
        # ===== 福岡（既存） =====
        "中洲": {
            "lat": 33.5902, "lng": 130.4017,
            "restaurants": [
                {"name": "博多もつ鍋 やまや 中洲店", "address": "福岡県福岡市博多区中洲3-6-7", "rating": 4.2, "total_ratings": 342, "phone": "092-281-XXXX", "hours": "17:00〜24:00（日曜定休）", "description": "博多名物もつ鍋を中心に、新鮮なホルモンと特製スープが自慢の人気店。", "features": ["もつ鍋", "焼酎", "個室あり", "宴会対応"], "price_range": "¥3,000〜¥5,000"},
                {"name": "中洲 鮨 よしだ", "address": "福岡県福岡市博多区中洲4-2-14", "rating": 4.6, "total_ratings": 128, "phone": "092-282-XXXX", "hours": "18:00〜翌2:00（不定休）", "description": "玄界灘の新鮮な魚介を使った本格江戸前寿司。カウンター席での会話も魅力。", "features": ["寿司", "刺身", "日本酒", "カウンター"], "price_range": "¥8,000〜¥15,000"},
                {"name": "焼鳥 中洲 とりかわ粋恭", "address": "福岡県福岡市博多区中洲2-8-20", "rating": 4.4, "total_ratings": 567, "phone": "092-263-XXXX", "hours": "18:00〜翌3:00（月曜定休）", "description": "博多名物とりかわを筆頭に、炭火で丁寧に焼き上げる焼鳥専門店。", "features": ["焼鳥", "とりかわ", "ビール", "テイクアウト可"], "price_range": "¥2,000〜¥4,000"},
                {"name": "屋台 ラーメン 長浜家", "address": "福岡県福岡市博多区中洲1-4-5", "rating": 4.0, "total_ratings": 891, "phone": "092-291-XXXX", "hours": "19:00〜翌4:00（年中無休）", "description": "中洲の屋台文化を守り続ける老舗。濃厚豚骨スープのラーメンが看板メニュー。", "features": ["ラーメン", "豚骨", "屋台", "深夜営業"], "price_range": "¥700〜¥1,200"},
            ],
            "bars": [
                {"name": "Bar Moonlight 中洲", "address": "福岡県福岡市博多区中洲4-7-3 ビル5F", "rating": 4.3, "total_ratings": 87, "phone": "092-283-XXXX", "hours": "20:00〜翌5:00（日曜定休）", "description": "中洲のネオン街を一望できるルーフトップバー。オリジナルカクテルが好評。", "features": ["バー", "カクテル", "夜景", "デート向き"], "price_range": "¥3,000〜¥6,000"},
            ],
        },
    }

    # エリアのマッチング（部分一致）
    matched_area = None
    for key in MOCK_DB:
        if key in area:
            matched_area = key
            break

    if not matched_area:
        # マッチしなければ新宿をデフォルトに
        matched_area = "新宿"

    data = MOCK_DB[matched_area]
    base_lat, base_lng = data["lat"], data["lng"]

    if business_type in ("bar", "night_club"):
        source = data.get("bars", []) + data.get("restaurants", [])[:2]
    else:
        source = data.get("restaurants", [])

    businesses = []
    for i, biz in enumerate(source):
        businesses.append({
            "place_id": f"mock_{matched_area}_{i}_{biz['name'][:4]}",
            "name": biz["name"],
            "address": biz["address"],
            "rating": biz["rating"],
            "total_ratings": biz["total_ratings"],
            "types": ["restaurant", "food"] if business_type != "bar" else ["bar"],
            "phone": biz.get("phone", ""),
            "hours": biz.get("hours", ""),
            "description": biz.get("description", ""),
            "features": biz.get("features", []),
            "price_range": biz.get("price_range", ""),
            "lat": base_lat + random.uniform(-0.003, 0.003),
            "lng": base_lng + random.uniform(-0.003, 0.003),
            "photo_ref": None,
            "business_status": "OPERATIONAL",
            "area": area,
            "discovered_at": datetime.now().isoformat(),
        })

    return businesses


def save_businesses(businesses: list[dict], filename: str = "discovered_businesses.json"):
    """発見したビジネスをJSONで保存"""
    filepath = os.path.join(GENERATED_SITES_DIR, filename)
    
    # 既存データがあればマージ
    existing = []
    if os.path.exists(filepath):
        with open(filepath, "r", encoding="utf-8") as f:
            existing = json.load(f)
    
    # place_idで重複排除
    existing_ids = {b["place_id"] for b in existing}
    for biz in businesses:
        if biz["place_id"] not in existing_ids:
            existing.append(biz)
            existing_ids.add(biz["place_id"])
    
    with open(filepath, "w", encoding="utf-8") as f:
        json.dump(existing, f, ensure_ascii=False, indent=2)
    
    print(f"[SAVED] {len(existing)} businesses → {filepath}")
    return existing


def load_businesses(filename: str = "discovered_businesses.json") -> list[dict]:
    """保存済みビジネスを読み込み"""
    filepath = os.path.join(GENERATED_SITES_DIR, filename)
    if not os.path.exists(filepath):
        return []
    with open(filepath, "r", encoding="utf-8") as f:
        return json.load(f)

# アポ太郎 v2 — Claude Code 作戦書

> 参考元: z-developer合同会社「アポ太郎」（Threads @z_developer_llc）
> 参考サイト: nakasuvision.zdev.co.jp

---

## ゴール

**「サイトを持っていない飲食店」を自動で発見し、プロ品質のHPを自動生成し、営業DMまで自動作成するローカルシステム**

人間がやるのは最終チェックだけ。

---

## 参考元との差分分析（現状の問題点）

| 項目 | 参考元（z-developer） | うち（現状v1） | v2で目指す |
|------|----------------------|---------------|-----------|
| **ターゲット抽出** | Googleマップから**サイト未登録店**を発見 | 全店舗を無差別に取得 | **website=null の店舗のみ抽出** |
| **画像** | Google Maps + Instagram から実写真取得、合成画像自動生成 | 画像なし（SVGプレースホルダー） | **実写真取得 + フリー画像フォールバック + SVG最終手段** |
| **デザイン** | プロのWeb制作会社レベル（nakasuvision参考） | 死ぬほどダサい（本人談） | **モダン・高品質・業種別テンプレート** |
| **コピーライティング** | AIが店舗情報から自動生成 | モック固定文 | **Claude APIで店舗データから自動生成** |
| **DM文面** | 自動生成 | なし | **Phase 2で実装** |
| **Telegram連携** | 全部Telegramで完結 | なし | **Phase 3で実装** |

---

## Phase 1: コア改修（今回Claude Codeでやること）

### 1.1 サイト未登録店舗の抽出

**Google Places APIの `website` フィールドを活用する。**

```python
# discovery.py の改修ポイント

def search_businesses_without_website(area, business_type, radius):
    """
    Google Places API で検索し、website フィールドが空の店舗のみ返す
    = HPを持っていない = 営業チャンスのある店舗
    """
    # Step 1: Nearby Search で候補を取得
    results = nearby_search(area, business_type, radius)

    # Step 2: 各店舗の Place Details を取得して website を確認
    targets = []
    for place in results:
        details = get_place_details(place["place_id"])
        
        # website が空 or 存在しない = ターゲット
        if not details.get("website"):
            targets.append({
                **place,
                "has_website": False,
                "phone": details.get("formatted_phone_number", ""),
                "hours": details.get("opening_hours", {}).get("weekday_text", []),
                "reviews": details.get("reviews", [])[:3],  # レビュー上位3件
                "photos": details.get("photos", []),  # photo_reference リスト
            })
    
    return targets
```

**重要なAPI呼び出しフロー：**
```
Nearby Search（1回） → 最大20件の候補
    ↓
Place Details（候補数 × 1回） → website有無を確認 + 詳細情報取得
    ↓
website=null の店舗だけ残す → ターゲットリスト完成
```

**モックモードでの対応：**
- モックデータに `has_website: false` フラグを追加
- 一部の店舗に `has_website: true` を設定して、フィルタの動作を確認可能に

### 1.2 画像取得パイプライン

**フォールバックチェーン（3段構え）：**

```
優先度1: Google Places Photo API
  → Place Details で取得した photo_reference を使用
  → maxwidth=1920 で高解像度取得
  → 1店舗あたり最大5枚
  │
  ├─ 取得成功 → ローカル保存して使用
  │
  └─ 失敗 or APIキーなし or 写真0枚
       │
       ▼
優先度2: フリー画像API（Pexels API 推奨）
  → 業種キーワード（英語）で検索
  → "japanese sushi restaurant interior" 等
  → Pexels は月間200リクエスト無料、商用利用OK
  │
  ├─ 取得成功 → ローカル保存して使用
  │
  └─ 失敗 or APIキーなし
       │
       ▼
優先度3: CSSグラデーション + SVGパターン
  → 業種ごとのリッチなビジュアル
  → 画像なしでも「それっぽく」見えるCSS演出
  → テクスチャ + グラデーション + パターンで最低限の品質保証
```

**なぜ Unsplash じゃなくて Pexels か：**
- Pexels API: 月200リクエスト無料、商用利用OK、クレジット不要
- Unsplash API: 月50リクエスト、クレジット表記必須
- → Pexels の方が営業HP用途に適している

**画像の種類と用途：**

| スロット | 推奨サイズ | 用途 |
|---------|-----------|------|
| `hero` | 1920×1080 | ヒーロー背景（全画面、オーバーレイ付き） |
| `gallery_1〜4` | 800×600 | ギャラリーセクション |
| `og_image` | 1200×630 | OGP（SNSシェア時のサムネイル） |

**images.py の設計：**
```python
class ImagePipeline:
    def __init__(self, google_key=None, pexels_key=None):
        self.google_key = google_key
        self.pexels_key = pexels_key

    def fetch_images(self, business: dict, output_dir: str) -> dict:
        """
        ビジネスの画像を取得
        Returns: {
            "hero": "images/hero.jpg" | None,
            "gallery": ["images/g1.jpg", ...],
            "source": "google" | "pexels" | "css_only",
            "count": 3
        }
        """
        images = {"hero": None, "gallery": [], "source": "css_only", "count": 0}
        os.makedirs(os.path.join(output_dir, "images"), exist_ok=True)

        # 1. Google Places Photos
        if self.google_key and business.get("photos"):
            fetched = self._fetch_google_photos(business["photos"], output_dir)
            if fetched:
                images["hero"] = fetched[0]
                images["gallery"] = fetched[1:5]
                images["source"] = "google"
                images["count"] = len(fetched)
                return images

        # 2. Pexels API
        if self.pexels_key:
            query = self._build_pexels_query(business)
            fetched = self._fetch_pexels(query, count=5, output_dir=output_dir)
            if fetched:
                images["hero"] = fetched[0]
                images["gallery"] = fetched[1:5]
                images["source"] = "pexels"
                images["count"] = len(fetched)
                return images

        # 3. CSS only（画像なし、CSSで演出）
        return images

    def _fetch_google_photos(self, photos, output_dir):
        """Google Places Photo API で写真をダウンロード"""
        downloaded = []
        for i, photo in enumerate(photos[:5]):
            ref = photo.get("photo_reference")
            if not ref:
                continue
            url = (
                f"https://maps.googleapis.com/maps/api/place/photo"
                f"?maxwidth=1920&photo_reference={ref}&key={self.google_key}"
            )
            path = os.path.join(output_dir, "images", f"photo_{i}.jpg")
            # urllib or requests でダウンロード
            # Pillow でリサイズ・最適化
            downloaded.append(f"images/photo_{i}.jpg")
        return downloaded

    def _build_pexels_query(self, business):
        """業種から英語の検索クエリを生成"""
        QUERIES = {
            "sushi": "japanese sushi restaurant",
            "ramen": "ramen noodle shop japan",
            "yakiniku": "japanese BBQ yakiniku",
            "izakaya": "japanese izakaya pub",
            "bar": "cocktail bar night",
            "french": "french restaurant fine dining",
            "cafe": "cafe coffee shop interior",
            "default": "japanese restaurant interior",
        }
        category = classify_business(business)
        return QUERIES.get(category, QUERIES["default"])

    def _fetch_pexels(self, query, count, output_dir):
        """Pexels API で画像を取得"""
        # GET https://api.pexels.com/v1/search?query={query}&per_page={count}
        # Authorization: {pexels_key}
        # レスポンスから photos[].src.large をダウンロード
        ...
```

### 1.3 AIコピーライティング

**店舗の生データ（名前・住所・評価・レビュー・業種）からプロ品質の紹介文を自動生成。**

```python
# copywriter.py

def generate_store_copy(business: dict) -> dict:
    """
    Claude API（またはローカルLLM）で店舗紹介文を生成
    
    Returns: {
        "tagline": "一文のキャッチコピー",
        "description": "3〜4文の紹介文",
        "sections": {
            "about": "当店についての詳細文",
            "atmosphere": "雰囲気の説明",
            "recommend": "おすすめポイント",
        }
    }
    """
    # 入力データを構造化
    context = f"""
    店名: {business['name']}
    住所: {business['address']}
    業種: {classify_business(business)}
    評価: {business['rating']}（{business['total_ratings']}件）
    特徴: {', '.join(business.get('features', []))}
    価格帯: {business.get('price_range', '不明')}
    営業時間: {business.get('hours', '不明')}
    レビュー抜粋: {_format_reviews(business.get('reviews', []))}
    """

    prompt = f"""
    以下の飲食店の情報から、ホームページ用の紹介文を日本語で生成してください。

    {context}

    以下の形式でJSON出力:
    {{
        "tagline": "キャッチコピー（15文字以内）",
        "description": "店舗紹介（3〜4文、80〜120文字）",
        "about": "詳しい紹介文（5〜8文、150〜250文字）",
        "atmosphere": "店の雰囲気の説明（2〜3文）",
        "recommend": "おすすめポイント（3つの箇条書き）"
    }}
    
    トーンは温かみがありつつプロフェッショナル。
    実際のHP掲載を想定した自然な文章で。
    """
    
    # Claude API or OpenAI API で生成
    # APIキーがなければモックコピーを返す
```

**APIキーなし時のモック対応：**
- 業種ごとのテンプレート文（5パターンずつ）を内蔵
- 店名・特徴をテンプレートに差し込んで疑似生成

### 1.4 デザイン大幅改善

**参考: nakasuvision.zdev.co.jp のデザイン要素分析**

```
【nakasuvision から学ぶべきポイント】

1. ヒーロー: 動画 or 高品質画像が全画面背景。テキストはシンプルに中央配置
2. CTAボタン: 常に視界に入る位置に。グラデーション背景で目立つ
3. セクション: カード型UI、アイコン付き、余白たっぷり
4. FAQ: アコーディオン形式
5. フッター: LINE/電話/Instagramへの導線
6. ポップアップ: 初回訪問時のキャンペーン告知
7. 配色: ダーク基調 + アクセントカラー（ゴールド系）
8. フォント: 見出し=太め、本文=読みやすいゴシック
9. アニメーション: スクロール連動のフェードイン
10. レスポンシブ: スマホファースト（中洲の客層を考慮）
```

**飲食店HPのデザイン原則：**

```
【NG（現状v1の問題点）】
✗ テキストだけの地味なカード
✗ 画像が一切ない
✗ 余白が少なすぎてギチギチ
✗ フォントサイズが均一で抑揚がない
✗ CTAが目立たない
✗ 「それっぽさ」がゼロ — 明らかにテンプレート感

【OK（v2で実現すること）】
✓ 全画面ヒーロー画像 + 半透明オーバーレイ + 大きな店名
✓ フォトギャラリー（グリッド or スライダー）
✓ カード型の店舗情報（アイコン + ラベル + 値）
✓ Google Maps埋め込み
✓ 電話CTAボタン（大きく、目立つ色）
✓ スクロールアニメーション（IntersectionObserver）
✓ モバイルファースト（中洲/新宿の客層はスマホ9割）
✓ OGPメタタグ（LINE/Xでシェアした時にリッチに表示）
```

---

## 設計書・スキル・ファイル構成

### ファイル構成（v2）

```
apo-taro/
├── CLAUDE.md                 # Claude Code が最初に読むファイル
├── config.py                 # 環境変数・設定（.env対応）
├── .env.example              # 環境変数テンプレート
├── requirements.txt
│
├── discovery.py              # ビジネス発見（website=null フィルタ付き）
├── images.py                 # 画像取得パイプライン（Google→Pexels→CSS）
├── copywriter.py             # AIコピーライティング（Claude API→モック）
├── generator.py              # HP生成エンジン（Jinja2テンプレート）
├── pipeline.py               # 全自動パイプライン + スケジューラ
├── app.py                    # Flask ダッシュボード + API
│
├── templates/
│   ├── dashboard.html        # 管理ダッシュボード
│   └── hp/                   # HP用Jinja2テンプレート
│       ├── base.html         # 共通ベース
│       ├── default.html      # 汎用飲食店
│       ├── japanese.html     # 和食（寿司・天ぷら・うなぎ・蕎麦）
│       ├── casual.html       # カジュアル（ラーメン・焼鳥・居酒屋）
│       ├── bar.html          # バー・クラブ
│       └── luxury.html       # 高級店（フレンチ・鉄板焼）
│
├── generated_sites/          # 生成済みHP出力先
│   └── {store_hash}/
│       ├── index.html
│       ├── images/
│       │   ├── hero.jpg
│       │   ├── g1.jpg〜g4.jpg
│       │   └── og.jpg
│       └── meta.json
│
├── skills/
│   └── hp-design/
│       └── SKILL.md          # HP生成スキル（カラー・テンプレ・品質基準）
│
└── reference/                # v1の動作済みコード（参考実装）
    ├── discovery.py
    ├── generator.py
    ├── pipeline.py
    ├── app.py
    └── dashboard.html
```

### 環境変数

```bash
# .env.example

# Google Places API（メイン：店舗発見 + 写真取得）
GOOGLE_PLACES_API_KEY=

# Pexels API（フォールバック画像）
# 取得: https://www.pexels.com/api/
PEXELS_API_KEY=

# Claude API（AIコピーライティング）※任意
# なければモックテンプレートで代替
ANTHROPIC_API_KEY=

# サーバー設定
HOST=127.0.0.1
PORT=5000
```

### パイプライン全体像（v2）

```
python pipeline.py --areas "新宿,渋谷,六本木" --type restaurant

  ┌─────────────────────────────────────┐
  │  STEP 1: DISCOVER                   │
  │  Google Places API で店舗検索        │
  │  → Place Details で website 確認     │
  │  → website=null の店舗だけ抽出       │
  │                                     │
  │  結果: "サイトを持っていない店" リスト │
  └──────────────┬──────────────────────┘
                 │
                 ▼
  ┌─────────────────────────────────────┐
  │  STEP 2: IMAGES                     │
  │  Google Places Photo API で実写真取得 │
  │  → 失敗なら Pexels API でフリー画像  │
  │  → 最終手段: CSSグラデーション       │
  │  Pillow でリサイズ・最適化            │
  └──────────────┬──────────────────────┘
                 │
                 ▼
  ┌─────────────────────────────────────┐
  │  STEP 3: COPY                       │
  │  Claude API で紹介文自動生成         │
  │  → 店名・評価・レビュー・業種を入力   │
  │  → tagline + description + about    │
  │  → APIキーなしならモックテンプレート  │
  └──────────────┬──────────────────────┘
                 │
                 ▼
  ┌─────────────────────────────────────┐
  │  STEP 4: GENERATE                   │
  │  業種判定 → Jinja2テンプレート選択    │
  │  → 画像配置 + コピー配置 + スタイル   │
  │  → 1店舗 = 1フォルダ（HTML + images）│
  └──────────────┬──────────────────────┘
                 │
                 ▼
  ┌─────────────────────────────────────┐
  │  STEP 5: REPORT                     │
  │  ダッシュボードで一覧管理             │
  │  → サムネイル付き一覧                │
  │  → HPプレビューリンク                │
  │  → 画像取得状況（📷3枚/Google）      │
  └─────────────────────────────────────┘
```

---

## Claude Code への指示手順

### 最初のプロンプト

```
以下のファイルを全て読んでからビルドを開始してください:
1. CLAUDE.md — プロジェクト概要
2. STRATEGY.md — この作戦書（最重要）
3. skills/hp-design/SKILL.md — デザインスキル

reference/ フォルダに v1 の動作済みコードがあります。

ビルド順序:
1. config.py（.env対応）
2. discovery.py（website=null フィルタ追加）
3. images.py（Google Photos → Pexels → CSS フォールバック）
4. copywriter.py（Claude API → モック）
5. templates/hp/（Jinja2テンプレート5種）★ デザインの品質がここで決まる
6. generator.py（Jinja2化 + 業種判定 + 画像配置）
7. pipeline.py（5ステップパイプライン）
8. app.py + dashboard.html（サムネイル付き一覧）
9. テスト: python pipeline.py --areas "新宿,渋谷,六本木,銀座,恵比寿"

まず全ファイル読んで、質問があれば聞いてください。
なければビルド開始してください。
```

### デザインで妥協しないための追加指示

テンプレートのデザインが気に入らなかったら：

```
テンプレートのデザインをもっとリッチにして。
参考: https://nakasuvision.zdev.co.jp
このサイトのデザインクオリティを飲食店HPに落とし込んで。

具体的に:
- ヒーロー画像をもっと全面的に使って、テキストはオーバーレイで
- ギャラリーはグリッドレイアウトで画像にホバーエフェクト
- 情報カードはもっとシャドウとボーダーラディウスで立体感を
- CTAボタンはもっと大きく、グラデーション背景で
- スクロールアニメーションをもっと滑らかに
```

---

## モックモードの完全動作保証

**APIキーゼロでも以下が全て動くこと：**

1. ✅ 東京5エリアのモック店舗データ（30店舗、`has_website=false`付き）
2. ✅ CSSグラデーション + パターンによるヒーロー演出（画像なしでもリッチ）
3. ✅ モックコピー（業種別テンプレート文の自動差し込み）
4. ✅ ダッシュボードで一覧表示・プレビュー
5. ✅ 全パイプラインが1コマンドで完走

---

## ロードマップ

| Phase | 内容 | 優先度 |
|-------|------|--------|
| **Phase 1** | サイト未登録店抽出 + 画像取得 + AIコピー + リッチHP生成 | 🔥 今ここ |
| **Phase 2** | DM文面自動生成 + メール送信機能 | 次 |
| **Phase 3** | Telegram Bot連携（布団の中からOK押すだけ） | その次 |
| **Phase 4** | HP閲覧トラッキング + コンバージョン計測 | 将来 |
| **Phase 5** | Instagram連携（自動投稿 + DM） | 将来 |

# アポ太郎 — 詳細設計書

## 1. システム概要

### 1.1 コンセプト

Threadsで話題になった「アポ太郎」にインスパイアされた営業自動化システム。
指定エリアの店舗を自動で発見し、**画像付きのリッチなHP**を自動生成し、一覧で管理する。

```
[パイプライン全体像]

エリア・業種を指定
       │
       ▼
┌─────────────────┐
│ 1. DISCOVER      │  Google Places API でビジネス検索
│    ビジネス発見   │  → 店名・住所・評価・写真ref・営業時間を取得
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│ 2. IMAGES        │  Google Places Photo API で店舗写真を取得
│    画像取得      │  → 取得失敗時は Unsplash API でカテゴリ画像をフォールバック
│                  │  → それも失敗なら SVG プレースホルダー生成
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│ 3. GENERATE      │  業種判定 → テンプレート選択 → 画像配置 → HTML生成
│    HP生成        │  → generated_sites/{store}/ に出力
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│ 4. DASHBOARD     │  Flask ダッシュボードで一覧管理・プレビュー
│    一覧管理      │  → 各HPへのリンク・ステータス管理
└─────────────────┘
```

### 1.2 3つの実行モード

| モード | コマンド | 用途 |
|--------|---------|------|
| **GUI** | `python app.py` → ブラウザで操作 | ワンクリック操作 |
| **CLI** | `python pipeline.py --areas "新宿,渋谷"` | コマンド1発で全自動 |
| **スケジューラ** | `python pipeline.py --schedule 09:00` | 毎日自動実行 |

---

## 2. 画像取得システム（images.py）

### 2.1 画像取得の優先順位（フォールバックチェーン）

```
Priority 1: Google Places Photo API
  → photo_reference から実際の店舗写真を取得
  → 最大5枚（hero用1 + gallery用4）
  │
  ├─ 成功 → ローカルに保存して使用
  │
  └─ 失敗 or APIキーなし
       │
       ▼
Priority 2: Unsplash API
  → 業種キーワードで検索（"japanese sushi restaurant", "ramen shop" 等）
  → 最大5枚
  │
  ├─ 成功 → ローカルに保存して使用
  │
  └─ 失敗 or APIキーなし
       │
       ▼
Priority 3: SVGプレースホルダー生成
  → 業種に応じた色・パターンのSVGを動的生成
  → 「写真準備中」のオーバーレイテキスト付き
  → APIキーゼロでも美しいHPを保証
```

### 2.2 画像の種類と用途

各店舗HPで使用する画像スロット：

| スロット | サイズ | 用途 | 取得方法 |
|---------|--------|------|---------|
| `hero` | 1920×1080 | ヒーロー背景（全画面） | Places Photo (最高解像度) or Unsplash |
| `gallery_1〜4` | 800×600 | ギャラリーセクション | Places Photo (複数枚) |
| `atmosphere` | 1200×400 | 中間セクション背景 | Unsplash (雰囲気) |
| `og_image` | 1200×630 | OGP画像（SNSシェア用） | hero画像をリサイズ |

### 2.3 画像キャッシュ

```
generated_sites/{store_name}/images/
├── hero.jpg          # ヒーロー画像
├── gallery_1.jpg     # ギャラリー1
├── gallery_2.jpg     # ギャラリー2
├── gallery_3.jpg     # ギャラリー3
├── gallery_4.jpg     # ギャラリー4
├── atmosphere.jpg    # 雰囲気背景
└── og.jpg            # OGP画像
```

- 一度取得した画像はローカルキャッシュ
- 再生成時は既存画像を再利用（API呼び出し節約）
- `--refresh-images` フラグで強制再取得可能

### 2.4 SVGプレースホルダー仕様

APIキーなしでも美しく見えるよう、業種ごとにデザインされたSVGを生成：

```python
PLACEHOLDER_THEMES = {
    "sushi":      {"bg": "#1a1a2e", "accent": "#c9a96e", "pattern": "wave",      "icon": "🍣"},
    "ramen":      {"bg": "#2d1b0e", "accent": "#ff6b35", "pattern": "steam",     "icon": "🍜"},
    "yakiniku":   {"bg": "#1c1917", "accent": "#dc2626", "pattern": "flame",     "icon": "🥩"},
    "izakaya":    {"bg": "#1a1520", "accent": "#f59e0b", "pattern": "lantern",   "icon": "🏮"},
    "bar":        {"bg": "#0a0a0a", "accent": "#a855f7", "pattern": "neon",      "icon": "🍸"},
    "cafe":       {"bg": "#fef3e2", "accent": "#8b6914", "pattern": "bean",      "icon": "☕"},
    "french":     {"bg": "#1a1a2e", "accent": "#3b82f6", "pattern": "geometric", "icon": "🍷"},
    "tempura":    {"bg": "#fefce8", "accent": "#a16207", "pattern": "droplet",   "icon": "🍤"},
    "default":    {"bg": "#111827", "accent": "#6366f1", "pattern": "grid",      "icon": "🏪"},
}
```

---

## 3. HP生成エンジン（generator.py）

### 3.1 業種判定ロジック

店舗名・カテゴリ・特徴から業種を自動判定し、テンプレートとカラーを決定：

```python
def classify_business(business: dict) -> str:
    """
    Returns: "sushi" | "ramen" | "yakiniku" | "izakaya" | "bar" |
             "cafe" | "french" | "italian" | "tempura" | "tonkatsu" |
             "soba" | "unagi" | "chinese" | "korean" | "luxury" | "default"
    """
    # name + types + features を結合してキーワードマッチ
    text = f"{name} {' '.join(types)} {' '.join(features)}".lower()

    RULES = [
        (["寿司", "鮨", "sushi"],           "sushi"),
        (["ラーメン", "つけ麺", "ramen"],     "ramen"),
        (["焼肉", "yakiniku", "牛"],         "yakiniku"),
        (["焼鳥", "やきとり"],               "yakitori"),
        (["居酒屋", "izakaya"],              "izakaya"),
        (["bar", "バー", "クラブ", "club"],   "bar"),
        (["カフェ", "cafe", "coffee"],       "cafe"),
        (["フレンチ", "french", "ビストロ"],  "french"),
        (["イタリアン", "italian", "パスタ"], "italian"),
        (["天ぷら", "tempura"],              "tempura"),
        (["とんかつ", "tonkatsu"],           "tonkatsu"),
        (["蕎麦", "そば", "soba"],           "soba"),
        (["うなぎ", "鰻", "unagi"],          "unagi"),
        (["中華", "chinese", "中国"],        "chinese"),
        (["韓国", "korean", "サムギョプサル"], "korean"),
    ]

    for keywords, category in RULES:
        if any(kw in text for kw in keywords):
            return category

    # 価格帯で高級判定
    if price_range and "10,000" in price_range or "15,000" in price_range:
        return "luxury"

    return "default"
```

### 3.2 テンプレートシステム

Jinja2ベースのテンプレート。業種ごとに以下が変わる：

| 要素 | 業種による変化 |
|------|--------------|
| **カラースキーム** | 寿司→紺×金、焼肉→黒×赤、バー→黒×紫 etc |
| **フォント** | 和食→Noto Serif JP、カジュアル→Zen Kaku Gothic、高級→Cormorant Garamond |
| **レイアウト** | 高級店→大きな余白+縦書き要素、ラーメン→コンパクト+インパクト重視 |
| **ヒーロー演出** | バー→パララックス+暗め、カフェ→明るい+柔らかい |
| **セクション構成** | 全店共通（hero/about/gallery/info/access/cta）だがスタイリングが異なる |

### 3.3 HPセクション構成

```html
<!-- 全業種共通のセクション構成 -->

1. [NAV]        固定ナビゲーション（スクロールで表示）
2. [HERO]       全画面ヒーロー（背景画像 + 店名 + タグライン + 評価）
3. [ABOUT]      店舗紹介（説明文 + 特徴タグ）
4. [GALLERY]    フォトギャラリー（2×2 or 横スクロール）
5. [MENU]       メニューハイライト（価格帯表示）※情報があれば
6. [INFO]       店舗情報カード（住所・電話・営業時間・価格帯）
7. [ACCESS]     Google Maps埋め込み + アクセス情報
8. [CTA]        お問い合わせ / 予約ボタン
9. [FOOTER]     フッター + Powered by表記
```

### 3.4 リッチHP要件チェックリスト

生成された各HPが満たすべき品質基準：

- [ ] ヒーロー画像がフルスクリーンで表示される（画像なしの場合はSVGプレースホルダー）
- [ ] ギャラリーに最低2枚の画像がある
- [ ] Google Mapsが正しい座標で埋め込まれている
- [ ] スマホ表示で崩れない（max-width: 100%, レスポンシブ）
- [ ] ページ読み込み時のフェードインアニメーションがある
- [ ] スクロールに連動したセクション表示アニメーション
- [ ] OGPメタタグ（title, description, og:image）が設定されている
- [ ] Google Fonts が正しく読み込まれている
- [ ] 電話番号がタップで発信可能（tel:リンク）
- [ ] Lighthouse Performance スコア 80+

---

## 4. ダッシュボード（app.py）

### 4.1 Flask API エンドポイント

| メソッド | パス | 説明 |
|---------|------|------|
| GET | `/` | ダッシュボード画面 |
| POST | `/api/auto-pipeline` | フル自動実行（検索→画像取得→HP生成） |
| POST | `/api/discover` | ビジネス検索のみ |
| POST | `/api/generate` | HP生成のみ（単体） |
| POST | `/api/generate-all` | HP一括生成 |
| GET | `/api/sites` | 生成済みサイト一覧 |
| GET | `/sites/<path>` | 生成済みHPの静的配信 |
| DELETE | `/api/sites/<folder>` | サイト削除 |

### 4.2 ダッシュボード画面要素

```
┌──────────────────────────────────────────────────────────┐
│  🤖 アポ太郎                                              │
│                                                          │
│  [サイドバー]            [メイン]                          │
│  ├ 統計                  ┌─ コントロールパネル ──────────┐ │
│  │ 発見: 25件            │ エリア: [新宿,渋谷,...]      │ │
│  │ 生成: 25件            │ 業種:  [飲食店 ▼]           │ │
│  │ 送信: 0件             │ [🔥 フル自動] [発見] [生成]  │ │
│  ├ モード                └──────────────────────────────┘ │
│  │ 🟢 LIVE               ┌─ HP一覧 ─────────────────────┐ │
│  ├ APIキー               │ 🏪 六本木 鮨 さいとう  [HP] [📷5] │
│  │ ✅ Google Places       │ 🏪 新宿 焼肉 牛蔵     [HP] [📷3] │
│  │ ✅ Unsplash            │ 🏪 渋谷 鳥よし        [HP] [📷4] │
│  └                       │ ...                          │ │
│                          └──────────────────────────────┘ │
│                          ┌─ ログ ────────────────────────┐ │
│                          │ [01:28] ✅ 25件生成完了        │ │
│                          └──────────────────────────────┘ │
└──────────────────────────────────────────────────────────┘
```

---

## 5. モックモード

APIキーが一切なくても完全動作するモックモードを提供：

### 5.1 モックビジネスデータ

東京5エリア（新宿・渋谷・六本木・銀座・恵比寿）+ 福岡（中洲）の
計30店舗以上のリアルなモックデータを内蔵。

各店舗データに含まれる項目：
- name, address, rating, total_ratings, phone, hours
- description（2〜3文の説明）
- features（4つの特徴タグ）
- price_range
- lat/lng（実際の座標に近い値）

### 5.2 モック画像

APIキーなし時は以下で対応：
1. **SVGプレースホルダー** — 業種ごとのカラー・パターン・アイコンで生成
2. **CSSグラデーション** — ヒーロー背景は画像なしでも美しいグラデーション

---

## 6. ファイル別実装仕様

### 6.1 config.py

```python
# 環境変数から読み込み。.env ファイル対応（python-dotenv）
GOOGLE_PLACES_API_KEY = os.environ.get("GOOGLE_PLACES_API_KEY", "")
UNSPLASH_ACCESS_KEY = os.environ.get("UNSPLASH_ACCESS_KEY", "")
USE_MOCK = not bool(GOOGLE_PLACES_API_KEY)

# 画像設定
MAX_PHOTOS_PER_STORE = 5
PHOTO_MAX_WIDTH = 1920
PHOTO_QUALITY = 85  # JPEG品質

# サーバー設定
HOST = "127.0.0.1"
PORT = 5000
```

### 6.2 images.py（新規）

```python
class ImageFetcher:
    """画像取得・キャッシュ管理"""

    def fetch_for_business(self, business: dict, output_dir: str) -> dict:
        """
        ビジネスの画像を取得してローカルに保存
        Returns: {"hero": "path", "gallery": ["path", ...], "atmosphere": "path"}
        """

    def _fetch_google_places_photos(self, photo_references: list, output_dir: str) -> list[str]:
        """Google Places Photo API から取得"""

    def _fetch_unsplash(self, query: str, count: int, output_dir: str) -> list[str]:
        """Unsplash API から取得"""

    def _generate_svg_placeholder(self, category: str, slot: str, output_dir: str) -> str:
        """SVGプレースホルダーを生成"""
```

### 6.3 generator.py（Jinja2化）

```python
from jinja2 import Environment, FileSystemLoader

class HPGenerator:
    def __init__(self):
        self.env = Environment(loader=FileSystemLoader("templates/hp"))
        self.image_fetcher = ImageFetcher()

    def generate(self, business: dict) -> dict:
        category = classify_business(business)
        template = self._select_template(category)
        images = self.image_fetcher.fetch_for_business(business, output_dir)
        color_scheme = COLOR_SCHEMES[category]

        html = template.render(
            business=business,
            images=images,
            colors=color_scheme,
            category=category,
        )
        # 出力
        ...
```

---

## 7. 拡張ロードマップ

### Phase 1（現在）: HP自動生成 ✅
- ビジネス発見 + リッチHP生成 + ダッシュボード

### Phase 2: DM自動生成
- 各店舗向けの営業DM文面を自動生成
- HP URLを含むパーソナライズドメッセージ
- Instagram DM / メール / GoogleフォームのURL生成

### Phase 3: Telegram Bot連携
- パイプライン実行結果をTelegramに通知
- 「承認」ボタンでDM送信を許可
- 布団の中からOK押すだけの運用

### Phase 4: 反応トラッキング
- HP閲覧数のトラッキング（アクセスログ）
- DM送信 → 開封 → HP訪問 → 問い合わせ のファネル管理
- ダッシュボードにコンバージョン表示

---

## 8. 依存パッケージ

```
# requirements.txt
flask>=3.0.0
jinja2>=3.1.0
python-dotenv>=1.0.0
Pillow>=10.0.0          # 画像リサイズ・最適化
requests>=2.31.0        # API呼び出し
```

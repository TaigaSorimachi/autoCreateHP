# アポ太郎 — Claude Code ビルド指示書

## これは何か

このドキュメントはClaude Codeへの指示書です。
以下の手順で、画像付きリッチHPを自動生成する営業自動化システムを構築してください。

---

## STEP 0: プロジェクトセットアップ

```bash
# ディレクトリ作成
mkdir -p apo-taro/{templates/hp,static/placeholder,generated_sites,skills/hp-generator,tests}

# CLAUDE.md を配置（すでに同梱）
# .env.example を配置（すでに同梱）

# 依存パッケージインストール
cd apo-taro
pip install flask jinja2 python-dotenv Pillow requests
pip freeze > requirements.txt
```

---

## STEP 1: config.py

`reference/config.py` をベースに、以下を追加：
- `python-dotenv` による `.env` 読み込み
- `UNSPLASH_ACCESS_KEY` の読み込み
- 画像関連の設定（`MAX_PHOTOS_PER_STORE`, `PHOTO_MAX_WIDTH`）
- モードの自動判定（`USE_MOCK`, `HAS_UNSPLASH`）

---

## STEP 2: discovery.py

`reference/discovery.py` をそのまま使用可能。
東京5エリア（新宿・渋谷・六本木・銀座・恵比寿）+ 福岡（中洲）のモックデータ内蔵済み。

---

## STEP 3: images.py（新規作成 — 最重要）

`DESIGN.md` のセクション2を参照して実装。

```python
class ImageFetcher:
    def fetch_for_business(self, business, output_dir) -> dict:
        """
        Returns: {
            "hero": "images/hero.jpg" or "images/hero.svg",
            "gallery": ["images/gallery_1.jpg", ...],
            "atmosphere": "images/atmosphere.jpg" or None,
            "source": "google_places" | "unsplash" | "placeholder"
        }
        """
        # 1. Google Places Photo APIを試す
        # 2. 失敗 → Unsplash APIを試す
        # 3. 失敗 → SVGプレースホルダーを生成
```

要件：
- Google Places Photo API: `photo_reference` からURLを構築して画像をダウンロード
- Unsplash API: 業種キーワード（英語）で検索、ダウンロード
- Pillow でリサイズ・JPEG圧縮（hero: 1920px幅, gallery: 800px幅）
- キャッシュ: 既に画像があればスキップ
- SVGプレースホルダー: `skills/hp-generator/SKILL.md` の仕様に従って生成

---

## STEP 4: generator.py（大幅改修）

`reference/generator.py` を Jinja2テンプレートベースに書き換え。

```python
from jinja2 import Environment, FileSystemLoader

class HPGenerator:
    def __init__(self):
        self.env = Environment(loader=FileSystemLoader("templates/hp"))
        self.image_fetcher = ImageFetcher()

    def generate(self, business: dict) -> dict:
        # 1. 業種判定
        category = classify_business(business)
        # 2. テンプレート選択
        template = self.env.get_template(f"{category}.html")
        # fallback: template = self.env.get_template("default.html")
        # 3. 画像取得
        images = self.image_fetcher.fetch_for_business(business, output_dir)
        # 4. カラースキーム取得
        colors = COLOR_SCHEMES.get(category, COLOR_SCHEMES["default"])
        # 5. HTML生成
        html = template.render(biz=business, images=images, colors=colors, ...)
        # 6. ファイル出力
        ...
```

---

## STEP 5: Jinja2テンプレート（templates/hp/）

### base.html — 共通ベース

全業種共通のHTML構造。子テンプレートでブロックをオーバーライド。

```jinja2
<!DOCTYPE html>
<html lang="ja">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{{ biz.name }}</title>
    <meta name="description" content="{{ biz.description }}">
    <meta property="og:title" content="{{ biz.name }}">
    <meta property="og:description" content="{{ biz.description }}">
    {% if images.hero %}<meta property="og:image" content="{{ images.hero }}">{% endif %}
    {% block fonts %}{% endblock %}
    <style>{% block styles %}{% endblock %}</style>
</head>
<body>
    {% block nav %}{% endblock %}
    {% block hero %}{% endblock %}
    {% block about %}{% endblock %}
    {% block gallery %}{% endblock %}
    {% block info %}{% endblock %}
    {% block access %}{% endblock %}
    {% block cta %}{% endblock %}
    {% block footer %}{% endblock %}
    <script>{% block scripts %}{% endblock %}</script>
</body>
</html>
```

### default.html — デフォルトテンプレート

`base.html` を継承。全セクションをフル実装。
他の業種テンプレート（`sushi.html`, `bar.html` 等）はこれを参考にスタイルだけ変更。

最低限作るテンプレート：
1. `default.html` — 汎用（必須）
2. `sushi.html` — 和食・寿司（紺×金、Noto Serif JP）
3. `bar.html` — バー・クラブ（黒×紫、パララックス）
4. `luxury.html` — 高級店（黒×金、Cormorant Garamond、大きな余白）

残りの業種は `default.html` のカラー変数を切り替えるだけで対応可能。

---

## STEP 6: pipeline.py

`reference/pipeline.py` をベースに、画像取得ステップを追加：

```
STEP 1: ビジネス発見
STEP 2: 画像取得        ← 追加
STEP 3: HP生成
STEP 4: レポート出力
```

---

## STEP 7: app.py + dashboard.html

`reference/app.py` と `reference/dashboard.html` をベースに以下を強化：

- HP一覧に画像サムネイルを表示（hero画像の縮小版）
- 画像取得状況の表示（📷 3枚 / ✅ Google Places / ⚠️ プレースホルダー）
- APIキー設定状態の表示

---

## STEP 8: テスト

```bash
# パイプラインテスト（モックモード）
python pipeline.py --areas "新宿,渋谷,六本木,銀座,恵比寿"

# 生成されたHPを確認
python app.py
# → http://127.0.0.1:5000 でダッシュボード
# → 各HPをクリックしてプレビュー

# 品質チェック
python -c "
from generator import HPGenerator
gen = HPGenerator()
issues = gen.validate_all()
for store, problems in issues.items():
    if problems:
        print(f'⚠️ {store}: {problems}')
    else:
        print(f'✅ {store}: OK')
"
```

---

## ビルド順序まとめ

```
1. config.py        — 設定（5分）
2. discovery.py     — そのまま使用（0分）
3. images.py        — 画像取得エンジン（30分）★最重要
4. generator.py     — Jinja2化 + 業種判定（20分）
5. templates/hp/*   — テンプレート4種（40分）★デザイン品質がここで決まる
6. pipeline.py      — 画像ステップ追加（10分）
7. app.py           — サムネイル追加（10分）
8. テスト            — パイプライン実行 + 確認（10分）
```

---

## 品質基準

生成されたHPが以下を全て満たすこと：

- [ ] ヒーロー画像（or SVGプレースホルダー）がフルスクリーン表示
- [ ] ギャラリーに2枚以上の画像
- [ ] 業種に応じたカラースキームが適用されている
- [ ] スマホで崩れない
- [ ] フェードイン + スクロールアニメーションがある
- [ ] Google Maps埋め込みがある
- [ ] OGPメタタグが設定されている
- [ ] 電話番号がタップ発信可能
- [ ] APIキーなし（モックモード）でも美しく表示される

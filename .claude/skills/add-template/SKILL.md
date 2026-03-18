---
name: add-template
description: 新しい業種テンプレートを追加する際に使用。ユーザーが「〇〇用のテンプレートを追加して」と言った時に実行。
---

# テンプレート追加スキル

## 手順

1. **業種名とカラースキームを確認**
   - ユーザーに業種名（例: curry, udon, teppanyaki）を確認
   - カラースキームの方向性を確認（和風、モダン、カジュアルなど）

2. **COLOR_SCHEMES に追加** (`generator.py`)
   ```python
   "新業種": {
       "bg": "#...", "surface": "#...", "accent1": "#...", "accent2": "#...",
       "text": "#...", "muted": "#...",
       "hero_overlay": "linear-gradient(...)",
       "font_display": "'フォント名', serif",
       "font_body": "'Noto Sans JP', sans-serif",
   },
   ```

3. **CLASSIFICATION_RULES に追加** (`generator.py`)
   ```python
   (["キーワード1", "キーワード2"], "新業種"),
   ```

4. **テンプレート作成** (`templates/hp/新業種.html`)
   - `default.html` を継承
   - カスタムスタイルを `{% block styles %}` で追加

5. **TEMPLATE_MAP に追加** (`generator.py`)
   ```python
   "新業種": "新業種.html",
   ```

6. **プレースホルダーテーマ追加** (`images.py`)
   ```python
   "新業種": {"bg": "#...", "accent": "#...", "pattern": "...", "icon": "🍛"},
   ```

7. **テスト実行**
   ```bash
   python pipeline.py --areas "新宿"
   ```

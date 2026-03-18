---
name: add-category
description: 新しい業種カテゴリ（判定ルールのみ）を追加する際に使用。テンプレートは既存のものを使用。
---

# カテゴリ追加スキル

## 手順

1. **業種名とキーワードを確認**
   - ユーザーに業種名を確認
   - 判定に使うキーワードを確認

2. **CLASSIFICATION_RULES に追加** (`generator.py`)
   ```python
   (["キーワード1", "キーワード2", "キーワード3"], "カテゴリ名"),
   ```

3. **COLOR_SCHEMES に追加**（テンプレートは default.html を使用）
   ```python
   "カテゴリ名": {
       "bg": "#...", "surface": "#...", "accent1": "#...", "accent2": "#...",
       "text": "#...", "muted": "#...",
       "hero_overlay": "linear-gradient(...)",
       "font_display": "'Noto Sans JP', sans-serif",
       "font_body": "'Noto Sans JP', sans-serif",
   },
   ```

4. **プレースホルダーテーマ追加** (`images.py`)
   ```python
   "カテゴリ名": {"bg": "#...", "accent": "#...", "pattern": "...", "icon": "🍴"},
   ```

5. **Unsplashキーワード追加** (`images.py`)
   ```python
   "カテゴリ名": "english search keyword",
   ```

6. **テスト実行**
   ```bash
   python pipeline.py --areas "新宿"
   ```

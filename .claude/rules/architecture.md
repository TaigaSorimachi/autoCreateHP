# アーキテクチャルール

## 1. モジュール構成

アポ太郎は以下の5モジュールで構成される:

| モジュール | 責務 |
|-----------|------|
| `config.py` | 環境変数・設定の一元管理 |
| `discovery.py` | Google Places API / モックデータによるビジネス発見 |
| `images.py` | 画像取得（Google Places Photo → Unsplash → SVG）|
| `generator.py` | Jinja2テンプレートによるHP生成 |
| `pipeline.py` | 全自動パイプライン・スケジューラ |
| `app.py` | Flask ダッシュボード・API |

## 2. 依存関係

```
config.py  ←── discovery.py, images.py, generator.py, pipeline.py, app.py
                     ↓
              generator.py ←── images.py
                     ↓
               pipeline.py
                     ↓
                  app.py
```

- 循環依存禁止
- config.pyは他モジュールからのみimportされる（依存しない）

## 3. エラーハンドリング

- API呼び出し失敗時はフォールバックで対応（画像: Google → Unsplash → SVG）
- ログ出力は `print()` で統一（将来的にloggingに移行可能）
- ユーザーフレンドリーなエラーメッセージを心がける

## 4. ファイル命名規則

- モジュール: snake_case.py
- テンプレート: kebab-case.html または snake_case.html
- 生成サイト: `{safe_name}_{hash8}/` 形式

## 5. HP生成原則

1. **画像必須**: 画像がない場合は必ずSVGプレースホルダーを生成
2. **業種別デザイン**: 寿司屋とラーメン屋で同じデザインにしない
3. **モバイルファースト**: 全HPがスマホで美しく表示されること
4. **Single-file HTML**: 外部CSSなし、1つのindex.htmlに全部入り
5. **APIキーなしでも動作**: モックデータ + SVGで完全動作

## 6. テンプレート継承構造

```
base.html（共通構造）
    └── default.html（汎用テンプレート）
            ├── sushi.html（寿司・和食）
            ├── bar.html（バー・クラブ）
            └── luxury.html（高級店）
```

- 新規テンプレートは default.html を継承して作成
- カラースキームは generator.py の COLOR_SCHEMES に追加

# テストルール

## テスト戦略

- **統合テスト優先**: モジュール間の連携を重視
- **モックモード**: APIキーなしで全機能をテスト可能

## テスト対象

### 1. パイプライン統合テスト
```bash
python pipeline.py --areas "新宿,渋谷"
```
- 正常終了すること
- 全HP品質チェック通過

### 2. HP品質チェック
`generator.py` の `HPGenerator.validate()` で以下を検証:
- 画像またはSVGプレースホルダーが存在する
- OGPメタタグが設定されている
- 電話リンク（tel:）が存在する
- レスポンシブ対応（@media）がある
- スクロールアニメーションがある
- Google Maps埋め込みがある

### 3. 業種判定テスト
```python
from generator import classify_business

# 期待される結果
assert classify_business({"name": "六本木 鮨 さいとう"}) == "sushi"
assert classify_business({"name": "Bar HIGH FIVE"}) == "bar"
```

## テスト実行

```bash
# パイプラインテスト
python pipeline.py --areas "中洲"

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

## ファイル配置

```
tests/
├── test_discovery.py      # ビジネス発見テスト
├── test_images.py         # 画像取得テスト
├── test_generator.py      # HP生成テスト
└── test_pipeline.py       # 統合テスト
```

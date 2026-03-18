# Claude Code: アポ太郎開発ルール

## プロジェクト概要

「アポ太郎」は、指定エリアの飲食店を自動発見し、**画像付きリッチなHP**を自動生成するローカル営業自動化システム。

## あなたの役割

あなたはPython + Flaskベースのこのプロジェクトの開発をサポートするエージェントです。

### 行動原則

1. **HP品質最優先**: 生成されるHPは必ず画像付き（取得失敗時はSVGプレースホルダー）
2. **業種別デザイン**: 寿司屋とラーメン屋で同じデザインにしない
3. **モバイルファースト**: 全HPがスマホで美しく表示されること
4. **APIキーなしでも動作**: モックモードで完全動作すること

## 実行プロセス

### 新機能開発時

1. 仕様を明確にする（ユーザーとの対話）
2. 影響範囲を特定する（どのモジュールを変更するか）
3. 実装する
4. `python pipeline.py --areas "新宿"` でテスト実行
5. 品質チェック通過を確認

### テンプレート追加時

1. `generator.py` の `COLOR_SCHEMES` に新カラースキーム追加
2. `generator.py` の `CLASSIFICATION_RULES` に判定ルール追加
3. `templates/hp/` に新テンプレート作成（default.htmlを継承）
4. `generator.py` の `TEMPLATE_MAP` にマッピング追加
5. テスト実行で品質チェック

### API連携追加時

1. `config.py` に環境変数追加
2. `images.py` または専用モジュールに実装
3. フォールバックを必ず用意
4. モックモードでの動作を確保

## ルール参照

- 技術スタック: `@rules/tech-stack.md`
- アーキテクチャ: `@rules/architecture.md`
- テスト: `@rules/testing.md`

## コマンドリファレンス

```bash
# ダッシュボード起動
python app.py

# 全自動パイプライン
python pipeline.py --areas "新宿,渋谷,六本木,銀座,恵比寿"

# スケジューラー（毎朝9時自動実行）
python pipeline.py --areas "新宿,渋谷" --schedule 09:00

# 画像強制再取得
python pipeline.py --areas "中洲" --refresh-images
```

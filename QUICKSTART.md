# 🚀 Claude Code クイックスタートガイド

## やること

```
1. このフォルダをローカルにダウンロード
2. Claude Code でプロジェクトを開く
3. 「ビルドして」と言うだけ
```

---

## 手順

### 1. ダウンロード後のフォルダ配置

```bash
# ダウンロードした apo-taro-handoff/ をプロジェクトフォルダとして使う
cd apo-taro-handoff

# .env を作成（APIキーを設定）
cp .env.example .env
# ↓ エディタで .env を開いてキーを入力
# GOOGLE_PLACES_API_KEY=your_key
# UNSPLASH_ACCESS_KEY=your_key
```

### 2. Claude Code で開く

```bash
claude
# Claude Code が起動したら...
```

### 3. 最初のプロンプト

Claude Code に以下を伝える：

```
CLAUDE.md と DESIGN.md と CLAUDE_CODE_PROMPT.md を読んで、
このプロジェクトをビルドしてください。

reference/ フォルダに動作済みのコードがあるので参考にしてください。
skills/hp-generator/SKILL.md にHP生成のベストプラクティスがあります。

まず全ファイルを読んでから、CLAUDE_CODE_PROMPT.md の
ビルド順序に従って実装してください。
```

### 4. ビルド完了後のテスト

```
東京5エリア（新宿,渋谷,六本木,銀座,恵比寿）で
パイプラインを実行して、生成されたHPをブラウザで確認させてください。
```

---

## フォルダ構成の説明

```
apo-taro-handoff/
│
├── CLAUDE.md               ★ Claude Code が最初に読むファイル
│                              プロジェクト概要・ディレクトリ構成・開発ルール
│
├── DESIGN.md               ★ 詳細設計書
│                              パイプライン設計・画像取得仕様・HP構造・API仕様
│
├── CLAUDE_CODE_PROMPT.md   ★ ビルド指示書（Step by Step）
│                              Claude Code に「これ読んでビルドして」で動く
│
├── .env.example            環境変数テンプレート
│
├── skills/
│   └── hp-generator/
│       └── SKILL.md        ★ HP生成スキル
│                              カラースキーム・テンプレート設計・品質基準
│                              Claude Code の /skills/ に配置可能
│
└── reference/              ★ 動作済みコード（参考実装）
    ├── config.py           設定ファイル
    ├── discovery.py        ビジネス発見（東京モックデータ内蔵）
    ├── generator.py        HP生成（現行版・画像なし）
    ├── pipeline.py         全自動パイプライン + スケジューラ
    ├── app.py              Flask ダッシュボード
    └── dashboard.html      ダッシュボードUI
```

---

## APIキーの取得方法

### Google Places API（メイン）

1. [Google Cloud Console](https://console.cloud.google.com/) にアクセス
2. 新規プロジェクト作成
3. 「APIとサービス」→「ライブラリ」で以下を有効化：
   - **Places API**
   - **Geocoding API**
4. 「認証情報」→「APIキーを作成」
5. `.env` に `GOOGLE_PLACES_API_KEY=取得したキー` を記入

※ 月間$200の無料枠あり。テスト用途なら余裕で足りる。

### Unsplash API（フォールバック画像用）

1. [Unsplash Developers](https://unsplash.com/developers) でアカウント作成
2. 「New Application」でアプリ作成
3. Access Key をコピー
4. `.env` に `UNSPLASH_ACCESS_KEY=取得したキー` を記入

※ 無料で月間50リクエスト。有料プランなら無制限。

### APIキーなしでも動く

設定しなくてもモックデータ + SVGプレースホルダーで完全動作します。
まずはAPIキーなしでビルド→確認し、後からキーを追加するのが安全です。

---

## 追加でClaude Codeに頼めること

ビルド完了後、以下のような追加依頼が可能：

- 「バーのテンプレートにパララックスエフェクトを追加して」
- 「新しいエリア（池袋、秋葉原）のモックデータを追加して」
- 「DM文面自動生成モジュールを追加して」
- 「HP一覧をCSVでエクスポートする機能を追加して」
- 「Telegram Bot連携を実装して」

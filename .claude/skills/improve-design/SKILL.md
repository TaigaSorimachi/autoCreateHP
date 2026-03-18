---
name: improve-design
description: 生成済みHPのデザインを改善する。「ダサい」「もっとかっこよく」「デザイン修正」「リッチに」と言われた時にトリガー。具体的なCSS修正パターンを持つ。
---

# デザイン改善スキル

## このスキルの使い方

ユーザーがデザインに不満を持った時、以下の手順で改善する。
**抽象的な改善ではなく、具体的なCSS値を変更する。**

## Step 1: 現状確認

```bash
# 最新の生成済みHPを開く
ls -t generated_sites/*/index.html | head -1
# そのHTMLの中身を確認
```

## Step 2: 問題特定チェックリスト

以下を順番にチェック。問題があれば対応するCSSパターンを適用。

### A. ヒーローが貧弱に見える

**症状**: 背景がほぼ単色、グラデーションが見えない

**修正**: templates/hp/default.html の `.hero-mesh`

```css
/* BAD: 薄すぎ */
color-mix(in srgb, var(--accent1) 15%, transparent)

/* GOOD: 視認できる強さ */
color-mix(in srgb, var(--accent1) 35%, transparent)
```

radial-gradient を3個以上に増やす。位置をバラす。

### B. ギャラリーが空っぽに見える

**症状**: 「PHOTO COMING SOON」テキストが並ぶだけ

**修正**: `.gallery-placeholder` のテキストを削除。代わりにCSSグラデーション背景を追加。

```css
.gallery-placeholder {
    background:
        radial-gradient(ellipse at 30% 40%, color-mix(in srgb, var(--accent1) 20%, transparent), transparent 70%),
        radial-gradient(ellipse at 70% 60%, color-mix(in srgb, var(--accent2) 15%, transparent), transparent 70%),
        var(--surface);
}
```

### C. カードが見えない

**症状**: info-item がカードとして認識できない

**修正**: 背景を `var(--surface)` に、ボーダーの opacity を上げる

```css
.info-item {
    background: var(--surface);
    border: 1px solid color-mix(in srgb, var(--accent1) 15%, transparent);
}
```

### D. CTAが埋もれる

**症状**: ボタンが小さい、目立たない

**修正**:
```css
.cta-btn {
    padding: 1.15rem 3rem;
    font-size: 1.1rem;
    box-shadow: 0 8px 30px color-mix(in srgb, var(--accent1) 25%, transparent);
}
```

### E. 全体が寂しい

**症状**: セクション間が空白だけ

**修正**: セクション間にディバイダーを追加
```html
<div class="section-divider"></div>
```
```css
.section-divider {
    width: 60px;
    height: 1px;
    background: linear-gradient(90deg, transparent, var(--accent1), transparent);
    margin: 0 auto;
}
```

### F. 「テンプレ感」がある

**症状**: 全業種で同じ見た目

**修正**: 
- hero-label テキストを業種ごとに変える
- font-size を店名の文字数で調整
- ドロップキャップを about セクションに追加

## Step 3: 修正後のテスト

```bash
python pipeline.py --areas "新宿"
# 生成されたHTMLをブラウザで確認
# 最低3業種（sushi, ramen, bar）で見た目が違うことを確認
```

## 絶対NG

- color-mix の % を 10% 以下にしない（見えなくなる）
- rgba(255,255,255,0.04) のような薄すぎる背景を使わない
- 「PHOTO COMING SOON」「準備中」等のテキストをプレースホルダーに表示しない
- 全業種で同じ hero-label テキスト（"WELCOME TO"）を使わない

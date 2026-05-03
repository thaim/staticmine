# staticmine - 設計ドキュメント

## 概要

staticmine は、Redmine 3.4.4.stable の全データ（プロジェクト・チケット・Wiki・添付ファイル）を静的 HTML サイトとしてエクスポートし、Redmine 本体の運用を廃止しても参照可能なアーカイブを構築する CLI ツールである。Fetcher / Converter / Builder の 3 段パイプラインで構成され、中間生成物の JSON ダンプ（`raw/`）を恒久アーカイブとして保管する。

## ドキュメントステータス凡例

| ステータス | 意味 |
|-----------|------|
| Draft | 初稿。内容が未確定な部分を含む |
| Review | レビュー中。レビュアーからのフィードバック待ち |
| Approved | レビュー完了・承認済み。変更時は再レビューが必要 |

## ドキュメント一覧

| ドキュメント | 説明 | ステータス |
|-------------|------|-----------|
| [requirements.md](./requirements.md) | 要求定義 | Review |
| [features.md](./features.md) | 機能設計 | Review |
| [architecture.md](./architecture.md) | アーキテクチャ設計 | Review |
| [repository.md](./repository.md) | リポジトリ構造設計 | Review |
| [guidelines.md](./guidelines.md) | 開発ガイドライン | Review |
| [glossary.md](./glossary.md) | 用語集 | Review |

## ドキュメント関連図

```
requirements.md（要求定義）
    ↓
features.md（機能設計）
    ↓
architecture.md（アーキテクチャ設計）
    ↓
repository.md ← guidelines.md
（リポジトリ構造）  （開発ガイドライン）
    ↓
glossary.md（全ドキュメントから用語抽出）
```

## 読み方ガイド

| 読者 | 推奨順序 | 読む目的 |
|-----|---------|---------|
| 新規参加者 | requirements → features → architecture | プロジェクトの背景・スコープと、Fetcher / Converter / Builder の役割分担を把握する |
| 実装担当者 | architecture → repository → guidelines | 各コンポーネントのインターフェースとデータモデル、ファイル配置先、コーディング規約・テスト方針を把握する |
| レビュアー | guidelines → features → architecture | レビュー基準と CI 必須項目を確認したうえで、変更対象機能の仕様および設計上の影響範囲を確認する |
| 用語確認 | glossary | Redmine 由来の用語、staticmine 固有の用語、関連技術用語を引く |

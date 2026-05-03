# staticmine - アーキテクチャ設計

## 概要

staticmine は Redmine 3.4.4.stable の全データ（プロジェクト・チケット・Wiki・添付ファイル）を静的 HTML サイトに変換するためのパイプライン型ツールである。Fetcher（取得）/ Converter（変換）/ Builder（ビルド）の 3 段階に分かれており、各段はファイルを介して疎結合で連携する。中間生成物である JSON ダンプ（`raw/`）はアーカイブとして永続保管され、Redmine 本体が消失しても再ビルドできる構成とする。

## 技術スタック

| カテゴリ | 技術 | 理由 |
|---------|-----|------|
| Fetcher 言語 | Python 3.13 / 3.14 | python-redmine による Redmine REST API 呼び出しが容易 |
| Fetcher ライブラリ | python-redmine | Redmine 公式 API のラッパーとして枯れており、ページネーション・include パラメータ等を抽象化 |
| Converter 言語 | Python 3.13 / 3.14 | Fetcher と同言語で統一。正規表現による Markdown 後処理に十分 |
| YAML パーサ | PyYAML | 設定ファイル・frontmatter 読み書きの標準的選択 |
| Builder | Hugo（最新 stable） | permalinks による URL 完全制御、taxonomy による多軸一覧の自動生成、単一バイナリで配布が容易 |
| 検索 | Pagefind | ビルド後の HTML をクロールしクライアント側全文検索を提供。SSG とは独立して導入可能 |
| 設定ファイル | YAML | 可読性が高く Python / Hugo の両方で扱える |
| データ中間形式 | JSON / Markdown + YAML frontmatter | JSON は機械可読アーカイブとして恒久保管、Markdown は人間可読・SSG 非依存 |
| 配信 | 任意の静的ファイルサーバ（Nginx, GitHub Pages, S3 等） | `public/` を配信できれば動作環境を選ばない |

## システム構成図

```
+------------------+
|  Redmine REST    |
|  API (3.4.4)     |
+--------+---------+
         |
         | HTTPS + python-redmine
         v
+------------------+        +-------------------+
|    Fetcher       | -----> |   raw/ (JSON +    |
|    (Python)      |        |   添付バイナリ)    |  <-- アーカイブとして永続保管
+------------------+        +---------+---------+
                                      |
                                      | ファイル読み出し（オフライン処理）
                                      v
                            +-------------------+        +--------------------+
                            |   Converter       | -----> |  content/          |
                            |   (Python)        |        |  (Markdown +       |
                            |   - frontmatter生成|        |   YAML frontmatter)|
                            |   - 独自記法変換   |        +---------+----------+
                            +-------------------+                  |
                                                                   v
                                                         +--------------------+
                                                         |   Builder (Hugo)   |
                                                         |   + Pagefind       |
                                                         +---------+----------+
                                                                   |
                                                                   v
                                                         +--------------------+
                                                         |  public/           |
                                                         |  (静的 HTML +      |
                                                         |   検索インデックス)|
                                                         +---------+----------+
                                                                   |
                                                                   v
                                                         +--------------------+
                                                         |  静的ファイル      |
                                                         |  サーバで配信       |
                                                         +--------------------+

設定ファイル (YAML) は Fetcher / Converter / Builder の全段に渡される。
```

## コンポーネント

### Fetcher

- **責務**:
  - 設定ファイルを読み込み Redmine REST API に接続する
  - 設定ファイルの Redmine URL が `https://` で始まることを起動時に検証し、`http://` の場合はエラー終了する
  - プロジェクト一覧を取得し Project Filter（F-2）で対象を絞り込む
  - Issue（journals.notes 含む、ステータス変更履歴は含まない）を取得する
  - Wiki ページの最新版を取得する（バージョン履歴は対象外）
  - 添付ファイルのバイナリをダウンロードする
  - 関連ユーザー情報を取得する
  - 取得結果を `raw/` 配下に JSON ファイルおよび添付バイナリとして保存する
  - HTTP 失敗時のリトライおよびログ出力を行う
- **技術スタック**: Python 3.13 / 3.14, python-redmine, PyYAML, requests（添付ダウンロード用）
- **依存関係**:
  - 上流: Redmine REST API、設定ファイル
  - 下流: `raw/` ディレクトリ（Converter が消費）

### Converter

- **エラーハンドリング方針**:
  - 1 件の JSON 解析失敗時は当該ファイルをスキップして処理を継続する
  - スキップした件数とファイルパスを実行ログ（WARNING レベル）に記録する
  - 全件スキップになった場合も処理自体は成功扱いとし、呼び出し元でログを確認する
- **責務**:
  - `raw/` 配下の JSON ファイルを読み込む
  - Issue / Wiki を Markdown 本文 + YAML frontmatter に整形する
  - Issue は description を本文先頭に置き、`journals[].notes` を時系列でコメントとして連結する
  - Permission Metadata（F-3）を frontmatter に出力する
  - Redmine 独自記法（`#123`, `[[PageName]]`, `[[Proj:Page]]`, `attachment:<file>`）を静的サイト URL に書き換える
  - リポジトリ参照（`commit:`, `source:`, `r<n>`）はそのまま残す
  - 添付ファイルを `content/attachments/` 配下にコピーして配置する
- **技術スタック**: Python 3.13 / 3.14, PyYAML, 標準ライブラリ（re, pathlib, hashlib）
- **依存関係**:
  - 上流: `raw/`、設定ファイル
  - 下流: `content/` ディレクトリ（Builder が消費）
  - Redmine への通信は行わない（完全オフライン）

### Builder

- **エラーハンドリング方針**:
  - Hugo ビルド失敗時は処理を中断し、Hugo の標準エラー出力をそのまま表示する（部分ビルドは行わない）
  - Pagefind 失敗時は警告ログを出力して処理を継続し、ビルド全体は成功扱いとする
- **責務**:
  - Hugo サイトスケルトン（`hugo.toml`, テンプレート, テーマ設定）を保持する
  - `content/` を Hugo の content ディレクトリとして読み込む
  - permalinks 設定で Redmine 互換 URL に出力する
  - taxonomy（project / status / tracker / assignee）で多軸一覧ページを自動生成する
  - `hugo` を実行し `public/` に静的 HTML を出力する
  - 添付ファイルを `public/attachments/<id>/<filename>` に配置する
  - Pagefind を実行し `public/pagefind/` に検索インデックスを生成する（F-7、`--no-search` で無効化可能）
- **技術スタック**: Hugo（最新 stable）, Pagefind, シェルスクリプトまたは Python ラッパー
- **依存関係**:
  - 上流: `content/`, `hugo.toml`, テーマ
  - 下流: `public/`（HTTP サーバが配信）

### Project Filter（横断機能）

- **責務**:
  - 設定ファイルの `filter.include` / `filter.exclude`（glob 配列）を評価する
  - プロジェクト identifier の集合を絞り込み、Fetcher / Converter / Builder の処理対象を決定する
- **技術スタック**: Python 標準ライブラリ（fnmatch）
- **依存関係**: 設定ファイル、各段から呼び出されるユーティリティ

## データフロー

```
1. ユーザーが `staticmine fetch --config config.yaml` を実行
2. Fetcher が設定ファイルを読み、Project Filter を適用してプロジェクト集合を決定
3. Fetcher が Redmine REST API から Project / Issue / Wiki / Attachment / User を取得し `raw/` に保存
4. ユーザーが `staticmine convert --config config.yaml` を実行
5. Converter が `raw/` の JSON を読み、frontmatter + Markdown 本文を組み立て、独自記法を書き換え `content/` に出力
6. ユーザーが `staticmine build --config config.yaml` を実行
7. Builder（Hugo）が `content/` から `public/` に静的 HTML を生成
8. Pagefind が `public/` をクロールし `public/pagefind/` に検索インデックスを生成
9. `public/` を任意の HTTP サーバで配信
```

各段はそれぞれ単独で再実行可能であり、`raw/` を保管している限り Redmine が停止していても 4 以降を任意回数実行できる。

## インターフェース

### CLI: staticmine

- **プロトコル**: コマンドラインインターフェース
- **エンドポイント**:
  - `staticmine fetch --config <path> [--out raw/]`
  - `staticmine convert [--config <path>] [--in raw/] [--out content/]`（`--in` と `--out` の両方を指定した場合は `--config` 省略可）
  - `staticmine build [--config <path>] [--in content/] [--out public/] [--no-search]`（`--in` と `--out` の両方を指定した場合は `--config` 省略可。`--no-search` 指定時は Pagefind を実行しない）
  - `staticmine all --config <path> [--no-search]`（fetch → convert → build を順次実行。`--no-search` は build に引き渡す）
- **認証**: 設定ファイル中の Redmine API キー（Fetcher のみが使用）

### Redmine REST API

- **プロトコル**: HTTPS のみ
- **エンドポイント**:
  - `GET /projects.json`
  - `GET /projects/<id>/issues.json?include=journals,attachments&status_id=*`
  - `GET /projects/<id>/wiki/index.json`
  - `GET /projects/<id>/wiki/<title>.json?include=attachments`
  - `GET /attachments/download/<id>/<filename>`
  - `GET /users/<id>.json`
- **認証**: API キー（HTTP ヘッダ `X-Redmine-API-Key` または `key` クエリパラメータ）

### 静的サイト URL（出力）

- **プロトコル**: HTTP / HTTPS（配信側で選択）
- **エンドポイント**:
  - `/issues/<id>/`
  - `/projects/<identifier>/wiki/<PageName>/`
  - `/projects/<identifier>/issues/`
  - `/status/<status>/`, `/tracker/<tracker>/`, `/assignee/<name>/`
  - `/attachments/<id>/<filename>`
- **認証**: なし（必要な場合は配信サーバ側で実施）

## データモデル

### 設定ファイル（YAML）

| フィールド | 型 | 説明 |
|-----------|---|------|
| `redmine.url` | string | Redmine の URL（`https://...`） |
| `redmine.api_key` | string | Redmine API キー |
| `filter.include` | string[] | 対象プロジェクトの glob パターン配列 |
| `filter.exclude` | string[] | 除外プロジェクトの glob パターン配列 |
| `output.raw` | string | JSON ダンプの出力先（既定 `raw/`） |
| `output.content` | string | Markdown 出力先（既定 `content/`） |
| `output.public` | string | 静的サイト出力先（既定 `public/`） |
| `hugo.config` | string | Hugo 設定ファイルへのパス |
| `search.enabled` | bool | Pagefind 実行有無（既定 true） |

### `raw/projects.json`

| フィールド | 型 | 説明 |
|-----------|---|------|
| `id` | int | Redmine プロジェクト ID |
| `identifier` | string | URL 用識別子 |
| `name` | string | 表示名 |
| `description` | string | 説明（Markdown） |
| `is_public` | bool | プロジェクトの公開可否 |
| `created_on` | ISO 8601 | 作成日時 |
| `updated_on` | ISO 8601 | 最終更新日時 |
| `parent_id` | int? | 親プロジェクト ID |

### `raw/issues/<id>.json`

| フィールド | 型 | 説明 |
|-----------|---|------|
| `id` | int | Issue ID |
| `project.id` | int | 親プロジェクト ID |
| `project.identifier` | string | 親プロジェクト identifier |
| `subject` | string | 件名 |
| `description` | string | 本文（Markdown） |
| `status.name` | string | ステータス名 |
| `tracker.name` | string | トラッカー名 |
| `priority.name` | string | 優先度名 |
| `author.id` / `author.name` | int / string | 起票者 |
| `assigned_to.id` / `assigned_to.name` | int? / string? | 担当者 |
| `created_on` / `updated_on` | ISO 8601 | 作成・更新日時 |
| `is_private` | bool | プライベートチケットフラグ |
| `journals[].id` | int | コメント ID |
| `journals[].user.name` | string | コメント投稿者 |
| `journals[].created_on` | ISO 8601 | コメント日時 |
| `journals[].notes` | string | コメント本文（Markdown） |
| `attachments[].id` | int | 添付 ID |
| `attachments[].filename` | string | 添付ファイル名 |
| `attachments[].content_type` | string | MIME タイプ |

注: `journals[].details`（属性変更差分）は取得対象外とし、保存しない。

### `raw/projects/<identifier>/wiki/<PageName>.json`

| フィールド | 型 | 説明 |
|-----------|---|------|
| `title` | string | ページタイトル |
| `text` | string | 本文（Markdown） |
| `version` | int | 取得時点のバージョン番号（参考保持、履歴は取得しない） |
| `author.name` | string | 最終編集者 |
| `created_on` / `updated_on` | ISO 8601 | 作成・更新日時 |
| `attachments[].id` | int | 添付 ID |
| `attachments[].filename` | string | 添付ファイル名 |

### `raw/users.json`

| フィールド | 型 | 説明 |
|-----------|---|------|
| `id` | int | ユーザー ID |
| `login` | string | ログイン名 |
| `firstname` | string | 名 |
| `lastname` | string | 姓 |
| `display_name` | string | 表示名。Redmine API レスポンスの `name` フィールド（Redmine が組み立てた表示名）をそのまま使用する |

### Markdown frontmatter（Issue）

| フィールド | 型 | 説明 |
|-----------|---|------|
| `id` | int | Issue ID |
| `subject` | string | 件名 |
| `author` | string | 起票者表示名 |
| `assignee` | string? | 担当者表示名 |
| `created_on` | ISO 8601 | 作成日時 |
| `updated_on` | ISO 8601 | 更新日時 |
| `status` | string | ステータス名 |
| `tracker` | string | トラッカー名 |
| `priority` | string | 優先度名 |
| `project_identifier` | string | 親プロジェクト identifier |
| `project_is_public` | bool | プロジェクト公開可否（記録のみ） |
| `issue_is_private` | bool | プライベートチケットフラグ（記録のみ） |

本文構造:

```
（description 本文）

## コメント

### <投稿者> - <created_on>

（notes 本文）

### <投稿者> - <created_on>

...
```

### Markdown frontmatter（Wiki）

| フィールド | 型 | 説明 |
|-----------|---|------|
| `title` | string | ページタイトル |
| `author` | string | 最終編集者 |
| `created_on` | ISO 8601 | 作成日時 |
| `updated_on` | ISO 8601 | 更新日時 |
| `project_identifier` | string | 親プロジェクト identifier |
| `project_is_public` | bool | プロジェクト公開可否（記録のみ） |

## セキュリティ設計

- Fetcher は Redmine URL のスキーマが `https://` であることを起動時に検証し、`http://` の場合はエラー終了する（API キー保護のため）
- Redmine API キーは設定ファイルに保存されるため、設定ファイルはバージョン管理対象外（`.gitignore`）とし、ファイル権限を `600` 相当に制限する
- 静的サイト側ではアクセス制御を実装しない。プライベートプロジェクト・プライベートチケットを含む構成を生成した場合、配信サーバ（Nginx Basic 認証、社内 VPN 配下、IAM 制御の S3 等）で配信範囲を制御する責任は運用者にある
- frontmatter に保持される `project_is_public` / `issue_is_private` は、配信構成判断のための記録情報であり、静的サイト自体の振る舞いには影響しない
- 添付ファイルは Redmine と同様にファイル名がそのまま URL になる。機密情報を含むファイル名がある場合は、配信前に運用者がレビューする
- HTTPS 配信を推奨するが、staticmine の機能としては配信プロトコルに関与しない

## 設計判断

### 中間形式に Markdown + SSG の 2 段構成を採用

- **選択肢**:
  1. Markdown + 静的サイトジェネレータ（Hugo）の 2 段構成
  2. HTML を直接生成する自作レンダラ
  3. wget による Redmine ミラーリング
- **決定**: 1（Markdown + Hugo の 2 段構成）
- **理由**:
  - JSON ダンプを残すことでテーマ変更・URL 体系変更が低コストで可能になる
  - Markdown は将来 Redmine と無関係な他ツール（Obsidian, MkDocs, Docusaurus 等）でも読めるため長期保管に向く
  - HTML 直接生成案は taxonomy / テンプレート機構を全て自作する必要があり保守コストが高い
  - wget ミラー案は JavaScript 依存の動的 UI が壊れる、検索が機能しない、URL 構造を変更できない、という 3 点で不適

### JSON ダンプを永続アーカイブとして必ず保管

- **選択肢**:
  1. JSON ダンプを永続保管し、Markdown と HTML は再生成可能とする
  2. Markdown のみ保管し、JSON は使い捨て
  3. HTML のみ保管
- **決定**: 1（JSON ダンプを永続保管）
- **理由**:
  - Redmine 本体が消失すると元データを再取得できなくなるため、最も生に近い形式で保管する必要がある
  - JSON は機械可読でスキーマが明確なため、将来別のツールに移行する場合もデータを失わない
  - Markdown のみ保管した場合、frontmatter スキーマや独自記法変換ルールを後で変更したくなった際に元情報が失われている
  - HTML のみ保管した場合、テーマ変更・検索改善・URL 変更のたびに情報損失なく再生成することができない

### 添付ファイルの配置方法

- **選択肢**:
  1. コピー
  2. シンボリックリンク
  3. ハードリンク
- **決定**: 1（コピー）
- **理由**:
  - 添付ファイル総量が小規模（3MB 程度）でディスクコストが無視できる
  - コピーであれば `content/` ディレクトリだけを別マシンに配布する場合も完結する
  - シンボリックリンクは `raw/` への依存が残り、`content/` のみを転送した際に参照切れが発生する事故要因となる

### Builder に Hugo を採用

- **選択肢**:
  1. Hugo
  2. Astro
  3. Eleventy
- **決定**: 1（Hugo）
- **理由**:
  - permalinks 設定で Redmine 互換 URL（`/issues/<id>/`, `/projects/<id>/wiki/<page>/`）を完全制御できる
  - taxonomy 機能で project / status / tracker / assignee 別の一覧ページを設定のみで自動生成できる
  - 単一バイナリで配布されるため依存解決の運用コストが低い
  - Astro / Eleventy は taxonomy 相当の機能を JavaScript / プラグインで実装する必要があり、Hugo に比べて手数が増える
  - Pagefind は SSG に依存しないクライアントサイド検索のため、Hugo を採用しても検索体験は他 SSG と同等

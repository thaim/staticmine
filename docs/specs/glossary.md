# staticmine - 用語集

本プロジェクトに登場する用語を、Redmine 由来の用語、staticmine 固有の用語、関連技術・ツールの 3 セクションに分けて整理する。

## Redmine 由来の用語

| 用語 | 定義 | 関連ドキュメント |
|-----|------|-----------------|
| Attachment | Redmine の Issue または Wiki ページに紐づく添付ファイル。staticmine では `raw/attachments/<id>/<filename>` にバイナリを保存し、`/attachments/<id>/<filename>` で配信する | requirements.md (FR-1), features.md (F-1, F-6), architecture.md |
| Issue | Redmine のチケット。件名・本文（description）・属性（status / tracker / priority / assignee 等）・コメント（journals.notes）を含む。staticmine では `/issues/<id>/` で参照可能な静的ページに変換される | requirements.md (FR-1, FR-4), features.md (F-1, F-4, F-6), architecture.md |
| Journal | Redmine の Issue に紐づく履歴エントリ。コメント本文（`notes`）と属性変更差分（`details`）を持つ。staticmine は `notes` のみを取得し、`details` は取得対象外とする | requirements.md (FR-1), features.md (F-1, F-4, F-6), architecture.md |
| Project | Redmine におけるチケット・Wiki・添付の管理単位。`identifier`（URL 用識別子）・`is_public`（公開フラグ）等を持つ。staticmine では Project Filter でビルド対象を絞り込む | requirements.md (FR-1, FR-2), features.md (F-1, F-2), architecture.md |
| project_identifier | Redmine プロジェクトの URL 用識別子。staticmine の出力 Markdown frontmatter および URL パス（`/projects/<identifier>/...`）で一貫して使用する | requirements.md (FR-3), features.md (F-3), architecture.md |
| Redmine | 本プロジェクトが対象とするオープンソースのプロジェクト管理ツール。staticmine は バージョン 3.4.4.stable に特化する | requirements.md, architecture.md |
| Redmine 独自記法 | Redmine の本文中で使われる相互参照記法。staticmine では `#<id>`（Issue 参照）、`[[PageName]]` / `[[Proj:Page]]`（Wiki リンク）、`attachment:<filename>`（添付参照）を変換対象とし、`commit:` / `source:` / `r<n>` 等のリポジトリ参照は変換せず原文のまま残す | requirements.md (FR-5), features.md (F-4, F-5), architecture.md |
| Textile | Redmine が標準採用する旧テキストフォーマット。staticmine の対象 Redmine では Markdown を使用しているため、Textile は変換対象外 | requirements.md（制約条件） |
| Wiki | Redmine のプロジェクト単位ドキュメント機能。staticmine では最新版のみを取得し、`/projects/<identifier>/wiki/<PageName>/` の静的ページに変換する。バージョン履歴は対象外 | requirements.md (FR-1, FR-4), features.md (F-1, F-4, F-6), architecture.md |
| is_private | Redmine Issue のプライベートフラグ。staticmine では Issue Markdown frontmatter の `issue_is_private` として記録のみ行い、静的サイト側での分岐には用いない | requirements.md (FR-3), features.md (F-3), architecture.md |
| is_public | Redmine プロジェクトの公開フラグ。staticmine では Markdown frontmatter の `project_is_public` として記録のみ行い、静的サイト側での分岐には用いない | requirements.md (FR-3), features.md (F-3), architecture.md |

## staticmine 固有の用語

| 用語 | 定義 | 関連ドキュメント |
|-----|------|-----------------|
| Builder | パイプラインの第 3 段。`content/` の Markdown を入力に Hugo を実行し、`public/` に静的 HTML を出力する。Pagefind による検索インデックス生成も担当する | requirements.md (FR-6, FR-7, FR-8), features.md (F-6, F-7, F-8), architecture.md |
| content/ | Converter の出力ディレクトリ。Markdown + YAML frontmatter のツリー。Builder の入力となる。Git 管理対象外 | architecture.md, repository.md |
| Converter | パイプラインの第 2 段。`raw/` の JSON を入力に、Markdown 本文と YAML frontmatter を出力する。Redmine 独自記法の書き換えも担う。Redmine への通信は行わずオフラインで完結する | requirements.md (FR-4, FR-5, FR-8), features.md (F-4, F-5, F-8), architecture.md |
| Fetcher | パイプラインの第 1 段。Redmine REST API を経由して Project / Issue / Wiki / Attachment / User を取得し、`raw/` に JSON および添付バイナリとして保存する | requirements.md (FR-1, FR-8), features.md (F-1, F-8), architecture.md |
| frontmatter | Markdown ファイル先頭に置く YAML 形式のメタデータブロック。staticmine は `id` / `subject` / `status` / `project_identifier` / `project_is_public` / `issue_is_private` 等を出力する | requirements.md (FR-3, FR-4), features.md (F-3, F-4), architecture.md |
| JSON dump | Fetcher が `raw/` 配下に書き出す Redmine データの恒久アーカイブ。Redmine 本体が消失しても、これだけから Converter / Builder を再実行できる | requirements.md (NFR-1, NFR-5), architecture.md（設計判断） |
| Project Filter | 設定ファイルの `filter.include` / `filter.exclude`（glob 配列）を評価し、Fetcher / Converter / Builder の処理対象プロジェクトを決定する横断機能 | requirements.md (FR-2), features.md (F-2), architecture.md |
| public/ | Builder の出力ディレクトリ。配信対象の静的 HTML と `public/pagefind/` の検索インデックスを含む。Git 管理対象外 | architecture.md, repository.md |
| raw/ | Fetcher の出力ディレクトリ。`raw/projects.json`、`raw/issues/<id>.json`、`raw/projects/<identifier>/wiki/<PageName>.json`、`raw/attachments/<id>/<filename>`、`raw/users.json` を含むアーカイブ。Git 管理対象外で、運用環境側で永続保管する | requirements.md (NFR-1, NFR-5), architecture.md, repository.md |
| staticmine | 本プロジェクト名。Redmine 3.4.4.stable の全データを静的 HTML サイトとしてエクスポートし、Redmine 本体運用を廃止しても参照可能なアーカイブを構築する CLI ツール | requirements.md, architecture.md |
| 冪等性 (idempotency) | 同一の入力 `raw/` から複数回 Converter / Builder を実行した場合、出力ファイルのバイト列が一致する性質。staticmine では NFR-2 として SHA-256 ハッシュ一致で測定する | requirements.md (NFR-2), features.md (F-4) |

## 関連技術・ツール

| 用語 | 定義 | 関連ドキュメント |
|-----|------|-----------------|
| click | staticmine の CLI フレームワーク。argparse の代替として採用。コマンド・サブコマンド・オプション定義をデコレータで宣言できる | features.md (F-8), architecture.md |
| exclude | Project Filter における除外パターン指定。`filter.exclude` に glob 配列で記述し、include 結果からマッチしたプロジェクトを除く | requirements.md (FR-2), features.md (F-2), architecture.md |
| glob パターン | ワイルドカード（`*` / `?` 等）でファイル名・識別子を一括指定する記法。staticmine では Project Filter の `include` / `exclude` で使用し、Python 標準ライブラリの `fnmatch` で評価する | requirements.md (FR-2), features.md (F-2), architecture.md |
| Hugo | staticmine が Builder として採用する Go 製の静的サイトジェネレータ。permalinks による URL 制御と taxonomy による多軸一覧の自動生成が選定理由。最新 stable の extended 版を使用する | requirements.md（制約条件）, architecture.md, repository.md |
| permalinks | Hugo の `hugo.toml` で宣言する URL ルーティング設定キー。staticmine では `/issues/:id/` および `/projects/:project/wiki/:title/` を定義して Redmine 互換 URL を実現する | features.md (F-6), architecture.md |
| include | Project Filter における対象パターン指定。`filter.include` に glob 配列で記述し、マッチしたプロジェクトのみを処理対象とする。省略時は全プロジェクトが候補 | requirements.md (FR-2), features.md (F-2), architecture.md |
| Markdown | staticmine の中間データ形式。Converter が `content/` 配下に Markdown + YAML frontmatter として出力し、Builder（Hugo）が HTML へレンダリングする | requirements.md (FR-4), features.md (F-4), architecture.md |
| Pagefind | staticmine が採用するクライアントサイド全文検索エンジン。`public/` の HTML をクロールして `public/pagefind/` にインデックスを生成し、ブラウザ側 JavaScript で検索を実行する。Go バイナリ版を使用し Node / npm 依存を持たない | requirements.md (FR-7), features.md (F-7), architecture.md, repository.md |
| python-redmine | Fetcher が Redmine REST API 呼び出しに使用する Python ライブラリ。ページネーションや `include` パラメータを抽象化する | requirements.md（制約条件）, architecture.md, repository.md |
| SSG (Static Site Generator) | 静的サイトジェネレータ。Markdown 等の入力から静的 HTML を生成するツールの総称。staticmine では Hugo を採用する | architecture.md（設計判断） |
| taxonomy | Hugo の分類軸機能。staticmine では project / status / tracker / assignee の 4 軸を宣言し、`/status/<status>/` 等の一覧ページを自動生成する | features.md (F-6), architecture.md |
| uv | staticmine の Python 依存管理に推奨するパッケージマネージャ。`uv.lock` をコミットして再現性を確保する | repository.md, guidelines.md |
| YAML | staticmine の設定ファイル形式および Markdown frontmatter の表現形式 | requirements.md（制約条件）, architecture.md |

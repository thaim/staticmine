# staticmine - 機能設計

## 機能一覧

| ID | 機能名 | 対応 FR | 優先度 | ステータス |
|----|-------|---------|--------|-----------|
| F-1 | Fetcher（Redmine データ取得） | FR-1 | Must | In Progress |
| F-2 | Project Filter（プロジェクトフィルタ） | FR-2 | Must | Draft |
| F-3 | Permission Metadata（権限メタデータ保持） | FR-3 | Must | Draft |
| F-4 | Converter（JSON → Markdown 変換） | FR-4 | Must | In Progress |
| F-5 | Redmine 独自記法の変換（Converter サブ機能） | FR-5 | Must | Draft |
| F-6 | Builder（Hugo 静的サイトビルド） | FR-6 | Must | In Progress |
| F-7 | Search（Pagefind 検索インデックス） | FR-7 | Should | Draft |
| F-8 | Pipeline Orchestration（パイプライン段階の独立実行） | FR-8 | Must | In Progress |

### 機能ステータス凡例

| ステータス | 意味 |
|-----------|------|
| Draft | 設計中 |
| In Progress | 実装中 |
| Done | 完了 |

## 機能詳細

### F-1: Fetcher（Redmine データ取得）

#### ユーザーストーリー

As a Redmine 運用担当者, I want Redmine の全プロジェクト・チケット・Wiki・添付ファイルを一括ダンプしたい, so that Redmine 本体の運用を停止してもデータを永続的に保管できる。

#### フロー

```
1. YAML 設定ファイル（接続情報・フィルタ）を読み込む
2. python-redmine 経由で Redmine REST API に接続
3. プロジェクト一覧を取得し、F-2 のフィルタで対象を絞り込む
4. 対象プロジェクトごとに Issue（journals.notes 含む）/ Wiki ページ（最新版のみ）/ Attachment メタデータを取得
5. 添付ファイルのバイナリをダウンロード
6. Issue / Wiki に登場するユーザー情報を収集
7. 全データを raw/ 配下に JSON および添付バイナリとして保存
```

#### 入出力

| 項目 | 型 | 説明 |
|-----|---|------|
| 入力: 設定ファイル | YAML | Redmine URL・API キー・プロジェクトフィルタ・出力先パス |
| 入力: Redmine REST API | HTTP(S) | Project / Issue / Wiki / Attachment / User エンドポイント |
| 出力: `raw/projects.json` | JSON 配列 | 取得対象プロジェクトのメタデータ一覧 |
| 出力: `raw/issues/<id>.json` | JSON | Issue 本体 + journals.notes |
| 出力: `raw/projects/<identifier>/wiki/<PageName>.json` | JSON | Wiki ページ最新版 |
| 出力: `raw/attachments/<id>/<filename>` | バイナリ | 添付ファイル実体 |
| 出力: `raw/users.json` | JSON 配列 | 関連ユーザー一覧 |
| 出力: 実行ログ | テキスト | 取得件数・失敗・リトライ |

#### 受け入れ条件

- [ ] `staticmine fetch --config config.yaml` で `raw/` 配下が生成される
- [ ] 設定ファイルの Redmine URL が `https://` で始まらない場合はエラー終了する
- [ ] `raw/issues/<id>.json` に `journals[].notes` が含まれ、ステータス変更等の差分情報は含まれない
- [ ] `raw/projects/<identifier>/wiki/<PageName>.json` には最新版のみが含まれ、過去バージョンは含まれない
- [ ] 添付ファイルが `raw/attachments/<id>/<filename>` に保存される
- [ ] HTTP 5xx / タイムアウト時に最低 3 回までリトライする
- [ ] 失敗した取得対象は実行ログに記録され、他の取得を中断しない

#### 画面/API 仕様

利用する Redmine REST API エンドポイント:

- `GET /projects.json`
- `GET /projects/<id>/issues.json?include=journals,attachments&status_id=*`
- `GET /projects/<id>/wiki/index.json`
- `GET /projects/<id>/wiki/<title>.json?include=attachments`
- `GET /attachments/download/<id>/<filename>`
- `GET /users/<id>.json`

CLI:

```
staticmine fetch --config <path/to/config.yaml> [--out raw/]
```

---

### F-2: Project Filter（プロジェクトフィルタ）

#### ユーザーストーリー

As a 運用担当者, I want 公開用と社内用で別々のプロジェクトセットを切り出したい, so that 同一 Redmine から複数の静的サイトを別ホストに配信できる。

#### フロー

```
1. 設定ファイルから filter.include / filter.exclude（glob 配列）を読み込む
2. 取得した全プロジェクト一覧の identifier に対し、include に一致するものを抽出
3. include 結果から exclude に一致するものを除外
4. 残ったプロジェクト集合を Fetcher / Converter / Builder の処理対象とする
```

#### 入出力

| 項目 | 型 | 説明 |
|-----|---|------|
| 入力: `filter.include` | glob 文字列の配列 | 対象とするプロジェクト identifier のパターン（省略時は全件） |
| 入力: `filter.exclude` | glob 文字列の配列 | 除外するプロジェクト identifier のパターン（省略時はなし） |
| 出力: 対象プロジェクト集合 | 内部データ構造 | F-1 / F-4 / F-5 が参照 |

#### 受け入れ条件

- [ ] `include: ["public-*"]` 指定時、`public-` で始まる identifier のみが対象となる
- [ ] `exclude: ["*-secret"]` 指定時、`-secret` で終わる identifier が対象から除外される
- [ ] `include` を省略すると全プロジェクトが候補となる
- [ ] `exclude` を省略すると除外なしとなる
- [ ] 対象外プロジェクトの Issue / Wiki / Attachment は raw / content / public のいずれにも出力されない
- [ ] 設定ファイルを差し替えて再実行すると、別の対象集合でビルドできる

#### 画面/API 仕様

設定ファイル例:

```yaml
redmine:
  url: https://redmine.example.com
  api_key: xxxxxxxx
filter:
  include:
    - "public-*"
    - "shared-docs"
  exclude:
    - "*-archive"
output:
  raw: raw/
  content: content/
  public: public/
```

---

### F-3: Permission Metadata（権限メタデータ保持）

#### ユーザーストーリー

As a 運用担当者, I want 元 Redmine の可視性情報（プライベートプロジェクト・プライベートチケット）を出力 Markdown に記録しておきたい, so that 後から配信範囲を見直す際に元の権限を参照できる。

#### フロー

```
1. Converter が Issue / Wiki の JSON を読み込む
2. 親プロジェクトの is_public, identifier を取得
3. Issue の場合は is_private を取得
4. Markdown frontmatter に project_identifier / project_is_public / issue_is_private を書き出す
```

#### 入出力

| 項目 | 型 | 説明 |
|-----|---|------|
| 入力: `raw/projects.json` | JSON | プロジェクトの `identifier`, `is_public` |
| 入力: `raw/issues/<id>.json` | JSON | Issue の `is_private` |
| 出力: Markdown frontmatter | YAML | `project_identifier`, `project_is_public`, `issue_is_private` |

#### 受け入れ条件

- [ ] Issue Markdown の frontmatter に `project_identifier`, `project_is_public`, `issue_is_private` の 3 フィールドが必ず存在する
- [ ] Wiki Markdown の frontmatter に `project_identifier`, `project_is_public` の 2 フィールドが必ず存在する
- [ ] 値は Redmine REST API のレスポンス値と一致する
- [ ] 静的サイト側のテンプレートやアクセス制御による分岐は行わない（記録専用）

#### 画面/API 仕様

frontmatter 例（Issue）:

```yaml
---
id: 123
subject: "サンプルチケット"
project_identifier: "internal-tools"
project_is_public: false
issue_is_private: true
status: "Closed"
tracker: "Bug"
---
```

---

### F-4: Converter（JSON → Markdown 変換）

#### ユーザーストーリー

As a 開発者, I want JSON ダンプを Markdown + frontmatter に変換したい, so that Hugo を含む任意の静的サイトジェネレータや将来のツールで再利用できる。

#### フロー

```
1. raw/ 配下の projects.json / issues/*.json / projects/*/wiki/*.json を読み込む
2. 各レコードを Markdown 本文と YAML frontmatter に整形
3. Issue は description を本文先頭に置き、journals[].notes を時系列でコメントとして連結
4. Wiki は text を本文として出力
5. 本文中の Redmine 独自記法を F-5（Redmine 独自記法の変換）のルールに従って書き換え
6. content/issues/<id>.md, content/wiki/<project>/<page>.md として書き出し
```

#### 入出力

| 項目 | 型 | 説明 |
|-----|---|------|
| 入力: `raw/issues/<id>.json` | JSON | Issue 本体 + journals.notes |
| 入力: `raw/projects/<identifier>/wiki/<PageName>.json` | JSON | Wiki 最新版 |
| 入力: `raw/users.json` | JSON | ユーザー ID → 表示名 |
| 出力: `content/issues/<id>.md` | Markdown | frontmatter + 本文 + コメント |
| 出力: `content/wiki/<identifier>/<PageName>.md` | Markdown | frontmatter + 本文 |
| 出力: `content/attachments/<id>/<filename>` | バイナリ（コピー） | F-6 が参照 |

#### 受け入れ条件

- [ ] Issue Markdown に `id`, `subject`, `author`, `created_on`, `updated_on`, `status`, `tracker`, `priority`, `assignee`, `project_identifier`, `project_is_public`, `issue_is_private` を含む frontmatter が出力される
- [ ] Wiki Markdown に `title`, `author`, `created_on`, `updated_on`, `project_identifier`, `project_is_public` を含む frontmatter が出力される
- [ ] Issue 本文の後に `## コメント` セクションが続き、`journals[].notes` が `created_on` 昇順で並ぶ
- [ ] 同一 `raw/` を入力に 2 回実行した結果、`content/` 配下の全 Markdown の SHA-256 が一致する
- [ ] Converter は Redmine への通信を行わない（オフラインで完結する）

#### 画面/API 仕様

CLI:

```
staticmine convert [--config <path/to/config.yaml>] [--in raw/] [--out content/]
```

`--in` と `--out` の両方を指定した場合、`--config` は省略可能。Redmine 通信を行わないため接続情報を必要としない（NFR-1 と整合）。

---

### F-5: Redmine 独自記法の変換（Converter サブ機能）

#### ユーザーストーリー

As a 閲覧者, I want 静的サイト上でも `#123` や `[[PageName]]` のリンクを辿りたい, so that Redmine 利用時と同じ感覚で関連情報を参照できる。

#### フロー

```
1. Converter が Markdown 本文を 1 件取得
2. 正規表現で Redmine 独自記法を順次マッチさせ書き換える
   - #<id>            → [#<id>](/issues/<id>/)
   - [[Page]]         → [Page](/projects/<current_identifier>/wiki/Page/)
   - [[Proj:Page]]    → [Page](/projects/Proj/wiki/Page/)
   - attachment:<f>   → ![<f>](/attachments/<id>/<f>)（画像拡張子の場合）
                       → [<f>](/attachments/<id>/<f>)（その他）
3. 既知のリポジトリ参照（commit:, source:, r<n>）はそのまま残す
4. 書き換え後の本文を Markdown ファイルに書き出す
```

#### 入出力

| 項目 | 型 | 説明 |
|-----|---|------|
| 入力: 生 Markdown 本文 | 文字列 | Redmine から取得した description / notes / wiki text |
| 入力: 添付ファイル一覧 | dict | filename → attachment id（同 Issue / Wiki スコープ） |
| 入力: 現在のプロジェクト identifier | 文字列 | `[[Page]]` を補完するため |
| 出力: 書き換え済み Markdown 本文 | 文字列 | 静的サイト上のリンクに変換済み |

#### 受け入れ条件

- [ ] `#123` が `[#123](/issues/123/)` に変換される
- [ ] `[[PageName]]` が同一プロジェクトの `/projects/<identifier>/wiki/PageName/` リンクに変換される
- [ ] `[[OtherProject:PageName]]` が `/projects/OtherProject/wiki/PageName/` リンクに変換される
- [ ] `attachment:image.png` が `![image.png](/attachments/<id>/image.png)` に変換される
- [ ] `attachment:report.pdf` が `[report.pdf](/attachments/<id>/report.pdf)` に変換される
- [ ] `commit:abcdef`, `source:repo/path`, `r123` は変換されず原文のまま残る
- [ ] コードブロック（``` で囲まれた領域、および行頭4スペースインデント領域）内の文字列は変換しない

---

### F-6: Builder（Hugo 静的サイトビルド）

#### ユーザーストーリー

As a 閲覧者, I want 静的 HTML サイトでチケット一覧・Wiki ページ・プロジェクト別 Issue 一覧を参照したい, so that Redmine が無くても普段と同じ URL で情報にアクセスできる。

#### フロー

```
1. Hugo サイトのスケルトン（hugo.toml + テーマ設定 + テンプレート）を用意
2. content/issues/, content/wiki/, content/attachments/ にシンボリックリンクまたはコピーを配置
3. permalinks 設定で Redmine 互換 URL にマッピング
   - issues:        /issues/:id/
   - wiki:          /projects/:project/wiki/:title/
4. taxonomy で project / status / tracker / assignee 別の一覧ページを自動生成
5. hugo コマンドで public/ に静的 HTML を出力
6. 添付ファイルは public/attachments/<id>/<filename> に配置
```

#### 入出力

| 項目 | 型 | 説明 |
|-----|---|------|
| 入力: `content/` | Markdown ディレクトリツリー | F-4 の出力 |
| 入力: `hugo.toml` | TOML | サイト設定（permalinks, taxonomies, baseURL） |
| 入力: Hugo テーマ | ディレクトリ | 標準的な Hugo テーマ（テーマ非依存で動作） |
| 出力: `public/` | 静的 HTML ツリー | Nginx 等で配信可能 |

#### 受け入れ条件

- [ ] `public/issues/<id>/index.html` が生成される
- [ ] `public/projects/<identifier>/wiki/<PageName>/index.html` が生成される
- [ ] `public/projects/<identifier>/issues/index.html` に当該プロジェクトの Issue 一覧が表示される
- [ ] taxonomy ページ `public/status/<status>/`, `public/tracker/<tracker>/`, `public/assignee/<name>/` が生成される
- [ ] テーマを差し替えても Markdown / frontmatter の修正なしでビルドできる
- [ ] `public/` を任意の静的ファイルサーバ（Nginx, GitHub Pages, S3 等）で配信できる

#### 画面/API 仕様

CLI:

```
staticmine build [--config <path/to/config.yaml>] [--in content/] [--out public/] [--no-search]
```

`--in` と `--out` の両方を指定した場合、`--config` は省略可能。Redmine 通信を行わないため接続情報を必要としない（NFR-1 と整合）。

主要 URL:

| パス | 内容 |
|------|------|
| `/issues/<id>/` | Issue 詳細 |
| `/projects/<identifier>/wiki/<PageName>/` | Wiki ページ |
| `/projects/<identifier>/issues/` | プロジェクト別 Issue 一覧 |
| `/status/<status>/` | ステータス別 Issue 一覧 |
| `/tracker/<tracker>/` | トラッカー別 Issue 一覧 |
| `/assignee/<name>/` | 担当者別 Issue 一覧 |
| `/attachments/<id>/<filename>` | 添付ファイル |

---

### F-7: Search（Pagefind 検索インデックス）

#### ユーザーストーリー

As a 閲覧者, I want 静的サイト上で全文検索したい, so that Redmine の検索機能が無くてもチケット・Wiki から目的の情報を探せる。

#### フロー

```
1. Builder（F-6）が public/ を出力した後に Pagefind を実行
2. Pagefind が public/ 配下の HTML をクロールし、検索インデックスを public/pagefind/ に生成
3. サイト内の検索 UI が public/pagefind/pagefind.js を読み込みクライアント側検索を実行
```

#### 入出力

| 項目 | 型 | 説明 |
|-----|---|------|
| 入力: `public/` | 静的 HTML ツリー | F-6 の出力 |
| 出力: `public/pagefind/` | JS / インデックスデータ | Pagefind ランタイム + 検索データ |

#### 受け入れ条件

- [ ] `public/pagefind/pagefind.js` および対応するインデックスファイルが生成される
- [ ] 検索 UI から Issue 本文・コメント・Wiki 本文に含まれる文字列でヒットする
- [ ] `--no-search` オプション指定時には Pagefind を実行せず `public/pagefind/` が生成されない
- [ ] 検索インデックス生成失敗時もビルド全体は失敗扱いとならない（警告のみ）

#### 画面/API 仕様

CLI:

```
staticmine build [--config <path/to/config.yaml>] [--no-search]
```

---

### F-8: Pipeline Orchestration（パイプライン段階の独立実行）

#### ユーザーストーリー

As a 運用担当者, I want Fetcher / Converter / Builder の各段を独立に実行したい, so that 変換ルールやテーマの試行錯誤時に Fetcher を再実行せず Converter / Builder のみを再実行できる。

As a 運用担当者, I want 全段を一括実行したい, so that 初回セットアップや定期更新を 1 コマンドで完結できる。

#### フロー

```
1. staticmine fetch   --config <path>         → raw/ を生成
2. staticmine convert [--config <path>] ...   → content/ を生成（raw/ が存在すれば単独実行可。--in/--out 両指定時は --config 省略可）
3. staticmine build   [--config <path>] ...   → public/ を生成（content/ が存在すれば単独実行可。--in/--out 両指定時は --config 省略可）
4. staticmine all     --config <path>         → fetch → convert → build を順次実行（上記 1〜3 を連結）
```

#### 入出力

| 項目 | 型 | 説明 |
|-----|---|------|
| 入力: 設定ファイル | YAML | Redmine 接続情報・フィルタ・出力先パス |
| 入力（convert/build/all のみ）: 前段の出力ディレクトリ | ディレクトリ | `convert` は `raw/`、`build` は `content/`。`all` は設定ファイルのみで前段ディレクトリ不要 |
| 出力: 各段の成果ディレクトリ | ディレクトリ | `raw/` / `content/` / `public/` |
| 出力: 実行ログ | テキスト | 各段の処理結果・失敗件数 |

#### 受け入れ条件

- [ ] `staticmine fetch --config <path>` が単独で成功し `raw/` が生成される
- [ ] `staticmine convert --config <path>` が既存 `raw/` を入力として単独で成功し `content/` が生成される
- [ ] `staticmine build --config <path>` が既存 `content/` を入力として単独で成功し `public/` が生成される
- [ ] `staticmine all --config <path>` が fetch → convert → build を順次実行し全段が成功する
- [ ] `staticmine convert` を `staticmine fetch` の実行なしに（`raw/` が存在する状態で）実行した場合、Redmine への通信は行われない
- [ ] `staticmine build` 失敗後に `staticmine build` を再実行すると、`staticmine fetch` や `staticmine convert` を再実行せずにビルドが完了する
- [ ] `staticmine all` の途中段（fetch または convert）が失敗した場合、以降の段を実行せずエラー終了する

#### 画面/API 仕様

CLI:

```
staticmine fetch   --config <path/to/config.yaml> [--out raw/]
staticmine convert [--config <path/to/config.yaml>] [--in raw/] [--out content/]
staticmine build   [--config <path/to/config.yaml>] [--in content/] [--out public/] [--no-search]
staticmine all     --config <path/to/config.yaml> [--no-search]
```

`convert` / `build` は `--in` と `--out` の両方を指定した場合に `--config` を省略可能。`fetch` および `all` は Redmine 接続情報が必要なため `--config` は必須。

---

## 実装マイルストーン

既存の F-1〜F-8 はそれぞれが完結した機能定義だが、これらをそのまま順次実装するとウォーターフォール的になり、全機能完成まで end-to-end 動作検証ができない。そのため**垂直スライス（vertical slice）方式**で、各マイルストーンごとに Fetcher → Converter → Builder の最小機能が揃って実際にブラウザで動作確認できる構成で実装する。

### マイルストーン一覧

| M | スコープ | 動作検証ゴール | 機能スライス |
|---|---------|---------------|-------------|
| M1 | プロジェクト一覧のみ | プロジェクト一覧ページがブラウザで表示される | F-1（プロジェクトAPIのみ）+ F-4（最小frontmatter）+ F-6（一覧ページ） |
| M2 | Issue 一覧（タイトル・ID・ステータス） | プロジェクト → Issue 一覧の遷移が動く | F-1（Issue API 追加）+ F-4（Issue 1行 Markdown）+ F-6（Issue 一覧テンプレート） |
| M3 | Issue 詳細（description + コメント） | Issue 詳細ページが見られる | F-1（comment 取得）+ F-4（本文 Markdown 化）+ F-6（詳細テンプレート） |
| M4 | Wiki ページ | Wiki ページが見られる | F-1（Wiki API）+ F-4（Wiki Markdown）+ F-6（Wiki テンプレート） |
| M5 | 添付ファイル | 添付ファイルがリンクから開ける | F-1（添付ダウンロード）+ F-4（リンク変換）+ F-6（静的配信） |
| M6 | Redmine 独自記法変換 | `#123` `[[PageName]]` `attachment:` が正しくリンク化される | F-5 全体 |
| M7 | プロジェクトフィルタ・permission frontmatter 完全化 | YAML 設定でプロジェクト絞り込みと private/public 表示 | F-2 / F-3 全体 |
| M8 | 全文検索 | Pagefind 検索ボックスが機能する | F-7 全体 |
| M9 | パイプライン CLI 統合 | `staticmine all` 1 コマンドで再構築完了 | F-8 全体 |

### 設計方針

- **垂直スライス**: 各マイルストーンで Fetcher / Converter / Builder の最小機能が揃い、実際に静的サイトとして動作確認できる
- **段階的範囲拡大**: F-1〜F-7 は単一マイルストーンで完成させず、M1〜M8 を跨いで段階的にスコープ拡大する
- **CLI**: M1〜M8 の各段では `staticmine fetch && staticmine convert && staticmine build` を手動チェーンで実行する。M9 で `staticmine all` に統合
- **独自記法の扱い**: M1〜M5 では Redmine 独自記法は素のまま表示（リンク切れ等を許容）。M6 で正しくリンク化する
- **早期フィージビリティ検証**: M1 完了時点で Hugo テーマ・URL構造・ディレクトリ配置の方針が確定する
- **ステータス管理**: 各マイルストーン完了時に対応する機能（F-x）の達成度を更新する。F-x のステータスは「対応マイルストーンまでの範囲が動作していること」を意味する

### マイルストーンと機能の対応マトリクス

各機能がどのマイルストーンで段階的に拡張されるかを示す:

| 機能ID | M1 | M2 | M3 | M4 | M5 | M6 | M7 | M8 | M9 |
|--------|----|----|----|----|----|----|----|----|----|
| F-1 (Fetcher) | プロジェクト | +Issue一覧 | +Issue詳細・コメント | +Wiki | +添付 | - | - | - | - |
| F-2 (Project Filter) | - | - | - | - | - | - | 全体 | - | - |
| F-3 (Permission Metadata) | 最小 | - | - | - | - | - | 完全化 | - | - |
| F-4 (Converter) | 最小Markdown | +Issue1行 | +本文 | +Wiki | +添付リンク | - | - | - | - |
| F-5 (Redmine 独自記法変換) | - | - | - | - | - | 全体 | - | - | - |
| F-6 (Builder) | 一覧 | +Issue一覧 | +Issue詳細 | +Wiki | +静的配信 | - | - | - | - |
| F-7 (Search) | - | - | - | - | - | - | - | 全体 | - |
| F-8 (Pipeline Orchestration) | 個別CLI | 個別CLI | 個別CLI | 個別CLI | 個別CLI | 個別CLI | 個別CLI | 個別CLI | `all` 統合 |

凡例:
- 「最小」「+xxx」: そのマイルストーンで実装される範囲
- 「全体」: そのマイルストーンで機能全体が完成
- 「-」: そのマイルストーンでは触れない
- 「個別CLI」: `fetch`/`convert`/`build` を個別実行するレベルの実装

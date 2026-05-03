# staticmine - 要求定義

## 概要

- **プロジェクト名**: staticmine
- **ステータス**: Draft

## 背景と目的

社内で運用してきた Redmine（バージョン 3.4.4.stable）は更新を停止しているが、過去のチケット・Wiki・添付ファイルは引き続き参照する必要がある。一方で Redmine 本体の運用（OS・Ruby・MySQL の保守、脆弱性対応、バックアップ運用）は廃止したい。

既存ツールの調査では、チケットと Wiki を統合して静的サイト化するツールは存在しなかった:

- Redmine 本家 Feature #17743 「Export a project as static HTML」は 2014 年起票で未実装
- dmichel35/redmine-wiki-exporter は Wiki 専用でチケット非対応

そこで、Redmine の全データ（プロジェクト・チケット・Wiki・添付ファイル）を一度ダンプし、静的サイトとして恒久的に参照可能なアーカイブを構築するツール staticmine を開発する。Redmine 本体が消滅しても、ダンプされた JSON から再ビルドできる構成とすることで、長期保管に耐えるアーカイブとすることを目的とする。

## スコープ

### 対象範囲

- Redmine REST API を用いた Project / Issue / Wiki / Attachment / User のフルダンプ
- ダンプデータ（JSON + 添付バイナリ）のローカルファイルとしての永続保管
- JSON ダンプから Markdown + frontmatter への変換
- Redmine 独自記法（`#123`, `[[PageName]]`, `attachment:filename.png`）の Markdown / 相対リンクへの変換
- Hugo による静的 HTML サイトの生成
- Redmine の主要 URL（`/issues/<id>/`, `/projects/<id>/wiki/<page>/`, `/projects/<id>/issues/`）との互換性維持
- プロジェクト単位の include / exclude フィルタ（glob パターン）
- 公開用・社内用など複数構成の並行ビルド
- 元 Redmine の可視性メタデータ（`project_is_public`, `issue_is_private`, `project_identifier`）の frontmatter 保持
- Pagefind による静的サイト全文検索インデックスの生成

### 対象外

- ガントチャート・カレンダー等の動的 UI
- リポジトリ連携（`commit:xxx`, `source:xxx`, `r123` 等のリビジョン参照）
- クエリパラメータベースのフィルタ URL（`/issues?status_id=open` 等）
- 静的サイト側でのアクセス制御・認証（メタデータの記録のみ）
- ニュース・フォーラム・Files（プロジェクトファイル一覧）等の周辺機能
- Issue journal のステータス変更履歴（コメント本文 `notes` のみ取得）
- Wiki のバージョン履歴（最新版のみ取得）
- 差分更新（毎回フルダンプ）
- Redmine への書き込み・更新

## 機能要件

### FR-1: Redmine データのフルダンプ取得

- **説明**: Redmine REST API を使用して Project / Issue（コメント含む）/ Wiki（最新版のみ）/ Attachment / User を取得し、構造化された JSON ファイルおよび添付バイナリとしてローカルに保存する。
- **優先度**: Must
- **受け入れ条件**:
  - [ ] `raw/projects.json` に取得対象プロジェクトの一覧が出力される
  - [ ] `raw/issues/<id>.json` に各 Issue が出力され、`journals[].notes` のコメント本文が含まれる
  - [ ] `raw/issues/<id>.json` に Issue journal のステータス変更等の履歴差分が含まれない
  - [ ] `raw/projects/<identifier>/wiki/<PageName>.json` に各 Wiki ページの最新版のみが出力される
  - [ ] `raw/attachments/<id>/<filename>` に添付ファイルのバイナリが保存される
  - [ ] `raw/users.json` に Issue / Wiki に登場するユーザーの ID・氏名・ログイン名が出力される
  - [ ] 取得失敗時にリトライおよびログ出力が行われる

### FR-2: プロジェクトフィルタ

- **説明**: YAML 設定ファイルでプロジェクトの include / exclude を glob パターンで指定する。複数の設定ファイルを切り替えることで、公開用・社内用など異なる構成を並行ビルドできる。
- **優先度**: Must
- **受け入れ条件**:
  - [ ] 設定ファイルで `include: ["public-*"]` のような glob 指定ができる
  - [ ] 設定ファイルで `exclude: ["internal-*"]` のような glob 指定ができる
  - [ ] include と exclude の両方が指定された場合、include に一致しかつ exclude に一致しないプロジェクトのみが対象となる
  - [ ] 別の設定ファイルを指定して再実行することで、同一の Redmine から異なるサブセットのサイトを生成できる
  - [ ] 対象外のプロジェクトに属する Issue / Wiki / Attachment は raw / content / public のいずれにも出力されない

### FR-3: 権限メタデータの保持

- **説明**: 元 Redmine の可視性情報を Markdown frontmatter に記録する。静的サイト側ではアクセス制御は実施しない（記録のみ）。
- **優先度**: Must
- **受け入れ条件**:
  - [ ] 各 Issue の Markdown frontmatter に `project_identifier`, `project_is_public`, `issue_is_private` が出力される
  - [ ] 各 Wiki ページの Markdown frontmatter に `project_identifier`, `project_is_public` が出力される
  - [ ] frontmatter の値は Redmine REST API のレスポンスと一致する

### FR-4: JSON から Markdown への変換

- **説明**: 取得した JSON を Markdown 本文 + YAML frontmatter に変換する。Issue は本文 + コメントを時系列で連結する。
- **優先度**: Must
- **受け入れ条件**:
  - [ ] `content/issues/<id>.md` に Issue 本文・属性 frontmatter・コメント時系列が出力される
  - [ ] `content/wiki/<project>/<page>.md` に Wiki 本文と frontmatter が出力される
  - [ ] frontmatter には `id`, `subject` / `title`, `author`, `created_on`, `updated_on`, `status`, `tracker`, `priority`, `assignee`, `project_identifier` のうち該当するフィールドが含まれる
  - [ ] 同一の `raw/` を入力に複数回実行しても出力 Markdown のバイト列が変わらない（冪等）

### FR-5: Redmine 独自記法の変換

- **説明**: Markdown 本文中の Redmine 独自記法を、静的サイト上で機能するリンク・画像参照に変換する。
- **優先度**: Must
- **受け入れ条件**:
  - [ ] `#123` が `/issues/123/` への Markdown リンクに変換される
  - [ ] `[[PageName]]` が同一プロジェクトの `/projects/<identifier>/wiki/PageName/` への Markdown リンクに変換される
  - [ ] `[[OtherProject:PageName]]` が `/projects/OtherProject/wiki/PageName/` へのリンクに変換される
  - [ ] `attachment:filename.png` が同 Issue / Wiki に紐づく添付ファイルへの相対リンクまたは画像表示に変換される
  - [ ] `commit:xxx`, `source:xxx`, `r123` 等のリポジトリ参照は変換せず元の文字列のまま残る
  - [ ] コードブロック（``` で囲まれた領域、および行頭4スペースインデント領域）内の Redmine 独自記法は変換しない（行頭4スペースインデントで記述されたコードブロック内の `#123` `[[PageName]]` `attachment:filename.png` を含む）

### FR-6: 静的サイトのビルドと URL 互換性

- **説明**: Hugo を使用して Markdown から静的 HTML サイトを生成する。Redmine の主要 URL パスとの互換性を維持する。
- **優先度**: Must
- **受け入れ条件**:
  - [ ] `public/issues/<id>/index.html` が存在し、対応する Issue を表示する
  - [ ] `public/projects/<identifier>/wiki/<PageName>/index.html` が存在し、対応する Wiki ページを表示する
  - [ ] `public/projects/<identifier>/issues/index.html` が存在し、当該プロジェクトの Issue 一覧を表示する
  - [ ] 出力された Markdown + frontmatter が標準的な Hugo テーマで描画可能（テーマ非依存）
  - [ ] `public/` 配下を任意の HTTP サーバ（Nginx 等）で配信できる
  - [ ] taxonomy 一覧ページ（`/status/<status>/`, `/tracker/<tracker>/`, `/assignee/<name>/`, `/projects/<identifier>/issues/`）が生成される

### FR-7: 全文検索インデックスの生成

- **説明**: ビルド済みの `public/` に対して Pagefind を実行し、ブラウザ側で動作する全文検索インデックスを生成する。
- **優先度**: Should
- **受け入れ条件**:
  - [ ] `public/pagefind/` 配下に Pagefind のインデックスと JS が出力される
  - [ ] 検索 UI から Issue 本文・コメント・Wiki 本文がヒットする
  - [ ] 検索インデックス生成を無効化するオプションがあり、無効化時はインデックスが生成されない

### FR-8: パイプライン段階の独立実行

- **説明**: Fetcher / Converter / Builder の各段を独立に実行できる。Fetcher を再実行せずに Converter / Builder のみを再実行することで、変換ルールやテーマの試行錯誤が可能となる。
- **優先度**: Must
- **受け入れ条件**:
  - [ ] Fetcher のみを実行するコマンドがある
  - [ ] Converter のみを実行するコマンドがある（入力は既存 `raw/`）
  - [ ] Builder のみを実行するコマンドがある（入力は既存 `content/`）
  - [ ] 全段を一括実行するコマンドがある

## 非機能要件

### NFR-1: アーカイブの再構築可能性

- **カテゴリ**: 可用性 / 保守性
- **説明**: Redmine 本体が停止・廃棄された後でも、保管されている `raw/` のみから `content/` および `public/` を再ビルドできる。
- **測定基準**: Redmine への接続を遮断した状態で Converter および Builder を実行し、`public/` が生成されること。

### NFR-2: 出力の冪等性

- **カテゴリ**: 信頼性
- **説明**: 同一の入力 `raw/` から複数回 Converter / Builder を実行した場合、出力ファイルのバイト列（タイムスタンプ等のメタ情報を除く）が一致する。
- **測定基準**: 同一 `raw/` から 2 回 Converter を実行し、`content/` 配下の Markdown ファイルの SHA-256 ハッシュが一致すること。

### NFR-3: 段階分離

- **カテゴリ**: 保守性
- **説明**: Fetcher / Converter / Builder の各段が、ファイル（`raw/`, `content/`, `public/`）を介して疎結合となっている。
- **測定基準**: 任意の 1 段のコードを変更しても、他の段のコードに変更が波及しないこと。

### NFR-4: スケール

- **カテゴリ**: パフォーマンス
- **説明**: 想定規模のデータを現実的な時間で処理できる。
- **測定基準**: 想定規模（プロジェクト 50・チケット 1000・添付 3MB）のフルダンプおよびビルドが、開発者のローカル PC で 30 分以内に完了すること。なお、この想定規模はツールの動作保証範囲の参考値であり、明示的な上限制約は設けない。これを超える規模での動作は保証しないが、技術的に禁止する制限は実装しない。

### NFR-5: アーカイブ可搬性

- **カテゴリ**: 保守性
- **説明**: `raw/` ディレクトリを単独でコピーすれば別環境で同一サイトを再ビルドできる。
- **測定基準**: `raw/` のみを別マシンに転送し、staticmine をクローン後に Converter + Builder を実行することで同等の `public/` が生成されること。

## 制約条件

- 対象 Redmine は バージョン 3.4.4.stable で固定
- Redmine 上のテキストフォーマットは Markdown（Textile は対象外）
- Fetcher は Python 3.13 または 3.14 + python-redmine ライブラリで実装
- Builder は Hugo（最新 stable）を使用
- 検索インデックスは Pagefind を使用
- 設定ファイル形式は YAML
- 静的サイト側でのアクセス制御は実装しない（必要な場合は配信サーバ側で実施）
- Redmine への接続は HTTPS のみサポートする。HTTP 接続は許容しない（API キー保護のため）
- 実行環境は Linux または macOS をサポートする。Windows は動作対象外

## 前提条件

- Redmine REST API が有効化されており、API キーまたは認証情報を取得済みである
- API キーは対象プロジェクト全件にアクセス可能な権限を持つ
- ダンプ実行マシンから Redmine への HTTPS 接続が可能

## 成功指標

- Redmine 本体を停止しても、過去のチケット・Wiki・添付ファイルが静的サイトから参照可能である（対応: NFR-1。Redmine への接続を遮断した状態で Converter + Builder を実行し `public/` が生成されることで確認）
- `raw/` をバックアップとして保管しておけば、テーマ変更や独自記法変換ルール改善のたびに再ビルドできる（対応: NFR-1, NFR-5。別マシンで `raw/` のみから `public/` を生成できることで確認）
- 同一 Redmine から「公開用」「社内用」など複数の構成を並行ビルドし、別ホストで配信できる（対応: FR-2。設定ファイルを切り替えて 2 構成をビルドし異なる `public/` が得られることで確認）
- 既存の Redmine URL（`/issues/<id>/` 等）でブックマークしていたページが、静的サイト上の同一パスで参照できる（対応: FR-6。`public/issues/<id>/index.html` の存在および内容一致で確認）

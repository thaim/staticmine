# staticmine 設計ドキュメント レビューレポート

レビュー実施日: 2026-04-26
対象: `docs/specs/` 配下の7ドキュメント

## サマリー

| 重要度 | 件数 |
|--------|------|
| Critical | 4件 |
| Warning | 7件 |
| Suggestion | 6件 |

---

## Critical（自動修正対象）

### [C-1] features.md: F-7 が機能一覧テーブルに存在しない

- **該当箇所**: features.md L4-12（機能一覧テーブル）
- **問題**: `F-7: Search（Pagefind 検索インデックス）` は機能一覧テーブルに `F-6` として記載されているが、機能詳細セクションでは `### F-7: Search` として定義されており、ID が不一致。テーブルの F-6 は機能詳細の F-6（Builder）に対応し、テーブルに F-7 が存在しない。具体的には機能一覧テーブル `F-6 | Search | FR-7 | Should` と機能詳細 `### F-7: Search` が矛盾している。
- **影響**: トレーサビリティが破綻しており、F-7 を参照するすべての記述（glossary.md、features.md 内など）が不整合になる。実装者が F-7 をスキップするリスクがある。
- **修正案**: 機能一覧テーブルの `F-6 | Search` を `F-7 | Search` に修正するか、機能詳細の `### F-7` を `### F-6` に統一する。機能詳細の F-6 と F-7 の番号を整理して一貫させる。

### [C-2] glossary.md と features.md の F 番号参照が不整合

- **該当箇所**: glossary.md L26-27（Builder, Converter の定義行）
- **問題**: glossary.md の Builder 定義は `features.md (F-6, F-7)` と参照しているが、[C-1] の通り機能一覧テーブルでは Search が F-6 と記載されている。Fetcher の定義は `features.md (F-1)` のみで F-7 への参照は Converter にないが、Builder が `F-7` を参照している点が [C-1] の矛盾を連鎖的に引き起こしている。
- **影響**: 設計ドキュメント全体で F 番号が信頼できなくなり、traceability テーブル作成やレビューに支障をきたす。
- **修正案**: [C-1] の修正後、glossary.md の各 `features.md (F-x)` 参照を正しい ID に合わせて一括修正する。

### [C-3] requirements.md FR-5 と features.md F-4/F-5 の対応関係が不明確

- **該当箇所**: features.md L11（機能一覧テーブル `F-4 | Converter | FR-4, FR-5`）および機能詳細 F-5 セクション
- **問題**: 機能一覧テーブルでは FR-5（Redmine 独自記法の変換）は F-4（Converter）に対応させているが、機能詳細では F-4 と F-5 が独立したセクションとして記述されている。F-5 は「Converter サブ機能」と明記されているものの、機能一覧テーブルに F-5 の行がない。F-5 が独立機能なのかサブ機能なのかが矛盾している。
- **影響**: FR-5 の受け入れ条件が F-4 と F-5 のどちらに帰属するか不明なため、テスト設計・実装スコープが曖昧になる。
- **修正案**: 機能一覧テーブルに `F-5 | Redmine 独自記法変換（Converter サブ機能） | FR-5 | Must | Draft` を追加するか、F-5 セクションを F-4 のサブセクションに統合して番号の独立性をなくす。後者を選ぶ場合は FR-5 の対応を `F-4` のみとし、glossary.md の「Redmine 独自記法」も更新する。

### [C-4] requirements.md FR-8 のトレーサビリティが architecture.md に欠落

- **該当箇所**: architecture.md（インターフェース / CLI セクション L141-150）
- **問題**: FR-8「パイプライン段階の独立実行」の受け入れ条件に「Converter のみを実行するコマンド（入力は既存 `raw/`）」「全段を一括実行するコマンド」があるが、architecture.md のインターフェース定義では `staticmine all --config <path>` コマンドが記載されているにもかかわらず、features.md の F-1 / F-4 / F-6 の CLI 仕様欄にはそれぞれ個別コマンドが記載されており、`staticmine all` コマンドの仕様（F-8 に対応する機能）が features.md の機能一覧に存在しない。FR-8 に対応する機能 ID が features.md 機能一覧では F-1 / F-4 / F-5（テーブル上は対応なし）に分散しており、単独の機能として追跡できない。
- **影響**: FR-8 に対応するテストケースやレビュー基準が明確に定義できない。`staticmine all` コマンドがどの機能設計に対応するかが特定できない。
- **修正案**: 機能一覧テーブルの F-1 / F-4 / F-6 の「対応 FR」列に FR-8 が記載されているため機能との対応は一応存在するが、`staticmine all` を対応する機能詳細（どの F-x の CLI 仕様に記述するか）を明示する。または FR-8 専用の機能セクションを追加する。

---

## Warning

### [W-1] features.md F-5: コードブロック内変換スキップの仕様が requirements.md に対応なし

- **該当箇所**: features.md F-5 受け入れ条件 L261「コードブロック（``` で囲まれた領域）内の文字列は変換しない」
- **問題**: この受け入れ条件は requirements.md の FR-5 に対応する受け入れ条件に存在しない。requirements.md FR-5 には `#123` / `[[PageName]]` / `attachment:` の変換と `commit:` 等の非変換のみが規定されており、コードブロック内の非変換は要求として明示されていない。
- **改善案**: requirements.md FR-5 の受け入れ条件に「コードブロック（``` で囲まれた領域）内の Redmine 独自記法は変換しない」を追加する。

### [W-2] architecture.md: `staticmine index` コマンドが CLI インターフェース定義に欠落

- **該当箇所**: architecture.md L141-150（CLI インターフェース定義）vs features.md F-7 L355-364
- **問題**: features.md F-7 の「画面/API 仕様」セクションでは `staticmine index --in public/` という独立コマンドが「または」として定義されているが、architecture.md のインターフェース定義の CLI エンドポイント一覧にはこのコマンドが含まれていない。
- **改善案**: architecture.md のインターフェース定義に `staticmine index --in <path>` を追加するか、features.md から当該コマンドを削除して `--no-search` オプションのみに絞る。どちらにするか設計判断を明示する。

### [W-3] requirements.md: 前提条件のうちネットワーク要件が実行環境依存で曖昧

- **該当箇所**: requirements.md L178「ダンプ実行マシンから Redmine への HTTP / HTTPS 接続が可能」
- **問題**: HTTP と HTTPS の両方を前提条件として列挙しているが、requirements.md のスコープ（L28）では「Redmine REST API を用いた」と記述しているのみで、HTTP での接続を前提とするかどうかの方針が制約条件に記載されていない。architecture.md のセキュリティ設計（L301）では「HTTPS 配信を推奨するが...」とあり、Fetcher が HTTP を許容するかどうかの設計方針が曖昧。
- **改善案**: 制約条件または前提条件に「Redmine への接続は HTTPS を推奨するが、HTTP も許容する」または「HTTP のみ / HTTPS のみ」を明記し、architecture.md セキュリティ設計と整合させる。

### [W-4] features.md F-6: taxonomy の URL パスが requirements.md に対応なし

- **該当箇所**: features.md F-6 受け入れ条件 L297「taxonomy ページ `public/status/<status>/`, `public/tracker/<tracker>/`, `public/assignee/<name>/` が生成される」
- **問題**: requirements.md FR-6 の受け入れ条件には taxonomy ページ生成の条件がない。また requirements.md スコープの「Redmine の主要 URL との互換性維持」（L28）にも taxonomy 由来の URL は含まれておらず、要求と機能設計の間に追加仕様が存在している。
- **改善案**: requirements.md FR-6 の受け入れ条件に taxonomy ページ生成を追加するか、features.md F-6 の注記として「FR-6 の範囲を超えた追加機能」と明示する。

### [W-5] guidelines.md: VCR カセットのフィルタ対象が不明確

- **該当箇所**: guidelines.md L105「記録時は API キー・ホスト名等の機微情報をフィルタする」
- **問題**: 「等の機微情報」という記述で、フィルタ対象が明確に定義されていない。具体的にどのレスポンスヘッダ・フィールドをフィルタするかが曖昧で、レビュー基準として機能しない。
- **改善案**: フィルタ対象を列挙する（例: `X-Redmine-API-Key` ヘッダ、レスポンス中の `login` / `mail` フィールド、実 URL のホスト部分等）か、VCR.py のフィルタ設定を `tests/conftest.py` に集約することを明記する。

### [W-6] architecture.md: Converter での添付ファイル配置方法が「コピーまたはシンボリックリンク」で未決定

- **該当箇所**: features.md F-4 入出力テーブル L203「バイナリ（コピーまたはシンボリックリンク）」、architecture.md Converter 責務 L93「添付ファイルを `content/attachments/` 配下に配置（コピーまたはシンボリックリンク）」
- **問題**: コピーとシンボリックリンクはどちらを使用するか未決定のまま設計ドキュメントに記載されている。シンボリックリンクは Windows 環境での動作に問題があり、冪等性（NFR-2）との関係も異なる。
- **改善案**: どちらを採用するか決定し、設計判断として architecture.md に記録する。Windows サポートが必要かどうかも合わせて制約条件（requirements.md）に明記する。

### [W-7] requirements.md: 添付ファイル総容量の前提条件が制約条件と混在

- **該当箇所**: requirements.md L179「添付ファイル総容量（3MB 程度）がローカルディスク容量に対して十分小さい」
- **問題**: NFR-4（スケール）の測定基準でも「添付 3MB」を前提としているが、これは特定の Redmine 環境の実測値であり、ツールの制約ではなく想定規模の例示である。前提条件として「十分小さい」という記述は曖昧で、上限の数値も定義されていない。
- **改善案**: 「添付ファイル総容量の上限は規定しないが、NFR-4 の測定基準（3MB）を参考値とする」と明記するか、実際の想定上限（例: 10GB まで対応）を制約条件に追記する。

---

## Suggestion

### [S-1] index.md: 各ドキュメントのステータスがすべて "Draft" で進捗管理が困難

- **該当箇所**: index.md L9-16（ドキュメント一覧テーブル）および requirements.md L6
- **提案**: ステータスの定義（Draft / Review / Approved 等）を index.md に記載し、レビュー完了後に更新するルールを guidelines.md に追記する。現状は全ファイルが Draft のため承認状態が不明。

### [S-2] features.md: 各機能の "ステータス" 列の定義が未記載

- **該当箇所**: features.md L5（機能一覧テーブルヘッダ `ステータス` 列）
- **提案**: 取り得る値（Draft / In Progress / Done 等）とその定義を機能一覧の直下か guidelines.md に記述する。現状は全行 "Draft" で管理指標として機能していない。

### [S-3] architecture.md: エラーハンドリング設計が Fetcher のリトライのみで不十分

- **該当箇所**: architecture.md Fetcher コンポーネント（L68-82）
- **提案**: Converter / Builder のエラー時の挙動（例: 1 件の JSON 解析失敗時に他を継続するか中断するか）が仕様に含まれていない。guidelines.md のコーディング規約に「継続 vs 中断」の方針があるが（L11）、それをコンポーネント設計として architecture.md にも明示することを推奨する。

### [S-4] requirements.md: 成功指標に測定方法が記載されていない

- **該当箇所**: requirements.md L181-186（成功指標セクション）
- **提案**: 成功指標がすべて定性的な文章であり、NFR の測定基準と対応していない。各成功指標に対応する NFR 番号または測定方法（例: 「Redmine 本体を停止しても参照可能 → NFR-1 の測定基準で確認」）を付記することで検証可能な形式にする。

### [S-5] guidelines.md: Hugo / Pagefind のバージョン固定手順が CI 定義任せで不明

- **該当箇所**: repository.md L122-130（依存関係管理）および guidelines.md CI/CD セクション L145-158
- **提案**: repository.md では「CI 定義および README で明示し、ピン留めする」と記載されているが、具体的なバージョン番号が仕様ドキュメントには記載されていない。ドキュメントに最低限の目標バージョン（例: Hugo >= 0.120.0、Pagefind >= 1.1.0）を記載し、アップグレード判断基準を明示することを推奨する。

### [S-6] glossary.md: `permalink` の定義が Hugo 機能の説明に留まり staticmine コンテキストで不完全

- **該当箇所**: glossary.md L12（`permalink` 定義行）
- **提案**: `permalink` の定義が「Hugo の URL ルーティング設定」という説明に留まっており、Redmine 由来の用語セクションに分類されている点が不自然（Hugo 固有の機能であり、関連技術・ツールセクションが適切）。また小文字 `permalink` と Hugo ドキュメントの `permalinks`（複数形）で表記ゆれがある。関連技術セクションへの移動と表記統一を推奨する。

---

## トレーサビリティ確認

| 要件ID | 機能設計 | アーキテクチャ | 状態 |
|-------|---------|--------------|------|
| FR-1 | F-1 | Fetcher コンポーネント | OK |
| FR-2 | F-2 | Project Filter コンポーネント | OK |
| FR-3 | F-3 | Converter コンポーネント（F-3 言及あり） | OK |
| FR-4 | F-4（テーブル上） | Converter コンポーネント | OK |
| FR-5 | F-4 テーブル記載 / F-5 詳細定義（番号矛盾） | Converter コンポーネント | NG（[C-3]） |
| FR-6 | F-5（テーブル） / F-6（詳細）（番号ズレ） | Builder コンポーネント | NG（[C-1]） |
| FR-7 | F-6（テーブル） / F-7（詳細）（番号ズレ） | Builder コンポーネント | NG（[C-1]） |
| FR-8 | F-1/F-4/F-6 に対応 FR 分散 | CLI インターフェース | NG（[C-4]） |
| NFR-1 | 対応機能なし（非機能） | 設計判断「JSON ダンプを永続保管」 | OK |
| NFR-2 | F-4 受け入れ条件に冪等性あり | Converter コンポーネント | OK |
| NFR-3 | 対応機能なし（非機能） | データフロー（段階分離） | OK |
| NFR-4 | 対応機能なし（非機能） | 記述なし | NG（アーキテクチャに測定基準の反映なし） |
| NFR-5 | 対応機能なし（非機能） | 記述なし | NG（アーキテクチャに設計的担保の記述なし） |

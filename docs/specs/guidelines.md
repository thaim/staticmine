# staticmine - 開発ガイドライン

## コーディング規約

### 基本方針

- Python コードは **PEP 8** に準拠する
- すべての公開関数・メソッド・クラスに **型ヒント** を付与する。`Any` の使用は最小化し、使用する場合は理由をコメントに残す
- すべての公開要素に **docstring**（Google 形式）を記述する。引数・戻り値・例外を `Args:` / `Returns:` / `Raises:` セクションで明示する
- I/O（ファイル・HTTP）と純粋ロジックを分離する。Converter の独自記法変換は副作用を持たない関数として実装し、ユニットテストしやすくする
- 例外は捕捉したまま握り潰さず、`logging` モジュールでログ出力するか上位に再送出する
- `print` ではなく `logging` を使用する。ログレベルは Fetcher 進捗 = INFO、リトライ = WARNING、致命的失敗 = ERROR、ループ詳細 = DEBUG とする

### フォーマット

- インデント: スペース 4 個
- 行長: 100 文字（ruff の `line-length = 100`）
- 文字列クォート: ダブルクォートを基本とする（ruff format のデフォルトに従う）
- import 順: 標準ライブラリ → サードパーティ → 自プロジェクト の 3 ブロック。各ブロック内はアルファベット順（ruff の isort ルールで自動整列）
- フォーマット適用は `ruff format` に統一し、`black` 等の他フォーマッタは併用しない

### リンター/フォーマッター設定

- **ruff**: lint と format を一元化。`pyproject.toml` の `[tool.ruff]` で以下を設定
  - `target-version = "py313"`
  - `line-length = 100`
  - 有効ルールセット: `E`, `F`, `W`, `I`（isort）, `N`（命名）, `UP`（pyupgrade）, `B`（bugbear）, `SIM`（simplify）, `RUF`
- **mypy**: `[tool.mypy]` で `strict = true` を有効化
  - `python_version = "3.13"`
  - 外部ライブラリのスタブが無いものは `ignore_missing_imports` を該当モジュール限定で許可
- **pytest**: `[tool.pytest.ini_options]` でテスト探索パスとカバレッジ設定を集約
- pre-commit や CI で `ruff check`, `ruff format --check`, `mypy`, `pytest` を実行し、合格しない PR はマージ不可とする

## Git 運用

### ブランチ戦略

採用方針: **GitHub Flow**（main + 短命の feature ブランチ）

| ブランチ | 用途 |
|---------|------|
| `main` | 常にデプロイ可能な状態を保つ唯一の長期ブランチ。直接コミット禁止、PR レビュー必須 |
| `feature/<topic>` | 機能追加・改善用の短命ブランチ。例: `feature/wiki-link-converter`, `feature/pagefind-integration` |
| `fix/<topic>` | バグ修正用の短命ブランチ。例: `fix/attachment-path-windows` |
| `docs/<topic>` | ドキュメントのみの変更。例: `docs/architecture-update` |

- main への直接 push は GitHub のブランチ保護で禁止する
- feature ブランチは作業完了後に削除する
- リリース用ブランチ・develop ブランチは設けない（ツール特性上、長期並行開発が発生しないため）

### コミットメッセージ

形式: **Conventional Commits** に準拠する。

```
<type>(<scope>): <subject>

<body>

<footer>
```

- `<type>`: `feat`, `fix`, `docs`, `refactor`, `test`, `chore`, `perf`, `ci`, `build` のいずれか
- `<scope>`（任意）: 影響モジュール（例: `fetcher`, `converter`, `cli`, `hugo`, `ci`）
- `<subject>`: 50 文字以内の現在形・命令形・先頭小文字
- `<body>`（任意）: 変更理由・背景・代替案検討。72 文字で改行
- `<footer>`（任意）: `BREAKING CHANGE:` 注記、関連 Issue 番号（`Refs #12`, `Closes #34`）

例:

```
feat(converter): convert [[Project:Page]] to absolute wiki URL

Cross-project wiki links were previously left as raw text. This change
extends the wiki-link regex to capture the project identifier and emit
/projects/<id>/wiki/<page>/ paths.

Closes #42
```

### プルリクエスト

- **タイトル**: コミットメッセージと同形式（`<type>(<scope>): <subject>`）
- **説明**: 以下を含む
  - 背景（なぜこの変更が必要か）
  - 変更内容の要約
  - 関連 Issue / 仕様ドキュメントへのリンク（`docs/specs/features.md` の機能 ID 等）
  - 動作確認方法（コマンド・期待結果）
  - 仕様変更を含む場合は `docs/specs/` 該当ファイルの更新箇所
- **レビュー**: 最低 1 名の approve を必須とする
- **マージ方式**: Squash and merge を基本とする（main の履歴を線形に保つ）
- **CI**: 全ジョブ成功が必須。失敗中は merge ブロック

## テスト方針

### テスト種類

| 種類 | 対象 | ツール |
|-----|------|-------|
| ユニットテスト | Converter のリンク変換ロジック、frontmatter 生成、Project Filter の glob 評価、設定ファイルパース | pytest |
| 統合テスト | `tests/fixtures/` の小規模 `raw/` を入力に、Converter → Hugo build までを通し、生成 HTML の存在および主要要素の有無を検証 | pytest + Hugo CLI |
| Fetcher テスト | Redmine REST API 呼び出し（実 API は叩かない） | pytest + **VCR.py**（カセット記録方式）。簡易ケースは `requests-mock` で代替可 |

- E2E テストは設けない（ツール性質上、本物の Redmine インスタンスを CI で常時用意することは現実的でない）
- VCR カセットは `tests/fixtures/cassettes/` に配置し、Git 管理する。記録時は以下の機微情報をフィルタする:
  - `X-Redmine-API-Key` リクエストヘッダ
  - `?key=<api_key>` URL パラメータ
  - レスポンス中のユーザーオブジェクトの `mail` フィールド
  - ホスト名（実 Redmine URL → `redmine.example.com` に置換）
- VCR.py のフィルタ設定は `tests/conftest.py` に集約する

### カバレッジ目標

- プロジェクト全体: **80 %** 以上
- Converter サブパッケージ: 90 % 以上（独自記法変換ロジックがリグレッションを起こしやすいため重点配分）
- Fetcher サブパッケージ: VCR / モックでカバーできる範囲を測定対象とし、外部 I/O ラッパー部分のみ低カバレッジを許容
- 計測は `pytest --cov=staticmine --cov-report=term-missing --cov-fail-under=80` で行う

### テスト命名規則

- ファイル名: `test_<対象モジュール名>.py`（例: `test_wiki_link.py`, `test_filter.py`）
- 関数名: `test_<対象機能>_<条件>_<期待結果>` の 3 段構成
  - 例: `test_convert_issue_link_with_hash_returns_markdown_link`
  - 例: `test_apply_filter_with_exclude_glob_removes_matching_projects`
- パラメタライズが多い場合は `pytest.mark.parametrize` を使用し、`ids` で各ケース名を付与する
- フィクスチャは `tests/conftest.py` または対象に近い `conftest.py` に集約する

## 動作検証

### 開発時の動作確認手順

自動テスト（ユニット / 統合）に加え、ブラウザでの実動作確認を行う。標準フロー:

```bash
uv run staticmine fetch --config staticmine.yaml
uv run staticmine convert --config staticmine.yaml
hugo serve --source hugo --contentDir ../content
```

ブラウザで `http://localhost:1313/` を開き、生成されたページが期待どおり表示されるか確認する。

### Hugo serve の制約と対処

`hugo serve --contentDir <hugo source 外のパス>` を指定した場合、Hugo は **指定 contentDir の変更を監視しない**。`hugo/` ディレクトリ内の変更のみが検知対象となる。

そのため以下を守る:

- 開発フローは **fetch → convert → hugo serve 起動** の順で実施する
- `staticmine convert` を再実行した場合は `hugo serve` も**再起動**する
- 静的ビルド（`hugo --contentDir ../content --destination public`）は外部 contentDir でも正常に反映される（serve のみの制約）

この制約を踏まえ、CI / 統合テストでは `hugo serve` ではなく `hugo build` を使用する（既に `tests/integration/test_build_smoke.py` で対応済み）。

## レビュー基準

### 必須チェック項目

- [ ] 追加・変更されたすべての公開関数・メソッド・クラスに型ヒントが付与されている
- [ ] 追加・変更されたロジックに対応するテストが追加されている（バグ修正は再現テストを含む）
- [ ] `ruff check` / `ruff format --check` / `mypy` / `pytest` が CI でパスしている
- [ ] 仕様変更（CLI 引数追加・設定キー追加・出力パス変更等）を含む場合、`docs/specs/` の該当ドキュメント（features / architecture / repository / glossary）が同一 PR で更新されている
- [ ] 公開 API・CLI の挙動を変更する場合、README の使用例も更新されている
- [ ] Redmine API キー・社内 URL・実プロジェクト名等の機微情報が含まれていない（fixture / VCR カセットを含む）

### ドキュメントステータス更新ルール

- PR がマージされた時点で、変更対象のドキュメントのステータスを更新する
- 初稿作成時: `Draft`
- レビュー依頼時: `Draft` → `Review`（レビュアーを PR に指定した時点）
- レビュー承認時: `Review` → `Approved`（全レビュアーが approve した時点）
- `Approved` のドキュメントを変更する PR は、変更内容が確定するまで `Review` に戻す
- features.md の機能ステータス（Draft / In Progress / Done）は実装 PR のマージ時に更新する

### 推奨チェック項目

- [ ] 設計判断（複数案から選んだ理由）が PR 説明またはコード上のコメントに記載されている
- [ ] パフォーマンスに影響しうる変更（ループ複雑度の変化、I/O 増加）について計測または見積もりが示されている
- [ ] 例外処理が「捕捉してログ出力 + 再送出」「捕捉して既定値で継続」のいずれであるか意図が明確になっている
- [ ] 新規依存パッケージ追加時、選定理由（既存依存で代替不能な点）が PR 説明に記載されている

## CI/CD

### パイプライン

GitHub Actions で以下を `push` / `pull_request` トリガで実行する。

```
1. setup           : Python 3.13 / 3.14 セットアップ、uv インストール、依存解決（uv sync）
2. lint            : ruff check + ruff format --check
3. type check      : mypy staticmine/
4. unit + cov      : pytest tests/unit --cov=staticmine --cov-fail-under=80
5. integration     : Hugo extended と Pagefind バイナリを導入、tests/integration を実行
6. build smoke     : examples/staticmine.yaml と tests/fixtures/raw/ を入力に
                     staticmine convert → hugo build を実行し、想定 HTML が出力されるか確認
```

- 各ステップは独立ジョブまたは同一ジョブ内のステップとして並列化可能なものは並列化する（lint と type check は並列、test 系は依存解決後に並列）
- Python 3.13 / 3.14 マトリクス × Ubuntu latest / macOS latest を対象とする（Windows は動作対象外）
- main へのマージは 1〜6 すべての成功を必須条件とする

### デプロイフロー

staticmine はライブラリ / CLI ツールであり、サービスとしての自動デプロイは行わない。リリースは以下の手動フローとする。

1. main 上で `pyproject.toml` の `version` を更新する PR を作成・マージする
2. メンテナがローカルで `git tag vX.Y.Z` を打ち、`git push --tags` する
3. GitHub Actions の `release` ワークフロー（タグ push トリガ）が以下を実施する
   - `uv build` で sdist / wheel を生成
   - GitHub Releases に成果物をアップロード
   - リリースノートをタグメッセージから自動生成
4. PyPI 公開は当面行わず、GitHub Releases からのダウンロードまたは `pip install git+https://...@vX.Y.Z` を案内する

バージョニングは **SemVer** に従う。`raw/` JSON スキーマや `content/` Markdown frontmatter の互換性を破る変更はメジャーバージョン更新とし、CHANGELOG に移行手順を明記する。

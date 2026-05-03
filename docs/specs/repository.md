# staticmine - リポジトリ構造設計

## ディレクトリ構成

```
staticmine/
├── staticmine/                # Python パッケージ（Fetcher + Converter + CLI）
│   ├── fetcher/               # Redmine REST API 取得層
│   ├── converter/             # JSON → Markdown 変換層（独自記法変換含む）
│   ├── filter/                # Project Filter（fnmatch ベース）
│   ├── config/                # YAML 設定ファイルのロード・バリデーション
│   └── cli.py                 # `staticmine` コマンドのエントリポイント
├── hugo/                      # Hugo サイトのスケルトン
│   ├── hugo.toml              # Hugo サイト設定（permalinks / taxonomies / baseURL）
│   ├── layouts/               # 既製テーマで足りない箇所の上書きテンプレート
│   ├── archetypes/            # 新規 content の雛形
│   └── static/                # 検索 UI 用の静的アセット（pagefind 連携 JS など）
├── tests/
│   ├── unit/                  # Converter ロジック中心のユニットテスト
│   ├── integration/           # fixture を入力とした end-to-end テスト
│   └── fixtures/              # サンプル raw/ JSON、期待 Markdown
├── docs/
│   └── specs/                 # 本ドキュメント群（requirements / features / architecture / repository / guidelines / glossary / index）
├── examples/
│   └── staticmine.yaml         # 設定ファイル例（include / exclude / output パス）
├── .github/
│   └── workflows/             # GitHub Actions 定義（lint / type / test / build smoke）
├── pyproject.toml             # Python パッケージ定義・依存・ツール設定（ruff / mypy / pytest）
├── uv.lock                    # uv による依存ロックファイル
├── .gitignore
├── LICENSE
└── README.md
```

### 生成物の扱い（Git 管理対象外）

以下のディレクトリはパイプラインの実行結果として生成されるものであり、リポジトリには含めない。`.gitignore` で除外する。

| ディレクトリ | 生成元 | 内容 |
|-------------|--------|------|
| `raw/` | Fetcher の出力 | Redmine からダンプした JSON および添付バイナリ。アーカイブとして運用環境側で永続保管する |
| `content/` | Converter の出力 | Markdown + YAML frontmatter |
| `public/` | Builder（Hugo + Pagefind）の出力 | 配信対象の静的 HTML と検索インデックス |

加えて以下も `.gitignore` で除外する。

- 利用者が作成する実設定ファイル（`staticmine.yaml` など。`examples/staticmine.yaml` のサンプルのみコミットする）
- Python ビルド成果物・キャッシュ（`__pycache__/`, `.pytest_cache/`, `.mypy_cache/`, `.ruff_cache/`, `dist/`, `build/`, `*.egg-info/`）
- Hugo ビルドキャッシュ（`hugo/resources/_gen/`, `hugo/.hugo_build.lock`）
- IDE / OS 由来ファイル（`.idea/`, `.vscode/`, `.DS_Store`）

## 主要ディレクトリの説明

| ディレクトリ | 説明 |
|-------------|------|
| `staticmine/` | Fetcher / Converter / Filter / Config / CLI を含む Python パッケージ。`pyproject.toml` で `staticmine` コマンドとして公開する |
| `staticmine/fetcher/` | python-redmine と requests を用いた Redmine REST API 取得処理。`raw/` への書き出しまでを担当する |
| `staticmine/converter/` | `raw/` の JSON を Markdown + frontmatter に整形し、Redmine 独自記法を静的サイト URL に書き換える |
| `staticmine/filter/` | `filter.include` / `filter.exclude` の glob 評価を提供。Fetcher / Converter / Builder ラッパーから呼び出される |
| `staticmine/config/` | YAML 設定ファイルのロード、スキーマ検証、既定値補完 |
| `hugo/` | Hugo サイトのスケルトン。`content/` は Builder 実行時に外部から注入される（`hugo/content/` は Git 管理しない） |
| `hugo/layouts/` | Issue / Wiki / プロジェクト Issue 一覧 / taxonomy など、既製テーマで不足するレイアウトの上書き |
| `tests/unit/` | Converter のリンク変換・frontmatter 生成・filter ロジック等のユニットテスト |
| `tests/integration/` | `tests/fixtures/` を入力に Converter → Hugo build までを通す smoke テスト |
| `tests/fixtures/` | 小規模な `raw/` サンプル一式と、対応する期待 Markdown / 期待 HTML |
| `docs/specs/` | 仕様駆動開発のドキュメント群 |
| `examples/` | 設定ファイルの記入例 |
| `.github/workflows/` | CI 定義 |

## 命名規則

### ファイル名

- Python ソース: snake_case（例: `wiki_link.py`, `redmine_macro.py`）
- テストファイル: `test_<対象モジュール名>.py`（例: `test_wiki_link.py`）
- Hugo テンプレート: kebab-case の `.html`（例: `single.html`, `list.html`, `issue-detail.html`）
- 設定・メタファイル: 慣習に従う（`pyproject.toml`, `hugo.toml`, `staticmine.yaml`）

### ディレクトリ名

- Python パッケージ・サブパッケージ: snake_case（例: `staticmine/converter/`）
- ドキュメント・アセット: snake_case を基本とする（例: `docs/specs/`, `tests/fixtures/`）
- Hugo 慣習に従うディレクトリ（`layouts/`, `archetypes/`, `static/`）はそのまま小文字単数形

### コード内命名

| 種類 | 規則 | 例 |
|-----|------|---|
| クラス | PascalCase | `RedmineFetcher`, `MarkdownConverter`, `ProjectFilter` |
| 関数・メソッド | snake_case | `fetch_issues`, `convert_wiki_link`, `apply_filter` |
| 変数 | snake_case | `project_identifier`, `attachment_map` |
| 定数 | UPPER_SNAKE_CASE | `DEFAULT_RAW_DIR`, `WIKI_LINK_PATTERN`, `MAX_RETRY` |
| プライベート要素 | 先頭にアンダースコア | `_build_frontmatter`, `_REDMINE_DATE_FORMAT` |
| モジュール | snake_case | `wiki_link.py`, `issue_macro.py` |

## 主要ファイル

| ファイル | 説明 |
|---------|------|
| `pyproject.toml` | Python パッケージのメタデータ、ランタイム/開発依存、`staticmine` CLI エントリポイント、ruff / mypy / pytest の設定を集約 |
| `uv.lock` | uv が生成する依存ロック。再現性のあるインストールのためコミットする |
| `staticmine/cli.py` | `staticmine fetch` / `convert` / `build` / `all` サブコマンドのディスパッチ |
| `examples/staticmine.yaml` | 設定ファイル例（Redmine 接続情報・filter・output パス・search 有効化フラグ）。実運用ファイルは Git 管理外 |
| `hugo/hugo.toml` | Hugo サイト設定。`permalinks` で Redmine 互換 URL（`/issues/<id>/` 等）を定義し、`taxonomies` で project / status / tracker / assignee を宣言 |
| `.github/workflows/ci.yml` | lint → type check → test → Hugo build smoke の CI パイプライン定義 |
| `.gitignore` | `raw/`, `content/`, `public/`, 実設定ファイル、各種キャッシュを除外 |
| `README.md` | インストール手順、CLI 使用例、設定ファイルの最小例、リンク先ドキュメント案内 |

## 依存関係管理

### Python

- パッケージマネージャ: **uv** を推奨（pip でも動作するよう `pyproject.toml` を PEP 621 準拠で記述）
- 依存定義は `pyproject.toml` の `[project]` / `[project.optional-dependencies]` に集約し、`requirements.txt` は配置しない
- ランタイム依存: `python-redmine`, `requests`, `PyYAML`, `click`（CLI フレームワーク）
- 開発依存（`[project.optional-dependencies].dev`）: `pytest`, `pytest-cov`, `ruff`, `mypy`, `vcrpy`（または `requests-mock`）
- ロックファイル `uv.lock` をコミットして再現性を確保
- サポート Python バージョン: 3.13 / 3.14（`requires-python = ">=3.13,<3.15"`）

### Hugo

- バージョン: 最新 stable の **Hugo extended** 版（SCSS 等の処理が不要であっても、テーマ互換性確保のため extended に統一）
- 配布形態: 単一バイナリ。CI では `peaceiris/actions-hugo` 等で固定バージョンをインストールし、ローカル開発ではユーザーが公式バイナリを導入する
- バージョンは CI 定義および README で明示し、ピン留めする

### Pagefind

- 配布形態: **Go バイナリ版**（`pagefind` 単一実行ファイル）を採用し、Node / npm への依存は持たない
- CI では公式リリースアーティファクトをダウンロードしてキャッシュする
- ローカル実行時もユーザーが `pagefind` バイナリを `PATH` に配置する。`staticmine build` は `pagefind` をサブプロセス起動する

### 最低バージョン

| ツール | 最低バージョン |
|--------|--------------|
| Hugo extended | >= 0.120.0 |
| Pagefind | >= 1.1.0 |
| Python | >= 3.13, < 3.15 |

### バージョン固定方針

- Python 依存は `uv.lock` で完全固定
- Hugo / Pagefind は CI 定義内でメジャー・マイナー・パッチまで明示し、アップグレード時は PR で差分を確認する
- メジャーバージョンアップ時は統合テスト（`tests/integration/`）でビルド出力の変化がないことを確認してからマージする

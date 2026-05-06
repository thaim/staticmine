# staticmine

Export Redmine projects, issues, wiki, and attachments as a static site.

## Requirements

- Python 3.13 or 3.14
- [uv](https://docs.astral.sh/uv/)
- [Hugo extended](https://gohugo.io/) 0.120 or later
- Linux / macOS

## Setup and Usage

```bash
git clone <this-repo> staticmine
cd staticmine
uv sync
cp examples/staticmine.yaml staticmine.yaml
# Edit url / api_key in staticmine.yaml

uv run staticmine fetch --config staticmine.yaml
uv run staticmine convert --config staticmine.yaml
uv run staticmine build --config staticmine.yaml
```

Local preview:

```bash
hugo serve --source hugo --contentDir ../content
```

For verification with bundled fixtures (no Redmine instance required), use `staticmine.dev.yaml` which reads `tests/fixtures/raw/` and writes to `content/dev-fixtures/` and `public/dev-fixtures/`:

```bash
uv run staticmine convert --config staticmine.dev.yaml
uv run staticmine build --config staticmine.dev.yaml
hugo serve --source hugo --contentDir ../content/dev-fixtures
```

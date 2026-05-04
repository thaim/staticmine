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

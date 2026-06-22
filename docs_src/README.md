# docs_src/

This directory is the **source for the documentation site** (built with mkdocs).

## Why symlinks?

The project has a flat structure: all `.md` files live at the repo root (e.g. `境界体系/炼气期.md`).
mkdocs requires `docs_dir` to be a subdirectory of the config file, so we use `docs_src/` as a
**virtual docs directory** containing symlinks to the real `.md` files.

## Building locally

```bash
pip install -r requirements-dev.txt
mkdocs build --strict
# → site/ directory contains the HTML
```

## Adding new pages

When you add a new `.md` file at the repo root, also create a symlink in `docs_src/`:

```bash
# 例：新增 飞升体系/飞升.md
mkdir -p docs_src/飞升体系
ln -s ../../飞升体系/飞升.md docs_src/飞升体系/飞升.md
```

Then add it to `mkdocs.yml` under `nav:`.

## Why not auto-generate symlinks?

mkdocs has no built-in symlink generation. We could write a build script, but that adds complexity.
For now, the explicit symlinks are intentional and serve as a manifest of "what's in the docs site".

## Deployment

`.github/workflows/docs.yml` builds and deploys this to GitHub Pages on every push to `main`.

URL: <https://shushuzn.github.io/xiuxian-structure/>
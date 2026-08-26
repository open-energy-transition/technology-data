# AGENTS.md — instructions for AI coding agents

`technologydata` is a Python package for managing techno-economic assumptions
(costs, efficiencies, lifetimes) for energy system models, with unit-aware
parameters, currency/inflation conversion, and data provenance tracking.
It is an open-source project (MIT for code, CC-BY-4.0 for processed data)
maintained by Open Energy Transition.

## Layout

- `src/technologydata/` — package source (src layout, installed editable).
  Core classes: `DataPackage`, `TechnologyCollection`, `Technology`,
  `Parameter`, `Source`, `SourceCollection`; equation system in
  `equations.py` with defaults in `equations_data/default_equations.yaml`
  (validated against `equations_data/default_equations.schema.json`).
- `src/technologydata/parsers/` — parsers for external data sources (e.g.
  DEA energy storage). JSON files under `parsers/*/v*/` are parser output —
  regenerate them via the parser, do not hand-edit.
- `test/` — pytest suite; shared fixtures in `test/conftest.py`, example
  data in `test/test_data/`.
- `docs/` — MkDocs documentation (Material theme, `mkdocs.yaml`).

## Setup

Requires Python ≥ 3.12 and [uv](https://docs.astral.sh/uv/):

```bash
uv sync            # creates .venv, installs package (editable) + dev/docs groups
```

Run tools via `uv run <cmd>` (or `.venv/bin/<cmd>`); no need to activate the venv.

## Testing

```bash
uv run pytest                      # full suite (coverage report is on by default)
uv run pytest -n auto              # parallel via pytest-xdist
uv run pytest test/test_technology.py -k <pattern>   # single file / test
```

Add or update tests for any behavior change. Tests are exempt from the
annotation lint rules, but keep them typed where practical.

## Linting, formatting, type checking

Pre-commit is the single entry point — prefer it over calling tools directly:

```bash
uv run pre-commit run --all-files
```

It runs ruff (lint + format), mypy in `--strict` mode, codespell, REUSE
license checks, YAML and Markdown formatting, and notebook cleanup.
Consequences for code you write:

- Full type annotations everywhere (mypy strict); no relative imports.
- Docstrings are required (pydocstyle) and use NumPy style, matching the
  existing code.
- pyupgrade targets modern syntax (e.g. `X | None`, builtin generics).

## Licensing (REUSE) — applies to every new file

The repo follows the [REUSE](https://reuse.software/) spec and CI enforces it.
Every new file needs SPDX copyright and license tags, either:

- as an inline header — copy the two comment lines from the top of any
  existing `.py` file (for Markdown, wrap them in an HTML comment), or
- via a `<filename>.license` companion file, or an entry in `REUSE.toml`
  (root `*.md`, `*.yaml`, and `docs/**` are already covered there).

Code is MIT; processed/derived data files are CC-BY-4.0.
Check with `uv run reuse lint`.

## Conventions

- Data models are pydantic v2 (`pydantic.BaseModel`, `Annotated[...,
  pydantic.Field(...)]`); validation happens at instantiation.
- Physical units use pint via the custom registry in
  `src/technologydata/utils/units.py`; currency/inflation via pydeflate;
  country/currency codes via hdx-python-country.
- `Parameter` and `Technology` track provenance — preserve source and
  transformation history when adding transformations.
- Commit messages loosely follow Conventional Commits
  (`feat(technology): ...`, `fix: ...`, `docs: ...`, `dep: ...`).

## Pull requests

- Branch from `master`; open PRs against `master` on
  `open-energy-transition/technology-data`.
- Before pushing: `uv run pre-commit run --all-files` and `uv run pytest`
  must both pass (CI runs the same; pre-commit.ci auto-fixes formatting on PRs).
- Do not commit `.venv/`, caches, `.coverage`, or notebook outputs
  (a pre-commit hook strips notebook metadata).
- Human contributor guide: `docs/contributing/instructions.md`.

## Documentation

```bash
uv run mkdocs serve    # live preview
uv run mkdocs build    # strict build, same as Read the Docs
```

Public API docs are generated with mkdocstrings from docstrings — keeping
docstrings accurate updates the docs.

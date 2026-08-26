<!--
SPDX-FileCopyrightText: technologydata contributors

SPDX-License-Identifier: MIT

-->

# Copilot instructions for `technologydata`

> Why this file exists: some Copilot surfaces (code review, Copilot Chat on
> github.com) do not yet read `AGENTS.md`. It is a thin summary for them —
> update `AGENTS.md` first and keep this file in sync.

The canonical, always-up-to-date agent instructions live in
[`AGENTS.md`](../AGENTS.md) at the repository root — follow that file.
Essentials:

- Python package (src layout, `src/technologydata/`) for techno-economic
  data for energy system models. Core classes: `DataPackage`,
  `TechnologyCollection`, `Technology`, `Parameter`, `Source`,
  `SourceCollection`; equation system in `equations.py` +
  `equations_data/default_equations.yaml`.
- Setup: `uv sync` (Python ≥ 3.12); run tools with `uv run <cmd>`.
- Tests: `uv run pytest` (fixtures in `test/conftest.py`, examples in
  `test/test_data/`). Add tests for behavior changes.
- Quality gate: `uv run pre-commit run --all-files` — ruff lint/format,
  mypy `--strict` (full type annotations, no relative imports), codespell,
  REUSE license check, NumPy-style docstrings required.
- Every new file needs SPDX license info (inline header, `.license`
  companion, or `REUSE.toml` entry). Code is MIT; processed data CC-BY-4.0.
- Parser output JSON under `src/technologydata/parsers/*/v*/` is generated —
  change the parser, don't hand-edit.
- PRs target `master`; commit messages loosely follow Conventional Commits.

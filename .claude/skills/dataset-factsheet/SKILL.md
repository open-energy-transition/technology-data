---
name: dataset-factsheet
description: Create or update the fact sheet in docs/datasets/<key>.md for a dataset shipped with technologydata, once its parser and parsed JSON exist. Use when a data source or a new version of one is added, or when a fact sheet's doctests fail after the data changed.
---

# Dataset fact sheet

<!--
SPDX-FileCopyrightText: technologydata contributors

SPDX-License-Identifier: MIT

-->

The template, section order and writing guidelines are in `docs/contributing/adding_a_dataset.md`; read it first and follow it exactly.
`docs/datasets/dea_energy_storage.md` and `docs/datasets/manual_input_usa.md` are finished examples.
This skill covers how to find each fact and how to check it.

Readers are experienced modellers and AI agents: tables and short bullets, no description of the parser code.
Only state what you verified in the code or the data; if something cannot be verified (e.g. the upstream license), write what is known and tell the user.

## Inputs

Determine, or ask the user if unclear:

- `<key>`: the `DataSourceName` value in `src/technologydata/data_accessor.py`.
- `<version>`: the directory in `src/technologydata/parsers/<key>/`.
- The parser module `src/technologydata/parsers/<key>/`, the raw file in `src/technologydata/parsers/raw/`, and `sources.json` of the version.

For a new version of an existing dataset, update the existing page instead (see the end of the checklist in `adding_a_dataset.md`).

## Where each fact comes from

| Section | Source |
|---|---|
| Front matter, At a glance | `sources.json` (title, authors, `url`, `url_archive`, `url_date`), the license in `REUSE.toml` and upstream, the parser (region, currency) |
| Years, cases, currency | the loaded data, see the snippet below |
| Available versions | `get_supported_versions()` of the parser, the parse options that reproduce the shipped JSON |
| Field mapping | the raw file's columns and the parser; trace one real row from raw value to parsed value |
| Naming conventions | the parser's cleaning functions (regexes, renames, case maps, unit replacements); one real example each |
| Assumptions and deviations | hard-coded values in the parser: fixed region, parameter filters, filled-in units, dropped rows, merged cases, row-level sources not kept |
| Known limitations | checks below |

```python
from technologydata import DataAccessor

df = DataAccessor(data_source="<key>", version="<version>").load().technologies.to_dataframe()
print(df[["region", "case"]].value_counts(), df["year"].min(), df["year"].max())
```

Run all Python from the repository root: `DataAccessor.load()` resolves the data relative to the working directory.

## Generate the code block outputs

Copy the `Accessing the data` and `Contents` blocks from the template, change only `data_source` and `version`, and pick a representative technology and parameter for `Accessing the data`.
Put a placeholder line as the expected output, then run:

```bash
uv run pytest test/test_docs.py --test-docs -k <key>
```

The failure report shows `Got:` for each block; paste that output into the page and run the test again until it passes.
Do not edit the output by hand; the tests compare it with whitespace normalised only.

## Checks for known limitations

Look for these and quantify them where cheap ("7 of about 76 parameters"):

- **Overwritten values**: parameters are stored in a dict per technology, so raw rows mapping to the same technology, case, year and parameter key overwrite each other.
  Count duplicates in the raw data after applying the parser's name cleaning.
- **Dropped data**: raw columns not mapped, rows removed by filters or failed parsing (compare raw row count with parsed parameter count).
- **Heterogeneous units**: visible in the `Parameters` table when one parameter has several reference units.
- **Order of operations** that loses precision, such as rounding before unit scaling.
- **Provenance**: whether row-level sources are kept, whether an archived copy of the source exists.

## Verify Reproduce

The documented `parse()` call must reproduce the shipped files.
It overwrites them, so check the working tree is clean for that directory first:

```bash
git status --short src/technologydata/parsers/<key>/
uv run python -c 'from technologydata import DataAccessor; DataAccessor(data_source="<key>", version="<version>").parse(input_file_name="<file>", num_digits=3)'
git diff --stat src/technologydata/parsers/<key>/
git checkout -- src/technologydata/parsers/<key>/
```

Only a trailing-newline difference is acceptable; otherwise adjust the documented options until the output matches.
Never use `archive_source=True` here: it calls the Wayback Machine and rewrites `sources.json`.

## Wire up and check

1. Add the page to the `Datasets` nav in `mkdocs.yaml` and a row to the table in `docs/datasets/index.md`.
2. If a user guide page `docs/user_guide/<key>_parser.md` exists, keep it to structure and usage and link to the fact sheet's `#reproduce`.
3. Run `uv run pytest test/test_docs.py --test-docs` and `uv run pre-commit run --all-files`.
   Codespell may flag domain abbreviations; add real terms to `.codespell.ignore`.
4. Report to the user: anything not verified, and parser problems found (such as overwritten values) as candidates for issues.

# Adding a dataset

<!--
SPDX-FileCopyrightText: technologydata contributors

SPDX-License-Identifier: MIT

-->

Every dataset shipped with `technologydata` has a fact sheet in `docs/datasets/`.
Fact sheets are short and structured information: what the data is, where it comes from, how to load and reproduce it, what it contains, and which important choices made for parsing the original data.

## Checklist

0. Clone the repository.
1. Add the raw file to `src/technologydata/parsers/raw/<key>/` and its license to `REUSE.toml`.
2. Add a parser under `src/technologydata/parsers/<key>/` and register `<key>` in `DataSourceName` and `DataAccessor.parse()`.
3. Run the parser and commit the output in `src/technologydata/parsers/<key>/<version>/`.
4. Copy the template below to `docs/datasets/<key>.md` and fill it in.
5. Add the fact sheet to the `Datasets` section in `mkdocs.yaml` and a row to `docs/datasets/index.md`.
6. Run `uv run pytest test/test_docs.py --test-docs`.
   The code blocks of every fact sheet are run as doctests, and their output must match the page.
   For the `Contents` section, run the code once and paste its output below it.

When the data of a dataset changes, the doctest will fail because the output of the code will no longer match the output in the documentation;
paste the new output into the fact sheet then to resolve.
When a new version is added, add a row to the `Available versions` table, add the version to the front matter and update `Accessing the data` and `Contents` to the new version.

!!! tip "Delegate work to AI agents"
    Once the parser and the parsed data exist, writing the fact sheet and the parser user guide page can be delegated to an AI agent.
    The repository contains the skill [`dataset-factsheet`](https://github.com/open-energy-transition/technology-data/blob/master/.claude/skills/dataset-factsheet/SKILL.md) with step-by-step instructions: where each fact comes from, how to generate the tables, how to write the parser pages and which checks to run.
    Claude Code picks it up automatically (ask e.g. "create the fact sheet for `<key>`" or run `/dataset-factsheet`); other agents are pointed to it by `AGENTS.md`.
    Always review the result created by AI; other people want to build their work on it.
    Pay particular attention to the assumptions, limitations and license.

## Guidelines

- Keep the fact sheet concise: tables and short bullets, no step-by-step description of the parser code - this should go into the parser itself.
- The front matter is the machine-readable summary hidden in the online documentation; keep it in sync with the `At a glance` table.
- *Assumptions and deviations* are choices that make the parsed data differ from the source (filters, fixed regions, filled-in units, merged cases).
- *Known limitations* are what gets lost or can mislead (dropped or overwritten values, heterogeneous units, missing sources).
- Code blocks meant to be tested use ` ``` py <code> ``` ` with `>>>` prompts. Code that should not be automatically tested uses ` ```python <code> ``` `.

## Template

````markdown
---
id: <key>
name: <Dataset name>
description: <One sentence: what the dataset covers.>
publisher: <Organisation>
upstream_url: <link to the original data>
documentation_url: <link to the documentation, if any>
license: <SPDX identifier>
versions: [<version>]
region: <region code set by the parser>
raw_file: src/technologydata/parsers/raw/<key>/<file>
parser: technologydata.parsers.<key>.<ParserClass>
---

# <Dataset name>

<!--
SPDX-FileCopyrightText: technologydata contributors

SPDX-License-Identifier: MIT

-->

<Two or three sentences: publisher, technologies covered, scope.>

## At a glance

| | |
|---|---|
| Package key | `<key>` |
| Publisher | <Organisation> |
| Original data | [<name>](<url>) ([archived](<url_archive from sources.json>)) |
| Documentation | [<name>](<url>) |
| License | <license, attribution requirements> |
| Region | `<region>` |
| Years | <first>–<last> |
| Cases | <case values and their meaning> |
| Currency | `<CUR_YEAR>` |
| Raw format | <format, sheet> |
| Parser | [`<ParserClass>`](#parser-api) |

## Available versions

| Version key | Upstream release | Raw file | Parse options | Status |
|---|---|---|---|---|
| `<version>` | <upstream release, date> | `<file>` | `num_digits=3`, … | latest |

## Accessing the data

``` py
>>> from technologydata import DataAccessor
>>> data = DataAccessor(data_source="<key>", version="<version>").load()
>>> tech = data.technologies.get(name="<name>", case="<case>")[0]
>>> print(tech.parameters["<parameter>"])
<output>
```

See the [tutorial](../tutorial/index.md) for filtering, unit and currency conversion.

## Contents

### Technologies

``` py
>>> import pandas as pd
>>> techs = DataAccessor(data_source="<key>", version="<version>").load().technologies
>>> def join(values):
...     return ", ".join(sorted({str(v) for v in values} - {"None"}))
>>> print(
...     techs.to_dataframe()
...     .groupby(["name", "detailed_technology"], as_index=False)
...     .agg(cases=("case", join), years=("year", join))
...     .to_markdown(index=False)
... )
<paste output>
```

### Parameters

`entries` counts the technology entries (one per name, case and year) that carry the parameter.

``` py
>>> params = pd.DataFrame(
...     [(key, str(p.units), str(p.carrier)) for t in techs for key, p in t.parameters.items()],
...     columns=["parameter", "units", "carriers"],
... )
>>> print(
...     params.groupby("parameter", as_index=False)
...     .agg(units=("units", join), carriers=("carriers", join), entries=("units", "size"))
...     .to_markdown(index=False)
... )
<paste output>
```

## Field mapping

| Raw column | Example raw value | Schema field | Example parsed value |
|---|---|---|---|
| `<column>` | `<value>` | `Technology.name` | `<value>` |
| — | — | `Technology.region` | `<region>` |
| `<column>` | | not kept | |

## Naming conventions

- **Technology names**: <how raw names are normalised, with one example>
- **Parameter keys**: <…>
- **Cases**: <…>
- **Units**: <…>

## Assumptions and deviations from the source

- **<Topic>**: <choice made by the parser and its effect>

## Reproduce

Run from the root of a repository checkout.
The parser overwrites the files shipped with the package.

```python
from technologydata import DataAccessor

DataAccessor(data_source="<key>", version="<version>").parse(
    input_file_names=["<file>"],
    num_digits=3,
)
```

With `archive_source=False` (the default) the existing `sources.json` is reused; `archive_source=True` archives the source on the Wayback Machine and rewrites `sources.json`.

## Known limitations

- **<Topic>**: <what is lost or can mislead>

## Citation

> <Recommended citation of the original data>

License: [<SPDX identifier>](<link to the license text>), if known

Please also cite `technologydata`, see [Citing](../index.md#citing).

## See also

- [<Parser> Parser](../user_guide/<key>_parser.md) (user guide)
- [Data Accessor](../user_guide/data_accessor.md)

## Parser API

The parser is only needed to reproduce or update the dataset, see [Reproduce](#reproduce); loading the data only needs `DataAccessor.load()`.
The dispatcher selects the parser of the requested version.

::: technologydata.parsers.<key>.<ParserClass>
    options:
      heading_level: 3

::: technologydata.parsers.<key>.<version_module>.<VersionParserClass>
    options:
      heading_level: 3
````

# Writing a parser

<!--
SPDX-FileCopyrightText: technologydata contributors

SPDX-License-Identifier: MIT

-->

A parser turns the raw file of a data source into the `technologies.json` and `sources.json` files shipped with `technologydata`.
It is only run to create or update a dataset; users load the result with `DataAccessor.load()`.
This page describes how a parser is structured; [Adding a dataset](adding_a_dataset.md) lists all steps from the raw file to the fact sheet.

The DEA energy storage parser in `src/technologydata/parsers/dea_energy_storage/` is the reference example for a single raw file, see its [fact sheet](../datasets/dea_energy_storage.md#parser-api) for the rendered API.
The legacy input data parser in `src/technologydata/parsers/legacy_input_data/` reads two raw files and uses the unit helpers in `src/technologydata/parsers/commons.py`.

## Layout

| Path | Content |
|---|---|
| `src/technologydata/parsers/raw/<key>/` | the raw file(s), with their license in `REUSE.toml` |
| `src/technologydata/parsers/<key>/__init__.py` | the dispatcher class, e.g. `DeaEnergyStorageParser` |
| `src/technologydata/parsers/<key>/parser_<version>.py` | one parser class per dataset version, e.g. `DeaEnergyStorageV10Parser` in `parser_v10.py` |
| `src/technologydata/parsers/<key>/<version>/` | the output: `technologies.json` and `sources.json` |

## Dispatcher

The dispatcher maps each supported version to its parser class and delegates `parse()` to it:

```python
class MyDatasetParser:
    def __init__(self) -> None:
        self._parsers: dict[str, type[ParserBase]] = {
            "v1": MyDatasetV1Parser,
        }

    def get_supported_versions(self) -> list[str]:
        return list(self._parsers.keys())

    def parse(self, version, input_path, num_digits, archive_source, filter_params, export_schema) -> None:
        ...  # raise ValueError for an unsupported version, else call the version parser
```

A new version of a dataset is a new parser class and a new entry in `_parsers`; existing versions and their output stay unchanged.

## Version parser

Each version parser subclasses `ParserBase` from `technologydata.parsers.data_parser_base` and implements

```python
def parse(self, input_path, num_digits, archive_source, **kwargs) -> None:
```

- `input_path`: a `pathlib.Path` for one raw file or a list of paths for several; validate what the version expects.
- `num_digits`: rounding of the values.
- `archive_source`: if `True`, build the `Source` objects, archive them with `Source.ensure_in_wayback()` and write `sources.json`; otherwise read the existing `sources.json`.
- `kwargs`: `filter_params` and `export_schema`, both booleans; document it if a parser ignores one.

The parser builds `Technology` objects with their `Parameter`s, collects them in a `TechnologyCollection` and writes it with `to_json()` to `<key>/<version>/technologies.json`.
The output paths are built from the current working directory, so parsers are run from the root of a repository checkout.

## Register the data source

In `src/technologydata/data_accessor.py`:

1. add `<key>` to `DataSourceName`,
2. import the dispatcher and select it for `<key>` in `DataAccessor.parse()`.

`DataAccessor.parse(input_file_names=[...])` then looks up the raw files in `parsers/raw/<key>/` and passes one path, or a list of paths for several files, to the dispatcher.

## Conventions for the parsed data

- **Units** must be understood by the package's unit registry; currencies carry their year, e.g. `EUR_2020` (use `Commons.update_unit_with_currency_year()` if the year is in a separate column).
- **Carriers** and **heating values** use the names of the package registries (`src/technologydata/utils/carriers.txt`); rename aliases of the raw data in the parser rather than adding them to the registry.
- A carrier or heating value belongs to the part of the unit it describes: in the denominator it is inverted (`EUR/MWh_H2` → carrier `1 / hydrogen`, heating value `1 / lower_heating_value`); electricity and heat have no heating value.
- **Region** and **case** are strings; use a fixed value if the raw data has none, and document it in the fact sheet.
- **Rounding** happens once, after all unit conversions, so small converted values keep their significant digits.

## Docstrings

The docstrings of the dispatcher and the version parsers are rendered in the `Parser API` section of the dataset's fact sheet, which is the only per-parser documentation.
Keep them complete and in sync with the code: parameters and their types, what the parser writes where, raised errors, and which options it ignores.

## Tests

- Unit tests for the cleaning and conversion functions, e.g. `test/test_dea_energy_storage_v10.py`.
- A parse-and-load test in `test/test_parser_data_accessor.py` that runs `DataAccessor.parse()` with the documented options and checks the loaded `DataPackage`.
  It writes to the shipped files in place; restore them with `git checkout` after running the tests.

## Next step

Run the parser, commit its output, and write the fact sheet as described in [Adding a dataset](adding_a_dataset.md).

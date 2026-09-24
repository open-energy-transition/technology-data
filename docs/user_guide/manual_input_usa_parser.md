# Manual Input USA Parser

`ManualInputUsaParser` produces the `manual_input_usa` dataset from the `manual_input_usa.csv` file of PyPSA technology-data.
For what the dataset contains and which choices the parser makes, see the [fact sheet](../datasets/manual_input_usa.md).

## Structure

- `ManualInputUsaParser` dispatches to a version-specific parser; `get_supported_versions()` lists the versions it knows (currently `v0.13.4`).
- `ManualInputUSAV0134Parser` reads the CSV, splits compound units into unit, carrier and heating value, and writes `technologies.json` and `sources.json` to `src/technologydata/parsers/manual_input_usa/v0.13.4/`.

## Usage

The recommended entry point is `DataAccessor.parse()`, see [Reproduce](../datasets/manual_input_usa.md#reproduce).
The parser can also be called directly:

```python
import pathlib

from technologydata.parsers.manual_input_usa import ManualInputUsaParser

ManualInputUsaParser().parse(
    version="v0.13.4",
    input_path=pathlib.Path("src/technologydata/parsers/raw/manual_input_usa.csv"),
    num_digits=3,
    archive_source=False,
    filter_params=False,
    export_schema=False,
)
```

- `num_digits`: number of decimals values are rounded to.
- `archive_source`: archive the source on the Wayback Machine and rewrite `sources.json`; otherwise the existing `sources.json` is reused.
- `filter_params`: required by the dispatcher, ignored by this parser.
- `export_schema`: also export the JSON schemas of the data models.

## API Reference

See the [API documentation](../api/manual_input_usa_parser.md).

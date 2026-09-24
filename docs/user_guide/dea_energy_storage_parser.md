# DEA Energy Storage Parser

`DeaEnergyStorageParser` produces the `dea_energy_storage` dataset from the Danish Energy Agency's energy storage catalogue.
For what the dataset contains and which choices the parser makes, see the [fact sheet](../datasets/dea_energy_storage.md).

## Structure

- `DeaEnergyStorageParser` dispatches to a version-specific parser; `get_supported_versions()` lists the versions it knows (currently `v10`).
- `DeaEnergyStorageV10Parser` reads the `alldata_flat` sheet of the Excel file, cleans names, years, parameters and units, and writes `technologies.json` and `sources.json` to `src/technologydata/parsers/dea_energy_storage/v10/`.

## Usage

The recommended entry point is `DataAccessor.parse()`, see [Reproduce](../datasets/dea_energy_storage.md#reproduce).
The parser can also be called directly:

```python
import pathlib

from technologydata.parsers.dea_energy_storage import DeaEnergyStorageParser

DeaEnergyStorageParser().parse(
    version="v10",
    input_path=pathlib.Path("src/technologydata/parsers/raw/Technology_datasheet_for_energy_storage.xlsx"),
    num_digits=3,
    archive_source=False,
    filter_params=True,
    export_schema=False,
)
```

- `num_digits`: number of decimals values are rounded to.
- `archive_source`: archive the source on the Wayback Machine and rewrite `sources.json`; otherwise the existing `sources.json` is reused.
- `filter_params`: keep only a predefined set of parameters.
- `export_schema`: also export the JSON schemas of the data models.

## API Reference

See the [API documentation](../api/dea_energy_storage_parser.md).

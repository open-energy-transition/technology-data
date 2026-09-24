# Legacy Input Data Parser

The `LegacyInputDataParser` is responsible for parsing data from the `raw/legacy_input_data/usa.csv` and `raw/legacy_input_data/other.csv` datasets. It is designed to handle different versions of the dataset, with a specific implementation for `v0.13.4`.

## Main Parser: `LegacyInputDataParser`

The main parser, `LegacyInputDataParser`, acts as a dispatcher that selects the appropriate version-specific parser based on the user's request.

### Key Features

-   **Version Dispatching**: Dynamically selects the correct parser for a given dataset version (e.g., `v0.13.4`).
-   **Supported Versions**: Provides a method to get a list of all supported dataset versions.
-   **Multi-file Processing**: Parses both `usa.csv` and `other.csv` files, tagging data with appropriate regions.

### Usage

While it is possible to use the parser directly, the recommended way to access the data is through the `DataAccessor` class, which provides a higher-level interface and handles the parsing process internally. See the [Data Accessor](./data_accessor.md) documentation for more details.

If you need to use the parser directly, you can instantiate `LegacyInputDataParser` and call the `parse` method with the desired version and other parameters.

```python
from technologydata.parsers.legacy_input_data import LegacyInputDataParser
import pathlib

# Instantiate the main parser
legacy_input_data_parser = LegacyInputDataParser()

# Define parameters
version = "v0.13.4"
input_files = [
    pathlib.Path("path/to/your/usa.csv"),
    pathlib.Path("path/to/your/other.csv")
]
num_digits = 3
archive_source = False
filter_params = True
export_schema = False

# Parse the data
legacy_input_data_parser.parse(
    version=version,
    input_path=input_files,
    num_digits=num_digits,
    archive_source=archive_source,
    filter_params=filter_params,
    export_schema=export_schema,
)
```

## Version-Specific Parser: `LegacyInputDataV0134Parser`

The `LegacyInputDataV0134Parser` is a concrete implementation that handles version `v0.13.4` of the `raw/legacy_input_data/usa.csv` and `raw/legacy_input_data/other.csv` datasets. It inherits from `ParserBase` and contains the logic for reading, cleaning, and transforming the raw data from both files.

### Key Responsibilities

-   **Data Loading**: Reads data from both CSV files (usa.csv and other.csv).
-   **Region Tagging**:
  -   USA data is tagged with `region='USA'`
  -   Other data is tagged with `region='not_available'`
-   **Data Cleaning**:
  -   Handles missing values in the `scenario` column
  -   Normalizes malformed units:
    -   `tCO2` → `t_CO2`
    -   `MWHh_el` → `MWh_el`
    -   `MWhth` → `MWh_th`
    -   `kWel` → `kW_el`
    -   `MWh_thdh` → `MWh_th`
    -   Removes `,dp` suffix from units
  -   Converts distance units: `1000km` → `km` (dividing values by 1000)
  -   Converts `per unit` → `%` (multiplying values by 100)
  -   Includes `currency_year` in the `unit` column where applicable
-   **Data Transformation**:
  -   Extracts standardized units, carriers, and heating values from complex unit strings using the `_extract_units_carriers_heating_value` method
  -   Supports 12 different unit patterns including:
    -   Currency with power/energy carriers
    -   Energy ratios with carriers
    -   Mass/energy ratios
    -   Standalone mass carriers (e.g., `t_CH4`)
    -   Energy to mass with carrier (e.g., `MWh/t_CO2`)
    -   Distance-based units (e.g., `EUR/(t_CO2/h)/km`)
-   **Object Creation**: Builds a `TechnologyCollection` from the processed data using the `_build_technology_collection` method
-   **Output Generation**: Exports the final `TechnologyCollection` and `SourceCollection` to JSON files

### `parse` Method

The `parse` method orchestrates the entire parsing process for the `v0.13.4` dataset.

**Parameters:**

-   `input_path` (`list[pathlib.Path]`): List of paths to the raw input CSV files (must contain both usa.csv and other.csv).
-   `num_digits` (`int`): Number of significant digits for rounding numerical values.
-   `archive_source` (`bool`): If `True`, archives the data source on the Wayback Machine.
-   `**kwargs`:
  -   `export_schema` (`bool`): If `True`, exports the Pydantic schema for the data models.

The processed data is saved to `technologies.json` and `sources.json` in the `src/technologydata/parsers/legacy_input_data/v0.13.4/` directory.

## API Reference

Please refer to the [API documentation](../api/legacy_input_data_parser.md) for detailed information on the class methods and attributes.

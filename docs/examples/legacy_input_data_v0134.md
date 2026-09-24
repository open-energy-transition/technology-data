# Legacy Input Data Parser Documentation

<!--
SPDX-FileCopyrightText: technologydata contributors

SPDX-License-Identifier: MIT

-->

## Overview

!!! note
    This example refers specifically to **version 0.13.4** (`v0134`) of the Legacy Input Data datasets.

The Legacy Input Data parser demonstrates a data-cleaning and transformation pipeline for converting manually curated, tabular data into the `technologydata` schema files `technologies.json` and `sources.json`. The parser is implemented in `../../src/technologydata/parsers/legacy_input_data`.

## Dataset Description

The original dataset is a manually curated CSV file containing technology parameters available from the [PyPSA technology-data repository](https://github.com/PyPSA/technology-data/blob/v0.13.4/inputs/US/manual_input_usa.csv) and [PyPSA technology-data repository](https://github.com/PyPSA/technology-data/blob/v0.13.4/inputs/manual_input.csv). The raw source files are included in the repository at `../../src/technologydata/parsers/raw/legacy_input_data`.

The dataset is in CSV format and includes a flat table of technology parameters for various energy technologies relevant to the USA context. Columns include `technology`, `parameter`, `year`, `value`, `unit`, `currency_year`, `source`, `further_description`, `financial_case`, and `scenario`. Rows are individual parameter records (parameter value + unit + context) for technologies with different scenarios and financial cases.

## Parser description

The parser is articulated in the following steps.

### Read the raw data

The parser reads both raw CSV files available at `../../src/technologydata/parsers/raw/legacy_input_data` into separate `pandas` dataframes:

- `usa.csv`: Contains USA-specific technology data, tagged with `region='USA'`
- `other.csv`: Contains rest-of-world technology data, tagged with `region='not_available'`

Both files use `pandas.read_csv(..., dtype=str, na_values="None")`. All entries are handled as strings initially except for the `value` column which is converted to float. After data cleaning and normalization, the two dataframes are concatenated into a single dataframe for processing.

### Data cleaning, validation and dealing with missing/null values

The data cleaning and validation happens with the following steps.

**Unit normalization**: The parser first normalizes malformed unit strings before processing:

- `tCO2` → `t_CO2` (adds missing underscore)
- `MWHh_el` → `MWh_el` (fixes capitalization)
- `MWhth` → `MWh_th` (adds missing underscore)
- `kWel` → `kW_el` (adds missing underscore)
- `MWh_thdh` → `MWh_th` (fixes typo)
- Removes `,dp` suffix from units (design point notation)

**Unit extraction**: Function `_extract_units_carriers_heating_value()` extracts standardized units, carriers, and heating values from input unit strings. This function maps complex unit representations to simplified unit, carrier, and heating value combinations using regex pattern matching across 12 different patterns. Examples include:

- `USD_2022/MW_FT` → unit: `USD_2022/MW`, carrier: `1/FT`, heating_value: `1/LHV`
- `MWh_H2/MWh_FT` → unit: `MWh/MWh`, carrier: `H2/FT`, heating_value: `LHV`
- `MWh_el/MWh_FT` → unit: `MWh/MWh`, carrier: `el/FT`, heating_value: `LHV`
- `t_CO2/MWh_FT` → unit: `t/MWh`, carrier: `CO2/FT`, heating_value: `LHV`
- `USD_2022/kWh_H2` → unit: `USD_2022/kWh`, carrier: `1/H2`, heating_value: `LHV`
- `USD_2023/t_CO2/h` → unit: `USD_2023/t/h`, carrier: `1/CO2`, heating_value: `None`
- `EUR/(tCO2/h)/km` → unit: `EUR/t/h/km`, carrier: `1/CO2`, heating_value: `None`
- `MWh_el/t_CO2` → unit: `MWh/t`, carrier: `el/CO2`, heating_value: `LHV`
- `MWh_th/t_CO2` → unit: `MWh/t`, carrier: `thermal/CO2`, heating_value: `LHV`
- `t_CH4` → unit: `t`, carrier: `CH4`, heating_value: `None` (standalone mass carrier)
- `MWh/t_CO2` → unit: `MWh/t`, carrier: `1/CO2`, heating_value: `LHV` (energy to mass with carrier)

**Missing values**: The parser fills missing values in the `scenario` column with `"not_available"`.

**Unit conversions**: The parser applies the following conversions:

- Convert `1000km` to `km` and divide the corresponding `value` by 1000.0, rounding to `num_digits` decimals.
- Convert `per unit` to `%` and multiply the corresponding `value` by 100.0, rounding to `num_digits` decimals.

**Currency year integration**: Function `Commons.update_unit_with_currency_year(unit, currency_year)` appends `currency_year` information to currency units when present. This is because `technologydata` follows the currency pattern `\b(?P<cu_iso3>[A-Z]{3})_(?P<year>\d{4})\b`, as for example `USD_2022`.

### Populate and export the source and technology collections

Function `_build_technology_collection()`:

- if `archive_source` is set, constructs `Source` objects for both the USA and other datasets, calls `ensure_in_wayback()` on each, and writes `sources.json`; otherwise reads an existing `sources.json`.
- groups the cleaned DataFrame by `scenario`, `year`, `technology`, `region`.
- for each group, builds a dictionary of `Parameter` objects (each with `magnitude`, `sources`, and optionally `carrier`, `heating_value`, `units`, `note`).
- captures the `financial_case` value from rows within each group to combine with `scenario`.
- creates a `case` value by combining `scenario` and `financial_case` in the format `"{scenario} - {financial_case}"` when `financial_case` is present; otherwise uses `scenario` alone.
- creates a `Technology` object for each group, with `name` = `technology`, `detailed_technology` = `technology`, `year` = `year`, `region` = region from the DataFrame (`"USA"` for USA data, `"not_available"` for other data), `case` = combined case value, and collects them into a `TechnologyCollection` object.
- writes the `TechnologyCollection` object to a `technologies.json`.

## Running the parser

### Execution instructions

The parser is run using the `DataAccessor` class. You need to create an instance of `DataAccessor` with the desired `data_source` and `version`, and then call the `parse()` method.

Here is an example of how to run the parser from a Python script:

```python
from technologydata import DataAccessor

# Create an accessor for the version to be parsed
parser_accessor = DataAccessor(
    data_source="legacy_input_data",
    version="v0.13.4"
)

# Run the parser with desired options
parser_accessor.parse(
    input_file_names=["usa.csv", "other.csv"],
    num_digits=3,
    archive_source=True,
    export_schema=True,
)

# You can also parse different CSV files with the same structure
# parser_accessor.parse(
#     input_file_names=["usa_alternative.csv", "other_alternative.csv"],
#     num_digits=3,
#     ...
# )
```

The `parse` method accepts the following arguments:

- `input_file_names` (list of str): A list of CSV file names located in `src/technologydata/parsers/raw/legacy_input_data/`. The first file should contain USA-specific data, and the second should contain rest-of-world data. This allows flexibility to parse alternative files with the same structure.
- `num_digits` (int, default 4): Number of decimals for rounding numeric values.
- `archive_source` (bool, default False): Whether to store the source on the Wayback Machine.
- `filter_params` (bool, default False): Whether to filter parameters (not used by this parser).
- `export_schema` (bool, default False): Whether to export Pydantic schemas.

### Outputs

The parser generates the following outputs inside `../../src/technologydata/parsers/legacy_input_data`:

- `technologies.json`
- `sources.json`

If `export_schema` is set to `True`, the Pydantic schema files are generated and moved to `src/technologydata/parsers/schemas/`.

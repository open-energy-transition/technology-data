# Danish Energy Agency Parser Documentation


## Overview
The Danish Energy Agency (DEA) data parser `dea_energy_storage.py` demonstrates a full data-cleaning and transformation pipeline for converting raw tabular data into the `technologydata` schema`technologies.json` and `sources.json`. The parser is implemented in `src/technologydata/package_data/dea_energy_storage/dea_energy_storage.py`.

## Dataset Description


Original dataset: https://ens.dk/media/6589/download

Raw source file included in the repository: `src/technologydata/package_data/raw/Technology_datasheet_for_energy_storage.xlsx`

Dataset description
- The Excel file contains a flat table (sheet `alldata_flat`) of technology parameters for a range of energy storage technologies.
- Typical columns include: `Technology`, `ws`, `par` (parameter name), `val` (value), `unit`, `year`, `est` (case/estimate), `priceyear`, plus metadata columns such as `cat`, `ref`, `note`.
- Rows are individual parameter records (parameter value + unit + context) for technologies and estimation cases.

Step‑by‑step description of the code

- Argument parsing
  - `parse_input_arguments()` defines and parses CLI flags:
    - `--num_digits` (int, default 4) — number of decimals used when rounding numeric values.
    - `--store_source` (boolean flag) — whether to store the source on the Wayback Machine.
    - `--filter_params` (boolean flag) — whether to limit exported parameters to a fixed allowed set.
    - `--export_schema` (boolean flag) — export JSON schema files.

- Read raw data
  - The script reads `src/technologydata/package_data/raw/Technology_datasheet_for_energy_storage.xlsx`, sheet `alldata_flat`, using `pandas.read_excel(..., dtype=str)` so all cells are handled as strings initially.

- Initial cleaning and validation
  - `drop_invalid_rows(df)`:
    - Validates required columns are present.
    - Drops rows with missing/null or empty critical fields (`Technology`, `par`, `val`, `year`).
    - Keeps rows where `year` contains a 4-digit year and `val` contains numeric characters and no comparator symbols (`<`, `>`, `≤`, `≥`).
    - Returns a cleaned DataFrame.

- Normalize text fields
  - `clean_technology_string()`:
    - Removes leading 3-digit numeric codes (e.g., `143a`), trims whitespace and lower-cases the string for consistent matching.
  - `clean_parameter_string()`:
    - Removes leading hyphens, removes text inside square brackets (units/notes), collapses extra spaces and lower-cases the parameter name.
  - `clean_est_string()`:
    - Normalizes the `est` column (casefold and replaces `ctrl` with `control`).

- Year and numeric formatting
  - `extract_year()`:
    - Extracts the first sequence of digits from the `year` string and converts it to an integer.
  - `format_val_number(value, num_decimals)`:
    - Parses numeric formats including comma decimal separators and scientific notation variants (e.g., `×10`), converts to float and rounds to `num_decimals`.

- Units standardization
  - `standardize_units([par, unit])`:
    - Completes missing units based on parameter name (e.g., capacity → `MWh`) via a parameter-to-unit map.
    - Replaces known incorrect unit strings (several substitutions implemented).
  - `Commons.update_unit_with_currency_year(unit, priceyear)`:
    - If present, appends `priceyear` information to currency units (done via `Commons` helper in the library).
  - Post-processing corrections:
    - Convert `MEUR_2020` and `kEUR_2020`/`KEUR_2020` to `EUR_2020` and scale numeric `val` accordingly (×1e6 or ×1e3).
    - Specific unit fixes (example: `mol/s/m/MPa1/2` → `mol/s/m/Pa` with value scaling).

- Parameter renaming and filtering
  - Certain `par` values (e.g., `energy storage capacity for one unit`, `tank volume of example`) are normalized to `capacity`.
  - `filter_parameters(df, filter_flag)`:
    - If `filter_flag` is true, keeps only an allowed set of parameters (e.g., `technical lifetime`, `fixed o&m`, `specific investment`, `variable o&m`, `charge efficiency`, `discharge efficiency`, `capacity`).
    - Otherwise returns the full set.

- Build and export collection objects
  - `build_technology_collection(df, sources_path, store_source, output_schema)`:
    - If `store_source` is set, constructs a `Source` object for the DEA dataset, calls `ensure_in_wayback()` and writes `sources.json`; otherwise reads existing `sources.json`.
    - Groups the cleaned DataFrame by `est`, `year`, `ws`, `Technology`.
    - For each group, builds a dictionary of `Parameter` objects (each with `magnitude`, `units`, `sources`, `provenance`).
    - Creates a `Technology` for each group (`name` = `ws`, `detailed_technology` = `Technology`, `year`, `region` = `EU`, `case` = `est`) and collects them into a `TechnologyCollection`.
    - Writes `technologies.json` using the library `to_json()` helpers.
  - Optional schema export:
    - If `--export_schema` is used, schema files produced during export are moved into `src/technologydata/package_data/schemas`.

Running the example
- From repository root:
  - Basic run: `python src/technologydata/package_data/dea_energy_storage/dea_energy_storage.py`
  - Example with options:
    - `--num_digits 3 --store_source --filter_params --export_schema`

Outputs
- `src/technologydata/package_data/dea_energy_storage/technologies.json` (produced by the script).
- `src/technologydata/package_data/dea_energy_storage/sources.json` (produced or read).
- Optional schema files moved to `src/technologydata/package_data/schemas` when `--export_schema` is used.


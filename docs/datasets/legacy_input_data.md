---
id: legacy_input_data
name: PyPSA technology-data manual inputs for the USA and Rest of World
description: Costs and efficiencies for electrolysis, batteries, CCS power plants, Fischer-Tropsch and direct air capture, compiled in PyPSA technology-data.
publisher: PyPSA technology-data contributors
upstream_url: https://github.com/PyPSA/technology-data/blob/v0.13.4/inputs/US/manual_input_usa.csv, https://github.com/PyPSA/technology-data/blob/v0.13.4/inputs/manual_input.csv
license: CC-BY-4.0
versions: [v0.13.4]
region: USA, Rest of World
raw_file: src/technologydata/parsers/raw/legacy_input_data/usa.csv, src/technologydata/parsers/raw/legacy_input_data/other.csv
parser: technologydata.parsers.legacy_input_data.LegacyInputDataParser
---

# PyPSA technology-data legacy input data

!!! info "Renamed dataset"
    This dataset was previously known as `manual_input_usa`. As of this version, it has been renamed to `legacy_input_data` to better reflect that it contains data for both USA and Rest of World regions. The data source key is now `"legacy_input_data"` instead of `"manual_input_usa"`.

<!--
SPDX-FileCopyrightText: technologydata contributors

SPDX-License-Identifier: MIT

-->

Hand-curated CSV files from [PyPSA technology-data](https://github.com/PyPSA/technology-data) with parameters for electrolysers, battery storage, CCS power plants, Fischer-Tropsch synthesis, direct air capture and hydrogen storage for USA and Rest of World regions.
The values are compiled from NREL ATB 2024, ICCT IRA e-fuels assumptions, JRC-EU-TIMES and Stöckl et al. (2021).

## At a glance

| | |
|---|---|
| Package key | `legacy_input_data` (formerly `manual_input_usa`) |
| Publisher | PyPSA technology-data contributors |
| Original data | [`inputs/US/manual_input_usa.csv`](https://github.com/PyPSA/technology-data/blob/v0.13.4/inputs/US/manual_input_usa.csv), [`inputs/manual_input.csv`](https://github.com/PyPSA/technology-data/blob/v0.13.4/inputs/manual_input.csv) (no archived copy) |
| Underlying sources | [NREL ATB 2024](https://atb.nrel.gov/electricity/2024/data), ICCT IRA e-fuels assumptions, [JRC-EU-TIMES](https://zenodo.org/records/3544900), [Stöckl et al. (2021)](https://doi.org/10.48550/arXiv.2005.03464) |
| License | CC-BY-4.0 |
| Region | `USA`, `Rest of World` (set by the parser) |
| Years | 2020–2050 |
| Cases | NREL ATB scenario and financial case, e.g. `Moderate - Market`; `not_available` for rows without a scenario |
| Currency | `USD_2022`, `USD_2023` |
| Raw format | CSV |
| Parser | [`LegacyInputDataParser`](../api/legacy_input_data_parser.md) |

## Available versions

| Version key | Upstream release | Raw files | Parse options | Status |
|---|---|---|---|---|
| `v0.13.4` | PyPSA technology-data v0.13.4 | `usa.csv`, `other.csv` | `num_digits=3` | latest |

## Accessing the data

``` py
>>> from technologydata import DataAccessor
>>> usa = DataAccessor(data_source="legacy_input_data", version="v0.13.4").load()
>>> fischer_tropsch = usa.technologies.get(name="Fischer-Tropsch", year=2020)[0]
>>> print(fischer_tropsch.parameters["hydrogen-input"])
1.43 dimensionless, carrier=hydrogen / fischer_tropsch, heating_value=lower_heating_value
```

See the [tutorial](../tutorial/index.md) for filtering, unit and currency conversion.

## Contents

### Technologies

``` py
>>> import pandas as pd
>>> techs = DataAccessor(data_source="legacy_input_data", version="v0.13.4").load().technologies
>>> techs_usa = [t for t in techs if t.region == "USA"]
>>> def join(values):
...     return ", ".join(sorted({str(v) for v in values} - {"None"}))
>>> df_usa = pd.DataFrame([t.model_dump() for t in techs_usa])
>>> print(
...     df_usa
...     .groupby(["name", "detailed_technology"], as_index=False)
...     .agg(cases=("case", join), years=("year", join))
...     .to_markdown(index=False)
... )
| name                                                  | detailed_technology                                   | cases                                                                      | years                  |
|:------------------------------------------------------|:------------------------------------------------------|:---------------------------------------------------------------------------|:-----------------------|
| Alkaline electrolyzer large size                      | Alkaline electrolyzer large size                      | Advanced - Market, Conservative - Market, Moderate - Market, not_available | 2020, 2030, 2040, 2050 |
| Coal integrated retrofit 90%-CCS                      | Coal integrated retrofit 90%-CCS                      | not_available                                                              | 2030                   |
| Coal integrated retrofit 95%-CCS                      | Coal integrated retrofit 95%-CCS                      | not_available                                                              | 2030                   |
| Coal-95%-CCS                                          | Coal-95%-CCS                                          | not_available                                                              | 2030                   |
| Coal-99%-CCS                                          | Coal-99%-CCS                                          | not_available                                                              | 2030                   |
| Coal-IGCC                                             | Coal-IGCC                                             | not_available                                                              | 2020                   |
| Coal-IGCC-90%-CCS                                     | Coal-IGCC-90%-CCS                                     | not_available                                                              | 2030                   |
| Fischer-Tropsch                                       | Fischer-Tropsch                                       | not_available                                                              | 2020, 2030             |
| NG 2-on-1 Combined Cycle (F-Frame)                    | NG 2-on-1 Combined Cycle (F-Frame)                    | not_available                                                              | 2020, 2030             |
| NG 2-on-1 Combined Cycle (F-Frame) 95% CCS            | NG 2-on-1 Combined Cycle (F-Frame) 95% CCS            | not_available                                                              | 2030                   |
| NG 2-on-1 Combined Cycle (F-Frame) 97% CCS            | NG 2-on-1 Combined Cycle (F-Frame) 97% CCS            | not_available                                                              | 2030                   |
| NG Combined Cycle F-Class integrated retrofit 90%-CCS | NG Combined Cycle F-Class integrated retrofit 90%-CCS | not_available                                                              | 2030                   |
| NG Combined Cycle F-Class integrated retrofit 95%-CCS | NG Combined Cycle F-Class integrated retrofit 95%-CCS | not_available                                                              | 2030                   |
| PEM electrolyzer small size                           | PEM electrolyzer small size                           | Advanced - Market, Conservative - Market, Moderate - Market, not_available | 2020, 2030, 2040, 2050 |
| SOEC                                                  | SOEC                                                  | Advanced - Market, Conservative - Market, Moderate - Market, not_available | 2020, 2030, 2040, 2050 |
| battery inverter                                      | battery inverter                                      | Advanced - Market, Conservative - Market, Moderate - Market, not_available | 2022, 2030, 2040, 2050 |
| battery storage                                       | battery storage                                       | Advanced - Market, Conservative - Market, Moderate - Market, not_available | 2022, 2030, 2040, 2050 |
| direct air capture                                    | direct air capture                                    | Advanced - Market, Conservative - Market, Moderate - Market, not_available | 2020                   |
| hydrogen storage compressor                           | hydrogen storage compressor                           | not_available                                                              | 2020                   |
| hydrogen storage tank type 1                          | hydrogen storage tank type 1                          | not_available                                                              | 2020                   |
```

### Parameters

`entries` counts the technology entries (one per name, case and year) that carry the parameter.

``` py
>>> techs_usa = [t for t in techs if t.region == "USA"]
>>> params = pd.DataFrame(
...     [(key, str(p.units), str(p.carrier)) for t in techs_usa for key, p in t.parameters.items()],
...     columns=["parameter", "units", "carriers"],
... )
>>> print(
...     params.groupby("parameter", as_index=False)
...     .agg(units=("units", join), carriers=("carriers", join), entries=("units", "size"))
...     .to_markdown(index=False)
... )
| parameter                     | units                                                                                            | carriers                                                    |   entries |
|:------------------------------|:-------------------------------------------------------------------------------------------------|:------------------------------------------------------------|----------:|
| FOM                           | percent / year                                                                                   |                                                             |        57 |
| capture_rate                  | percent                                                                                          |                                                             |         9 |
| carbondioxide-input           | metric_ton / megawatt_hour                                                                       | carbon_dioxide / fischer_tropsch                            |         1 |
| compression-electricity-input | dimensionless                                                                                    | electricity / hydrogen                                      |         1 |
| efficiency                    | percent                                                                                          |                                                             |        13 |
| electricity-input             | dimensionless, megawatt_hour / metric_ton                                                        | electricity / carbon_dioxide, electricity / fischer_tropsch |         2 |
| heat-input                    | megawatt_hour / metric_ton                                                                       | thermal / carbon_dioxide                                    |         1 |
| hydrogen-input                | dimensionless                                                                                    | hydrogen / fischer_tropsch                                  |         1 |
| investment                    | USD_2022 / kilowatt, USD_2022 / kilowatt_hour, USD_2022 / megawatt, USD_2023 / hour / metric_ton | 1 / carbon_dioxide, 1 / fischer_tropsch, 1 / hydrogen       |        66 |
| lifetime                      | year                                                                                             |                                                             |        17 |
| min_fill_level                | percent                                                                                          |                                                             |         1 |
```

## Field mapping

| Raw column | Example raw value | Schema field | Example parsed value |
|---|---|---|---|
| `technology` | `Fischer-Tropsch` | `Technology.name`, `Technology.detailed_technology` | `Fischer-Tropsch` |
| `year` | `2020` | `Technology.year` | `2020` |
| `scenario`, `financial_case` | `Moderate`, `Market` | `Technology.case` | `Moderate - Market` |
| — | — | `Technology.region` | `USA` |
| `parameter` | `hydrogen-input` | parameter key | `hydrogen-input` |
| `value` | `1.43` | `Parameter.magnitude` | `1.43` |
| `unit`, `currency_year` | `MWh_H2/MWh_FT`, empty | `Parameter.units`, `.carrier`, `.heating_value` | `dimensionless`, `hydrogen / fischer_tropsch`, `lower_heating_value` |
| `further_description` | `0.995 MWh_H2 per output, …` | `Parameter.note` | same text |
| `source` | `NREL, 2024 ATB Excel Workbook, …` | not kept | |

## Naming conventions

- **Technology names and parameter keys** are kept verbatim from PyPSA technology-data (`FOM`, `investment`, `hydrogen-input`, …), so they match PyPSA naming.
- **Cases**: `"{scenario} - {financial_case}"`, or `scenario` alone; rows without a scenario get `not_available`.
- **Units**: `per unit` is converted to `percent` (value × 100); `currency_year` is folded into the currency (`USD` + `2022` → `USD_2022`).
- **Compound units** such as `MWh_H2/MWh_FT` are split into unit, carrier and heating value by a fixed mapping of nine patterns in `LegacyInputDataV0134Parser._extract_units_carriers_heating_value`; carrier and heating value names are then expanded by the package registries (`H2` → `hydrogen`, `LHV` → `lower_heating_value`).

## Assumptions and deviations from the source

- **Heating value**: all compound energy units are assumed to be on a lower heating value basis; the raw file does not state it.
- **Financial case**: `R&D` and `Market` rows of the same scenario, technology and year are merged, and the case is labelled `- Market`.
  In v0.13.4 both financial cases carry identical values, so no numbers are lost, only the `R&D` label.
- **Region**: entries from `usa.csv` are labelled `USA`, entries from `other.csv` are labelled `Rest of World`.

## Reproduce

Run from the root of a repository checkout.
The parser overwrites the files shipped with the package.

```python
from technologydata import DataAccessor

DataAccessor(data_source="legacy_input_data", version="v0.13.4").parse(
    input_file_name=["usa.csv", "other.csv"],
    num_digits=3,
)
```

With `archive_source=False` (the default) the existing `sources.json` is reused; `archive_source=True` archives the source on the Wayback Machine and rewrites `sources.json`.

## Known limitations

- **Row-level sources are dropped.** Every parameter cites the CSV as a single source; the original reference (NREL ATB 2024, ICCT, JRC-EU-TIMES, Stöckl et al.) is only in the `source` column of the raw file.
- **No archived source**: `sources.json` has no Wayback Machine copy.
- **Sparse coverage**: most technologies outside the NREL ATB have a single year and no scenario (`not_available`).

## Citation

> PyPSA technology-data contributors: technology-data v0.13.4, `inputs/US/manual_input_usa.csv` and `inputs/manual_input.csv`, accessed 2025-10-20. <https://github.com/PyPSA/technology-data/tree/v0.13.4>

License: [CC-BY-4.0](https://creativecommons.org/licenses/by/4.0/); the underlying sources may have their own terms.

Please also cite the underlying sources listed above and `technologydata`, see [Citing](../index.md#citing).

## See also

- [Legacy Input Data Parser](../user_guide/legacy_input_data_parser.md) (user guide) and [API reference](../api/legacy_input_data_parser.md)
- [Data Accessor](../user_guide/data_accessor.md)

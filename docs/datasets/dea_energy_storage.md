---
id: dea_energy_storage
name: DEA Technology Data for Energy Storage
description: Techno-economic data for electricity, heat, gas and hydrogen storage technologies from the Danish Energy Agency.
publisher: Danish Energy Agency
upstream_url: https://ens.dk/media/6589/download
documentation_url: https://ens.dk/media/6588/download
license: CC-BY-4.0
versions: [v10]
region: EU
raw_file: src/technologydata/parsers/raw/Technology_datasheet_for_energy_storage.xlsx
parser: technologydata.parsers.dea_energy_storage.DeaEnergyStorageParser
---

# DEA Technology Data for Energy Storage

<!--
SPDX-FileCopyrightText: technologydata contributors

SPDX-License-Identifier: MIT

-->

The Danish Energy Agency (DEA) technology catalogue for energy storage: costs, efficiencies, lifetimes and capacities for electricity, heat, gas and hydrogen storage technologies, with a central estimate and an uncertainty range for projection years up to 2050.

## At a glance

| | |
|---|---|
| Package key | `dea_energy_storage` |
| Publisher | Danish Energy Agency |
| Original data | [Excel data sheet](https://ens.dk/media/6589/download) ([archived](https://web.archive.org/web/20251008092400/https://ens.dk/media/6589/download)) |
| Documentation | [Technology descriptions (PDF)](https://ens.dk/media/6588/download) |
| License | CC-BY-4.0, attribution to the Danish Energy Agency required |
| Region | `EU` (set by the parser) |
| Years | 2015–2050 |
| Cases | `control` (central estimate), `lower`, `upper` (uncertainty range) |
| Currency | `EUR_2020` |
| Raw format | Excel, sheet `alldata_flat` |
| Parser | [`DeaEnergyStorageParser`](../api/dea_energy_storage_parser.md) |

## Versions

| Version key | Upstream release | Raw file | Parse options | Status |
|---|---|---|---|---|
| `v10` | May 2025, downloaded 2025-10-08 | `Technology_datasheet_for_energy_storage.xlsx` | `num_digits=3`, `filter_params=True` | latest |

## Accessing the data

``` py
>>> from technologydata import DataAccessor
>>> dea = DataAccessor(data_source="dea_energy_storage", version="v10").load()
>>> batteries = dea.technologies.get(name="lithium ion battery", case="control")
>>> [t.year for t in batteries]
[2025, 2030, 2035, 2040, 2050]
>>> print(batteries[0].parameters["specific investment"])
288000.0 EUR_2020 / megawatt_hour
```

See the [tutorial](../tutorial/index.md) for filtering, unit and currency conversion.

## Contents

### Technologies

``` py
>>> import pandas as pd
>>> techs = DataAccessor(data_source="dea_energy_storage", version="v10").load().technologies
>>> def join(values):
...     return ", ".join(sorted({str(v) for v in values} - {"None"}))
>>> print(
...     techs.to_dataframe()
...     .groupby(["name", "detailed_technology"], as_index=False)
...     .agg(cases=("case", join), years=("year", join))
...     .to_markdown(index=False)
... )
| name                        | detailed_technology                                                          | cases                 | years                              |
|:----------------------------|:-----------------------------------------------------------------------------|:----------------------|:-----------------------------------|
| caes                        | compressed air energy storage                                                | control, lower, upper | 2015, 2020, 2030, 2050             |
| flywheels                   | flywheels                                                                    | control, lower, upper | 2018, 2020, 2030, 2050             |
| hydrogen storage - caverns  | hydrogen storage - caverns                                                   | control, lower, upper | 2015, 2020, 2030, 2040, 2050       |
| hydrogen storage - lohc     | hydrogen storage - lohc                                                      | control, lower, upper | 2015, 2020, 2030, 2040, 2050       |
| hydrogen storage - tanks    | pressurized hydrogen gas storage system (compressor & type i tanks @ 200bar) | control, lower, upper | 2019, 2020, 2030, 2040, 2050       |
| large hot water tank        | large-scale hot water tanks (steel)                                          | control, lower, upper | 2015, 2020, 2030, 2040, 2050       |
| lithium ion battery         | lithium-ion battery (utility-scale)                                          | control, lower, upper | 2025, 2030, 2035, 2040, 2050       |
| molten salt carnot battery  | carnot battery                                                               | control, lower, upper | 2025, 2030, 2035, 2040, 2050       |
| na-nicl2 battery            | na-nicl2 battery                                                             | control, lower, upper | 2015, 2020, 2030, 2050             |
| na-s battery                | nas battery                                                                  | control, lower, upper | 2015, 2020, 2030, 2050             |
| ptes seasonal               | pit thermal energy storage [ptes]                                            | control, lower, upper | 2020, 2025, 2030, 2035, 2040, 2050 |
| pumped hydro storage        | pumped hydro storage                                                         | control, lower, upper | 2015, 2020, 2030, 2050             |
| rock-based carnot battery   | carnot battery                                                               | control, lower, upper | 2025, 2030, 2035, 2040, 2050       |
| small scale hot water tank  | small-scale hot water tanks (steel)                                          | control, lower, upper | 2015, 2020, 2030, 2040, 2050       |
| underground storage of gas  | natural gas storage underground                                              | control               | 2020, 2030, 2040, 2050             |
| vanadium redox flow battery | vanadium redox battery (vrb)                                                 | control, lower, upper | 2020, 2025, 2030, 2035, 2040, 2050 |
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
| parameter            | units                                                                                                                                  | carriers   |   entries |
|:---------------------|:---------------------------------------------------------------------------------------------------------------------------------------|:-----------|----------:|
| capacity             | liter, megawatt_hour, meter ** 3                                                                                                       |            |       126 |
| charge efficiency    | percent                                                                                                                                |            |        94 |
| discharge efficiency | percent                                                                                                                                |            |        98 |
| fixed o&m            | EUR_2020 / gigawatt_hour / year, EUR_2020 / megawatt / year, EUR_2020 / megawatt_hour / year, EUR_2020 / year, percent, percent / year |            |       127 |
| specific investment  | EUR_2020 / gigawatt_hour, EUR_2020 / kilowatt, EUR_2020 / kilowatt_hour, EUR_2020 / megawatt, EUR_2020 / megawatt_hour                 |            |       128 |
| technical lifetime   | year                                                                                                                                   |            |       128 |
| variable o&m         | EUR_2020 / megawatt_hour, percent / year                                                                                               |            |       113 |
```

## Field mapping

| Raw column | Example raw value | Schema field | Example parsed value |
|---|---|---|---|
| `ws` | `180 Lithium Ion Battery` | `Technology.name` | `lithium ion battery` |
| `Technology` | `Lithium-ion battery (Utility-scale)` | `Technology.detailed_technology` | `lithium-ion battery (utility-scale)` |
| `year` | `2025` | `Technology.year` | `2025` |
| `est` | `ctrl` | `Technology.case` | `control` |
| — | — | `Technology.region` | `EU` |
| `par` | `Specific investment [MEUR2020/MWh]` | parameter key | `specific investment` |
| `val` | `0.288` | `Parameter.magnitude` | `288000.0` |
| `unit`, `priceyear` | `MEUR/MWh`, `2020` | `Parameter.units` | `EUR_2020 / megawatt_hour` |
| `cat`, `note`, `ref` | | not kept | |

## Naming conventions

- **Technology names** (`ws`, `Technology`): leading three-digit code with optional letter removed, whitespace trimmed, lower-cased (`143a Rock-based Carnot battery` → `rock-based carnot battery`).
- **Parameter keys** (`par`): leading hyphens and bracketed unit text removed, lower-cased (`- Charge efficiency [%]` → `charge efficiency`).
  `energy storage capacity for one unit` and `tank volume of example` are both renamed to `capacity`.
- **Cases** (`est`): `ctrl` → `control`, `Lower`/`Upper` → `lower`/`upper`.
- **Years**: first number in the cell (`Uncertainty (2050)` → `2050`).
- **Units**: made readable by pint, currencies written as `EUR_2020`.
  `MEUR` and `kEUR` are converted to `EUR` with the value scaled accordingly; `pct.` to `percent`, `m3` to `meter**3`, and `⁰C` to `C`.

## Assumptions and deviations from the source

- **Parameter subset**: only 7 parameters are shipped (`filter_params=True`).
  The raw sheet has about 76 distinct parameters, e.g. round trip efficiency, cycle life, energy density, construction time; re-run the parser with `filter_params=False` to get all of them.
- **Region**: every entry is assumed to be valid for Europe (region = `EU`). The sources used by the DEA are not specific enough to only assume Danish conditions.
- **Missing units** are filled from the parameter name, e.g. `fixed o&m` without a unit becomes `percent / year`, `energy storage capacity for one unit` becomes `MWh`.
- **Non-numeric values** and values with comparators (`<1`, `>20,000`) are dropped, as are rows without technology, parameter, value or a four-digit year.
- **Sources**: every parameter cites the catalogue as a whole; the row-level `ref` and `note` columns are dropped.

## Reproduce

Run from the root of a repository checkout.
The parser overwrites the files shipped with the package.

```python
from technologydata import DataAccessor

DataAccessor(data_source="dea_energy_storage", version="v10").parse(
    input_file_name="Technology_datasheet_for_energy_storage.xlsx",
    num_digits=3,
    filter_params=True,
)
```

With `archive_source=False` (the default) the existing `sources.json` is reused; `archive_source=True` re-archives the source on the Wayback Machine and rewrites `sources.json`.

## Known limitations

- **Duplicate parameters are overwritten.** Where a technology reports the same parameter twice in different units, only the last row in the sheet is kept:
  `specific investment` of `caes` (per MWh and per kW, the kept unit varies by year) and `flywheels` (per MW kept, per MWh dropped), and `capacity` of hot water tanks and Carnot batteries (volume kept, energy dropped).
- **Heterogeneous units**: `specific investment`, `fixed o&m` and `capacity` use different reference units across technologies (per MWh, MW, kW, percent of investment, …). Check units before comparing technologies.
- **Rounding before scaling**: values are rounded to `num_digits` in the original unit, before `MEUR`/`kEUR` are converted, so `MEUR` values are precise to 1,000 EUR.

## Citation

> Danish Energy Agency (2025): Technology Data for Energy Storage. <https://ens.dk/media/6589/download>

License: [CC-BY-4.0](https://creativecommons.org/licenses/by/4.0/)

Please also cite `technologydata`, see [Citing](../index.md#citing).

## See also

- [DEA Energy Storage Parser](../user_guide/dea_energy_storage_parser.md) (user guide) and [API reference](../api/dea_energy_storage_parser.md)
- [Data Accessor](../user_guide/data_accessor.md)

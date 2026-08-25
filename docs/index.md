<p align="center">
  <img src="assets/logo/technology_data_logo.png" alt="technologydata Header Logo" width="400"/>
</p>

[![PyPI version](https://img.shields.io/pypi/v/technologydata.svg)](https://pypi.python.org/pypi/technologydata)
[![License: MIT](https://img.shields.io/badge/license-MIT-blue.svg)](https://github.com/open-energy-transition/technology-data/blob/prototype-2/LICENSE)
[![Python](https://img.shields.io/pypi/pyversions/technologydata.svg)](https://pypi.python.org/pypi/technologydata)

# technologydata: techno-economic assumptions for energy models

`technologydata` is a Python package that supports the management of techno-economic assumptions for energy system models. It provides a structured way to store, retrieve, and manipulate data related to various technologies used in energy systems, including unit-ful parameters, currency conversions, inflation adjustment, and temporal modelling.

The goal of this package is to make energy system modelling easier and more efficient, automating common tasks and transformations to reduce errors and allowing for easier data exchange between models.

Techno-economic catalogues are published in different currencies, price years, physical units, heating-value conventions and parameter naming schemes. Combining two of them into one model therefore requires a sequence of conversions that is easy to get wrong and rarely recorded.

The package represents each value as a `Parameter` that carries its unit, currency year, energy carrier, heating-value basis, provenance and bibliographic sources. Conversions act on that object, so currency, inflation, unit and heating-value adjustments are explicit operations rather than manual arithmetic, and dimensionally or semantically invalid combinations raise an error instead of producing a number.

## Installation

```bash
pip install technologydata
```

Or, using [uv](https://docs.astral.sh/uv/):

```bash
uv pip install technologydata
```

The package requires Python 3.12 or newer. The bundled datasets are installed with it; no
additional download step is needed.

## Example

Two independent catalogues report the investment cost of utility-scale lithium-ion battery storage. The Danish Energy Agency publishes it in `EUR_2020` per `MWh` under the parameter name `specific investment`; the US dataset derived from the NREL Annual Technology Baseline publishes it in `USD_2022` per `kWh` under the name `investment`. The following converts both to `USD_2023` per `kWh` so that they can be compared directly.

```python
import pathlib

import technologydata
from technologydata.parsers.data_accessor import DataAccessor

# The bundled catalogues ship inside the installed package.
data = pathlib.Path(technologydata.__file__).parent / "parsers"

dea = DataAccessor(data_source="dea_energy_storage", version="v10", data_path=data).load()
atb = DataAccessor(data_source="manual_input_usa", version="v0.13.4", data_path=data).load()

# The DEA rows carry region "EU", which is not an ISO 3166 alpha-3 code, so the
# country used for the inflation adjustment has to be given explicitly.
eu = dea.technologies.get(
    name="lithium ion battery", case="control",
    region=None, year=None, detailed_technology=None,
).to_currency("USD_2023", source="worldbank", overwrite_country="DEU")

us = atb.technologies.get(
    name="battery storage", case="Moderate - Market",
    region=None, year=None, detailed_technology=None,
).to_currency("USD_2023", source="worldbank")

for t in eu.technologies:
    if t.year == 2030:
        p = t.parameters["specific investment"].to("USD_2023/kWh")
        print(f"DEA v10  {t.year}: {p.magnitude:7.2f} {p.units}")

for t in us.technologies:
    if t.year == 2030:
        p = t.parameters["investment"]
        print(f"NREL ATB {t.year}: {p.magnitude:7.2f} {p.units}")
```

```text
DEA v10  2030:  351.74 USD_2023 / kilowatt_hour
NREL ATB 2030:  264.23 USD_2023 / kilowatt_hour
```

Each converted `Parameter` retains the sources of the value it came from, so the origin of a number remains traceable after conversion. The currency conversion uses exchange-rate and deflator series retrieved through [pydeflate](https://github.com/jm-rivera/pydeflate); the World Bank series is used above and is downloaded on first use.

## What the package provides

- **Unit-ful parameters.** Units are handled with [pint](https://pint.readthedocs.io/), including custom currency units of the form `XYZ_YYYY` (ISO 4217 code and price year, e.g. `USD_2020`). `Parameter.to()` converts between compatible physical units.
- **Currency and inflation adjustment.** `to_currency()` combines exchange-rate conversion and deflation between price years, at parameter, technology and collection level.
- **Heating-value handling.** Parameters can record an `LHV` or `HHV` basis and be converted between them with `change_heating_value()`, using energy densities bundled with the package.
- **Arithmetic with compatibility checks.** Adding parameters with incompatible units, carriers or heating-value bases raises `ValueError` rather than returning a misleading value.
- **Provenance and sources.** Every `Parameter` carries a `provenance` string and a `SourceCollection`. The bundled energy-density constants each carry a citation and an access date.
- **Filtering and export.** `TechnologyCollection.get()` filters by case-insensitive regular expression on name, region, year, case and detailed technology; collections export to `pandas.DataFrame`, CSV and JSON, and reload from JSON.
- **Growth models.** `LinearGrowth` and `ExponentialGrowth` can be fitted to the values of a parameter across years with `fit()` and used to project it to further years with `project()`.

## Bundled datasets

Two parsed catalogues ship with the package, each in a version-pinned directory. The raw source files are shipped alongside them, so the parsed output can be regenerated.

| Data source | Version | Technologies | Distinct names | Region | Currency | Years |
|---|---|---|---|---|---|---|
| `dea_energy_storage` — Danish Energy Agency, *Technology Data for Energy Storage* | `v10` | 136 | 16 | `EU` | `EUR_2020` | 2015–2050 |
| `manual_input_usa` — derived from the NREL Annual Technology Baseline | `v0.13.4` | 85 | 20 | `USA` | `USD_2022`, `USD_2023` | 2020–2050 |

## Frequently asked questions

### How do I add a new data source?

A data source is a package of a name, one or more versioned parsers, and a dispatcher:

1. Add a member to the `DataSourceName` enumeration in `parsers/data_accessor.py`.
2. Add `parsers/<source>/parser_v<version>.py` containing a class that subclasses `ParserBase` and implements its abstract `parse()` method.
3. Add `parsers/<source>/__init__.py` containing a dispatcher class that maps version strings to parser classes and exposes `get_supported_versions()`.
4. Register the dispatcher in `DataAccessor.parse()`.
5. Place the raw input file in `parsers/raw/`. The parser writes the parsed catalogue to `parsers/<source>/<version>/technologies.json`.

### If I use the package today, will the data change when I update the package later?

Datasets are shipped in version-pinned directories — `dea_energy_storage/v10`, `manual_input_usa/v0.13.4` — and are selected with the `version` argument of `DataAccessor`. A new edition of an upstream catalogue is added as a new directory rather than replacing an existing one, so requesting an explicit version continues to return the same data for as long as that directory is shipped. The project does not currently state a policy for how long old versions are retained.

### I would like to get involved, what can I do?

Contributions are welcome. The [Contributing](contributing/instructions.md) section of this documentation describes the development setup and conventions, and `CONTRIBUTING.md` in the repository summarises them. Bug reports and feature proposals are handled through the [issue tracker](https://github.com/open-energy-transition/technology-data/issues).

## Citing

If you use `technologydata` in your research, please cite it as:

```text
technologydata: Data for Energy Systems Models.

The package is available at: https://github.com/open-energy-transition/technology-data/tree/prototype-2.

Authors: Johannes Hampp, Fabrizio Finozzi
```

## License

`technologydata` is released under the [MIT license](home/license.md).

## Contacts

- For **bugs and feature requests**, use the [issue tracker](https://github.com/open-energy-transition/technology-data/issues).
- For **contributions**, open a pull request on [GitHub](https://github.com/open-energy-transition/technology-data). Ideas, suggestions and problem reports are equally welcome as issues.
